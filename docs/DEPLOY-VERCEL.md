# ScholarBot: Vercel Hobby + Supabase Free

Status 8 Oktober 2026: proyek `scholarbot-demo-api` sudah dibuat di akun Hobby dan build FastAPI sukses.
URL backend: https://scholarbot-demo-api.vercel.app . Health masih 503 karena Supabase belum dihubungkan.
Secret Groq sudah dikirim sebagai sensitive production environment variable dengan izin pemilik akun.
Frontend holding tetap https://scholarbot-ai-demo.pages.dev/ sampai alur utama lulus uji publik.

## Arsitektur

- Vercel hanya menjalankan FastAPI (`main.py`). Dependencies API ada di pyproject.toml.
- Landing/workspace tetap Cloudflare Pages; Vite hanya menerima URL API, bukan secret.
- `SESSION_BACKEND=supabase`: tiap request membaca sesi dari database, bukan cache proses.
- Riwayat, potongan dokumen, konteks kuis/mode, serta revisi sesi disimpan dalam JSONB.
- Penyimpanan memakai compare-and-swap revisi: konflik tidak menimpa data request lain.
  Jika konflik/penyimpanan gagal setelah chat mulai streaming, output memberi instruksi muat ulang;
  pengguna harus memuat ulang sebelum mengirim ulang. Tidak ada penggabungan otomatis.
- Kuota POST serta GET `/api/quiz` memakai RPC database atomik lintas instance: 10 per menit kalender
  dan 100 per hari UTC. Berbeda dari kuota lokal rolling 60/86400 detik. Restart tidak mereset database.
- Ketika database gagal, API gagal tertutup dengan 503, tanpa fallback file/memori.
- Sesi kedaluwarsa setelah 24 jam sejak simpan terakhir; tidak dapat dibaca setelah itu.
  Baris kedaluwarsa dibersihkan pada penyimpanan berikutnya, bukan janji penghapusan fisik tepat waktu.
- Batas demo: file 1 MB, teks ekstraksi 100000 karakter, 5 dokumen/sesi, pesan 8000 karakter,
  payload sesi 2 MB, 60 pesan/100 skor/50 topik terakhir. PDF kecil masih dapat mengembang dalam memori
  saat ekstraksi; uji beban hosting belum dilakukan.

## Hubungkan Supabase

Gunakan project Free terpisah agar schema/demo tidak mencampuri project lain.
Login CLI lokal tanpa membagikan token di chat:

```powershell
npx --yes supabase login --agent no --output-format text
npx --yes supabase projects list --output json
```

Login dapat diselesaikan di Brave. CLI dan browser login merupakan dua sesi berbeda.
Jika belum ada project demo, pemilik akun menyelesaikan pembuatan project Free dan password database
langsung di dashboard; jangan memilih upgrade berbayar.

Jalankan [schema SQL](../deploy/supabase.sql) di SQL Editor project demo.
Table memakai RLS tanpa policy publik; RPC hanya diberi EXECUTE kepada service_role.
Service role key hanya dipakai backend dan dapat melewati RLS; jangan diberikan ke browser.

Tambahkan environment Production di Vercel project `scholarbot-demo-api`:

- `SUPABASE_URL`: URL project dari dashboard.
- `SUPABASE_SERVICE_ROLE_KEY`: backend service role key, tandai Sensitive.
- `GROQ_API_KEY`: sudah dikonfigurasi; tidak perlu dikirim ulang melalui chat.

Variabel nonsecret dan batas default ada di vercel.json. Jangan set SESSION_BACKEND=local di Vercel.
`.vercelignore` mengecualikan .env, file sesi lokal, environment, frontend, serta evaluasi.

## Deploy dan verifikasi

CLI 63.1.0 gagal auto-setup Services pada repo ini dengan konflik framework/functions.
CLI 50.44.0 berhasil link/build FastAPI; gunakan versi ini untuk reproduksi konfigurasi ini.
Jangan menginstal plugin tambahan yang ditawarkan CLI sebagai syarat deploy.

```powershell
npx --yes vercel@50.44.0 deploy --prod --yes --scope loxleyftscks-projects
```

Setelah environment database tersedia, redeploy agar variabel baru berlaku.
Periksa health (healthy, groq_configured true, session_backend supabase), lalu upload TXT,
reload sesi, chat tentang isi dokumen, kartu sumber/sitasi, kuis, rangkuman, mind map, dan kuota.
Health mengecek koneksi database tetapi tidak membuktikan Groq menerima key.
Uji RPC SQL sebenarnya dan penolakan akses anon sebelum menganggap database siap.
Tes lokal 149 lolos; tes shared store memakai mock sehingga tidak menggantikan uji Supabase.

Setelah backend lulus, build dan publish frontend:

```powershell
$env:VITE_API_BASE_URL='https://scholarbot-demo-api.vercel.app'
npm --prefix scholarbot-web run build:demo
npx wrangler pages deploy dist-demo --project-name scholarbot-ai-demo --branch feature/v3.2-semantic-feedback
```

Pastikan build benar-benar menjadi production Pages, bukan hanya preview. Periksa landing dan reload `/app/`.
Jika gagal, pertahankan/rollback ke holding. Jangan publikasikan klaim demo siap sebelum pemeriksaan publik lolos.

## Batas operasional

Vercel Hobby untuk personal/nonkomersial. Supabase Free dapat dipause setelah seminggu tidak aktif.
Tidak ada ping berkala untuk menghindari batas penyedia. Kuota model Groq tetap berlaku terpisah.
Sesi memakai ID acak sebagai akses, belum login pengguna; gunakan dokumen contoh yang bukan pribadi.
Database belum membatasi jumlah sesi secara global. Pantau ukuran database, request dan penggunaan Groq.
GitHub sudah dihubungkan ke proyek Vercel oleh proses link; push selanjutnya dapat memicu deploy.

Sumber: [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi),
[Hobby](https://vercel.com/docs/plans/hobby), [Supabase Free](https://supabase.com/pricing).
