# Hasil implementasi inti Fase A

Tanggal: 7 Oktober 2026. Perubahan lokal; tidak dideploy atau dipush pada tahap ini.

## Perubahan

- Keyword tanpa overlap bernilai nol; frekuensi kata dihitung sebagai token utuh.
- Pertanyaan yang menyebut file/dokumen memakai RAG; kontrol eksplisit tidak memanggil retrieval.
- Follow-up menggunakan pertanyaan sebelumnya/ekspansi konteks. Pergantian mode tidak membawa konteks kuis lama.
- Chunk paragraph/size/semantic dan fallback memakai batas ukuran; teks pendek serta akhir dokumen tidak dibuang. Potongan yang dipecah ulang tidak mempertahankan embedding lama yang tidak lagi cocok.
- Pemilihan konteks menghitung overhead label sitasi dan separator dalam anggaran 1.200 karakter. Prompt, header, kartu sumber, dan sumber yang disimpan menggunakan paket terpilih yang sama.
- Prompt dokumen memisahkan pengetahuan tambahan dan menginstruksikan pernyataan sumber tidak cukup. Ini instruksi, bukan bukti bahwa semua jawaban model sudah benar.
- Kuis/mind map gagal mengembalikan HTTP 503; UI menunjukkan error, tidak membuat soal atau node generik.
- Progress awal ditampilkan sebagai belum dinilai. Penilaian konsep nyata masih pekerjaan Fase D.
- Skor retrieval tidak ditampilkan sebagai persen confidence. Klaim nomor halaman di landing diganti dengan potongan sumber.
- Mode rangkuman mempunyai instruksi cakupan. Ini belum rangkuman menyeluruh seluruh dokumen.
- History pada chat API dibatasi 16.000 karakter, menjaga giliran terbaru tanpa assistant di awal. Ini bukan tokenizer model dan belum membatasi seluruh input.
- Artefak lokal `.wrangler/` diabaikan Git.

## Verifikasi

1. Backend/core: `scholarbot/.venv/Scripts/python.exe -m pytest scholarbot/tests --ignore=scholarbot/tests/test_react_bridge.py --ignore=scholarbot/tests/test_streaming_manager.py --ignore=scholarbot/tests/test_ui_tokens.py -q` — **119 passed**.
2. Test baru: `scholarbot/tests/test_rag_regressions.py` — **35 kasus** untuk retrieval, routing, coverage/batas chunk, budget konteks, konsistensi sumber, follow-up, pergantian mode dan error generasi. Provider dimock agar deterministik; fixture API baru tidak menyimpan sesi ke disk.
3. `npm --prefix scholarbot-web run build` — berhasil. Vite masih memberi peringatan bundle lebih dari 500 kB; optimasi belum dilakukan.
4. `npm --prefix scholarbot-web run check:markdown` — **10 pemeriksaan lolos**.
5. Browser pada build lokal dengan respons API dimock: tiga topik awal belum dinilai; kegagalan kuis tidak menampilkan soal statis atau submit skor; kegagalan mind map tidak membuat node; tidak ada JavaScript error.
6. `git diff --check` — bersih.

Suite UI Streamlit tidak dijalankan pada environment API. Ada warning deprecation dari TestClient/HTTPX; test tetap lolos. Tidak ada klaim benchmark terhadap provider embedding aktif, kualitas jawaban Groq langsung, atau peningkatan hasil belajar pengguna.

## Sisa sebelum menutup Gate A

- Anggaran token seluruh request (system, pertanyaan, history dan output reserve), dengan perilaku jelas untuk pertanyaan terlalu panjang; pendekatan karakter saat ini harus diberi label estimasi.
- Kebijakan ringkasan history dan pemulihan konteks mode/follow-up setelah restart.
- Evaluasi manual kepatuhan jawaban terhadap bukti; sitasi ber-ID valid belum membuktikan klaim didukung.
- Uji validasi schema JSON generasi lebih lengkap; respons JSON yang sintaksnya valid tetapi strukturnya salah belum tervalidasi menyeluruh.

Fase B selanjutnya membangun dataset Indonesia dan mengukur retrieval. Hybrid fusion, metadata halaman, kuis berbasis dokumen, logo baru, dan deployment belum diimplementasikan pada tahap ini.
