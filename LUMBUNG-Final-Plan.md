# LUMBUNG — Final Plan
### AI-Powered Smart Inventory untuk Koperasi Desa Merah Putih

**Versi dokumen:** 1.0
**Fokus utama:** Arsitektur Offline-First + Inventory Decision Engine
**Status:** Final plan untuk eksekusi

---

## 1. Ringkasan Eksekutif

Lumbung adalah platform smart inventory yang dirancang untuk kondisi nyata koperasi desa: **histori penjualan nyaris nol, modal kerja terbatas, pemasok informal, dan internet yang putus-nyambung**.

Tiga keputusan arsitektural yang menentukan seluruh desain:

1. **Offline-first, bukan offline-tolerant.** Perangkat kasir adalah *source of truth* sementara. Server adalah titik konvergensi, bukan prasyarat operasional. Koperasi harus bisa berjualan 30 hari tanpa internet tanpa kehilangan satu transaksi pun.
2. **Keputusan dihitung deterministik, bukan oleh LLM.** Seluruh rekomendasi (ROP, safety stock, alokasi anggaran) dihasilkan algoritma yang dapat diaudit dan **berjalan penuh di perangkat, offline**. AI Agent hanya lapisan penjelasan dan orkestrasi.
3. **Tidak menggantikan SIMKOPDES.** Lumbung masuk sebagai *Technology Provider Member* — server Lumbung yang berbicara dengan sistem nasional, bukan perangkat di desa.

---

## 2. Konteks & Constraint

| Constraint | Implikasi Desain |
|---|---|
| Histori penjualan kosong (koperasi baru) | Cold-start estimation berbasis analog koperasi/desa serupa |
| Permintaan tidak teratur (banyak SKU zero-sales harian) | Intermittent demand forecasting (Croston/SBA), bukan moving average |
| Modal kerja terbatas | Optimasi pembelian sebagai *constrained allocation*, bukan sekadar "isi sampai ROP" |
| Pemasok informal (WhatsApp, tanpa kontrak) | Lead time = variabel acak; registry pemasok dengan skor keandalan |
| Internet tidak stabil | Offline-first penuh (Bagian 4) |
| Literasi digital pengurus bervariasi | One-click decision + penjelasan bahasa awam |
| Perangkat kelas bawah (Android RAM 2–3 GB) | Budget performa & storage ketat |

---

## 3. Prinsip Desain

1. **Local-first**: dataset satu koperasi cukup kecil (ratusan SKU, puluhan ribu transaksi/tahun) untuk direplikasi penuh di perangkat.
2. **Append-only**: mutasi ditulis sebagai *event* immutable, bukan `UPDATE stok SET qty = ...`. Ini yang membuat merge offline mungkin.
3. **Deterministik & reproducible**: input sama → output sama di perangkat mana pun. Tidak ada randomness tanpa seed.
4. **Degradasi bertingkat, bukan blocking**: fitur yang butuh jaringan turun jadi mode antre, bukan tombol mati.
5. **Tidak pernah menghilangkan data secara diam-diam**: operasi yang ditolak server masuk *quarantine* yang terlihat pengurus.
6. **Transparansi angka**: setiap rekomendasi bisa ditelusuri sampai ke asumsi.

---

## 4. OFFLINE-FIRST — DEEP DIVE

### 4.1 Definisi Tingkat Ketersediaan

Bukan semua fitur bisa (atau perlu) offline. Matriks ini adalah kontrak produk:

| Kapabilitas | Offline | Catatan |
|---|---|---|
| Catat penjualan / POS | ✅ Penuh | Wajib. Tidak boleh ada dependensi jaringan sama sekali |
| Terima barang (GRN) & fill rate | ✅ Penuh | Termasuk pencatatan batch & expiry |
| Stock opname & adjustment | ✅ Penuh | |
| Pencatatan lost sales | ✅ Penuh | |
| FEFO allocation | ✅ Penuh | Deterministik berbasis expiry date |
| Forecast (Croston/SBA) | ✅ Penuh | Dihitung on-device |
| ROP + two-variance safety stock | ✅ Penuh | On-device |
| ABC-XYZ + greedy allocation | ✅ Penuh | On-device |
| Deteksi dead stock | ✅ Penuh | |
| Penjelasan rekomendasi | ⚠️ Template | Offline: template rule-based. Online: narasi LLM |
| Draft purchase order | ✅ Penuh | Tersimpan sebagai draft lokal |
| Kirim PO via WhatsApp | ⚠️ Antre | Masuk outbox; fallback: salin teks / share intent |
| Registry pemasok (baca) | ✅ Penuh | Snapshot lokal |
| Update skor pemasok lintas koperasi | ❌ Online | Butuh agregasi server |
| Joint procurement | ❌ Online | Butuh koordinasi multi-koperasi |
| Transfer stok darurat | ❌ Online | Butuh settlement tercatat dua pihak |
| Sinkronisasi SIMKOPDES | ❌ Online | Server-side, tidak menyentuh perangkat |

**Target SLO:** perangkat mampu beroperasi **≥ 30 hari** offline tanpa degradasi fungsi inti dan tanpa kehilangan data.

---

### 4.2 Stack Teknis Klien

**Pilihan: PWA (Next.js) + SQLite WASM (OPFS)**

Alasan:
- PWA menghindari friksi distribusi APK di desa (tidak butuh Play Store, update instan, bisa "Add to Home Screen").
- SQLite di OPFS (Origin Private File System) memberi query relasional penuh untuk perhitungan FEFO, agregasi ledger, dan ABC-XYZ — yang berat kalau dipaksakan ke IndexedDB key-value.
- Service Worker menangani app shell caching (cache-first untuk aset, network-first untuk data non-kritis).

**Fallback:** jika target perangkat termasuk Android WebView lawas tanpa dukungan OPFS, gunakan `wa-sqlite` dengan backend IndexedDB VFS. Deteksi kapabilitas saat instalasi, simpan di `device_profile`.

**Budget performa (perangkat acuan: Android Go, 2 GB RAM):**
- Cold start app shell: < 3 detik
- Catat 1 transaksi (tulis + proyeksi stok): < 150 ms
- Recompute full decision engine 500 SKU: < 4 detik (dijalankan di Web Worker agar UI tidak beku)
- Storage total: < 150 MB

---

### 4.3 Model Data Lokal: Event Log + Projection

Inti yang membuat sinkronisasi offline bisa bekerja: **kuantitas stok tidak pernah disimpan sebagai nilai yang di-overwrite**. Stok adalah hasil *fold* atas ledger.

```
stock_ledger (append-only)
├── id            ULID (client-generated)
├── op_id         UUID idempotency key
├── device_id
├── koperasi_id
├── product_id
├── batch_id      (nullable, untuk FEFO)
├── delta_qty     INTEGER  (+terima, -jual, ±adjustment)
├── reason        ENUM(SALE, RECEIPT, ADJUSTMENT, WASTE, TRANSFER_OUT, TRANSFER_IN, OPNAME)
├── ref_id        (sale_id / grn_id / opname_id)
├── occurred_at   device time (ISO)
├── hlc           hybrid logical clock
├── server_seq    NULL sampai ter-ack
└── created_at
```

**Projection** (tabel turunan, boleh dibangun ulang kapan saja):

```
stock_on_hand (product_id, batch_id) → SUM(delta_qty)
```

Konsekuensi penting: dua perangkat yang offline dan sama-sama mencatat penjualan **tidak menghasilkan konflik**, karena `-3` dan `-2` bersifat komutatif dan asosiatif. Hasil akhir `-5` benar tanpa peduli urutan tiba. Ini pola *G-Counter / PN-Counter* dari keluarga CRDT, diterapkan pada domain yang tepat.

Yang tidak komutatif (nama produk, harga, status PO) ditangani terpisah di 4.6.

---

### 4.4 Identitas & Waktu

**ID:** ULID di-generate klien, dengan prefix device pendek (`{device_short}_{ULID}`). Sortable secara waktu, tidak butuh koordinasi server, praktis bebas kolisi.

**Masalah jam:** perangkat murah di desa sering punya jam salah — bisa meleset berjam-jam bahkan berhari-hari (baterai RTC habis, tidak pernah sync NTP). Ini fatal untuk forecasting (musiman, kalender lokal) dan untuk LWW.

**Solusi: Hybrid Logical Clock (HLC) + dual timestamp.**

```
hlc = (physical_ms, logical_counter, device_id)
```

Setiap event menyimpan:
- `occurred_at_device` — apa yang dilihat pengguna
- `hlc` — untuk pengurutan kausal
- `server_received_at` — diisi server saat sync
- `clock_offset_ms` — selisih jam device vs server, diukur setiap sync

**Aturan:**
- Pengurutan kausal & LWW → pakai **HLC**, tidak pernah wall clock mentah.
- Forecasting & agregasi kalender → pakai **`occurred_at_device` yang dikoreksi** dengan `clock_offset_ms` terdekat.
- Jika `|clock_offset| > 24 jam` terdeteksi saat sync, munculkan banner minta pengurus mengoreksi tanggal perangkat, dan tandai event terdampak `time_suspect = true` agar bisa direkonsiliasi.

---

### 4.5 Protokol Sinkronisasi

**Model: outbox + cursor-based delta sync, pull-then-push.**

```
┌──────────────┐                    ┌──────────────┐
│  Perangkat   │                    │    Server    │
│              │  1. PULL           │              │
│  last_seq=   │ ─────────────────► │  changes     │
│    1204      │ ◄───────────────── │  since=1204  │
│              │  2. Merge lokal    │              │
│              │                    │              │
│  outbox[]    │  3. PUSH ops       │              │
│              │ ─────────────────► │  dedupe by   │
│              │ ◄───────────────── │  op_id       │
│              │  accepted/rejected │  assign seq  │
└──────────────┘                    └──────────────┘
```

**Endpoint:**

```http
GET  /v1/sync/changes?koperasi_id=&since_seq=&limit=500
POST /v1/sync/ops
POST /v1/sync/heartbeat        # ukur clock offset + cek flag remote-wipe
GET  /v1/sync/params?version=  # parameter pack (lihat 4.9)
```

**Payload push (ringkas, field pendek untuk hemat bandwidth):**

```json
{
  "d": "dev_7QK",
  "ops": [
    {"i":"op_01HX...","e":"ledger","t":"create",
     "p":{"pid":"prd_9","b":"bt_3","dq":-2,"r":"SALE","ref":"sl_88"},
     "h":"1723459200000:3:dev_7QK"}
  ]
}
```

**Aturan wajib:**
- **Idempoten**: server punya unique index pada `op_id`. Push ulang setelah timeout aman.
- **Batching**: maksimal 200 ops atau 64 KB per request, mana yang lebih dulu tercapai.
- **Kompresi**: gzip request/response.
- **Target payload sync harian normal**: < 50 KB. Realistis untuk jaringan 2G/EDGE.
- **Backoff eksponensial** dengan jitter: 5s → 15s → 60s → 5m → 15m → 1j (maks).
- **Gambar tidak ikut sync utama** — antrean terpisah, prioritas rendah, hanya jalan saat terdeteksi WiFi/koneksi baik.

**Pemicu sinkronisasi:**
1. Aplikasi dibuka
2. Event `online` + **verifikasi nyata** (ping endpoint ringan — `navigator.onLine` sering berbohong: terhubung WiFi tapi tanpa internet)
3. Periodik tiap 15 menit saat foreground
4. Background Sync API saat tersedia
5. Manual — tombol "Sinkronkan sekarang" (penting untuk rasa kendali pengurus)

**Penanganan penolakan:** ops yang ditolak server (mis. produk sudah dihapus di server) **tidak dibuang**. Masuk tabel `quarantine` dan tampil di layar "Perlu Ditinjau" dengan aksi konkret: Buat produk baru / Petakan ke produk lain / Abaikan.

---

### 4.6 Strategi Resolusi Konflik per Entitas

Ini bagian yang paling sering salah dirancang. Tidak ada satu strategi universal — setiap entitas punya semantik berbeda.

| Entitas | Strategi | Alasan |
|---|---|---|
| `stock_ledger` | **Additive merge** (union of events) | Delta komutatif; tidak ada konflik secara definisi |
| `products` (nama, kategori) | **LWW per-field** via HLC | Edit jarang; granularitas field mengurangi tabrakan |
| `products.harga_jual` | **Server-authoritative** jika ada kebijakan pusat; selain itu LWW per-field | Harga adalah keputusan pengurus, bukan kasir |
| `suppliers` skor keandalan | **Server-computed** | Butuh agregasi lintas koperasi |
| `purchase_orders.status` | **State machine rank** | `draft(0) < sent(1) < confirmed(2) < received(3) < closed(4)` → rank tertinggi menang. Mundur status hanya lewat aksi eksplisit yang membuat event baru |
| `stock_opname` | **Snapshot menang atas ledger sebelum waktunya** | Opname adalah reset otoritatif: sistem menghasilkan event `ADJUSTMENT` sebesar selisih, bukan menimpa ledger |
| Penghapusan | **Tombstone** (`deleted_at` + soft delete) | Delete-vs-update tanpa tombstone menyebabkan resurrection |
| `lost_sales` | Additive | Sama seperti ledger |

**Kasus khusus — opname yang bertabrakan dengan transaksi offline:**
Perangkat A melakukan opname jam 10:00 (stok fisik 40). Perangkat B, offline, mencatat penjualan 5 unit jam 09:30 yang baru masuk jam 11:00.
→ Sistem **tidak** menerapkan penjualan itu ke hasil opname secara buta. Event dengan `occurred_at < opname_at` yang tiba setelah opname ditandai `late_arrival` dan ditampilkan di laporan rekonsiliasi. Stok tetap 40 (opname otoritatif), tetapi penjualan tetap tercatat untuk keperluan forecasting dan laporan keuangan. **Ini pemisahan penting: kebenaran stok fisik ≠ kebenaran catatan penjualan.**

---

### 4.7 Multi-Device dalam Satu Koperasi

Skenario nyata: satu tablet kasir + satu HP pengurus, keduanya offline berhari-hari.

**Risiko utama: oversell.** Perangkat A dan B sama-sama melihat stok 10, masing-masing menjual 7. Total −14 dari stok 10.

Ini **tidak bisa dicegah** tanpa jaringan — hukum fisika distributed system (tidak ada koordinasi tanpa komunikasi). Yang bisa dilakukan adalah **mendeteksi, membatasi dampak, dan merekonsiliasi**:

1. **Toleransi stok negatif** di level data, tidak pernah menolak transaksi penjualan. Barang sudah keluar dari rak secara fisik; menolak mencatat justru merusak data.
2. **Peran perangkat**: tetapkan satu `primary_pos_device` per koperasi. Perangkat lain masuk mode "read + entri terbatas". Ini konvensi operasional, bukan penguncian teknis.
3. **Banner kesegaran data**: "Terakhir sinkron 3 hari lalu — angka stok mungkin belum termasuk transaksi perangkat lain."
4. **Deteksi pasca-merge**: server menandai `negative_stock_event` dan memunculkan tugas "Cek fisik & opname" untuk SKU terdampak.
5. **Confidence downgrade**: rekomendasi pembelian untuk SKU yang stoknya negatif atau `late_arrival`-nya tinggi diturunkan confidence-nya dan diberi label "perlu verifikasi fisik".

---

### 4.8 Offline AI: Pemisahan Compute vs Narasi

Ini keputusan arsitektural terpenting untuk membuat "AI-powered" tetap berguna tanpa internet.

```
┌────────────────────────────────────────────────────┐
│ LAPISAN 1 — DECISION LAYER (100% OFFLINE)          │
│ Croston/SBA · ROP · Two-variance SS · ABC-XYZ ·    │
│ Greedy allocation · FEFO · Dead stock              │
│ → Deterministik, TypeScript murni di Web Worker    │
│ → Output: DecisionResult (JSON terstruktur)        │
└────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────┐
│ LAPISAN 2 — NARRATION LAYER                        │
│ OFFLINE : template rule-based Bahasa Indonesia     │
│ ONLINE  : LLM merangkai narasi + tanya-jawab bebas │
│ → Tidak pernah mengubah angka, hanya menjelaskan   │
└────────────────────────────────────────────────────┘
```

**Kontrak ketat: narration layer tidak boleh menghitung apa pun.** Semua angka datang dari `DecisionResult`. Ini sekaligus menghilangkan risiko halusinasi angka.

**Contoh output offline (template):**

> **Beras Premium 5 kg — Pesan 24 karung**
> Stok sekarang 6 karung. Rata-rata terjual 3,2 karung/hari. Pemasok butuh 4 hari (±1,5 hari).
> Titik pesan ulang: 18 karung → stok Anda sudah di bawah itu.
> Kelas A-X (nilai tinggi, permintaan stabil) → prioritas 1 dari 12 usulan.
> Anggaran terpakai: Rp 2.880.000 dari sisa Rp 5.000.000.

**Contoh output online (LLM):** narasi yang sama, ditambah kemampuan menjawab "kenapa tidak 30 karung?", "bandingkan dengan bulan lalu", "kalau anggaran cuma 3 juta gimana?" — dengan tetap memanggil ulang decision engine lokal untuk skenario what-if.

**Caching:** narasi LLM terakhir untuk setiap rekomendasi disimpan lokal (`explanation_cache`) dan ditampilkan dengan label "dijelaskan pada 8 Agu" jika input belum berubah signifikan (hash dari `DecisionResult`).

---

### 4.9 Parameter Pack & Versioning

Cold-start priors, kalender lokal (Lebaran, gajian, panen), dan koefisien analog koperasi **tidak dihitung di perangkat** — tapi harus tersedia offline.

**Mekanisme:** server menerbitkan *parameter pack* — JSON kecil (< 200 KB) yang di-cache lokal.

```json
{
  "pack_version": "2026.08.01",
  "valid_until": "2026-11-01",
  "calendar": {
    "lebaran_2026": {"date": "2026-03-20", "uplift_window_days": 21},
    "payday": {"days_of_month": [25,26,27,1,2], "uplift": 1.35},
    "panen_padi": {"region": "bali_buleleng", "months": [3,4,8,9], "uplift": 1.15}
  },
  "cold_start_priors": {
    "cluster": "desa_agraris_1500_2500kk",
    "categories": {
      "beras": {"daily_mean": 12.4, "cv": 0.31},
      "minyak_goreng": {"daily_mean": 8.1, "cv": 0.44}
    }
  },
  "service_level_defaults": {"A": 0.95, "B": 0.90, "C": 0.85}
}
```

**Aturan:**
- Perangkat menyimpan **dua versi**: aktif + sebelumnya (untuk rollback jika pack baru bermasalah).
- Setiap `DecisionResult` mencatat `pack_version` yang dipakai → hasil dapat direproduksi dan diaudit.
- Pack kedaluwarsa tidak memblokir perhitungan; sistem menandai "parameter kalender mungkin usang" dan menurunkan confidence.
- Ukuran pack dijaga kecil — dikirim per-cluster koperasi, bukan nasional.

---

### 4.10 Storage, Retensi & Kompaksi

Perangkat murah punya storage terbatas dan pengguna tidak akan mengelolanya. Kompaksi harus otomatis.

**Kebijakan:**

| Data | Retensi lokal penuh | Setelah itu |
|---|---|---|
| `stock_ledger` | 180 hari | Di-*snapshot* jadi saldo awal bulanan; event lama dihapus **hanya jika `server_seq` sudah terisi** (terkonfirmasi tersimpan di server) |
| `sales` + `sale_items` | 180 hari | Diringkas jadi agregat harian per produk (cukup untuk forecasting) |
| `forecast_cache` | 30 hari | Recompute on demand |
| `explanation_cache` | 60 hari | Dibuang, bisa diminta ulang saat online |
| `outbox` | Sampai ter-ack | Tidak pernah dihapus tanpa ack |

**Proses kompaksi:** jalan saat idle (app di-background atau > 5 menit tanpa interaksi), dalam transaksi SQLite tunggal, dengan `PRAGMA wal_checkpoint` setelahnya.

**Guard rail:** jika estimasi storage tersisa < 50 MB, aplikasi menampilkan peringatan dan memaksa kompaksi agresif. Fungsi pencatatan penjualan **tidak pernah diblokir** oleh kondisi storage — jika perlu, ringkas data lain lebih dulu.

---

### 4.11 Keamanan pada Mode Offline

Perangkat berisi data keuangan koperasi dan bisa hilang/dipinjam.

- **Autentikasi offline**: token akses berumur pendek + refresh token panjang (90 hari). Saat offline, verifikasi lokal memakai PIN 6 digit yang di-hash (Argon2id) dan tersimpan di perangkat. Grace period offline: 30 hari; setelah itu wajib sync untuk memperpanjang.
- **Enkripsi at-rest**: kunci diturunkan dari PIN via PBKDF2/Argon2 + salt per-device, disimpan di WebCrypto non-extractable key. Database SQLite terenkripsi.
- **Auto-lock**: 5 menit idle.
- **Remote wipe**: flag dievaluasi setiap heartbeat sync. Jika perangkat dilaporkan hilang, sync berikutnya memicu penghapusan lokal — tetapi **hanya setelah outbox berhasil dikirim**, agar transaksi tidak ikut hilang.
- **Audit trail**: setiap event membawa `device_id` + `user_id`. Tidak bisa dihapus, hanya bisa dikoreksi lewat event baru.
- **Prinsip data minimum**: perangkat hanya menyimpan data koperasinya sendiri. Data lintas koperasi (joint procurement, skor pemasok agregat) tidak pernah direplikasi ke perangkat.

---

### 4.12 UX Mode Offline

Prinsip: **pengguna harus selalu tahu status data, tanpa merasa aplikasinya rusak.**

**Indikator status (selalu terlihat di header):**

| Status | Tampilan | Perilaku |
|---|---|---|
| Tersinkron | ● Hijau — "Tersinkron" | Normal |
| Offline < 24 jam | ● Kuning — "Offline · 5 jam" | Normal, tanpa peringatan |
| Offline 1–7 hari | ● Oranye — "Offline · 3 hari · 47 transaksi menunggu" | Rekomendasi diberi label "berdasarkan data lokal" |
| Offline > 7 hari | ● Merah — "Perlu sinkron" | Confidence rekomendasi diturunkan; joint procurement disembunyikan |
| Sedang sinkron | ● Berputar — "Menyinkronkan 47/120" | Progress terlihat |
| Ada quarantine | ● Merah + badge angka | Tugas "Perlu Ditinjau" muncul di beranda |

**Aturan UI:**
- Tombol yang butuh jaringan **tidak pernah disabled**. Diubah labelnya: "Kirim WhatsApp" → "Antre kirim WhatsApp (1 menunggu)".
- Setiap angka stok menampilkan waktu segar data jika > 24 jam.
- Tidak ada spinner tak berujung. Setiap operasi lokal selesai instan; operasi jaringan langsung masuk antrean.

---

### 4.13 Antrean Aksi Eksternal (WhatsApp)

PO yang disetujui offline masuk `action_outbox`:

```
action_outbox
├── id, type=WHATSAPP_PO
├── payload  (nomor tujuan, teks pesan, po_id)
├── status   PENDING | SENT | FAILED | CANCELLED
├── attempts, next_retry_at
└── approved_by, approved_at
```

**Tiga jalur, berurutan:**
1. **Online** → kirim via WhatsApp Business API, status `SENT` dengan bukti message_id.
2. **Offline** → pesan tetap dihasilkan dan dapat **disalin manual** atau dibagikan lewat share intent Android (pengurus bisa mengirim sendiri saat kebetulan dapat sinyal). Sistem menandai `SENT_MANUAL`.
3. **Gagal berulang** (> 5 kali) → eskalasi jadi tugas di beranda: "PO #124 belum terkirim ke Pak Wayan".

**Anti-duplikasi:** PO membawa nomor unik dan hash konten. Jika pengurus sudah kirim manual lalu perangkat online, sistem menanyakan konfirmasi sebelum mengirim otomatis — **tidak pernah mengirim ulang secara diam-diam** (risiko pesanan ganda ke pemasok adalah kerugian nyata).

---

### 4.14 Observability

**Di perangkat (untuk pengurus):**
Layar "Kesehatan Data" — terakhir sinkron, jumlah transaksi menunggu, item quarantine, sisa storage, selisih jam perangkat.

**Di server (untuk tim Lumbung):**

| Metrik | Target |
|---|---|
| Sync success rate | > 98% |
| Median durasi offline per koperasi | Dipantau per wilayah |
| P95 latensi sync (100 ops) | < 8 detik pada 3G |
| Rasio ops quarantine | < 0,5% |
| Insiden stok negatif per koperasi/bulan | < 2 |
| Koperasi tanpa sync > 14 hari | Trigger outreach lapangan |
| Rata-rata payload sync harian | < 50 KB |

---

### 4.15 Failure Mode & Rencana Pengujian

| Failure mode | Mitigasi | Uji |
|---|---|---|
| Aplikasi dimatikan saat menulis | Transaksi SQLite atomik; WAL mode | Kill process saat write loop |
| `navigator.onLine` bohong (WiFi tanpa internet) | Verifikasi lewat ping endpoint ringan | Simulasi captive portal |
| Jam perangkat mundur 3 hari | HLC + `clock_offset`; flag `time_suspect` | Uji dengan set tanggal manual |
| Outbox membengkak (30 hari offline) | Batching + kompresi + resume per-batch | Uji sync 5.000 ops di 2G |
| Sync terputus di tengah | Cursor-based, resume dari `last_seq` | Putus koneksi acak tiap 3 detik |
| Storage penuh | Kompaksi agresif; POS tidak pernah diblokir | Isi storage sampai 95% |
| Dua perangkat oversell | Toleransi negatif + tugas opname | Matriks konflik dua-perangkat |
| Server down saat push | Backoff + idempotency | Chaos: server 503 selama 1 jam |
| Pack parameter korup | Rollback ke versi sebelumnya + checksum | Inject pack rusak |

**Suite pengujian wajib sebelum rilis:**
- **30-day offline soak test**: perangkat offline 30 hari simulasi (500 transaksi/hari), lalu sync — verifikasi zero data loss dan konsistensi saldo.
- **Two-device conflict matrix**: 20 kombinasi operasi bersamaan, verifikasi konvergensi.
- **Network chaos**: latensi 2.000 ms, packet loss 30%, bandwidth 50 kbps.
- **Convergence property test**: N perangkat, urutan sync acak → semua perangkat harus mencapai state identik (uji berbasis properti, bukan contoh).

---

## 5. Inventory Decision Engine

Seluruh bagian ini berjalan **on-device**, deterministik, dan reproducible.

### 5.1 Cold-Start Demand Estimation

Untuk koperasi tanpa histori, gunakan *shrinkage* terhadap prior dari koperasi analog:

```
d̂ = w · d_observed + (1 − w) · d_prior
w = n / (n + k),   k = 21   (n = jumlah hari data tersedia)
```

- Hari ke-0: sepenuhnya prior.
- Hari ke-21: bobot 50/50.
- Hari ke-90: prior praktis hilang (w ≈ 0,81).

Prior dipilih dari cluster: jumlah KK desa, jenis mata pencaharian dominan, jarak ke pasar/kota, dan kategori produk. Bersumber dari `parameter pack` (4.9).

### 5.2 Intermittent Demand Forecasting

Croston dengan koreksi Syntetos-Boylan (SBA) untuk SKU dengan banyak hari nol:

```
Jika terjadi permintaan:
  z_t = α·y_t + (1−α)·z_{t−1}      (ukuran permintaan)
  p_t = α·q  + (1−α)·p_{t−1}       (interval antar permintaan)
  q = 1
Jika tidak: q += 1

d̂_SBA = (1 − α/2) · z_t / p_t
```

α = 0,1–0,2. Pemilihan metode otomatis berdasarkan ADI (average demand interval) dan CV²:

| ADI | CV² | Klasifikasi | Metode |
|---|---|---|---|
| < 1,32 | < 0,49 | Smooth | SES / moving average |
| ≥ 1,32 | < 0,49 | Intermittent | Croston |
| < 1,32 | ≥ 0,49 | Erratic | SES + safety stock lebih tebal |
| ≥ 1,32 | ≥ 0,49 | Lumpy | SBA + confidence rendah |

**Pengayaan kalender lokal:** hasil forecast dikalikan faktor uplift dari `parameter pack` untuk jendela Lebaran, gajian, dan musim panen — diterapkan per kategori, bukan global.

### 5.3 Reorder Point & Two-Variance Safety Stock

```
SS  = z · √( L̄ · σ_d²  +  d̄² · σ_L² )
ROP = d̄ · L̄ + SS
```

- `σ_L` diambil dari registry pemasok (variabilitas lead time aktual, bukan janji pemasok).
- `z` mengikuti service level per kelas ABC: A = 95%, B = 90%, C = 85%.
- Untuk SKU lumpy, `σ_d` dihitung dari distribusi empiris, bukan asumsi normal.

### 5.4 Optimasi Kuantitas Pembelian

```
Q_ideal = ROP + review_period · d̄ − stok_saat_ini − on_order
Q_moq   = ceil(Q_ideal / MOQ) · MOQ
Q_final = min(Q_moq, kapasitas_rak − stok_saat_ini)
```

Untuk produk perishable, tambahan batas: `Q ≤ d̄ × shelf_life_hari × 0,7` (menghindari pembelian yang pasti kedaluwarsa).

### 5.5 Prioritas ABC-XYZ & Alokasi Greedy

**ABC** berdasarkan nilai konsumsi tahunan (Pareto 80/15/5).
**XYZ** berdasarkan CV permintaan (X < 0,5; Y 0,5–1,0; Z > 1,0).

**Skor prioritas:**

```
score = (nilai_penjualan_harian × bobot_kelas × risiko_stockout) / biaya_pesan
risiko_stockout = 1 − (stok_saat_ini / ROP),  di-clamp ke [0,1]
```

Bobot kelas: AX = 1,0 · AY = 0,9 · AZ = 0,7 · BX = 0,8 · … · CZ = 0,2. Barang pokok (sembako) mendapat *floor* prioritas agar tidak pernah kalah oleh barang bernilai tinggi non-esensial.

**Alokasi greedy** terhadap anggaran:

```
urutkan usulan by score desc
untuk setiap usulan:
    jika biaya ≤ sisa_anggaran:  terima penuh
    lain jika bisa dikurangi ke kelipatan MOQ yang muat: terima sebagian
    lain: tandai "ditunda — anggaran"
```

Ditampilkan sebagai dua daftar: **"Beli sekarang"** dan **"Tunda"** — dengan alasan eksplisit pada setiap item yang ditunda.

### 5.6 FEFO, Dead Stock, Lost Sales, Fill Rate

- **FEFO**: alokasi batch diurutkan `expiry_date ASC, batch_id ASC` (tie-break deterministik agar semua perangkat menghasilkan alokasi identik). Peringatan bertingkat: 30 / 14 / 7 hari sebelum kedaluwarsa, dengan usulan diskon.
- **Dead stock**: tidak ada penjualan ≥ 60 hari **dan** stok > 30 hari kebutuhan → usul markdown / retur / transfer.
- **Lost sales**: satu ketukan saat pelanggan mencari barang kosong. Data ini krusial — tanpa itu forecast belajar dari permintaan yang tersensor dan terus meremehkan kebutuhan.
- **Fill rate**: dicatat saat penerimaan (`qty_diterima / qty_dipesan`) → masuk skor keandalan pemasok → memengaruhi `σ_L` dan pemilihan pemasok berikutnya.

### 5.7 Registry Pemasok

```
supplier_score = 0,4·fill_rate + 0,3·ketepatan_lead_time
               + 0,2·stabilitas_harga + 0,1·kualitas
```

Dievaluasi dari transaksi aktual, bukan input manual. Ditampilkan sebagai peringkat sederhana (⭐1–5) dengan rincian yang bisa dibuka.

---

## 6. Integrasi SIMKOPDES

**Posisi:** Lumbung sebagai *Technology Provider Member* — pelengkap, bukan pengganti.

```
Perangkat Desa ──► Server Lumbung ──► Adapter SIMKOPDES ──► Sistem Nasional
   (offline-first)     (agregasi)        (mapping+antrean)
```

**Prinsip:**
- Perangkat **tidak pernah** berbicara langsung ke SIMKOPDES. Ketersediaan sistem nasional tidak boleh memengaruhi operasional kasir di desa.
- Adapter memetakan skema Lumbung ke format SIMKOPDES, dengan antrean dan retry sendiri.
- Arah data: Lumbung → SIMKOPDES untuk pelaporan persediaan & transaksi; SIMKOPDES → Lumbung untuk master data koperasi & katalog produk terstandar (jika tersedia).
- Rekonsiliasi terjadwal harian, dengan laporan selisih yang dapat ditinjau.

---

## 7. Fitur Lanjutan

### 7.1 Joint Procurement
Menggabungkan permintaan beberapa koperasi untuk mencapai tier harga grosir.
- Jendela agregasi (mis. setiap Senin), minimum partisipan, komitmen mengikat setelah deadline.
- Alokasi biaya proporsional; penunjukan koperasi *lead* untuk penerimaan.
- **Sepenuhnya online** — perangkat menampilkan status terakhir yang ter-cache.

### 7.2 Transfer Stok Darurat
Untuk barang pokok non-perishable antar koperasi berdekatan.
- Hanya untuk SKU yang ditandai esensial; koperasi pemberi harus tetap di atas safety stock-nya.
- Settlement terdokumentasi: harga transfer = harga perolehan + biaya angkut, dicatat sebagai piutang/utang antar koperasi.
- Butuh persetujuan dua pihak → online, dengan event `TRANSFER_OUT` / `TRANSFER_IN` yang berpasangan.

---

## 8. Roadmap

| Fase | Durasi | Cakupan | Definition of Done |
|---|---|---|---|
| **F0 — Fondasi** | Bulan 1–2 | Skema event log, SQLite OPFS, outbox, protokol sync, autentikasi offline | 30-day offline soak test lulus, zero data loss |
| **F1 — MVP Operasional** | Bulan 2–4 | POS, penerimaan barang, FEFO, opname, lost sales, laporan dasar | 3 koperasi pilot berjalan 4 minggu |
| **F2 — Decision Engine** | Bulan 4–6 | Cold-start, Croston/SBA, ROP+SS, ABC-XYZ, greedy allocation, parameter pack | Rekomendasi dihasilkan offline; akurasi forecast diukur vs baseline |
| **F3 — AI Agent & PO** | Bulan 6–8 | Narasi template + LLM, draft PO, WhatsApp outbox, registry pemasok | Pengurus menyetujui ≥ 60% rekomendasi tanpa perubahan |
| **F4 — SIMKOPDES** | Bulan 8–10 | Adapter, mapping, rekonsiliasi | Pelaporan otomatis diterima sistem nasional |
| **F5 — Jaringan** | Bulan 10–14 | Joint procurement, transfer darurat | ≥ 5 koperasi dalam satu klaster bertransaksi bersama |

---

## 9. KPI Keberhasilan

**Teknis**
- Zero data loss pada seluruh skenario offline
- Sync success rate > 98%
- Konvergensi penuh antar perangkat < 5 menit setelah online

**Dampak operasional (6 bulan pasca-implementasi)**
- Stockout barang pokok turun ≥ 40%
- Dead stock turun ≥ 30%
- Perputaran persediaan naik ≥ 25%
- Waktu penyusunan pesanan: dari ~2 jam menjadi < 10 menit
- Nilai kedaluwarsa terbuang turun ≥ 50%

**Adopsi**
- ≥ 80% transaksi tercatat di sistem (bukan di buku)
- ≥ 60% rekomendasi disetujui tanpa modifikasi
- Retensi koperasi aktif > 85% pada bulan ke-6

---

## 10. Risiko Utama

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Pengurus kembali ke pencatatan manual | Tinggi | POS harus lebih cepat dari menulis di buku; pelatihan pendampingan; ukur waktu per transaksi |
| Prior cold-start meleset jauh | Sedang | Shrinkage cepat (k=21); confidence ditampilkan; pengurus bisa override dengan alasan tercatat |
| Lost sales tidak dicatat | Tinggi | Satu ketukan; muncul otomatis saat stok = 0 saat pencarian produk |
| Perangkat hilang/rusak | Sedang | Sync rutin; remote wipe; prosedur pemulihan dari server |
| Oversell akibat multi-device | Sedang | Peran primary device; deteksi + tugas opname |
| Pemasok informal tak konsisten | Sedang | Registry skor; usul pemasok alternatif otomatis |
| Ketergantungan pada WhatsApp API | Sedang | Fallback manual share/copy selalu tersedia |
| Perubahan kebijakan SIMKOPDES | Sedang | Adapter terisolasi; inti sistem tidak bergantung padanya |

---

## Lampiran A — Skema Tabel Lokal (ringkas)

```sql
-- Append-only
stock_ledger(id, op_id, device_id, product_id, batch_id, delta_qty,
             reason, ref_id, occurred_at, hlc, server_seq, time_suspect)
sales(id, op_id, total, payment_method, occurred_at, hlc, server_seq)
sale_items(id, sale_id, product_id, batch_id, qty, unit_price)
lost_sales(id, product_id, qty_estimated, occurred_at, hlc)
receipts(id, po_id, supplier_id, received_at, fill_rate)
receipt_items(id, receipt_id, product_id, batch_id, qty_ordered, qty_received, expiry_date)

-- Mutable (LWW per-field)
products(id, name, category, unit, cost_price, sell_price,
         moq, shelf_capacity, is_essential, is_perishable, shelf_life_days,
         _fields_hlc JSON, deleted_at)
suppliers(id, name, phone, lead_time_mean, lead_time_sd, score, _fields_hlc, deleted_at)
purchase_orders(id, supplier_id, status, status_rank, total, created_at, _fields_hlc)

-- Derived (rebuildable)
stock_on_hand(product_id, batch_id, qty, updated_at)
forecast_cache(product_id, method, d_mean, d_sd, adi, cv2, computed_at, pack_version)
decision_cache(product_id, rop, safety_stock, qty_suggested, class_abc, class_xyz,
               priority_score, confidence, computed_at, pack_version)

-- Sistem
outbox(op_id, entity, type, payload, attempts, next_retry_at, created_at)
action_outbox(id, type, payload, status, attempts, next_retry_at, approved_by)
quarantine(op_id, payload, reject_reason, created_at, resolved_at)
sync_state(koperasi_id, last_pulled_seq, last_sync_at, clock_offset_ms)
param_pack(version, payload, valid_until, is_active)
explanation_cache(decision_hash, text, generated_at, source)
```

## Lampiran B — Alur Sinkronisasi (pseudocode)

```ts
async function sync(): Promise<SyncResult> {
  if (!(await hasRealConnectivity())) return { skipped: 'offline' };

  const state = await getSyncState();

  // 1. PULL — server lebih dulu, agar push berjalan di atas state terbaru
  let cursor = state.last_pulled_seq;
  while (true) {
    const res = await api.getChanges(cursor, 500);
    await db.transaction(async () => {
      for (const change of res.changes) await mergeChange(change);
      await setLastPulledSeq(res.next_seq);
    });
    cursor = res.next_seq;
    if (!res.has_more) break;
  }

  // 2. PUSH — batched, idempoten
  for (const batch of chunk(await getOutbox(), 200)) {
    const res = await api.pushOps(batch);
    await db.transaction(async () => {
      await ackOps(res.accepted);          // hapus dari outbox, isi server_seq
      await quarantineOps(res.rejected);   // simpan, jangan buang
    });
  }

  // 3. Kalibrasi jam + parameter pack
  await calibrateClock();
  await refreshParamPackIfStale();

  // 4. Bangun ulang proyeksi & jalankan decision engine
  await rebuildProjections();
  await runDecisionEngine();               // di Web Worker

  return { ok: true, at: now() };
}
```

## Lampiran C — Contoh `DecisionResult`

```json
{
  "product_id": "prd_beras_premium_5kg",
  "computed_at": "2026-08-10T07:12:00+08:00",
  "pack_version": "2026.08.01",
  "inputs": {
    "stock_on_hand": 6,
    "on_order": 0,
    "demand_mean_daily": 3.2,
    "demand_sd_daily": 1.1,
    "lead_time_mean_days": 4.0,
    "lead_time_sd_days": 1.5,
    "method": "SBA",
    "data_days": 47,
    "cold_start_weight": 0.31
  },
  "outputs": {
    "safety_stock": 5.4,
    "reorder_point": 18.2,
    "qty_ideal": 22.6,
    "qty_after_moq": 24,
    "qty_final": 24,
    "class_abc": "A",
    "class_xyz": "X",
    "priority_rank": 1,
    "priority_score": 8.74,
    "budget_used": 2880000,
    "confidence": 0.82,
    "flags": ["below_rop"]
  },
  "constraints_applied": ["MOQ=6", "shelf_capacity=40", "budget_remaining=5000000"]
}
```

---

*Dokumen ini adalah rencana final. Perubahan pada bagian offline-first (4.3–4.7) harus melalui review arsitektur, karena berdampak langsung pada integritas data lapangan.*
