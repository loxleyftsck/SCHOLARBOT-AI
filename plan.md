# Plan Upgrade ScholarBot AI untuk Portofolio

Tanggal rencana: **7 Oktober 2026**
Status: **Fase A: perbaikan inti lokal, A8/grounding masih terbuka; Fase B: benchmark dan pemilihan retrieval selesai lokal; Fase C–G belum dimulai.**

### Progress implementasi — 7 Oktober 2026

| Item | Status lokal | Bukti / pekerjaan tersisa |
| --- | --- | --- |
| A1–A3 | Implementasi dan regresi lolos | Keyword tanpa overlap ditolak, routing pertanyaan dokumen diperbaiki, chunk/fallback dibatasi dan isi pendek/tail dipertahankan |
| A4–A5 | Implementasi dan regresi lolos | Prompt/header/kartu sumber memakai konteks terpilih yang sama; instruksi saat sumber kurang diperjelas. Kepatuhan model dan dukungan setiap klaim belum diukur |
| A6–A7 | Implementasi dan pemeriksaan UI lolos | Error generasi menggantikan hasil statis, progress awal belum dinilai, skor pencarian tanpa persen, klaim halaman diperbaiki |
| A8 | Sebagian diimplementasikan | Mode rangkuman, pergantian mode dan follow-up diuji; history dibatasi 16.000 karakter. Budget token seluruh input dan ringkasan history masih perlu dikerjakan |

Validasi: **119 tes backend/core yang relevan, 10 pemeriksaan markdown, build React, dan smoke test browser lolos**. Suite UI Streamlit tidak dijalankan karena environment API tidak memasang Streamlit. Tidak ada benchmark akurasi atau pengujian LLM langsung untuk perubahan ini. Deployment tetap ditunda.

Catatan terperinci: [hasil Fase A](docs/PHASE-A-RESULTS.md). Gate A belum ditutup penuh sampai sisa A8 dan evaluasi kepatuhan sumber selesai.
Dasar: [Review fitur, RAG, dan logo](docs/REVIEW-2026-10.md).

## 1. Tujuan dan positioning

Bangun demo asisten belajar bahasa Indonesia berbasis dokumen yang sumber jawabannya bisa diperiksa, kualitas retrieval-nya diukur, dan hasil latihannya dicatat secara nyata.

Audiens portofolio: recruiter, engineer, dan calon pengguna yang ingin memahami masalah, keputusan arsitektur, hasil pengujian, serta batas sistem dalam beberapa menit.

Alur utama yang harus utuh:

**Unggah materi → tanyakan isi → periksa sumber → latihan → lihat kesalahan → latihan ulang.**

Fondasi yang dipertahankan: React/Vite, FastAPI, integrasi Groq, streaming, markdown/matematika, dan modul RAG. Perubahan model atau framework diputuskan dari hasil evaluasi. Deployment lanjutan tetap ditunda sampai pengguna meminta dilanjutkan dan kriteria demo terpenuhi.

## 2. Baseline dan aturan pengerjaan

- [ ] Catat commit baseline, versi dependency, model, konfigurasi chunking/retrieval, serta kemampuan yang sudah aktif.
- [ ] Jalankan pemeriksaan backend yang relevan, pemeriksaan markdown, dan build frontend; simpan hasil aktual dan perintahnya.
- [ ] Bedakan test API/RAG dari test UI Streamlit yang memerlukan dependency tambahan. Jangan mengklaim seluruh suite lolos bila hanya subset yang dijalankan.
- [ ] Rekam contoh sebelum perbaikan untuk query tak relevan, pertanyaan yang menyebut dokumen, embedding gagal, dan sitasi yang tidak masuk konteks.
- [ ] Gunakan dokumen sintetis atau materi berlisensi sesuai; data pribadi tidak dimasukkan ke fixture, screenshot, atau laporan.
- [ ] Kerjakan satu fase dalam perubahan yang mudah direview; tambahkan test regresi untuk perilaku bermasalah, bukan test yang hanya menyalin implementasi.
- [ ] Simpan API key di environment backend; jangan masukkan secret atau direktori `.wrangler/` ke commit.

Bukti dari sesi sebelumnya dapat menjadi referensi, tetapi bukan pengganti pengujian pada implementasi baru. Review lama belum memberikan benchmark akurasi end-to-end.

## 3. Tahapan upgrade

### Fase A — Perbaiki kebenaran RAG dan tampilan (P0)

**Tujuan:** hilangkan perilaku yang membuat jawaban terlihat bersumber padahal bukti tidak memadai.

| ID | Pekerjaan | Kriteria selesai |
| --- | --- | --- |
| A1 | Perbaiki bonus panjang dan ambang keyword retrieval | Query fotosintesis terhadap dokumen keuangan tidak mengembalikan sumber hanya karena bonus panjang |
| A2 | Bedakan intent pertanyaan dari kontrol dokumen | “Jelaskan dokumen ini” memakai RAG; perintah hapus/reset ditangani sebagai kontrol; follow-up menggunakan konteks pertanyaan yang sesuai |
| A3 | Batasi ukuran chunk di semua fallback | Embedding gagal, paragraf panjang, dan kalimat pendek tidak menghasilkan chunk tak terbatas atau kehilangan isi penting; batas dan overlap diuji |
| A4 | Susun satu paket konteks untuk prompt dan sitasi | ID sumber dalam prompt, metadata respons, dan UI konsisten; sumber yang tidak dimasukkan ke model tidak ditawarkan sebagai sitasi |
| A5 | Tambahkan perilaku saat sumber tidak cukup | Mode dokumen menyatakan keterbatasan sumber; pengetahuan tambahan dipisahkan; sitasi tidak dibuat untuk klaim tanpa bukti |
| A6 | Perbaiki label dan fallback UI | Persentase retrieval tidak disebut probabilitas kebenaran; contoh statis diberi label; kegagalan kuis/mind map tidak menghitung progress |
| A7 | Koreksi klaim landing | Klaim nomor halaman diganti menjadi potongan sumber sampai metadata halaman benar-benar tersedia |
| A8 | Perbaiki pergantian mode dan history | Mode rangkuman memiliki instruksi/alur jelas; kembali ke belajar tidak membawa state kuis yang salah; konteks percakapan punya batas token |

Lokasi utama: `scholarbot/services/retriever.py`, `semantic_search.py`, `chunker.py`, `scholarbot/core/rag_context.py`, `scholarbot/api.py`, `scholarbot-web/src/App.jsx`, dan `landing/index.html`.

**Gate A:** seluruh regresi di atas lolos; sumber, kegagalan, dan contoh statis ditampilkan secara jujur. Jangan menambah fitur besar sebelum gate ini tercapai.

### Fase B — Ukur kualitas dan pilih retrieval (P1)

**Hasil lokal:** [laporan Fase B](docs/evaluation/RESULTS.md). 50 query, 6 metode retrieval; BM25 dipilih sebagai default. Recall@5 pilot 100% dibanding keyword 82,7%. Reproduksi 300 ranking/konteks identik. Review 14 respons Groq: no-answer 7/7, ID sitasi 14/14 valid; grounding masih kurang (10/14 unit sepenuhnya didukung, bukan audit semua klaim atomik). Target ≥90% klaim belum terbukti. Status tugas di bawah menandai pekerjaan pengukuran, bukan seluruh target kualitas lolos.

**Tujuan:** punya bukti bahwa upgrade memperbaiki kualitas, bukan hanya mengganti nama teknologi.

- [x] Buat dataset awal sekitar **50 pertanyaan** bahasa Indonesia dengan jawaban acuan dan sumber: 15 langsung, 10 parafrase, 10 lintas dokumen, 5 follow-up, dan 10 tanpa jawaban.
- [x] Gunakan beberapa dokumen dan sertakan istilah teknis, dokumen tidak relevan, serta materi pendek/panjang. Cegah duplikasi dekat antara pertanyaan tuning dan evaluasi.
- [x] Tetapkan bagian tuning dan bagian evaluasi terpisah. Catat bahwa ukuran ini pilot, belum membuktikan generalisasi luas.
- [x] Bandingkan baseline keyword, dense embedding, dan BM25 + dense dengan fusion RRF pada dokumen serta pertanyaan yang sama.
- [x] Uji kandidat embedding multilingual terhadap model saat ini; periksa prefix query/passage, batas input, kebutuhan RAM, latency, ketersediaan provider, dan biaya.
- [x] Tambahkan validasi dimensi/output embedding, cache dengan identitas model, serta indikator fallback. Kegagalan provider tidak boleh tersamarkan sebagai semantic search sukses.
- [x] Filter relevansi sebelum diversifikasi lintas dokumen; eksperimen reranker hanya jika hasil pilot menunjukkan kebutuhan.
- [x] Catat Recall@k, precision konteks, ketepatan sitasi, jawaban tanpa sumber, latency p50/p95, jumlah panggilan provider, dan pemakaian token.
- [x] Periksa sampel jawaban secara manual. Jika memakai evaluasi otomatis seperti Ragas, catat evaluator, prompt, dan keterbatasannya.

**Target pilot yang diusulkan, bukan hasil yang sudah dicapai:**

| Ukuran | Target awal |
| --- | --- |
| Recall@5 untuk pertanyaan dengan sumber berlabel | ≥ 85%; jelaskan perhitungan untuk kasus lintas dokumen |
| ID sitasi merujuk sumber yang benar-benar diberikan | 100% |
| Klaim bersitasi yang didukung sumber, pada sampel manual | ≥ 90% |
| Kasus tanpa jawaban yang menyatakan sumber tidak cukup | ≥ 90% |
| Performa dan biaya | Dilaporkan beserta ukuran dokumen, perangkat, provider, serta kondisi cold/warm; budget ditetapkan setelah baseline |

Target ditetapkan sebelum membandingkan kandidat. Jika tidak tercapai, simpan hasil dan penyebabnya; jangan mengganti definisi metrik agar terlihat lolos.

**Gate B:** ada laporan evaluasi yang dapat diulang dan alasan pemilihan retrieval. Fusion atau model baru hanya dipertahankan bila manfaatnya sebanding dengan biaya dan latency.

### Fase C — Sumber yang dapat ditelusuri (P1)

- [ ] Pertahankan metadata halaman PDF saat ekstraksi; jangan mengubah nomor chunk menjadi nomor halaman.
- [ ] Tambahkan `document_id`, `chunk_id`, halaman/rentang halaman, serta metadata versi dokumen pada struktur yang konsisten.
- [ ] Gunakan rentang teks yang valid terhadap hasil ekstraksi; jelaskan keterbatasan pencocokan posisi pada PDF.
- [ ] Buat viewer/preview sumber yang membuka halaman atau potongan terkait ketika sitasi diklik.
- [ ] Tangani penghapusan, unggah ulang dengan nama sama, dan pemulihan sesi tanpa menghubungkan sitasi ke dokumen yang salah.
- [ ] Tampilkan pesan yang jelas untuk PDF scan atau ekstraksi sebagian. OCR masuk backlog kecuali kebutuhan demo mengharuskannya.

**Gate C:** satu alur PDF dari upload sampai klik sumber dapat dibuktikan; TXT tetap mempunyai kutipan yang dapat ditemukan tanpa klaim nomor halaman palsu.

### Fase D — Siklus belajar berdasarkan dokumen (P1)

- [ ] Kuis menerima dokumen/topik terpilih dan memakai sumber dari pipeline yang sama dengan chat.
- [ ] Gunakan schema terstruktur untuk soal, opsi, jawaban, alasan, konsep, tingkat kesulitan, dan referensi sumber; validasi sebelum ditampilkan.
- [ ] Simpan ID soal dan evaluasi jawaban di server. Jangan menerima boolean kebenaran dari client sebagai bukti hasil belajar.
- [ ] Buat set latihan awal 5 soal; beri penjelasan beserta sumber dan hint bertahap.
- [ ] Mulai progress dari “belum dinilai”; tampilkan jumlah soal, percobaan, hasil, dan konsep yang perlu diulang.
- [ ] Simpan catatan kesalahan konsep dan tawarkan latihan ulang. Soal statis/demo tidak masuk statistik.
- [ ] Ubah pujian menjadi sesuai bukti, misalnya “jawaban soal ini benar”, bukan menyatakan pemahaman sempurna setelah satu soal.
- [ ] Rangkuman mempertimbangkan cakupan dokumen dan batas konteks, bukan hanya tiga chunk pertama.
- [ ] Kaitkan node mind map dengan sumber; pisahkan inferensi model dari isi dokumen. Pastikan mode mind map tidak memicu generasi chat tambahan tanpa kebutuhan.

**Gate D:** pengguna bisa menjalankan alur belajar utama dengan progress yang berubah dari hasil nyata, termasuk ketika jawaban salah dan provider gagal.

### Fase E — Identitas visual dan pengalaman demo (P1)

Arah desain yang direkomendasikan: **logo utama S + halaman + penanda sumber**, robot sebagai maskot pendamping, dan palet paper/walnut yang konsisten dengan aplikasi. Ini arah konsep; desain final dipilih setelah melihat alternatif.

- [ ] Buat 2–3 konsep logo untuk dibandingkan pada navbar, favicon, kartu proyek, serta screenshot LinkedIn.
- [ ] Siapkan logo SVG, wordmark, versi satu warna, terang/gelap, dan ikon 16/24/32 px; pastikan keterbacaan tanpa bayangan/gradasi.
- [ ] Gunakan komponen identitas yang sama di landing, React, README, dan materi portofolio.
- [ ] Tampilkan contoh penggunaan nyata, urutan kerja, batas fitur, serta tombol demo yang mencerminkan status sistem.
- [ ] Periksa viewport 360, 390, 768, dan 1440 px; tidak ada overflow yang menghalangi tugas utama.
- [ ] Periksa navigasi keyboard, focus, label kontrol, kontras teks, target sentuh, reduced motion, dan kondisi JavaScript/aset gagal.
- [ ] Perbaiki metadata judul, deskripsi, favicon, dan gambar preview sosial; verifikasi preview setelah publikasi.

**Gate E:** satu identitas konsisten, UI dapat digunakan di desktop/ponsel, dan presentasi fitur sesuai implementasi.

### Fase F — Kesiapan demo publik (P1, deployment menunggu instruksi)

- [ ] Terapkan batas unggahan, jumlah dokumen/chunk/sesi, umur sesi, dan anggaran konteks agar memori terkendali.
- [ ] Batasi seluruh endpoint generasi, termasuk GET `/api/quiz`; pertimbangkan concurrency, request per pengguna/sesi, serta kuota global provider.
- [ ] Tentukan apakah sesi perlu autentikasi atau token akses; pastikan sesi pengguna tidak dapat dibaca/diubah pengguna lain hanya dengan mengganti ID.
- [ ] Perlakukan isi dokumen sebagai data; uji prompt injection dokumen dan jangan mengizinkan dokumen mengubah kebijakan sistem.
- [ ] Tambahkan logging metode retrieval, error provider, latency, dan penggunaan token tanpa menyimpan secret atau isi dokumen pribadi secara default.
- [ ] Jelaskan persistensi dan penghapusan data. Bila menggunakan filesystem sementara, jangan mengklaim riwayat permanen.
- [ ] Siapkan dokumen contoh, tombol reset, dan error/retry yang mudah dipahami pengunjung.
- [ ] Setelah pengguna melanjutkan deployment: pilih hosting yang sesuai batas biaya/kartu, deploy frontend dan backend, atur origin sebenarnya, lalu uji URL publik.
- [ ] Verifikasi chat, upload, sitasi, kuis, mind map, reload sesi, cold start, serta kegagalan provider dari browser publik.

**Gate F:** aplikasi lengkap berfungsi di URL publik. Landing online saja tidak dihitung sebagai live demo AI. Jika hosting belum tersedia, gunakan video demo lokal dan nyatakan statusnya dengan jelas.

### Fase G — Paket portofolio profesional (P1)

- [ ] Perbarui README: masalah pengguna, target audiens, alur demo, fitur aktif, batas, cara menjalankan, dan konfigurasi tanpa secret.
- [ ] Tambahkan diagram arsitektur: ingest → chunk → index/retrieve → context → generation → citation → learning record.
- [ ] Tulis case study: masalah awal, tiga bug penting, keputusan perbaikan, baseline vs hasil upgrade, dan tradeoff.
- [ ] Publikasikan dataset evaluasi yang boleh dibagikan, konfigurasi, perintah reproduksi, hasil, dan contoh kegagalan.
- [ ] Siapkan 3–5 screenshot serta video demo 60–90 detik yang menunjukkan sumber dan latihan, bukan hanya layar chat.
- [ ] Buat satu slide/kartu ringkas proyek dan teks LinkedIn dengan kontribusi teknis serta hasil yang benar-benar terukur.
- [ ] Rapikan roadmap, lisensi kode/aset, credit, instruksi instalasi, dan status deployment.

**Gate G:** reviewer dapat memahami tujuan, menjalankan atau menonton demo, memeriksa hasil evaluasi, dan mengenali kontribusi developer tanpa membaca seluruh repository.

## 4. Urutan dan estimasi

Estimasi usaha awal untuk satu developer, bukan tanggal janji; dapat berubah setelah baseline.

| Urutan | Fase | Estimasi kerja fokus | Dependensi |
| --- | --- | --- | --- |
| 1 | Baseline + A | 3–5 hari | Repo dan environment lokal tersedia |
| 2 | B | 3–5 hari | Gate A; akses embedding jika menguji dense |
| 3 | C | 2–4 hari | Struktur paket konteks stabil |
| 4 | D | 4–6 hari | Gate A/C; sumber dapat ditelusuri |
| 5 | E | 2–4 hari | Bisa paralel setelah alur utama stabil |
| 6 | F | 2–3 hari | Gate A–E; deployment baru setelah diminta |
| 7 | G | 2–3 hari | Laporan evaluasi dan demo lokal stabil |

Total perkiraan **18–30 hari kerja fokus**. Jadikan setiap fase satu milestone yang dapat ditinjau. Untuk portofolio engineering awal, prioritaskan A–C serta G dengan demo lokal; untuk klaim produk belajar lengkap, selesaikan D–F juga.

## 5. Bukti dan artefak yang disiapkan

| Artefak yang direncanakan | Isi |
| --- | --- |
| `docs/evaluation/` | Dataset, label sumber, konfigurasi, hasil, dan petunjuk reproduksi |
| `docs/architecture.md` | Diagram, kontrak data, keputusan teknologi dan tradeoff |
| `docs/case-study.md` | Before/after, temuan, kontribusi, metrik dan batas |
| `docs/demo/` | Skenario, screenshot dan tautan video; tanpa data pribadi |
| `docs/brand/` | Arah logo, aset final, palet dan aturan pemakaian |
| `README.md` / `DEPLOYMENT.md` | Jalur masuk reviewer, setup dan status layanan sebenarnya |

Lokasi ini rencana keluaran; belum berarti berkas atau hasilnya sudah ada.

## 6. Checklist kelayakan portofolio

- [ ] Bug RAG P0 selesai dan mempunyai bukti regresi.
- [ ] Hasil evaluasi dilaporkan dengan dataset, metode, model, konfigurasi, serta keterbatasan.
- [ ] Sitasi dapat ditelusuri ke konteks yang dipakai model; klaim halaman sesuai metadata.
- [ ] Tidak ada progress palsu, confidence palsu, atau fallback yang menyamar sebagai hasil AI.
- [ ] Kuis/progress berbasis bukti bila ditampilkan sebagai kemampuan produk.
- [ ] README, diagram, case study, screenshot, video, dan logo konsisten.
- [ ] Demo dapat direproduksi lokal; status publik dijelaskan secara akurat.
- [ ] Tidak ada API key, data pengguna, atau artefak credential dalam materi yang dibagikan.
- [ ] Tidak mengklaim “100% akurat”, “anti-halusinasi”, atau peningkatan hasil belajar tanpa penelitian yang mendukung.

## 7. Backlog setelah milestone portofolio

OCR PDF scan, tabel/multimodal, flashcard dan spaced repetition, kolaborasi kelas, audio/video, GraphRAG/agent, serta vector database berskala besar. Pilih berdasarkan kebutuhan dan benchmark setelah fondasi selesai.

Referensi teknis dan produk beserta konteks waktunya tersedia di [review Oktober 2026](docs/REVIEW-2026-10.md). Periksa kembali dokumentasi provider ketika implementasi dimulai karena dukungan model, API, harga, dan batas hosting dapat berubah.
