# LUMBUNG
## AI Replenishment Copilot untuk Growing Independent Retailers

**Versi:** 2.0  
**Kategori AIC:** Smart Commerce  
**Status:** Basis proposal kompetisi, belum merupakan laporan hasil pilot  
**Janji produk:** Lumbung membantu owner menentukan produk yang perlu dibeli, jumlahnya, dan prioritasnya saat modal kulakan terbatas.

---

## 1. Ringkasan Eksekutif

Toko kelontong besar dan minimarket independen mengelola ratusan hingga ribuan SKU, beberapa pemasok, jadwal kunjungan sales, stok yang berubah setiap hari, dan modal kerja yang terbatas. Banyak software kasir sudah mencatat penjualan, stok, purchase order, dan batas stok minimum. Namun, owner tetap harus mengubah catatan tersebut menjadi keputusan kulakan: SKU mana yang perlu dibeli sekarang, berapa jumlahnya, dan SKU mana yang harus ditunda ketika anggaran tidak cukup.

Lumbung dirancang sebagai **AI replenishment copilot** yang bekerja di atas data toko yang sudah ada. Pengguna mengunggah satu file snapshot berisi histori penjualan, stok, harga beli, lead time, minimum order quantity, dan anggaran. Lumbung menghasilkan daftar **Beli Sekarang** dan **Tunda**, lengkap dengan jumlah, nilai belanja, risiko kehabisan stok, alasan, dan tingkat keyakinan.

Core inference Lumbung terdiri dari dua tahap yang dapat diaudit:

1. model probabilistik memperkirakan kebutuhan setiap SKU selama lead time dan review period;
2. optimizer memilih kombinasi pembelian yang memberi perlindungan stok terbesar di bawah batas anggaran dan kelipatan pembelian.

Versi ini sengaja tidak membangun POS, sistem sinkronisasi offline, autentikasi, jaringan koperasi, joint procurement, SIMKOPDES, chatbot, atau arsitektur terdistribusi. Scope tersebut tidak diperlukan untuk membuktikan keputusan inti pada babak penyisihan AIC.

---

## 2. Keputusan Produk

### 2.1 Target customer final

**Segmen awal yang dipilih:**

> Growing independent grocery retailers: minimarket independen, warung besar, dan toko kelontong modern yang memiliki banyak SKU, sudah mencatat transaksi secara digital atau dapat mengekspor CSV, tetapi belum memiliki inventory planner atau sistem demand planning.

**Profil operasional untuk rekrutmen pilot:**

| Dimensi | Kriteria seleksi awal | Status bukti |
|---|---|---|
| Bentuk usaha | Toko kelontong besar atau minimarket independen | Keputusan segmentasi |
| Cabang | 1-3 outlet | Hipotesis pilot, perlu validasi |
| Kompleksitas katalog | Sekitar 300-3.000 SKU aktif | Ambang screening yang diusulkan, bukan statistik nasional |
| Data | Minimal 3-6 bulan transaksi POS/CSV dan stok terkini | Syarat teknis model |
| Pengambil keputusan | Owner atau store manager memilih pembelian | Didukung studi kasus, perlu wawancara tambahan |
| Pemasok | Beberapa pemasok dengan jadwal dan MOQ berbeda | Hipotesis operasional |
| Constraint utama | Modal kulakan membatasi daftar pembelian | Hipotesis nilai, wajib diuji |

**User utama:** owner atau store manager.  
**Buyer:** owner.  
**Penerima manfaat lain:** staf pembelian dan kasir yang menyiapkan daftar stok.

### 2.2 Alasan memilih segmen ini

Empat sumber memberi dasar yang cukup untuk memilih segmen pilot, meski belum membuktikan product-market fit:

- Kajian Bank Indonesia terhadap 304 UMKM menemukan 58,22% responden belum melakukan pencatatan keuangan formal. Temuan ini menunjukkan hambatan digitalisasi masih besar, tetapi juga berarti Lumbung tidak cocok untuk seluruh UMKM karena model memerlukan data transaksi yang konsisten. [[Bank Indonesia](https://www.bi.go.id/id/publikasi/kajian/Documents/Kajian-Inovasi-Model-Bisnis-Pembiayaan-Digital-Kepada-UMKM.pdf)]
- Studi IPB tahun 2024 pada BunHen Mart menemukan catatan persediaan belum terstruktur, dokumen belum lengkap, dan terdapat rangkap jabatan. Kondisi ini menunjukkan kebutuhan perbaikan proses pada minimarket independen, sekaligus risiko kualitas data yang harus disaring sebelum adopsi. [[IPB University](https://repository.ipb.ac.id/handle/123456789/154621)]
- Studi pada Minimarket Lok Jaya melaporkan bahwa toko menggunakan POS dan kartu stok, lalu owner memeriksa perputaran persediaan setiap hari dan menentukan restock berdasarkan jadwal kunjungan sales. Kasus ini mendukung peluang decision layer setelah pencatatan digital tersedia. [[Journal of Economics and Business UBS](https://jurnal.ubs-usg.ac.id/index.php/joeb/article/download/228/506)]
- Kementerian Perdagangan mencatat komunitas SRC memiliki lebih dari 243 ribu toko anggota pada 2023. Angka tersebut menunjukkan adanya kanal komunitas ritel tradisional yang besar, tetapi tidak boleh diperlakukan sebagai ukuran pasar Lumbung karena tidak semua anggota memenuhi syarat data dan kompleksitas. [[Ditjen Perdagangan Dalam Negeri](https://ditjenpdn.kemendag.go.id/berita/direktur-jenderal-perdagangan-dalam-negeri-bapak-isy-karim-memberikan-sambutan-pada-acara-sampoerna-retail-community-src-ngobrol-bareng-umkm-maju-untuk-indonesia-jadilebihbaik)]

### 2.3 Segmen yang tidak diprioritaskan

| Segmen | Alasan tidak menjadi beachhead |
|---|---|
| Warung mikro dengan sedikit SKU dan pencatatan manual | Biaya input data dapat melebihi manfaat rekomendasi. Owner juga dapat mengingat katalog kecil tanpa model. |
| Jaringan ritel besar | Mereka lebih mungkin memiliki ERP, replenishment rules, tim perencana, dan proses integrasi enterprise. Siklus penjualan terlalu panjang untuk MVP kompetisi. |
| KDKMP atau koperasi desa baru | Dokumen awal mengasumsikan cold start, internet buruk, SIMKOPDES, dan jaringan antarkoperasi. Belum ada bukti lapangan dalam materi sumber yang menunjukkan KDKMP sebagai pengguna paling membutuhkan atau siap mengadopsi. |
| Restoran dan warteg | Mereka menghadapi perishability dan recipe-level inventory yang berbeda. Problem valid, tetapi menambah kebutuhan bill of materials dan waste tracking. |

**Kesimpulan segmentasi:** Lumbung tidak lagi berfokus pada KDKMP. Koperasi dapat menjadi ekspansi jika tim memperoleh bukti kesiapan data, proses pembelian, dan willingness-to-pay.

---

## 3. Real User Problem

### 3.1 Job to be done

> Saat saya menyiapkan kulakan, bantu saya membagi anggaran ke SKU yang paling perlu dibeli agar barang penting tidak habis dan uang tidak tertahan di stok lambat.

### 3.2 Alur kerja saat ini

Owner biasanya menggabungkan beberapa sinyal:

- kartu stok atau laporan POS;
- ingatan tentang produk cepat laku;
- stok fisik di rak dan gudang;
- jadwal sales atau pemasok;
- harga beli, kelipatan dus, dan uang yang tersedia.

Software pencatatan membantu owner melihat data. Keputusan pembelian masih memerlukan perbandingan banyak SKU dengan horizon lead time yang berbeda. Accurate, misalnya, dapat membuat purchase order dari daftar barang yang berada di bawah minimum stok. Moka, Majoo, dan Olsera menyediakan pencatatan stok, supplier, purchase order, stock opname, atau peringatan stok. Sumber publik ini membuktikan bahwa kategori inventory software sudah ramai. Sumber tersebut tidak cukup untuk memastikan apakah setiap produk memiliki rekomendasi probabilistik yang dibatasi anggaran. Proposal ini tidak mengklaim fitur kompetitor yang tidak dapat diverifikasi. [[Accurate](https://help.accurate.id/product/accurate-online/fitur-aol/persediaan/barang-stok-minimum/stok-minimum-po/)] [[Moka](https://www.mokapos.com/manajemen-stok)] [[Majoo](https://majoo.id/prime/retail)] [[Olsera](https://www.olsera.com/id/feature)]

### 3.3 Problem statement

Growing independent retailers perlu membuat keputusan replenishment lintas banyak SKU, tetapi tools yang mereka gunakan sering berhenti pada pencatatan, peringatan batas stok, atau formulir purchase order. Static minimum stock juga tidak menyesuaikan pola permintaan, lead time, musim, dan keterbatasan anggaran pada setiap siklus pembelian.

Akibat yang perlu dibuktikan dalam pilot:

- produk cepat laku habis sebelum pemasok datang;
- modal tertahan pada SKU yang bergerak lambat;
- owner menghabiskan waktu meninjau SKU satu per satu;
- keputusan berubah menurut intuisi orang yang bertugas;
- purchase order tidak mencerminkan prioritas risiko ketika anggaran terbatas.

### 3.4 Evidence gap yang wajib ditutup

Desk research belum menjawab pertanyaan berikut:

1. Berapa lama owner menyiapkan satu rencana kulakan?
2. Berapa kali dalam sebulan mereka menunda SKU karena uang tidak cukup?
3. Data mana yang tersedia dan cukup akurat: sales, stock on hand, stock adjustment, purchase price, lead time, atau lost sales?
4. Apakah keputusan dibuat per kunjungan sales, per pemasok, atau dalam satu rencana lintas pemasok?
5. Berapa biaya yang bersedia dibayar setelah Lumbung membuktikan penghematan?

Proposal harus menyebut temuan wawancara sebagai hasil hanya setelah tim melakukan wawancara, observasi, atau pilot dan menyimpan bukti.

---

## 4. Solusi

### 4.1 Konsep produk

Lumbung menerima satu file `store_snapshot.csv` dan menghasilkan rencana pembelian yang dapat langsung ditinjau owner.

**Input minimum:**

```text
date, sku_id, category, sales_qty, stock_on_hand, on_order,
unit_cost, unit_margin, lead_time_days, moq, available_budget
```

`available_budget` merupakan nilai tingkat toko yang diulang di setiap baris agar MVP tetap memakai satu aksi input: unggah satu file.

**Output utama:**

```text
ANGGARAN TERSEDIA: Rp5.000.000
USULAN BELANJA:    Rp4.860.000

BELI SEKARANG
Indomie Goreng   4 dus   Risiko stockout tinggi sebelum pemasok datang
Minyak 1 L       2 dus   Stok di bawah kebutuhan P90 selama lead time
Aqua 600 ml      3 dus   Penjualan naik dan rasio perlindungan/rupiah tinggi

TUNDA
Biskuit A        Stok masih menutup 18 hari
Sirup B          Risiko rendah dalam horizon pembelian
Snack C          Kalah prioritas di bawah batas anggaran
```

### 4.2 User flow penyisihan

1. Pengguna membuka aplikasi lokal.
2. Pengguna mengunduh template atau memilih contoh data.
3. Pengguna mengunggah satu file snapshot.
4. Backend memvalidasi skema dan menjalankan inference.
5. UI menampilkan rencana Beli Sekarang dan Tunda.
6. Pengguna membuka alasan per SKU dan mengunduh hasil CSV.

Tidak ada login, dashboard analitik, database terdistribusi, background job, atau integrasi eksternal pada MVP.

### 4.3 Prinsip rekomendasi

- Owner menyetujui pembelian. Sistem tidak mengirim PO otomatis.
- Setiap jumlah membawa alasan, input utama, versi model, dan confidence.
- Sistem menolak inference jika kolom kritis hilang atau stok tidak masuk akal.
- Sistem menampilkan fallback rule-based jika model berada di luar cakupan data.
- Penjelasan memakai template numerik, bukan LLM.

---

## 5. AI Necessity dan Core Inference

### 5.1 Mengapa AI diperlukan

Rule stok minimum memberi ambang yang sama sampai pengguna mengubahnya. Permintaan ritel berubah menurut pola mingguan, harga, promosi, hari libur, tren SKU, dan interaksi kategori. Model global dapat belajar lintas SKU dan memperbarui estimasi kebutuhan setiap kali pengguna memberikan snapshot baru.

AI diperlukan untuk memperkirakan **distribusi kebutuhan selama lead time**, bukan hanya satu angka penjualan. Optimizer membutuhkan median dan upper quantile untuk membedakan SKU stabil, SKU tidak teratur, dan SKU berisiko tinggi. M5 Competition menyediakan 42.840 time series ritel hierarkis dan menunjukkan bahwa forecasting ritel dapat dievaluasi pada skala SKU. Track uncertainty M5 juga menilai quantile forecast, sesuai kebutuhan safety stock berbasis risiko. [[M5 Accuracy paper](https://www.sciencedirect.com/science/article/pii/S0169207021001874)] [[M5 Uncertainty paper](https://doi.org/10.1016/j.ijforecast.2021.10.009)]

### 5.2 Definisi core inference

```text
recommend_replenishment(store_snapshot)
    -> replenishment_plan
```

`replenishment_plan` berisi SKU, jumlah pesan, nilai belanja, forecast P50/P90, risiko stockout, confidence, prioritas, dan alasan.

### 5.3 Tahap inference

**A. Probabilistic demand model**

- Model: global gradient-boosted decision trees dengan objective quantile.
- Target: total unit demand per SKU selama `lead_time + review_period`.
- Output: P50 dan P90 demand.
- Fitur: lag penjualan, rolling mean, rolling zero-rate, hari dalam minggu, bulan, kategori, harga, promosi jika tersedia, lead time, dan umur SKU.
- Fine-tuning: pencarian parameter pada training fold saja, lalu pemilihan berdasarkan mean pinball loss lintas rolling-origin folds.

**B. Deterministic replenishment layer**

```text
target_stock = forecast_P90
raw_order = max(0, target_stock - stock_on_hand - on_order)
order_qty = ceil(raw_order / MOQ) * MOQ
```

Sistem menghitung nilai perlindungan per rupiah dari peluang stockout, margin, dan biaya pembelian. Bounded knapsack memilih kombinasi kuantitas di bawah `available_budget`. Parameter bisnis tetap terlihat dan dapat diuji tanpa melatih ulang model.

### 5.4 Baseline wajib

Tim tidak boleh menilai model hanya dari satu skor. Lumbung perlu dibandingkan dengan:

1. seasonal naive, nilai hari yang sama pada minggu lalu;
2. moving average 7/28 hari;
3. static minimum stock;
4. SBA atau Croston untuk SKU intermittent;
5. model quantile Lumbung.

AI layak dipakai jika model dan optimizer meningkatkan outcome keputusan pada data holdout atau simulasi tanpa melanggar anggaran. Jika moving average memberi hasil setara, tim harus memilih baseline yang lebih sederhana.

---

## 6. Competitors dan Existing Alternatives

| Alternatif | Kekuatan | Gap yang ditarget Lumbung | Implikasi |
|---|---|---|---|
| Ingatan owner, cek rak, chat sales | Tidak perlu setup; sesuai kebiasaan | Sulit membandingkan banyak SKU dan risiko secara konsisten | Lumbung harus menghemat waktu sejak penggunaan pertama |
| Excel atau Google Sheets | Fleksibel dan murah | Formula perlu dirawat; sulit membuat probabilistic forecast per SKU | Import/export CSV harus menjadi jalur utama |
| POS dan inventory suites seperti Moka, Majoo, Olsera | Data transaksi, stok, PO, supplier, stock opname | Lumbung menarget keputusan jumlah dan prioritas lintas SKU di bawah anggaran | Integrasi menjadi strategi ekspansi, bukan MVP |
| Accurate minimum-stock PO | Membuat PO dari item di bawah batas minimum | Ambang statis tidak otomatis memodelkan distribusi demand dan budget allocation | Benchmark langsung untuk MVP |
| Enterprise demand planning | Forecasting dan workflow yang matang | Biaya, implementasi, dan kompleksitas dapat berlebihan untuk toko independen kecil | Lumbung harus tetap sempit dan ringan |

### 6.1 Edge yang diusulkan

1. **Budget-aware:** sistem meranking kebutuhan lintas SKU ketika uang tidak cukup untuk membeli semua rekomendasi.
2. **Probabilistic:** rekomendasi memakai rentang risiko, bukan satu point forecast.
3. **Overlay:** pengguna mempertahankan kasir yang sudah digunakan.
4. **Auditable:** owner melihat angka, constraint, dan alasan tanpa narasi generatif.
5. **Outcome-based evaluation:** tim mengukur stockout, fill rate, inventory value, dan waktu membuat rencana.

Kelima poin ini merupakan product thesis. Wawancara kompetitor, uji pengguna, dan product teardown masih diperlukan untuk membuktikan keunikan komersial.

---

## 7. Methodology

### 7.1 Dataset

**Tahap penyisihan:**

- M5 retail forecasting dataset sebagai data publik utama. Dataset berisi unit sales, calendar, price, hierarchy, dan banyak time series SKU-store. Repository penyelenggara menyediakan data serta benchmark. [[M5 repository](https://github.com/Mcompetitions/M5-methods)]
- Procurement constraints sintetis untuk `stock_on_hand`, `on_order`, `lead_time`, `MOQ`, `unit_cost`, dan `available_budget`. Tim harus melabelinya sebagai data sintetis karena M5 tidak menyediakan semua variabel tersebut.
- Satu file contoh berukuran kecil untuk proof of work dan inference lokal.

**Tahap validasi lapangan:**

- Data POS anonim dari calon pilot yang memberi persetujuan.
- Stock snapshot dan purchase history untuk mengukur inventory accuracy.
- Catatan keputusan owner, termasuk rekomendasi diterima, diubah, atau ditolak beserta alasan.

### 7.2 Data preparation

1. Ubah sales menjadi panel harian per `store_id x sku_id`.
2. Pertahankan zero-sales days. Jangan menghapus nol karena pola intermittent menjadi sinyal.
3. Buat fitur lag hanya dari tanggal sebelum cutoff.
4. Pisahkan train, validation, dan test berdasarkan waktu.
5. Fit encoder, imputer, dan tuner hanya pada training fold.
6. Simpan skema, checksum data, seed, feature list, dan versi model.

### 7.3 Leakage control

- Harga atau promosi setelah tanggal inference tidak boleh masuk sebagai fitur kecuali diketahui saat pemesanan.
- Rolling statistics memakai window yang berakhir sebelum tanggal target.
- Split acak lintas baris dilarang untuk time series.
- Data sintetis untuk lead time dan stok tidak boleh dipakai untuk mengklaim dampak lapangan.
- Lost sales tidak dapat diestimasi dari zero sales tanpa sinyal ketersediaan. Proposal harus menyebut demand censoring sebagai batas model.

### 7.4 Training dan fine-tuning

- Gunakan rolling-origin validation dengan beberapa cutoff.
- Tune `learning_rate`, `num_leaves`, `max_depth`, `min_data_in_leaf`, feature fraction, dan regularisasi.
- Catat seluruh run dan pilih satu model berdasarkan metric utama yang ditetapkan sebelum test.
- Bekukan model, preprocessing, parameter optimizer, dan schema untuk core inference penyisihan.

### 7.5 Evaluation

**Forecast metrics:**

- mean pinball loss untuk P50 dan P90;
- WAPE atau MASE sebagai metric skala-independen;
- bias per kategori;
- coverage P90;
- hasil terpisah untuk fast-moving dan intermittent SKU.

**Decision metrics melalui backtest/simulasi:**

- stockout units atau stockout days;
- fill rate;
- average inventory value;
- expired or dead-stock proxy jika data memungkinkan;
- budget violation count, wajib nol;
- total protected margin atau cost proxy dengan definisi yang transparan.

**Ablation:** bandingkan model tanpa calendar, tanpa category pooling, dan tanpa optimizer agar kontribusi tiap komponen terlihat.

### 7.6 Integration

```text
Browser UI
  -> POST /recommend dengan satu CSV
  -> Schema validator
  -> Feature pipeline
  -> Frozen quantile model
  -> Replenishment optimizer
  -> Explanation formatter
  -> Recommendation JSON
  -> Beli Sekarang / Tunda
```

Stack yang proporsional:

- frontend ringan, misalnya React atau Next.js;
- backend FastAPI;
- model LightGBM atau XGBoost yang diserialisasi;
- optimizer OR-Tools atau implementasi bounded knapsack yang teruji;
- `docker compose up` menjalankan seluruh aplikasi di localhost;
- unit test untuk schema, rounding MOQ, budget constraint, dan deterministic output.

---

## 8. Scope MVP Sesuai Guideline AIC

### 8.1 Included pada penyisihan

- satu alur upload snapshot dan menerima rekomendasi;
- validasi file dan pesan error yang jelas;
- satu model quantile yang sudah di-fine-tune;
- satu optimizer dengan parameter statis;
- output Beli Sekarang dan Tunda;
- alasan numerik per SKU;
- benchmark serta evaluasi holdout;
- local execution melalui `docker compose`;
- README, sample data, API contract, test, dan model card ringkas;
- Git history dengan Conventional Commits.

### 8.2 Explicitly out of scope

- POS dan pencatatan transaksi harian;
- offline-first sync dan event ledger;
- akun, role, dan multi-tenant database;
- OCR nota;
- WhatsApp Business API;
- LLM explanation atau chatbot;
- SIMKOPDES;
- supplier marketplace, joint procurement, dan transfer stok;
- multi-store orchestration;
- cloud deployment dan background retraining.

### 8.3 Kandidat pengembangan final

Tim hanya menambah fitur setelah core inference terbukti:

1. OCR nota pembelian dengan human confirmation;
2. import CSV dari satu POS partner;
3. feedback loop accept, edit, reject;
4. actual supplier lead-time learning;
5. inventory accuracy check sebelum recommendation.

---

## 9. Business Value dan Adoption

### 9.1 Value equation

Lumbung harus membuktikan nilai dengan rumus yang dapat diaudit:

```text
monthly_verified_value
= avoided_lost_margin
+ avoided_dead_stock_or_write_off
+ planning_hours_saved * agreed_hour_value
- incremental_inventory_cost
```

Tim tidak memiliki bukti untuk menetapkan angka penghematan atau harga langganan. Proposal tidak boleh mengklaim penurunan stockout, peningkatan turnover, atau return on investment sebelum backtest dan pilot selesai.

### 9.2 Model bisnis yang akan diuji

- subscription per outlet untuk recommendation engine;
- paket melalui penyedia POS atau komunitas retailer;
- pilot berbayar setelah baseline outcome tercatat.

Harga final mengikuti willingness-to-pay dan nilai terverifikasi. Tim dapat memakai wawancara terstruktur dan price-sensitivity test, tetapi hasilnya harus ditampilkan sebagai data primer dengan jumlah responden.

### 9.3 Go-to-market awal

1. Rekrut 5-10 calon pengguna yang memenuhi kriteria data.
2. Jalankan concierge test: tim membuat rekomendasi mingguan dari CSV tanpa integrasi.
3. Bandingkan keputusan Lumbung dengan keputusan owner dan actual sales.
4. Identifikasi alasan override.
5. Tawarkan pilot setelah owner melihat outcome pada datanya sendiri.

Jumlah di atas merupakan target riset, bukan pengguna yang sudah diperoleh.

---

## 10. Governance dan Responsible AI

Surat Edaran Menteri Kominfo Nomor 9 Tahun 2023 memberi pedoman etika AI untuk pelaku usaha dan penyelenggara sistem elektronik. UU Nomor 27 Tahun 2022 mengatur pelindungan data pribadi. Lumbung perlu menerjemahkan prinsip tersebut ke kontrol produk, meski data penjualan SKU tidak selalu merupakan data pribadi. [[SE Menkominfo 9/2023](https://jdih.komdigi.go.id/produk_hukum/view/id/883/t/surat%2Bedaran%2Bmenteri%2Bkomunikasi%2Bdan%2Binformatika%2Bnomor%2B9%2Btahun%2B2023)] [[UU PDP 27/2022](https://jdih.dpr.go.id/setjen/detail-dokumen/tipe/uu/id/1814)]

| Risiko governance | Kontrol produk |
|---|---|
| Model menyarankan pembelian berlebih | Human approval, budget hard limit, MOQ check, cap terhadap kapasitas jika tersedia |
| Forecast confidence rendah | Tampilkan confidence, fallback baseline, dan warning |
| Data toko bocor | Minimalkan data, hapus nama pelanggan, enkripsi saat transit dan tersimpan, batasi retensi |
| Model drift | Monitor error per waktu dan kategori, tetapkan retraining trigger |
| Bias terhadap SKU baru atau slow-moving | Laporkan performa per cohort dan gunakan fallback kategori |
| Penjelasan menyesatkan | Gunakan alasan template dari input dan output, bukan LLM |
| Owner terlalu bergantung pada model | Owner wajib konfirmasi; simpan override dan alasan |
| Data stok tidak akurat | Jalankan validation gate dan minta stock check untuk SKU berisiko |

Setiap hasil mencatat `model_version`, `data_cutoff`, `parameter_version`, input checksum, dan timestamp. Tim dapat mereproduksi keputusan yang dipersoalkan.

---

## 11. KPI dan Acceptance Gates

### 11.1 Model

| KPI | Acceptance gate penyisihan |
|---|---|
| P50/P90 pinball loss | Lebih baik dari baseline yang ditetapkan pada holdout |
| Coverage P90 | Dilaporkan dan dikalibrasi, bukan dipilih dari test set |
| WAPE/MASE | Tidak memburuk secara material terhadap baseline terbaik |
| Budget violations | 0 |
| Reproducibility | Input dan versi yang sama menghasilkan output yang sama |

### 11.2 Decision outcome

| KPI | Cara ukur |
|---|---|
| Stockout days/units | Backtest kebijakan pembelian pada horizon holdout |
| Fill rate | Demand terpenuhi dibagi demand total |
| Average inventory value | Rata-rata unit on hand dikali unit cost |
| Budget utilization | Nilai rekomendasi dibagi anggaran |
| Recommendation stability | Perubahan daftar akibat perubahan kecil pada input |

### 11.3 Product dan business

| KPI | Cara ukur pilot |
|---|---|
| Time to plan | Durasi keputusan manual vs assisted |
| Acceptance rate | Rekomendasi diterima tanpa edit |
| Override rate dan reason | Proporsi edit/tolak serta alasan terstruktur |
| Repeated use | Toko kembali memakai pada siklus pembelian berikutnya |
| Verified monthly value | Rumus pada Bagian 9.1 |
| Willingness-to-pay | Wawancara setelah menunjukkan hasil pada data toko |

Angka target dampak ditetapkan setelah baseline pilot tersedia. Proposal tidak memakai angka aspiratif sebagai hasil.

---

## 12. Risiko Utama

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Target customer tidak memiliki data yang cukup | Model tidak dapat digunakan | Screening data maturity; jangan target semua warung |
| Stok sistem berbeda dari stok fisik | Rekomendasi salah | Freshness check, anomaly rules, stock-check prompt |
| Zero sales berasal dari stockout | Model meremehkan demand | Minta availability flag; laporkan censoring sebagai limit |
| M5 tidak mewakili toko Indonesia | Model tidak transfer | Pakai M5 untuk prototype; validasi ulang pada data lokal |
| Lead time dan MOQ tidak tercatat | Optimizer memakai asumsi lemah | Template onboarding dan human confirmation |
| Kompetitor menambah fitur serupa | Edge menyempit | Fokus pada budget allocation, auditability, dan integration speed |
| Owner tidak percaya rekomendasi | Adoption rendah | Tampilkan alasan numerik, confidence, dan override |
| Model lebih buruk dari rule sederhana | AI tidak layak | Acceptance gate melawan baseline; gunakan rule bila menang |
| Scope melebar menjadi ERP | MVP tidak selesai | Pertahankan explicit out-of-scope list |
| Klaim dampak tidak didukung | Proposal kehilangan kredibilitas | Pisahkan benchmark, simulasi, pilot, dan hipotesis |

---

## 13. Roadmap

| Fase | Fokus | Deliverable | Exit criterion |
|---|---|---|---|
| Penyisihan | Buktikan core inference | Satu upload, model, optimizer, output, Docker, README, evaluasi | Menang atas baseline pada metric yang ditetapkan dan tidak melanggar anggaran |
| Validasi masalah | Cek kebutuhan owner | Wawancara, observasi kulakan, data audit | Pola pain dan workflow konsisten pada retailer yang memenuhi screening |
| Concierge pilot | Buktikan nilai tanpa integrasi | Rekomendasi mingguan dari CSV | Owner memakai hasil dan outcome dapat dihitung |
| Final AIC | Perbaiki workflow inti | Feedback accept/edit/reject dan satu ingestion improvement | Demo lokal stabil; perubahan didukung data pilot |
| Post-competition | Integrasi dan komersialisasi | Connector POS pertama, governance, monitoring | Retention dan willingness-to-pay terbukti |

---

## 14. Rencana Validasi Lapangan

### 14.1 Pertanyaan wawancara

1. Tunjukkan proses terakhir saat Anda membuat daftar kulakan.
2. Data atau layar apa yang Anda buka?
3. SKU mana yang paling sulit diputuskan dan mengapa?
4. Ceritakan pembelian terakhir yang harus dikurangi karena anggaran.
5. Produk apa yang habis sebelum sales berikutnya datang?
6. Produk apa yang terlalu lama diam di rak?
7. Siapa yang dapat mengubah jumlah pesanan?
8. Ekspor data apa yang tersedia dari POS?
9. Rekomendasi seperti apa yang akan Anda tolak?
10. Setelah melihat hasil pada data sendiri, nilai apa yang cukup untuk membuat Anda membayar?

Hindari pertanyaan seperti “Apakah Anda tertarik memakai AI?” Fokus pada kejadian terakhir, dokumen yang digunakan, waktu, uang, dan keputusan.

### 14.2 Evidence ledger

| Claim | Bukti yang dibutuhkan | Metode | Status |
|---|---|---|---|
| Owner menghabiskan waktu besar untuk replenishment | Durasi observed pada beberapa siklus | Observation + screen recording dengan izin | Belum ada |
| Budget merupakan constraint rutin | Bukti SKU ditunda dan nilai anggaran | Interview + purchase list | Belum ada |
| POS tersedia tetapi keputusan tetap manual | Export dan workflow owner | Data audit + interview | Didukung satu studi kasus; belum divalidasi tim |
| Model mengurangi stockout tanpa menaikkan inventory berlebih | Backtest dan pilot | Rolling holdout + prospective pilot | Belum ada |
| Owner bersedia membayar | Pilihan nyata setelah pilot | Paid pilot atau letter of intent | Belum ada |

---

## 15. Struktur Proposal PDF Maksimal 20 Halaman

| Bagian | Alokasi halaman yang disarankan |
|---|---:|
| Cover | Di luar batas jika guideline mengizinkan |
| Executive summary dan problem | 2 |
| Evidence dan target customer | 2 |
| Solution dan user flow | 2 |
| AI necessity dan core inference | 2 |
| Competitor, edge, dan business value | 2 |
| Dataset dan methodology | 3 |
| Evaluation dan hasil aktual | 2 |
| Architecture dan integration | 1 |
| Governance dan risks | 1 |
| MVP scope, roadmap, conclusion | 2 |
| Total | 19 |

Halaman hasil aktual hanya boleh memuat metric dari run final yang dapat direproduksi. Screenshot UI, diagram integration, dan satu tabel benchmark lebih berguna daripada uraian arsitektur panjang.

---

## 16. Kesimpulan

Lumbung v2 memilih satu keputusan bisnis yang sempit: alokasi anggaran replenishment lintas SKU. Segmen awalnya adalah growing independent retailers yang sudah memiliki data digital, tetapi masih mengandalkan owner untuk menyusun pembelian. Posisi ini menghindari beban membangun POS atau ERP baru dan memberi ruang bagi AI untuk mengestimasi risiko demand yang tidak dapat ditangani static minimum stock dengan baik.

Peluang tersebut belum menjadi product-market fit. Tim masih perlu membuktikan tiga hal: retailer mengalami pain yang cukup mahal, data mereka cukup andal, dan rekomendasi Lumbung mengubah outcome lebih baik daripada rule sederhana. MVP AIC harus berfokus pada pembuktian tersebut melalui satu inference flow, benchmark yang jujur, dan evaluasi keputusan yang dapat diaudit.

---

## Lampiran A. Mapping ke Kriteria AIC

| Kriteria | Respons Lumbung v2 |
|---|---|
| Orisinalitas dan dampak | Budget-aware probabilistic replenishment untuk independent high-SKU retailers; dampak diuji melalui stockout, inventory value, dan waktu planning |
| Implementasi teknologi | Model quantile, optimizer deterministik, komponen terpisah, parameter statis, inference sinkron |
| Kesiapan MVP | Satu upload dan satu output keputusan; local Docker; explicit out-of-scope |
| Proposal dan proses | Evidence ledger, baseline, rolling validation, leakage control, ablation, decision metrics |
| Relevansi tema | Smart Commerce pada operasional toko dan pembelian persediaan |
| Business value | Verified value equation dan paid-pilot path, tanpa klaim penghematan yang belum diuji |
| Governance | Human approval, model versioning, confidence, data minimization, drift monitoring |

## Lampiran B. Definition of Done Penyisihan

- [ ] Repository publik dibuat selama periode lomba.
- [ ] Seluruh commit memakai Conventional Commits.
- [ ] `docker compose up` menjalankan frontend dan backend di localhost.
- [ ] Sample CSV menghasilkan output yang sama pada clean run.
- [ ] Model artifact, preprocessing, dan parameter versioned.
- [ ] README menjelaskan setup, data schema, endpoint, model, dan batasan.
- [ ] Test mencakup invalid schema, missing values, MOQ rounding, budget cap, dan deterministic inference.
- [ ] Benchmark memakai temporal holdout tanpa leakage.
- [ ] Proposal membedakan data publik, data sintetis, dan data pilot.
- [ ] Proof-of-work video menampilkan terminal dan aplikasi tanpa cut sesuai guideline.
- [ ] Video promosi menjelaskan masalah, keputusan AI, dan dampak tanpa klaim palsu.

## Lampiran C. Sumber Utama

1. `GUIDELINES.md`, dokumen ketentuan AIC yang diberikan pengguna.
2. `LUMBUNG-Final-Plan.md`, rencana Lumbung v1 yang diberikan pengguna.
3. Bank Indonesia, *Kajian Inovasi Model Bisnis Pembiayaan Digital kepada UMKM*.
4. IPB University, *Review Penerapan SOP Sistem Persediaan pada BunHen Mart* (2024).
5. Studi kasus sistem pengendalian persediaan Minimarket Lok Jaya.
6. Official feature pages: Moka, Majoo, Olsera, dan Accurate.
7. M5 Competition papers dan official repository.
8. SE Menkominfo Nomor 9 Tahun 2023 dan UU Nomor 27 Tahun 2022.
