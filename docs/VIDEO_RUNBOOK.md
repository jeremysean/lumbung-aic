# AIC Video Runbook

Ganti `[NAMA TIM]` setelah tim mengonfirmasi nama resmi. Jangan merekam path folder yang menampilkan institusi pendidikan. Buka terminal pada folder repository lalu gunakan judul jendela yang netral.

## Proof of Work

Judul YouTube:

```text
COMPFEST 18 AIC: PROOF OF WORK - [NAMA TIM] - Lumbung
```

Atur visibility menjadi **unlisted**. Durasi maksimal tujuh menit. Tampilkan terminal dan aplikasi dalam satu frame serta tampilkan timestamp. Rekam satu take tanpa cut. Panitia mengizinkan fast-forward.

### Persiapan sebelum merekam

- Tutup notifikasi, email, tab pribadi, dan aplikasi yang menampilkan identitas institusi.
- Pastikan Docker Desktop sudah berjalan dan memiliki ruang disk yang cukup.
- Siapkan `data/sample_store_snapshot.csv`.
- Periksa working tree dengan `git status --short --branch`.
- Periksa commit dengan `git log -1 --format="%h %an <%ae> %s"`.
- Jalankan `python scripts/verify_release.py`.
- Atur jam sistem agar timestamp terlihat pada frame.

### Alur rekaman, target 6 menit 30 detik

| Waktu | Terminal dan aplikasi | Narasi |
|---|---|---|
| 00:00 sampai 00:25 | Tampilkan timestamp, commit, dan working tree | Sebut nama tim, Lumbung, dan tujuan rekomendasi belanja di bawah budget |
| 00:25 sampai 01:40 | Jalankan `docker compose up --build` | Jelaskan dua container: React dan Nginx untuk UI, FastAPI untuk inference |
| 01:40 sampai 02:10 | Tampilkan `docker compose ps` dan `/health` | Sebut model version dari response health |
| 02:10 sampai 02:45 | Buka aplikasi dan unduh sample CSV | Jelaskan schema, 28 hari histori per SKU, stok, on-order, biaya, margin, lead time, MOQ, dan budget |
| 02:45 sampai 03:35 | Upload sample dan buat rekomendasi | Tunjukkan satu interaksi sinkron dari input ke output |
| 03:35 sampai 04:35 | Tinjau summary dan tabel | Tunjukkan P50, P90, stok, risiko, MOQ, biaya, Beli Sekarang, dan Tunda |
| 04:35 sampai 05:05 | Tunjukkan audit checksum dan unduh hasil | Jelaskan determinisme dan owner approval |
| 05:05 sampai 05:45 | Buka `/docs` | Tunjukkan endpoint template, recommendation, error contract, dan health |
| 05:45 sampai 06:15 | Jalankan release verifier jika belum tampil | Sebut budget dan MOQ checks tanpa mengklaim hasil lapangan |
| 06:15 sampai 06:30 | Kembali ke aplikasi | Tutup dengan batas hasil sintetis dan rencana validasi data lokal |

Jika build pertama memakan waktu, gunakan fast-forward pada bagian build. Pertahankan video sebagai satu file tanpa cut.

### Kalimat yang aman untuk demo

> Lumbung membantu owner menyusun prioritas pembelian dari satu CSV. Model memperkirakan demand P50 dan P90, lalu optimizer memilih bundle MOQ di bawah budget input.

> Tim melatih dan menguji artifact ini pada data sintetis. Pada 432 contoh temporal holdout sintetis, model mencatat mean pinball loss 1.786392, dibandingkan 1.828699 pada moving-average baseline.

> Hasil ini memvalidasi pipeline prototype. Tim masih perlu menguji dampak stockout, fill rate, dan nilai bisnis pada data toko yang berizin.

## Video Promosi

Judul YouTube:

```text
COMPFEST 18 AIC: [NAMA TIM] - Lumbung
```

Atur visibility menjadi **public**. Durasi maksimal lima menit dan resolusi minimal 720p.

### Struktur target 4 menit 30 detik

| Waktu | Isi |
|---|---|
| 00:00 sampai 00:35 | Owner harus memilih barang saat budget tidak cukup untuk membeli seluruh kebutuhan |
| 00:35 sampai 01:10 | Owner menggabungkan histori penjualan, stok, on-order, lead time, MOQ, biaya, dan margin |
| 01:10 sampai 02:10 | Demo upload CSV dan hasil Beli Sekarang serta Tunda |
| 02:10 sampai 03:05 | Jelaskan forecast quantile, kalibrasi, dan optimizer budget |
| 03:05 sampai 03:45 | Tampilkan hasil synthetic holdout dengan label yang jelas |
| 03:45 sampai 04:15 | Jelaskan human approval, checksum, model version, dan data minimization |
| 04:15 sampai 04:30 | Tutup dengan rencana pilot pada retailer yang memiliki data digital |

Gunakan satu masalah dan satu keputusan inti. Jangan memasukkan POS, OCR, chatbot, marketplace supplier, atau SIMKOPDES sebagai fitur MVP saat ini.

