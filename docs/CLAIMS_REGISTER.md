# Lumbung Claims Register

Gunakan register ini saat tim menulis proposal, narasi video, caption, dan materi presentasi. Cocokkan setiap angka dengan artifact pada commit final.

## Klaim yang memiliki bukti

| Klaim | Batas klaim | Bukti repository |
|---|---|---|
| Lumbung menjalankan satu alur upload CSV dan menghasilkan rencana belanja | Berlaku untuk MVP lokal pada source ini | `frontend/src/App.tsx`, `backend/app/main.py` |
| Model memakai LightGBM quantile P50 dan P90 | Model memakai histori sintetis yang tim generate | `scripts/train_model.py`, `artifacts/model_metadata.json` |
| Tim melakukan tuning dengan dua expanding temporal folds | Tim menguji tiga kandidat parameter | `scripts/train_model.py`, field `validation.tuning_results` pada metadata |
| Mean pinball loss model mencapai 1.786392 | Hasil berasal dari 432 contoh temporal holdout sintetis | `artifacts/model_metadata.json` |
| Moving-average baseline mencapai mean pinball loss 1.828699 | Gunakan baseline ini untuk konteks hasil model | `artifacts/model_metadata.json` |
| WAPE P50 model mencapai 0.200564 | Hasil sintetis, bukan hasil toko Indonesia | `artifacts/model_metadata.json` |
| P90 coverage mencapai 0.891204 | Nilainya mendekati target 90 persen dan masih memiliki gap kalibrasi | `artifacts/model_metadata.json` |
| Optimizer menjaga usulan belanja di bawah anggaran input | Unit tests dan release verifier memeriksa constraint ini | `backend/tests/test_optimizer.py`, `scripts/verify_release.py` |
| Sistem membulatkan pesanan sesuai MOQ | Unit tests dan release verifier memeriksa kelipatan MOQ | `backend/tests/test_optimizer.py`, `backend/tests/test_service.py` |
| Input dan versi model yang sama menghasilkan output yang sama | Tests membandingkan dua inference penuh | `backend/tests/test_service.py` |
| Sistem memberi alasan numerik tanpa LLM | Backend membentuk alasan dari forecast, stok, dan hasil optimizer | `backend/app/service.py` |
| Owner tetap menyetujui pembelian | MVP tidak mengirim purchase order | `README.md`, tampilan footer aplikasi |

## Klaim yang harus menyebut konteks sintetis

Gunakan pola berikut:

> Pada temporal holdout sintetis berisi 432 contoh, model Lumbung mencatat mean pinball loss 1.786392, dibandingkan 1.828699 pada moving-average baseline.

> Release verifier pada commit final mengonfirmasi bahwa rekomendasi sample mematuhi budget dan MOQ serta menghasilkan output deterministik.

Hindari frasa "terbukti di lapangan", "siap produksi", atau "akurat untuk retailer Indonesia". Repository belum memiliki data yang mendukung frasa tersebut.

## Klaim yang belum memiliki bukti

| Klaim | Bukti yang tim butuhkan sebelum memakai klaim |
|---|---|
| Lumbung mengurangi stockout | Backtest kebijakan pembelian pada data toko yang memiliki sinyal availability, lalu pilot prospektif |
| Lumbung meningkatkan fill rate | Baseline fill rate dan pengukuran pada horizon pilot |
| Lumbung menurunkan dead stock atau waste | Data umur stok, expiry, dan write-off |
| Lumbung menghemat biaya atau menaikkan margin | Purchase history, lost-sales estimate, inventory carrying cost, dan margin aktual |
| Owner menghemat waktu perencanaan | Pengukuran waktu manual dan assisted pada pengguna yang sama |
| Retailer bersedia membayar | Paid pilot, kontrak, atau letter of intent |
| Model mewakili pola retailer Indonesia | Dataset lokal yang berizin dan evaluasi temporal terpisah |
| Produk mematuhi seluruh regulasi | Review hukum terhadap alur data, operator, deployment, dan kontrak yang akan dipakai |

Sebut butir di atas sebagai target evaluasi, hipotesis, atau rencana pilot. Jangan menulisnya sebagai hasil.

## Batas sumber data

Tim harus memakai tiga label berikut secara konsisten:

- **Data sintetis:** `data/synthetic_training_history.csv` dan `data/sample_store_snapshot.csv`.
- **Hasil model:** metrik yang tersimpan pada `artifacts/model_metadata.json`.
- **Data pilot:** belum tersedia pada repository ini.

Tim tidak boleh mengubah angka metadata secara manual. Jalankan ulang generator dan training script jika tim mengganti data atau model, lalu perbarui semua tabel dari output baru.

## Pemeriksaan sebelum publikasi

- Cocokkan hash data, versi model, dan metrik dengan commit yang akan tim push.
- Jalankan `python scripts/verify_release.py`.
- Hapus nama institusi pendidikan dari layar, narasi, slide, deskripsi, dan profil yang terlihat pada rekaman.
- Tandai hasil sintetis pada tabel, caption, dan voice-over.
- Jangan memakai angka dampak, jumlah pengguna, pendapatan, atau penghematan tanpa evidence artifact.

