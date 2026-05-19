"""ScholarBot learning mode templates.

Extracted from app.py Phase 1 refactor.
Each mode provides a starting prompt for specific learning activities.
"""

MODES = {
    "📚 Tutor Mode": "Bantu saya memahami konsep ini secara mendalam dan berikan penjelasan yang mudah dimengerti.",
    "✍️ Rangkum Materi": "Tolong rangkum materi atau teks berikut menjadi poin-poin penting yang mudah diingat:",
    "🧪 Quiz Generator": "Buat 5 soal latihan (pilihan ganda atau essay) beserta kunci jawaban tentang topik:",
    "🗺️ Mind Map": """When the user requests a mind map, automatically generate it in Mermaid.js mindmap syntax compatible with Mermaid Live Editor.
IMPORTANT:
- Output ONLY valid Mermaid code blocks
- Use proper `mindmap` structure
- Keep hierarchy clean and readable
- Generate structured learning trees, not random bullet lists
- Organize concepts from general → specific
- Support nested branches up to 4–5 levels
- Use concise labels
- Avoid overly long text inside nodes
- Make the result visually balanced when rendered
- Ensure compatibility with mermaid.live rendering

OUTPUT FORMAT:

```mermaid
mindmap
  root((Main Topic))
    Branch 1
      Subtopic
        Detail
    Branch 2
      Subtopic
```

Topik yang ingin dibuatkan mind map:""",
    "💡 Rekomendasi Belajar": "Berikan roadmap dan rekomendasi sumber belajar terbaik untuk mempelajari:",
}

MODE_PLACEHOLDERS = {
    "📚 Tutor Mode": "Topik apa yang ingin kamu pelajari lebih dalam?",
    "✍️ Rangkum Materi": "Teks atau materi apa yang ingin dirangkum?",
    "🧪 Quiz Generator": "Topik apa yang ingin dijadikan kuis?",
    "🗺️ Mind Map": "Ketik topik untuk dibuatkan Mind Map (misal: Fotosintesis)...",
    "💡 Rekomendasi Belajar": "Topik apa yang ingin kamu kuasai?",
}
