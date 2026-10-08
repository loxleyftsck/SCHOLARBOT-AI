# Live demo gratis: Cloudflare Pages + Render

Landing ada di `/`, workspace React di `/app/`, dan FastAPI di Render.
Jangan unggah `.env` atau memasukkan GROQ_API_KEY sebagai variabel Vite: semua variabel Vite dapat dibaca pengunjung.

## 1. Backend Render

Push perubahan ke GitHub, kemudian di https://dashboard.render.com pilih **New > Blueprint** dan hubungkan repository ini serta branch yang memuat `render.yaml`.
Blueprint secara eksplisit memilih **Free**; jangan menggantinya dengan paket berbayar.
Jika Render mengembalikan `402` atau `need_payment_info`, akun perlu diverifikasi melalui dashboard Billing sebelum layanan dapat dibuat. Verifikasi harus diselesaikan pemilik akun; jangan membagikan informasi kartu melalui chat. Render menyebut transaksi verifikasi US$1 yang dikembalikan setelah selesai. Paket Free tetap memiliki batas penggunaan; penggunaan bandwidth di luar kuota dapat dikenakan biaya bila metode pembayaran tersimpan.

Isi variabel yang diminta:

- `GROQ_API_KEY`: masukkan melalui dashboard Render, bukan chat atau GitHub.
- `ALLOWED_ORIGINS`: URL Pages yang sebenarnya, tanpa garis miring akhir, misalnya `https://nama-project.pages.dev`. Jika belum tersedia, set setelah langkah 2.

Salin URL backend yang diberikan Render. Buka `<URL-backend>/api/health`; hasil harus `status: healthy` dan `groq_configured: true`.
Nama service tidak menjamin nama subdomain; gunakan URL yang benar-benar diberikan dashboard.

## 2. Cloudflare Pages

Di https://dash.cloudflare.com pilih **Workers & Pages > Create application > Pages > Connect to Git** dan hubungkan repository serta branch deployment.

| Pengaturan | Nilai |
| --- | --- |
| Framework preset | None |
| Root directory | kosong (root repo) |
| Build command | `npm --prefix scholarbot-web ci && npm --prefix scholarbot-web run build:demo` |
| Build output directory | `dist-demo` |
| Environment variable | `VITE_API_BASE_URL` = URL HTTPS Render yang sebenarnya |
| Node version | `NODE_VERSION` = `22` |

Set `VITE_API_BASE_URL` pada environment Production; jika memakai Preview, set juga pada Preview.
Alternatif upload langsung dari perangkat yang sudah login: `npx wrangler pages deploy dist-demo --project-name scholarbot-ai-demo --branch feature/v3.2-semantic-feedback`. Proyek upload langsung tidak otomatis membangun ulang ketika GitHub berubah; jalankan build dan deploy lagi setelah perubahan.
Build demo sengaja gagal jika URL HTTPS backend belum diisi. Setelah Pages memberi URL publik, masukkan URL tersebut ke `ALLOWED_ORIGINS` Render lalu redeploy backend.
Origin preview hanya diizinkan jika ditambahkan secara eksplisit, dipisah koma. CORS bukan autentikasi dan tidak mencegah akses langsung ke API.

## 3. Verifikasi sebelum dibagikan

1. Buka landing, klik **Coba live demo**, dan reload `/app/` untuk memeriksa routing serta aset.
2. Tunggu status **Demo siap**, lalu kirim pertanyaan pendek.
3. Unggah TXT contoh, tanyakan isinya, lalu periksa kartu sumber dan sitasi.
4. Coba kuis, rangkuman, dan mind map; periksa Console/Network jika ada kegagalan.
5. Coba lewat ponsel atau jendela privat untuk memastikan CORS bekerja.

## Batas demo

Render Free dapat tidur setelah 15 menit tanpa trafik dan biasanya membutuhkan sekitar satu menit untuk bangun. UI mencoba health check saat aplikasi dibuka, maksimal sekitar 90 detik, tanpa ping berkala untuk mencegah server tidur.
Riwayat dan dokumen memakai memori serta filesystem sementara; data dapat hilang saat restart, redeploy, atau server tidur. Jangan gunakan dokumen pribadi.
Unggahan dibatasi 5 MB per file. Blueprint membatasi seluruh POST dan GET `/api/quiz` menjadi 10 permintaan per menit dan 100 permintaan dalam 24 jam bergulir untuk semua pengunjung bersama. Kuota disimpan pada satu worker dan reset saat restart; ini tidak menggantikan batas token dan kuota akun Groq. Pantau penggunaan di dashboard Groq, dan suspend backend saat demo tidak diperlukan.
Satu worker dipakai karena sesi dan pembatas permintaan masih di memori. Demo ini belum memakai autentikasi atau penyimpanan permanen.
Retrieval default memakai BM25 lokal berdasarkan hasil pilot Fase B. Mode dense bersifat opsional dan memakai fallback keyword yang ditampilkan jika provider embedding tidak tersedia.

## Build lokal

PowerShell:

```powershell
$env:VITE_API_BASE_URL = 'https://URL-BACKEND-YANG-SEBENARNYA.onrender.com'
npm --prefix scholarbot-web run build:demo
```

Output `dist-demo` tidak memuat kode Python, storage sesi, atau `.env`.
Untuk preview dengan backend lokal port 8000, jalankan `npm --prefix scholarbot-web run build:demo -- --local`, lalu sajikan `dist-demo` pada `http://127.0.0.1:4175`. Jangan unggah build `--local`; bangun ulang dengan URL Render untuk publikasi.

Referensi: [Render Free](https://render.com/docs/free), [Render Blueprint](https://render.com/docs/blueprint-spec), [Cloudflare Vite](https://developers.cloudflare.com/pages/framework-guides/deploy-a-vite3-project/).
