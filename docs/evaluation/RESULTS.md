# Fase B — Evaluasi retrieval ScholarBot

Tanggal: 7 Oktober 2026. **Benchmark dan pemilihan retrieval selesai secara lokal; kualitas grounding jawaban belum memenuhi gate portofolio.** Deployment tetap ditunda.

BM25 dipilih sebagai default sementara karena seluruh sumber acuan pada pilot tersedia dalam top 3 dan konteks, tanpa model/provider embedding. E5 int8 lebih baik daripada MiniLM int8 pada korpus ini, tetapi fusion tidak memperbaiki recall BM25 dan menambah latency serta memori. Reranker belum beralasan untuk pilot ini. Keputusan berlaku untuk dataset kecil ini dan perlu diperiksa ulang dengan dokumen nyata yang boleh dibagikan.

## Dataset dan desain

[dataset.json](dataset.json): **50 pertanyaan sintetis bahasa Indonesia**, 27 potongan dari 10 dokumen, CC0-1.0. Komposisi: 15 langsung, 10 parafrase, 10 lintas dokumen, 5 follow-up, 10 tanpa jawaban. Jawaban acuan dan ID sumber ditulis dari isi korpus. Terdapat teks teknis, materi pendek, dan satu distractor panjang.

15 tuning dan 35 evaluasi: evaluasi mencakup 28 answerable dan 7 tanpa jawaban. Keluarga pertanyaan yang mengulang fakta/follow-up berada pada split yang sama; tidak ada family ID menyeberang split. Dokumen tetap bersama untuk semua metode. Ini split pertanyaan, bukan pengujian generalisasi ke dokumen baru. Tidak ada pencarian hyperparameter; BM25 k1=1.5/b=0.75, RRF=60, cosine minimal=0.0 ditetapkan sebelum hasil dilihat. Pemilihan kandidat memakai hasil pilot ini, jadi pengujian eksternal baru masih diperlukan.

Chunk sudah dikurasi sebagai paragraf semantik untuk menjaga segmentasi identik. Benchmark ini **tidak mengukur ingest PDF, OCR, chunking otomatis, atau routing follow-up API**. Follow-up memakai `resolved_query` yang telah dilabeli, bukan LLM rewriting. Regresi routing API diuji terpisah.

## Hasil evaluasi

| Metode | Recall@1 | Recall@3 | Recall@5 | Semua gold@5 | Recall sumber dalam konteks | Precision konteks | p50/p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| keyword | 60.1% | 82.7% | 82.7% | 75.0% | 65.5% | 19.9% | 0.20/0.24 |
| bm25 | 79.2% | 100.0% | 100.0% | 100.0% | 100.0% | 41.9% | 0.25/0.49 |
| dense_minilm | 63.1% | 81.5% | 82.7% | 75.0% | 82.7% | 21.4% | 2.45/3.15 |
| rrf_minilm | 77.4% | 91.7% | 100.0% | 100.0% | 100.0% | 26.4% | 2.74/3.47 |
| dense_e5 | 82.7% | 98.2% | 98.2% | 96.4% | 98.2% | 25.7% | 3.49/4.21 |
| rrf_e5 | 82.7% | 100.0% | 100.0% | 100.0% | 100.0% | 26.4% | 3.83/4.98 |

Recall@k adalah rata-rata per pertanyaan dari jumlah sumber gold yang ditemukan dibagi jumlah gold. Untuk lintas dokumen semua gold dihitung; kolom “semua gold” lebih ketat, mengharuskan seluruh ID tersedia. Precision adalah gold ID / ID hasil yang tersedia (macro average), bukan validasi teks jawaban. Kolom konteks dihitung setelah budget 1.200 karakter, termasuk label sumber dan separator. Potongan yang terpangkas tetap dihitung pada level ID; keutuhan klaim dalam teks terpangkas belum dinilai otomatis.

Semua metode mengambil kandidat untuk **7/7 pertanyaan tanpa jawaban**: empty-retrieval rate=0%. Kata kunci/topik yang cocok tidak menjamin fakta yang diminta ada. Angka ini tidak sama dengan kegagalan abstention jawaban model.

Contoh kelemahan keyword: precision rendah karena kata pertanyaan umum dan round-robin mengangkat dokumen lain. Recall sumber setelah batas konteks turun menjadi 65,5%. BM25 menyaring stopword dan mengurutkan skor global; hasil ini membandingkan paket tokenizer+ranking+diversifikasi, bukan mengisolasi efek formula BM25 saja.

## Model, sumber daya, dan biaya

Dua model memakai **ONNX dynamic int8** dengan mean pooling bertopeng attention dan normalisasi L2, CPUExecutionProvider, 2 thread, batch 8, seed konfigurasi 0. MiniLM memakai batas 256 token tanpa prefix; E5 memakai batas 512 dengan `query: ` dan `passage: `. Revision dan SHA-256 tokenizer/weights disimpan dalam manifest. API embedding lama tidak digunakan untuk menghasilkan angka dense ini.

Model MiniLM 22.0 MiB; E5 112.9 MiB. Satu input MiniLM terpangkas; E5 nol. Total token encoding korpus+50 query: MiniLM 2454, E5 1815. Waktu index, load, RSS dan peak working set tercatat per run. RSS proses bukan tambahan RAM satu model dan run memuat kedua model berurutan; jangan menyimpulkan dari angka itu bahwa hosting 512 MB aman.

Latency tabel adalah encoding query sekali + ranking, dengan model dimuat dan index korpus siap; bukan waktu API, download, generation, atau cold start hosting. Latency query cached/ranking saja tersimpan per prediksi. Kondisi mesin: Windows CPU `AMD64 Family 25 Model 116 Stepping 1, AuthenticAMD`. Run awal termasuk download disimpan, sedangkan tabel menggunakan cache weights hangat. Warm-load/index dicatat terpisah. Tidak ada biaya provider embedding (0 panggilan); komputasi lokal tidak berarti tanpa biaya sumber daya.

## Sampel jawaban langsung dan review

14 panggilan Groq pada `openai/gpt-oss-120b` dengan temperature=0.7, max_tokens=900, BM25 top3 dan budget konteks aplikasi. Sampel dipilih sebelum panggilan: 7 answerable, semua 7 no-answer pada split evaluasi. Ini prompt RAG komponen, bukan end-to-end browser/streaming/history.

- **14/14 penanda sitasi** merujuk ID konteks yang benar-benar diberikan.
- **7/7 no-answer** menyatakan data yang diminta tidak tersedia; tidak mengarang nilai spesifik.
- Pemeriksaan manual Codex atas 14 unit bersitasi menemukan **10/14 sepenuhnya didukung (71,4%)** menurut rubric konservatif pada paragraf/kalimat/sel yang membawa marker. Unit lain menambah contoh/fakta luar sumber: glukosa, username/password, cuaca mendung/malam, dan hash “unik”. Ini ketidakcukupan bukti sumber, bukan pernyataan bahwa semua detail tersebut salah secara umum.
- Detail tambahan tanpa sitasi juga muncul, misalnya jenis struktur indeks dan klaim performa retrieval. Cakupan semua klaim belum dihitung, dan target ≥90% klaim atomik **belum dapat dinyatakan lolos**.
- Token aktual: prompt=12414, completion=4434, total=16848. p50/p95 generation 5941/8635 ms. Biaya tagihan provider belum diperiksa; tidak diklaim gratis berdasarkan token ini.

Respons mentah, usage, sumber, dan catatan penilaian tersedia di [sampel respons](answers/20261007T141555Z/responses.json), [review manual](answers/20261007T141555Z/manual-review.json), dan [ringkasan](answers/20261007T141555Z/summary.json). Review bukan penilai manusia independen, bukan Ragas, dan sampelnya kecil. Ada sitasi valid secara ID yang masih membawa detail di luar bukti—alasan untuk tidak menyebut sistem anti-halusinasi.

## Perubahan aplikasi

`RETRIEVAL_METHOD` mendukung `bm25` (default), `keyword`, dan `dense`. Nama fungsi `hybrid_retrieve` dipertahankan untuk kompatibilitas; dense dengan fallback bukan fusion. BM25 tidak meminta embedding ketika retrieval. Proses chunking semantic opsional masih dapat meminta embedding bila provider dikonfigurasi.

Embedding: validasi matriks 2D, jumlah vector, dimensi model yang dikenal, nilai finite, norm nonzero, batch ≤32, dan dimensi antar batch/query. Cache membawa identitas model, revision, endpoint, prefix dan hash isi serta bertahan saat sesi disimpan. Vector lama tanpa identitas dihasilkan ulang; query yang dimensinya berbeda memakai fallback keyword yang dilaporkan. Respons provider/log tidak mencetak token atau body error.

Chat memaparkan `X-Retrieval-Status`, menyimpan metode/fallback dalam pesan dan menampilkan fallback di UI. Pencarian dalam dokumen memakai jalur retrieval yang sama dan selalu mengembalikan objek `results`; sebelumnya fallback mengembalikan array yang tidak dibaca UI. Fusion hanya berada dalam evaluasi. Threshold semantic 0 belum dikalibrasi untuk penolakan, sehingga mode dense belum layak dianggap detektor kecukupan bukti.

## Reproduksi dan validasi

Run utama: [20261007T142113Z-68cde39c](runs/20261007T142113Z-68cde39c/manifest.json). Pengulangan: [20261007T142115Z-365a263a](runs/20261007T142115Z-365a263a/manifest.json). [Verifier](runs/20261007T142115Z-365a263a/reproduction.json) memeriksa hash code/dataset/hasil dan menghitung ulang agregat: **300 pasangan ranking, skor dan konteks identik**. Latency tidak identik dan tidak dijanjikan stabil. Source snapshot disimpan karena working tree belum di-commit. Percobaan float penuh yang dihentikan dan run eksplorasi tetap dicatat, tidak dipakai pada tabel utama.

139 tes backend/core relevan lolos, 10 pemeriksaan markdown lolos, build React lolos, dan smoke browser dengan API mock membuktikan fallback terlihat setelah streaming tanpa error JavaScript. Tiga suite UI Streamlit tetap dikecualikan karena dependency tidak tersedia. Warning bundle >500 kB dan deprecation TestClient masih ada.

## Gate dan tindak lanjut

Gate B untuk dataset, perbandingan reproducible dan alasan pemilihan retrieval terpenuhi. Gate kualitas keseluruhan belum ditutup: target grounding ≥90% klaim belum terbukti; confidence atas penolakan 7 kasus masih terbatas; Gate A8 tentang token budget seluruh request juga terbuka.

Sebelum klaim portofolio/live demo: perlu memperketat pemisahan detail luar sumber, anotasi klaim atomik dengan reviewer independen, menambah korpus dokumen nyata berizin dan pertanyaan berambiguitas, serta menguji ulang hasil model saat temperature/history berbeda. Jangan menambahkan reranker atau model besar hanya untuk mengejar nama teknologi. Fase C berikutnya dapat menjaga metadata/traceability, tetapi tidak menggantikan pekerjaan grounding yang tersisa.

## Referensi implementasi

Dokumentasi [Hugging Face feature extraction](https://huggingface.co/docs/inference-providers/tasks/feature-extraction) untuk authentication/output/prefix API; kartu model [MiniLM](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) dan [multilingual E5](https://huggingface.co/intfloat/multilingual-e5-small) untuk batas/pooling/prefix. Ketersediaan inference provider tidak disamakan dengan kemampuan menjalankan artifact ONNX lokal.
