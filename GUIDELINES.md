# Ketentuan Lomba AI Innovation Challenge (AIC)

## 1. Deskripsi
AI Innovation Challenge (AIC) merupakan kompetisi inovasi berbasis teknologi Artificial Intelligence (AI) yang terbuka untuk seluruh Warga Negara Indonesia berusia maksimal 25 tahun[cite: 1]. AIC menantang peserta untuk merancang dan membangun inovasi AI yang menjawab permasalahan nyata di sektor industri dan perdagangan Indonesia[cite: 1]. Inovasi dapat berupa aplikasi web, IoT, dan software/hardware lain yang mengintegrasikan AI[cite: 1]. 

Melalui AIC, peserta akan melalui rangkaian tahapan mulai dari pendaftaran, babak penyisihan, workshop edukatif (AIC Talks), hingga babak final[cite: 1]. Delapan tim terbaik akan maju ke babak final untuk menyempurnakan karya mereka dengan bimbingan mentor di bidang AI dan Product Management, sebelum mempresentasikan solusi secara langsung di hadapan juri[cite: 1].

## 2. Tema
Tema AIC pada tahun ini adalah **"AI for the Backbone of the Economy"**, yang bertujuan untuk menggali potensi AI dalam mentransformasi rantai nilai bisnis di Indonesia[cite: 1]. Peserta didorong untuk mengembangkan solusi berbasis AI yang mencakup tiga area utama rantai pasok pasca-produksi primer:
* **Smart Manufacturing (Pabrik):** Penerapan AI di proses pengolahan dan operasi pabrik[cite: 1].
* **Smart Logistics (Gudang & Distribusi):** Penerapan AI di pergerakan barang[cite: 1].
* **Smart Commerce (Toko & Pasar):** Penerapan AI di sisi konsumen, sales operasional, serta transaksi komersial[cite: 1].

## 3. Teknis & Kriteria

### A. Teknis Penyisihan
* **Ketentuan Produk:**
    * Proyek inovasi memanfaatkan AI sesuai tema dan merupakan karya orisinal tim[cite: 1].
    * Proyek hanya dikerjakan selama perlombaan berlangsung (17 Juni - 25 Agustus 2026 pukul 23.55 WIB)[cite: 1]. Dilarang melanjutkan proyek yang sudah pernah dikerjakan di luar periode tersebut[cite: 1].
    * Proyek penyisihan wajib dilanjutkan sebagai proyek yang dikerjakan saat tahap Final[cite: 1].
* **Batasan Ruang Lingkup MVP (Minimum Viable Product):**
    * **Frontend (UI):** Fokus pada alur interaksi inti (menerima input tunggal pengguna dan menampilkan output AI)[cite: 1]. Tidak perlu fitur pelengkap rumit seperti dashboard analitik tingkat lanjut atau sistem otentikasi[cite: 1].
    * **Backend & Integrasi:** Fokus pada pemrosesan interaksi sinkron dan wajib dapat dijalankan lokal menggunakan `docker compose`[cite: 1]. Tidak perlu *background jobs* atau database terdistribusi[cite: 1].
    * **Model AI & Algoritma:** Fokus pada fungsionalitas inferensi utama (*core inference*) dengan parameter statis[cite: 1].
* **Ketentuan Deliverables & Pengumpulan:**
    * Wajib commit dan push via GitHub (visibility *public*)[cite: 1]. Pesan commit wajib mengikuti konvensi *Conventional Commits* (seperti `feat:`, `fix:`, `refactor:`)[cite: 1].
    * Deadline pengumpulan semua berkas di situs COMPFEST adalah **25 Agustus 2026 pukul 23.55 WIB**[cite: 1].
    * Diperbolehkan menggunakan dataset publik/sintetik dan *pre-trained model* maupun API, namun model wajib di-*fine tune*[cite: 1].
* **Berkas yang Wajib Dikumpulkan:**
    1. **Link Repository Source Code di GitHub:** Wajib memuat setup guide yang jelas di file `README.md` dan `docker compose`[cite: 1].
    2. **Link Video Proof of Work:** Durasi maksimal 7 menit, diunggah ke YouTube dengan visibility *unlisted* (Format: `COMPFEST 18 AIC: PROOF OF WORK - [Nama Tim] - [Nama Proyek]`)[cite: 1]. Video harus menampilkan *double screen* (terminal & aplikasi) dan *timestamp*[cite: 1]. Dilarang keras melakukan *cut* pada video, hanya boleh melakukan *fast-forward* (dipercepat)[cite: 1].
    3. **Link Video Promosi Inovasi:** Durasi maksimal 5 menit (resolusi min 720p), diunggah ke YouTube dengan visibility *public* (Format: `COMPFEST 18 AIC: [Nama Tim] - [Nama Proyek]`)[cite: 1].
    4. **Proposal (PDF):** Maksimal 20 halaman (tanpa cover, lampiran, dll)[cite: 1]. Memuat Nama, Latar Belakang, Tujuan, Metodologi (dataset, pengembangan model, integrasi), dan Kesimpulan[cite: 1].
* **Ketentuan Tambahan:** 
    * Dilarang menunjukkan latar belakang institusi pendidikan[cite: 1]. 
    * Peserta diharapkan bersiap siaga (*standby*) di Discord pada tanggal 9 & 10 September 2026 pukul 20.00 untuk permintaan klarifikasi atau *live demo* oleh panitia[cite: 1].

### B. Teknis Final
* Tahap final terdiri dari Mentoring (20 September 2026), Hackathon (26 September 2026), dan Live Pitching (27 September 2026) secara luring[cite: 1].
* **Hackathon:** Berlangsung non-stop selama 10 jam di lokasi yang telah ditentukan[cite: 1]. Finalis mengembangkan iterasi produk secara langsung dan wajib melakukan *push* secara berkala[cite: 1]. Setelah fase ini berakhir, finalis dilarang keras mengubah repository[cite: 1].
* **Live Pitching:** Hasil pengembangan tidak wajib di-deploy ke cloud, tapi setidaknya siap didemonstrasikan secara lokal (*localhost*) di hadapan juri[cite: 1].
* **Hardware:** Jika produk melibatkan perangkat keras, perangkat sepenuhnya menjadi tanggung jawab peserta dan wajib didaftarkan sebelum acara final[cite: 1].

## 4. Kriteria Penilaian Babak Penyisihan (Total Akumulasi: 105%)

* **Orisinalitas dan Dampak Sosial (Bobot: 20%)**
    * Keunikan dan inovasi solusi yang ditawarkan (apakah ini pendekatan baru yang belum pernah terpikirkan sebelumnya dan berbeda dari solusi yang sudah ada)[cite: 2].
    * Relevansi solusi dengan konteks permasalahan, seberapa mendesak (urgent) masalah yang diangkat, serta kesesuaiannya dengan kebutuhan target pengguna maupun kebutuhan global[cite: 2].
    * Kemampuan solusi dalam mengatasi masalah individu atau mendukung pertumbuhan bisnis[cite: 2].

* **Implementasi Teknologi & Kematangan Arsitektur (Bobot: 25%)**
    * Pemilihan teknologi (model AI, framework, stack) yang sesuai dan proporsional dengan kebutuhan solusi[cite: 2].
    * Implementasi AI yang berfokus pada core inference yang bersih, dengan parameter yang terdefinisi dengan jelas[cite: 2].
    * Arsitektur yang modular, di mana komponen AI, backend, dan frontend terpisah dengan bersih[cite: 2].
    * Terdapat dokumentasi teknis (README) yang cukup untuk memahami alur sistem secara keseluruhan[cite: 2].

* **Kesiapan Minimum Viable Product (MVP) untuk Babak Final (Bobot: 15%)**
    * Ruang lingkup MVP sudah tepat sesuai batasan yang ditentukan (tidak overbuilt atau underbuilt)[cite: 2].
    * MVP sudah mencakup fungsionalitas inti yang cukup untuk dievaluasi dan dikembangkan lebih lanjut pada babak final[cite: 2].
    * Arsitektur yang dibangun memiliki fleksibilitas memadai untuk dikembangkan tanpa perombakan total[cite: 2].
    * Terdapat komponen atau aspek sistem yang diakui tim sebagai area yang masih dapat ditingkatkan secara signifikan[cite: 2].

* **Video Promosi (Bobot: 15%)**
    * Video mampu mengomunikasikan masalah yang diangkat dan bagaimana solusi AI menyelesaikannya dengan bahasa yang lugas dan mudah dipahami[cite: 2].
    * Video menceritakan proses perancangan karya (latar belakang ide hingga eksekusi) dengan storytelling yang menarik[cite: 2].
    * Video menarik untuk stakeholders (pemerintah, industri, dll)[cite: 2].
    * Konten video lengkap dan sesuai ketentuan[cite: 2].

* **Kualitas Proposal & Proses Pengembangan (Bobot: 15%)**
    * Struktur dan kelengkapan proposal sudah sesuai (metodologi, alur dataset, alur integrasi model)[cite: 2].
    * Metodologi serta argumentasi teknis dipaparkan secara jelas, rinci, dan logis[cite: 2].
    * Pengambilan keputusan (decision making) dalam pemilihan teknologi, model, dan arsitektur dijelaskan dengan alasan yang berbasis data atau analisis[cite: 2].
    * Cerita pengembangan produk mencerminkan proses iteratif yang reflektif, bukan sekadar deskripsi fitur[cite: 2].

* **Relevansi dengan Tema (Bobot: 10%)**
    * Inovasi sesuai dengan tema yang sudah ditentukan ("AI for the Backbone of the Economy")[cite: 2].
    * Penggunaan AI dalam solusi relevan dan tidak dipaksakan terhadap tema[cite: 2].

* **Business Value dan Governance (BONUS - Bobot: 3.5%)**
    * Tim menyertakan model bisnis atau analisis kelayakan adopsi industri yang realistis[cite: 2].
    * Solusi mempertimbangkan aspek regulasi AI, etika, atau prinsip sistem cerdas yang bertanggung jawab[cite: 2].

* **AIC Talks (BONUS - Bobot: 1.5%)**
    * Mengikuti dan mengisi presensi AIC Talks[cite: 2].
