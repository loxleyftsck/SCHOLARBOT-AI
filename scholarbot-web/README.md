# 🎓 ScholarBot — AI Native Web Workspace (Next-Gen React Migration)

Workspace belajar interaktif yang dimigrasi sepenuhnya ke arsitektur web modern menggunakan **React, Vite, Tailwind CSS, dan Framer Motion** untuk menghadirkan micro-animation premium kelas dunia.

## 🚀 Fitur Unggulan
1.  **Warm Cream Editorial Aesthetic**: Desain visual minimalis dengan font serif elegan, palet warna beige/cream yang cozy, dan tata letak bebas gangguan (*clutter-free*).
2.  **Breathtaking Framer Motion Animations**:
    *   *Floating 3D Mascot*: Maskot robot 3D interaktif yang melayang secara halus di layar selamat datang.
    *   *Smooth Slide Transitions*: Efek transisi pudar (*fade*) dan geser (*slide*) super halus ketika beralih antar mode belajar.
    *   *Staggered List Animation*: Suggestion chips yang meluncur masuk satu per satu secara beruntun.
3.  **Interactive Visual Mind Map**: Peta konsep berbentuk pohon nodus interaktif yang dapat diklik untuk meluaskan penjelasan subtopik secara langsung dengan kalkulasi koordinat visual.
4.  **Premium Latihan Soal (Quiz Cerdas)**: Widget kuis interaktif dengan skor dinamis, validasi jawaban benar/salah instan, dan visual perayaan skor 100 dengan efek *sparkle explosion*.
5.  **Multi-Document RAG Upload**: Area unggah dokumen PDF/TXT langsung di sidebar dengan integrasi pratinjau daftar berkas aktif.
6.  ** Walnut Circular Input Bar**: Bar pencarian premium yang serasi dengan mockup, lengkap dengan tombol kirim sirkular walnut yang responsif.

---

## 🛠️ Cara Menjalankan Halaman Web (Lokal)

Pastikan komputer Anda sudah terinstall **Node.js** (versi 18 ke atas disarankan).

1.  **Masuk ke direktori web app**:
    ```bash
    cd scholarbot-web
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Jalankan dev server**:
    ```bash
    npm run dev
    ```

4.  **Akses aplikasi**:
    Buka peramban browser Anda di alamat: `http://localhost:3000` (atau port yang tertera pada terminal).

---

## 📂 Struktur Direktori Workspace Baru
```
scholarbot-web/
├── index.html          # File HTML utama dengan link Google Fonts
├── package.json        # Manifest package dengan library Framer Motion & Lucide
├── tailwind.config.js  # Token sistem desain editorial warm beige
├── vite.config.js      # Konfigurasi server port 3000
└── src/
    ├── main.jsx        # File entry point react
    ├── index.css       # Style Tailwind dan global scrollbar
    └── App.jsx         # Komponen tunggal (SPA) terpadu dengan state & animasi
```

---

*Selamat mengeksplorasi workspace belajar masa depan Anda!* 🎓✨
