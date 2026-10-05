# Live demo gratis: Cloudflare Pages + Render

Landing ada di `/`, workspace React di `/app/`, dan FastAPI di Render.
Jangan unggah `.env` atau memasukkan GROQ_API_KEY sebagai variabel Vite: semua variabel Vite dapat dibaca pengunjung.

## 1. Backend Render

Push perubahan ke GitHub, kemudian di https://dashboard.render.com pilih **New > Blueprint** dan hubungkan repository ini serta branch yang memuat `render.yaml`.
Blueprint secara eksplisit memilih **Free**; jangan menggantinya dengan paket berbayar.

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
Unggahan dibatasi 5 MB per file. Blueprint membatasi seluruh POST menjadi 10 permintaan per menit untuk semua pengunjung bersama; batas ini tidak menggantikan kuota harian Groq. Pantau penggunaan di dashboard Groq, dan suspend backend saat demo tidak diperlukan.
Satu worker dipakai karena sesi dan pembatas permintaan masih di memori. Demo ini belum memakai autentikasi atau penyimpanan permanen.
Retrieval semantik menggunakan layanan eksternal dan memiliki fallback keyword; kualitas retrieval dapat berbeda ketika layanan embedding tidak tersedia.

## Build lokal

PowerShell:

```powershell
$env:VITE_API_BASE_URL = 'https://URL-BACKEND-YANG-SEBENARNYA.onrender.com'
npm --prefix scholarbot-web run build:demo
```

Output `dist-demo` tidak memuat kode Python, storage sesi, atau `.env`.
Untuk preview dengan backend lokal port 8000, jalankan `npm --prefix scholarbot-web run build:demo -- --local`, lalu sajikan `dist-demo` pada `http://127.0.0.1:4175`. Jangan unggah build `--local`; bangun ulang dengan URL Render untuk publikasi.

Referensi: [Render Free](https://render.com/docs/free), [Render Blueprint](https://render.com/docs/blueprint-spec), [Cloudflare Vite](https://developers.cloudflare.com/pages/framework-guides/deploy-a-vite3-project/).
