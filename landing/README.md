# Landing page ScholarBot AI

Halaman statis: HTML, CSS, dan satu berkas JavaScript tanpa dependensi.
Tidak ada langkah build, tidak ada `node_modules`.

## Menjalankan secara lokal

```bash
cd landing && python -m http.server 4177
```

Lalu buka `http://localhost:4177`. Membuka `index.html` langsung lewat `file://`
juga bisa, hanya saja beberapa browser membatasi pemuatan font lokal dari protokol itu.

## Menyebarkan

Unggah seluruh isi folder ini apa adanya ke hosting statis mana pun
(GitHub Pages, Netlify, Vercel, Cloudflare Pages). Tidak ada konfigurasi khusus.

## Struktur

```
landing/
├── index.html      # seluruh markup
├── styles.css      # token desain dicerminkan dari scholarbot-web/tailwind.config.js
├── main.js         # reveal saat scroll, parallax, penghitung, demo chat
├── CREDITS.md      # sumber dan lisensi tiap aset
└── assets/
    ├── fonts/      # DM Serif Display, DM Sans, JetBrains Mono (subset latin)
    ├── icons/      # logo teknologi dari Simple Icons
    └── img/        # dua foto Unsplash + maskot dari repo ini
```

## Catatan implementasi

**Motif catatan kaki.** Penanda `[n]` dipakai di seluruh halaman — di judul, di kartu
fitur, sampai di footer — karena fitur utama produknya memang sitasi inline. Gaya
badge-nya sengaja disamakan dengan komponen React di `scholarbot-web/src/markdown.jsx`.

**Semuanya tetap terbaca tanpa JavaScript.** `main.js` menambahkan kelas `js` ke
elemen `<html>` sebelum paint pertama; hanya setelah itu CSS menyembunyikan elemen
yang akan dianimasikan. Kalau skripnya gagal dimuat, halaman tampil utuh, demo chat
tetap menampilkan jawaban lengkap beserta sitasinya, dan angka metrik tetap benar
karena nilainya ada di markup (skrip hanya menganimasikan hitungannya).

**`prefers-reduced-motion` dihormati.** Sudah diuji: dengan preferensi itu aktif,
53 elemen reveal semuanya tampil, tanpa animasi dan tanpa konten tersembunyi.

**Aset disimpan lokal.** Font, ikon, dan foto diunduh ke repo, bukan hotlink ke CDN,
supaya halaman tidak bergantung pada layanan pihak ketiga saat tampil.
