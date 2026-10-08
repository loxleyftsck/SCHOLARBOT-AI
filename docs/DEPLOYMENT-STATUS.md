# Status deployment — 8 Oktober 2026

Target: demo portofolio Cloudflare Pages Free + Render Free Web Service + Groq Free. Paket berbayar tidak dipilih.

## Hasil aktual

- GitHub dan Cloudflare OAuth masih terhubung.
- Akun Render dapat diakses, tetapi daftar services kosong.
- Pembuatan `scholarbot-demo-api` dengan `--plan free` ditolak HTTP 402: payment information required. Backend tidak dibuat, dan belum ada URL API publik yang dapat diuji.
- Landing holding sebelumnya: https://scholarbot-ai-demo.pages.dev/ . Ini bukan bukti live demo AI; status belum siap harus tetap terlihat sampai backend aktif.
- Build lokal landing + workspace tersedia pada http://127.0.0.1:4175/ dan `/app/`; backend lokal pada port 8000. Endpoint health dan aset sudah diverifikasi lokal pada sesi sebelumnya.

## Persiapan yang selesai

- Batas global 10 request/menit serta 100 request/24 jam bergulir pada satu worker untuk seluruh POST dan GET `/api/quiz`.
- GET health/session tidak ikut diblokir ketika kuota demo habis.
- Retry-After dan CORS pada respons 429 tetap dapat dibaca frontend.
- BM25 dipilih eksplisit dalam konfigurasi Render, tanpa model embedding lokal.
- 143 tes backend/core relevan lolos; tiga suite UI Streamlit tidak dijalankan karena dependency tidak tersedia.
- `.env`, data sesi, OAuth credentials, bobot model, dan environment lokal tidak diikutkan Git.

Kuota ini ada di memori dan reset ketika proses restart. Ini bukan jaminan batas token provider atau proteksi penyalahgunaan yang lengkap.

## Langkah yang menunggu pemilik akun

Pemilik akun memilih apakah bersedia menyelesaikan verifikasi Render di https://dashboard.render.com/billing. Informasi kartu hanya dimasukkan pada dashboard penyedia. Jika tetap tanpa kartu, backend membutuhkan penyedia alternatif yang lolos pemeriksaan paket/akses akun; jangan menganggap deploy Render berhasil atau beralih diam-diam ke layanan berbayar.

Setelah backend tersedia: masukkan secret Groq di backend, set origin Pages yang sebenarnya, deploy backend dari branch ini, bangun frontend menggunakan URL API HTTPS yang diberikan Render, lalu verifikasi chat, upload, sumber, kuis, mind map, routing `/app/`, kuota dan cold start melalui URL publik.

## Pemulihan

Jika health atau alur utama gagal, jangan publikasikan build aplikasi sebagai live demo. Pertahankan landing holding, periksa log backend tanpa mencetak secret, dan rollback frontend ke deployment holding sebelumnya bila diperlukan. Jangan menggunakan ping berkala untuk menghindari sleep paket gratis.
