# Status deployment — 8 Oktober 2026

Target aktif: Cloudflare Pages Free + Vercel Hobby + Supabase Free + Groq.
Render dibatalkan karena akun meminta billing; alwaysdata ditunda sesuai pilihan pengguna.

## Selesai

- Vercel CLI login sebagai loxleyftsck; scope loxleyftscks-projects terdeteksi Hobby.
- Proyek scholarbot-demo-api dibuat, repository GitHub dihubungkan, build FastAPI berhasil.
- URL API: https://scholarbot-demo-api.vercel.app . Build sukses bukan berarti live demo AI siap.
- GROQ_API_KEY tersimpan sebagai sensitive secret production setelah izin eksplisit pengguna.
- Konfigurasi serverless membaca sesi dari Supabase, menyimpan revisi, dan memakai kuota database atomik.
- 149 tes API/core/RAG/kuota/storage lolos. Tes shared store memakai mock; RPC SQL belum diuji di server.
- Frontend holding tetap https://scholarbot-ai-demo.pages.dev/ . Full workspace belum dipublikasikan ulang.

## Belum selesai

- Supabase CLI belum login. Login GitHub di Brave tidak otomatis menghubungkan CLI/browser in-app.
- SUPABASE_URL dan SUPABASE_SERVICE_ROLE_KEY belum dikonfigurasi di Vercel.
- Schema SQL belum dijalankan pada project demo Free.
- Health publik terverifikasi 503: Penyimpanan demo belum dikonfigurasi.
- Upload/chat/RAG/sitasi/kuis/mind map serta kuota publik belum diuji.

Panduan dan langkah berikutnya: [Vercel](DEPLOY-VERCEL.md).
Pertahankan landing holding hingga backend dan alur utama siap. Tidak ada paket berbayar dipilih.
