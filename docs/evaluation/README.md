# Evaluasi ScholarBot — pilot bahasa Indonesia

Mulai dari [hasil dan batas kesimpulan](RESULTS.md). Dataset sintetis `dataset.json` boleh dibagikan dengan CC0-1.0; model mengikuti lisensi repositori asal, weights tidak masuk Git.

Jalankan dari root repo, PowerShell:

```powershell
scholarbot\.venv\Scripts\python.exe -m venv .venv-eval
.venv-eval\Scripts\python.exe -m pip install -r docs/evaluation/requirements-local-lock.txt
.venv-eval\Scripts\python.exe -X utf8 scripts/evaluate_retrieval.py --dense
```

Dua model ONNX int8 dan tokenizer diunduh ke `.eval-cache/`, kemudian dipakai offline. Download hanya dari revision model yang dicatat dalam runner. Environment evaluasi dan weights diabaikan Git dan tidak ditambahkan ke dependency API produksi. Untuk lexical-only, jalankan runner tanpa `--dense` dengan Python API yang sudah memiliki numpy/httpx; status model ditulis `not_run`.

Setiap run menghasilkan manifest, konfigurasi ter-resolve, hash code/dataset/artifact, source snapshot, package version, latency, prediksi query dan metrik per split/kategori. Tuning dan evaluasi tidak digabungkan. Run yang gagal tidak boleh dipresentasikan sebagai angka dense; runner tidak memakai vector palsu.

Uji reproduksi pada dua run lengkap:

```powershell
.venv-eval\Scripts\python.exe -X utf8 scripts/verify_evaluation.py docs/evaluation/runs/20261007T142113Z-68cde39c docs/evaluation/runs/20261007T142115Z-365a263a
```

Raw snapshot memungkinkan memeriksa versi kode pada run sebelum commit. Perintah normal menjalankan kode working tree saat ini; pastikan hash source cocok saat mengklaim reproduksi. Numerical equality diamati pada pasangan run ini, bukan janji lintas OS/CPU/runtime. ONNX artifact bernama avx512_vnni diuji pada CPU mesin ini; CPU lain perlu verifikasi runtime.

Sampel generation optional (mengirim hanya korpus sintetis, memakai kuota Groq yang dikonfigurasi di backend):

```powershell
scholarbot\.venv\Scripts\python.exe -X utf8 scripts/evaluate_answers.py
# Hanya bila run gagal/partial:
scholarbot\.venv\Scripts\python.exe -X utf8 scripts/evaluate_answers.py --resume docs/evaluation/answers/NAMA_RUN
```

API key dibaca dari environment/`scholarbot/.env` dan tidak masuk artifact. Hasil model nondeterministik, temperature=0.7. Review manual tidak otomatis direplikasi atau dianggap lulus pada run baru; periksa semua jawaban/sumber kembali. Biaya tagihan tidak dihitung tanpa data billing. Jangan mengubah label metrik ketepatan ID menjadi dukungan klaim.


Pemeriksaan browser fallback menggunakan API mock, bukan layanan Groq langsung. Jalankan frontend build melalui server lokal, sediakan Playwright/Chrome, lalu:

```powershell
# Jika Playwright tersedia di luar node_modules proyek, set PLAYWRIGHT_MODULE ke lokasi module-nya.
$env:SCHOLARBOT_UI_URL = 'http://127.0.0.1:4180'
node docs/evaluation/check-fallback-ui.cjs
```

Script memeriksa indikator fallback setelah respons streaming. API di-mock seluruhnya; ini tidak menguji ketersediaan hosting atau API provider.
