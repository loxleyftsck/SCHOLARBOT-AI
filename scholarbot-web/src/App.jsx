import React, { useState, useEffect, useRef } from 'react';
import { 
  motion, 
  AnimatePresence 
} from 'framer-motion';
import { 
  BookOpen, 
  FileText, 
  Compass, 
  Share2, 
  History, 
  Upload, 
  Trash2, 
  Crown, 
  Send, 
  Check, 
  CornerDownRight, 
  Bot, 
  User, 
  Award,
  Sparkles,
  ArrowRight,
  Maximize2,
  ChevronDown,
  RefreshCw,
  Plus,
  HelpCircle,
  X
} from 'lucide-react';

// ─── STATIC DATA & ASSETS ──────────────────────────────────────────────────────

const PERSONALITIES = {
  "😊 Santai & Friendly": "Menjelaskan materi dengan bahasa santai, penuh analogi kehidupan sehari-hari.",
  "🧠 Akademik & Detil": "Bahasa formal akademis, referensi ilmiah, terstruktur, dan sangat mendalam.",
  "💡 Kreatif & Interaktif": "Mengajak berpikir kritis dengan teka-teki, pertanyaan balik, dan skenario seru."
};

const SUGGESTION_CHIPS = [
  "Jelaskan Teorema Pythagoras",
  "Rangkum Perang Dunia II",
  "Apa itu Machine Learning?",
  "Buat soal Stoikiometri Kimia"
];

// Mock AI response generator based on question and mode
const generateAIResponse = (question, mode, personality) => {
  const lowercaseQ = question.toLowerCase();
  
  if (mode === "rangkuman" || lowercaseQ.includes("rangkum")) {
    return `### ✍️ RANGKUMAN MATERI: ${question}\n\nBerikut adalah poin-poin penting terstruktur untuk pemahaman cepat:\n\n*   **Intisari Utama**: Topik ini membahas konsep mendasar mengenai struktur, mekanisme operasional, dan aplikasi praktis di dunia nyata.\n*   **Komponen Kunci**:\n    1.  *Landasan Teoretis*: Aturan universal yang mendasari fenomena ini.\n    2.  *Metodologi*: Langkah taktis sistematis untuk menyelesaikan studi kasus.\n    3.  *Variabel Pendukung*: Faktor eksternal yang memengaruhi hasil akhir.\n*   **Kesimpulan Praktis**: Memahami topik ini mempermudah penyelesaian masalah analisis tingkat lanjut.\n\n*Analisis disesuaikan dengan gaya ${personality}.*`;
  }
  
  if (mode === "latihan" || lowercaseQ.includes("soal") || lowercaseQ.includes("kuis")) {
    return `### 🧪 GENERATOR LATIHAN SOAL\n\nSaya telah membuat kuis interaktif berdasarkan topik **${question}**.\n\nSilakan gunakan panel **Latihan Soal** di bawah untuk menjawab pertanyaan pilihan ganda secara langsung dengan visual interaktif!`;
  }

  if (mode === "mindmap" || lowercaseQ.includes("mind map") || lowercaseQ.includes("peta konsep")) {
    return `### 🗺️ MIND MAP GENERATED\n\nSaya telah memetakan struktur kognitif untuk **${question}**.\n\nAnda dapat mengeksplorasi peta konsep interaktif ini pada tab **Mind Map** di sebelah kiri untuk melihat keterkaitan antar konsep secara visual.`;
  }

  // Default chat response
  if (lowercaseQ.includes("pythagoras")) {
    return `### 📐 Teorema Pythagoras\n\nTeorema Pythagoras menyatakan bahwa pada **segitiga siku-siku**, kuadrat panjang sisi miring (hipotenusa) sama dengan jumlah kuadrat panjang sisi-sisi siku-sikunya.\n\n$$\na^2 + b^2 = c^2\n$$\n\n*   **a & b**: Sisi-sisi siku-siku (tegak dan mendatar)\n*   **c**: Sisi miring (terpanjang)\n\n**Contoh Analogi Nyata (${personality})**:\nBayangkan Anda ingin menyeberangi lapangan rumput berbentuk persegi panjang. Daripada berjalan memutari tepi lapangan (sisi tegak lalu mendatar), Anda berjalan memotong secara diagonal (sisi miring). Jarak diagonal ini selalu mengikuti aturan Pythagoras!`;
  }

  if (lowercaseQ.includes("machine learning") || lowercaseQ.includes("ml")) {
    return `### 🧠 Pengantar Machine Learning\n\n**Machine Learning (ML)** adalah cabang dari kecerdasan buatan (AI) yang fokus pada pengembangan sistem agar mampu belajar mandiri dari data tanpa perlu diprogram secara eksplisit.\n\n*   **Supervised Learning**: Belajar dari data yang sudah diberi label (contoh: memprediksi harga rumah dari data historis).\n*   **Unsupervised Learning**: Menemukan pola tersembunyi dari data tanpa label (contoh: mengelompokkan segmen pelanggan).\n*   **Reinforcement Learning**: Belajar melalui trial-and-error berdasarkan sistem reward dan punishment.\n\n*Gaya penjelasan saat ini mengikuti kepribadian: **${personality}**.*`;
  }

  return `### 🎓 Penjelasan Materi: ${question}\n\nTerima kasih atas pertanyaannya! Berdasarkan gaya **${personality}**, mari kita bedah konsep ini:\n\n1.  **Definisi Dasar**: Ini adalah pilar fundamental yang wajib dipahami terlebih dahulu.\n2.  **Cara Kerja**: Sistem bekerja secara runtut berdasarkan input data yang masuk.\n3.  **Aplikasi Praktis**: Digunakan secara luas di industri modern dan akademisi.\n\nAda poin spesifik yang ingin Anda bahas lebih dalam?`;
};

// ─── SUB-COMPONENTS ───────────────────────────────────────────────────────────

// Floating 3D-styled Mascot Animation
function AnimatedMascot() {
  return (
    <motion.div 
      className="relative w-44 h-44 flex items-center justify-center cursor-pointer"
      animate={{ 
        y: [0, -10, 0],
        rotate: [0, 1, -1, 0]
      }}
      transition={{ 
        duration: 5,
        repeat: Infinity,
        ease: "easeInOut"
      }}
      whileHover={{ scale: 1.05 }}
    >
      {/* Sparkle effects around mascot */}
      <motion.div 
        className="absolute top-2 left-6 text-primary"
        animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.2, 0.8] }}
        transition={{ duration: 3, repeat: Infinity, delay: 0.5 }}
      >
        <Sparkles className="w-5 h-5 fill-current" />
      </motion.div>
      <motion.div 
        className="absolute bottom-6 right-2 text-primary"
        animate={{ opacity: [0.2, 0.9, 0.2], scale: [0.7, 1.1, 0.7] }}
        transition={{ duration: 2.5, repeat: Infinity, delay: 1 }}
      >
        <Sparkles className="w-4 h-4 fill-current" />
      </motion.div>

      {/* Main Mascot Image Container */}
      <div className="w-36 h-36 rounded-full bg-surface-raised border border-border flex items-center justify-center overflow-hidden shadow-lg p-2">
        {/* Render a beautifully styled Mascot Illustration (Graduation cap robot reading book) */}
        <svg viewBox="0 0 200 200" className="w-full h-full text-walnut" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="100" cy="100" r="70" fill="#FAF6F0" stroke="#4A3728" strokeWidth="4"/>
          {/* Glasses / Face screen */}
          <rect x="50" y="70" width="100" height="50" rx="25" fill="#1C1814" stroke="#4A3728" strokeWidth="3" />
          {/* Eyes */}
          <path d="M 70 95 C 75 90, 85 90, 90 95" stroke="#FAF6F0" strokeWidth="4" strokeLinecap="round" fill="none"/>
          <path d="M 110 95 C 115 90, 125 90, 130 95" stroke="#FAF6F0" strokeWidth="4" strokeLinecap="round" fill="none"/>
          {/* Smiling Mouth */}
          <path d="M 85 138 Q 100 152 115 138" stroke="#4A3728" strokeWidth="4" strokeLinecap="round" fill="none"/>
          {/* Graduation Cap */}
          <path d="M 100 20 L 165 42 L 100 64 L 35 42 Z" fill="#4A3728" stroke="#1C1814" strokeWidth="2"/>
          <rect x="80" y="44" width="40" height="22" fill="#4A3728" stroke="#1C1814" strokeWidth="2"/>
          {/* Tassel */}
          <path d="M 165 42 L 165 75 C 165 80, 160 85, 165 90" stroke="#8B6914" strokeWidth="2" strokeLinecap="round" fill="none"/>
          <rect x="161" y="90" width="8" height="12" rx="2" fill="#8B6914" />
        </svg>
      </div>
    </motion.div>
  );
}

// Interactive Mind Map Component
function InteractiveMindMap({ topic = "Machine Learning" }) {
  const [activeNode, setActiveNode] = useState(null);
  
  const nodes = [
    { id: 1, label: topic, x: 250, y: 150, type: 'root', desc: 'Topik utama yang sedang kita bedah bersama.' },
    { id: 2, label: 'Supervised', x: 120, y: 80, type: 'branch', desc: 'Belajar dari data berlabel. Contoh: Regresi & Klasifikasi.' },
    { id: 3, label: 'Unsupervised', x: 380, y: 80, type: 'branch', desc: 'Mencari struktur tersembunyi tanpa label. Contoh: Clustering.' },
    { id: 4, label: 'Reinforcement', x: 250, y: 250, type: 'branch', desc: 'Sistem belajar mandiri menggunakan reward & punishment.' },
  ];

  return (
    <div className="w-full bg-surface-raised border border-border rounded-2xl p-6 shadow-sm overflow-hidden relative min-h-[360px] flex flex-col justify-between">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h4 className="font-serif text-lg text-text-primary flex items-center gap-2">
            <Share2 className="w-5 h-5 text-primary" /> Visual Mind Map
          </h4>
          <p className="text-xs text-text-muted">Klik node untuk mengeksplorasi subtopik</p>
        </div>
        <button className="text-xs font-semibold text-primary flex items-center gap-1 hover:underline">
          <Maximize2 className="w-3.5 h-3.5" /> Ekspansi
        </button>
      </div>

      {/* SVG Canvas */}
      <div className="relative flex-1 bg-background rounded-xl border border-border p-2 overflow-hidden min-h-[220px]">
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          {/* Connection Lines with animations */}
          <motion.line 
            x1="250" y1="150" x2="120" y2="80" 
            stroke="#C5BAB0" strokeWidth="2" strokeDasharray="4 4"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1 }}
          />
          <motion.line 
            x1="250" y1="150" x2="380" y2="80" 
            stroke="#C5BAB0" strokeWidth="2" strokeDasharray="4 4"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, delay: 0.2 }}
          />
          <motion.line 
            x1="250" y1="150" x2="250" y2="250" 
            stroke="#C5BAB0" strokeWidth="2" strokeDasharray="4 4"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, delay: 0.4 }}
          />
        </svg>

        {/* Nodes */}
        {nodes.map((node) => (
          <motion.button
            key={node.id}
            className={`absolute px-4 py-2 rounded-full border text-xs font-medium shadow-sm transition-all flex items-center gap-1.5 z-10
              ${node.type === 'root' 
                ? 'bg-walnut text-surface-raised border-walnut-muted' 
                : 'bg-surface-raised border-border text-text-body hover:border-walnut'
              }`}
            style={{ 
              left: `calc(${node.x}px - 60px)`, 
              top: `calc(${node.y}px - 20px)`,
              width: '120px',
              justifyContent: 'center'
            }}
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => setActiveNode(node)}
          >
            {node.type === 'root' && <Sparkles className="w-3.5 h-3.5 fill-current text-primary-light" />}
            {node.label}
          </motion.button>
        ))}

        {/* Description Panel overlay */}
        <AnimatePresence>
          {activeNode && (
            <motion.div 
              className="absolute bottom-2 left-2 right-2 bg-surface-raised border border-border rounded-xl p-3 shadow-md z-20 flex justify-between items-start gap-4"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 15 }}
            >
              <div>
                <span className="text-[10px] uppercase font-bold tracking-widest text-primary-light">
                  {activeNode.type.toUpperCase()} NODE
                </span>
                <h5 className="font-semibold text-text-primary text-sm mt-0.5">{activeNode.label}</h5>
                <p className="text-xs text-text-body mt-1 leading-relaxed">{activeNode.desc}</p>
              </div>
              <button 
                onClick={() => setActiveNode(null)}
                className="text-[10px] font-bold text-text-muted hover:text-text-primary"
              >
                TUTUP
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// Interactive Latihan Soal (Quiz generator) with animations
function InteractiveQuiz({ sessionId, onScoreUpdate }) {
  const [currentStep, setCurrentStep] = useState(0); // 0: start, 1: question 1, 2: score
  const [selectedAns, setSelectedAns] = useState(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [score, setScore] = useState(0);
  const [quizData, setQuizData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchQuizQuestion = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/quiz?session_id=${sessionId}`);
      if (!response.ok) throw new Error("Gagal mengambil kuis");
      const data = await response.json();
      setQuizData(data);
      setCurrentStep(1);
    } catch (err) {
      console.warn("Backend quiz failed, using fallback:", err);
      // Fallback kuis jika API gagal
      setQuizData({
        topic: "Machine Learning & AI",
        question: "Manakah pernyataan berikut yang paling tepat menggambarkan 'Supervised Learning'?",
        options: [
          { key: "A", text: "Proses melatih model kecerdasan buatan tanpa pengawasan manusia sama sekali." },
          { key: "B", text: "Melatih model komputer menggunakan data historis yang sudah diberi label jawaban benar." },
          { key: "C", text: "Algoritma tebak-tebakan acak menggunakan trial-and-error berulang kali." },
          { key: "D", text: "Mengelompokkan data pelanggan berdasarkan kesamaan perilaku tanpa pembagian kategori." }
        ],
        correct: "B"
      });
      setCurrentStep(1);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = async (key) => {
    if (isAnswered) return;
    setSelectedAns(key);
    setIsAnswered(true);
    const isCorrect = key === quizData.correct;
    if (isCorrect) {
      setScore(100);
    } else {
      setScore(0);
    }

    // Call state update in parent context
    if (onScoreUpdate) {
      onScoreUpdate(quizData.topic || "Machine Learning & AI", isCorrect);
    }

    // Submit score to backend
    try {
      await fetch('http://127.0.0.1:8000/api/quiz/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          topic: quizData.topic || "Machine Learning & AI",
          is_correct: isCorrect
        })
      });
    } catch (e) {
      console.warn("Gagal menyimpan skor kuis di backend:", e);
    }
  };

  return (
    <div className="w-full bg-surface-raised border border-border rounded-2xl p-6 shadow-sm relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full filter blur-xl pointer-events-none" />
      
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Award className="w-5 h-5 text-primary" />
          <h4 className="font-serif text-lg text-text-primary">Kuis Interaktif Cerdas</h4>
        </div>
        <span className="text-[10px] font-bold bg-surface border border-border px-2.5 py-1 rounded-full text-text-muted">
          SOAL 1 DARI 1
        </span>
      </div>

      <AnimatePresence mode="wait">
        {currentStep === 0 ? (
          <motion.div 
            key="start"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="text-center py-6"
          >
            <div className="w-14 h-14 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-3">
              <Compass className="w-7 h-7 text-primary" />
            </div>
            <h5 className="font-serif text-text-primary text-base mb-1.5">Uji Pemahaman Anda</h5>
            <p className="text-xs text-text-muted max-w-sm mx-auto mb-5">
              Mari uji pemahaman kognitif Anda dengan kuis singkat yang dirancang khusus oleh AI untuk menguji memori jangka panjang Anda.
            </p>
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              disabled={loading}
              onClick={fetchQuizQuestion}
              className="px-6 py-2.5 bg-walnut text-surface-raised rounded-xl text-xs font-semibold hover:bg-walnut-light shadow-md disabled:opacity-50 flex items-center gap-2 mx-auto"
            >
              {loading ? (
                <>
                  <span className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-surface-raised" />
                  Membangun Kuis AI...
                </>
              ) : (
                "Mulai Kuis Sekarang"
              )}
            </motion.button>
          </motion.div>
        ) : currentStep === 1 ? (
          <motion.div 
            key="question"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            className="flex flex-col gap-4"
          >
            <div className="text-[10px] font-bold text-walnut uppercase tracking-wide">
              Topik: {quizData.topic || "Evaluasi Belajar"}
            </div>
            <p className="text-sm font-medium text-text-primary leading-relaxed bg-background p-4 rounded-xl border border-border">
              {quizData.question}
            </p>

            <div className="flex flex-col gap-2.5">
              {quizData.options.map((opt) => {
                const isSelected = selectedAns === opt.key;
                const isCorrectOpt = opt.key === quizData.correct;
                let btnStyle = "border-border bg-surface-raised hover:border-walnut text-text-body";
                
                if (isAnswered) {
                  if (isCorrectOpt) {
                    btnStyle = "border-secondary bg-secondary/10 text-secondary font-semibold";
                  } else if (isSelected) {
                    btnStyle = "border-red-400 bg-red-50 text-red-700";
                  } else {
                    btnStyle = "border-border bg-surface-raised text-text-muted opacity-60";
                  }
                }

                return (
                  <motion.button
                    key={opt.key}
                    onClick={() => handleSelectOption(opt.key)}
                    whileHover={!isAnswered ? { scale: 1.015, x: 2 } : {}}
                    whileTap={!isAnswered ? { scale: 0.99 } : {}}
                    className={`w-full text-left p-3.5 rounded-xl border text-xs flex items-start gap-3 transition-colors ${btnStyle}`}
                  >
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border flex-shrink-0 mt-0.5
                      ${isSelected 
                        ? isCorrectOpt ? 'bg-secondary border-secondary text-white' : 'bg-red-500 border-red-500 text-white'
                        : 'bg-background border-border text-text-muted'
                      }`}
                    >
                      {opt.key}
                    </span>
                    <span className="leading-relaxed">{opt.text}</span>
                  </motion.button>
                );
              })}
            </div>

            {isAnswered && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-2 flex items-center justify-between"
              >
                <div className="flex items-center gap-1.5 text-xs">
                  {selectedAns === quizData.correct ? (
                    <span className="text-secondary font-semibold flex items-center gap-1">✓ Jawaban Anda Benar! Hebat!</span>
                  ) : (
                    <span className="text-red-500 font-semibold flex items-center gap-1">✗ Salah. Jawaban benar adalah {quizData.correct}.</span>
                  )}
                </div>
                <button
                  onClick={() => setCurrentStep(2)}
                  className="px-4 py-2 bg-walnut text-surface-raised rounded-lg text-xs font-semibold hover:bg-walnut-light flex items-center gap-1"
                >
                  Lihat Skor <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </motion.div>
            )}
          </motion.div>
        ) : (
          <motion.div 
            key="score"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-6 flex flex-col items-center"
          >
            <motion.div 
              className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4 relative"
              animate={{ scale: [1, 1.15, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
            >
              <Award className="w-8 h-8 text-primary" />
              {score === 100 && (
                <motion.div 
                  className="absolute -inset-1 border-2 border-primary rounded-full"
                  animate={{ scale: [1, 1.3, 1], opacity: [1, 0, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              )}
            </motion.div>

            <h5 className="font-serif text-text-primary text-lg mb-1">Hasil Kuis Akademik</h5>
            <p className="text-xs text-text-muted mb-4">
              {score === 100 ? "Luar biasa! Pemahaman Anda dinilai sempurna!" : "Mari coba kembali untuk memperdalam pemahaman!"}
            </p>
            
            <div className="bg-background border border-border px-6 py-3 rounded-2xl mb-6">
              <span className="text-3xl font-serif font-bold text-walnut">{score}</span>
              <span className="text-xs text-text-muted"> / 100</span>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => {
                  setIsAnswered(false);
                  setSelectedAns(null);
                  fetchQuizQuestion();
                }}
                className="px-4 py-2.5 bg-background border border-border hover:border-walnut text-text-body rounded-xl text-xs font-semibold transition-colors"
              >
                Buat Soal Baru
              </button>
              <button
                onClick={() => {
                  setCurrentStep(0);
                  setIsAnswered(false);
                  setSelectedAns(null);
                  setScore(0);
                }}
                className="px-4 py-2.5 bg-walnut text-surface-raised hover:bg-walnut-light rounded-xl text-xs font-semibold transition-colors"
              >
                Tutup Kuis
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── MAIN APP COMPONENT ────────────────────────────────────────────────────────

export default function App() {
  const [activeMode, setActiveMode] = useState('belajar'); // 'belajar', 'rangkuman', 'latihan', 'mindmap'
  const [personality, setPersonality] = useState('😊 Santai & Friendly');
  const [user_name, setUserName] = useState('Budi');
  const [sessionId] = useState(() => {
    const saved = localStorage.getItem("scholarbot_session_id");
    if (saved) return saved;
    const fresh = `sess-${Math.random().toString(36).substring(2, 11)}`;
    localStorage.setItem("scholarbot_session_id", fresh);
    return fresh;
  });

  // Gamification progress states
  const [mlProgress, setMlProgress] = useState(78);
  const [chemProgress, setChemProgress] = useState(45);
  const [historyProgress, setHistoryProgress] = useState(60);
  
  // Chat input
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([
    {
      id: "welcome-bot",
      role: "assistant",
      content: "Halo! Selamat datang di **ScholarBot AI** — workspace belajar cerdas bertenaga kecerdasan buatan. Silakan klik suggestion chip di bawah atau ketik topik apa saja yang ingin Anda diskusikan secara interaktif hari ini!",
      time: "18:00"
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [selectedPreviewDoc, setSelectedPreviewDoc] = useState(null);
  
  // Ref for auto scroll
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Load session from backend on mount
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/session/${sessionId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages);
          }
          if (data.uploaded_docs) {
            setUploadedDocs(data.uploaded_docs);
          }
        }
      } catch (e) {
        console.warn("Gagal memulihkan sesi pada saat inisialisasi:", e);
      }
    };
    restoreSession();
  }, [sessionId]);

  // Handler for sending messages
  const handleSendMessage = async (textToSend) => {
    if (!textToSend.trim()) return;

    // 1. User message
    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: textToSend,
      time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
    };
    
    setMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setIsTyping(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: textToSend,
          session_id: sessionId,
          personality: personality,
          user_name: user_name,
          mode: activeMode
        })
      });

      if (!response.ok) {
        throw new Error("Gagal terhubung ke API Server");
      }

      // Retrieve RAG sources from custom header
      const sourcesHeader = response.headers.get("X-RAG-Sources");
      let retrievedSources = [];
      if (sourcesHeader) {
        try {
          retrievedSources = JSON.parse(sourcesHeader);
        } catch (e) {
          console.warn("Gagal mengurai header RAG sources:", e);
        }
      }

      setIsTyping(false);

      const botMsgId = `bot-${Date.now()}`;
      const botMsg = {
        id: botMsgId,
        role: "assistant",
        content: "",
        time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
        sources: retrievedSources
      };
      setMessages(prev => [...prev, botMsg]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunk = decoder.decode(value, { stream: !done });
          setMessages(prev => prev.map(msg => 
            msg.id === botMsgId 
              ? { ...msg, content: msg.content + chunk }
              : msg
          ));
        }
      }
    } catch (error) {
      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: `⚠️ Hubungan terputus. Pastikan FastAPI backend Anda berjalan di http://localhost:8000 dengan menjalankan command:\n\`uvicorn api:app --reload\` di folder \`scholarbot\`.`,
        time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
      }]);
    }
  };

  // Message Feedback (Like/Dislike) handler
  const handleMessageFeedback = async (msgId, type) => {
    // Toggles the local feedback state instantly for a premium responsive UI feel
    setMessages(prev => prev.map(msg => 
      msg.id === msgId 
        ? { ...msg, feedback: msg.feedback === type ? "neutral" : type } 
        : msg
    ));

    try {
      await fetch(`http://127.0.0.1:8000/api/session/${sessionId}/message/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message_id: msgId,
          feedback: type
        })
      });
    } catch (e) {
      console.warn("Gagal mengirim feedback pesan ke backend:", e);
    }
  };

  // Reset Chat handler
  const handleResetChat = async () => {
    try {
      await fetch(`http://127.0.0.1:8000/api/session/${sessionId}/reset`, {
        method: 'POST'
      });
    } catch (e) {
      console.warn("Gagal mereset sesi di backend:", e);
    }

    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: "assistant",
        content: "Sesi obrolan dan workspace dibersihkan! Mari mulai topik diskusi baru yang segar.",
        time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setActiveMode('belajar');
  };

  // Drag and drop / file uploader
  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("session_id", sessionId);

      try {
        const response = await fetch('http://127.0.0.1:8000/api/upload', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || "Gagal mengunggah");
        }

        const data = await response.json();
        setUploadedDocs(data.uploaded_docs);
      } catch (err) {
        alert(`Gagal mengunggah ${file.name}: ${err.message}`);
      }
    }
  };

  // Delete individual uploaded document
  const handleDeleteDoc = async (filename) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/session/${sessionId}/doc/${encodeURIComponent(filename)}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        const data = await response.json();
        setUploadedDocs(data.uploaded_docs);
        if (selectedPreviewDoc && selectedPreviewDoc.filename === filename) {
          setSelectedPreviewDoc(null);
        }
      }
    } catch (e) {
      console.warn("Gagal menghapus dokumen tunggal:", e);
    }
  };

  // Clear uploaded documents
  const handleClearDocs = async () => {
    try {
      await fetch(`http://127.0.0.1:8000/api/session/${sessionId}/clear-docs`, {
        method: 'POST'
      });
      setUploadedDocs([]);
      setSelectedPreviewDoc(null);
    } catch (e) {
      console.warn("Gagal menghapus dokumen di backend:", e);
    }
  };

  return (
    <div className="flex h-screen bg-background text-text-body font-sans overflow-hidden">
      
      {/* ─── LEFT SIDEBAR (PREMIUM COMPACT LAYOUT) ──────────────────────────────── */}
      <aside className="w-80 bg-surface border-r border-divider flex flex-col justify-between p-6 flex-shrink-0">
        
        <div className="flex flex-col gap-6 overflow-y-auto pr-1">
          {/* Logo & title */}
          <div className="flex items-center gap-3 pb-5 border-b border-divider">
            <div className="w-11 h-11 rounded-xl bg-surface-raised border border-border flex items-center justify-center text-walnut shadow-sm">
              <BookOpen className="w-6 h-6 stroke-[1.8]" />
            </div>
            <div>
              <h1 className="font-serif text-xl font-medium text-text-primary leading-none">ScholarBot</h1>
              <span className="text-[10px] text-text-muted font-bold tracking-widest uppercase mt-1.5 block">
                AI Study Workspace
              </span>
            </div>
          </div>

          {/* Profile mini-card */}
          <div className="flex items-center gap-3 p-3 bg-surface-raised border border-border rounded-2xl shadow-sm">
            <div className="w-9 h-9 rounded-full bg-divider border border-border text-walnut flex items-center justify-center font-serif text-lg font-semibold">
              {user_name[0]?.toUpperCase() || 'S'}
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-text-primary leading-tight">Halo, {user_name}!</span>
              <span className="text-[10px] text-text-muted mt-0.5">Semangat belajar hari ini!</span>
            </div>
          </div>

          {/* Personality selector */}
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] uppercase font-bold tracking-wider text-text-muted px-1">Personality AI</label>
            <div className="relative">
              <select 
                value={personality}
                onChange={(e) => setPersonality(e.target.value)}
                className="w-full bg-surface-raised border border-border text-xs rounded-xl py-2.5 px-3 text-text-body focus:outline-none focus:border-walnut shadow-sm cursor-pointer appearance-none pr-8"
              >
                {Object.keys(PERSONALITIES).map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-text-muted absolute right-3 top-3.5 pointer-events-none" />
            </div>
          </div>

          {/* Menu Utama */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase font-bold tracking-wider text-text-muted px-1 mb-1.5">Menu Utama</label>
            
            {/* Belajar */}
            <button 
              onClick={() => setActiveMode('belajar')}
              className={`w-full py-2.5 px-3.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-3 text-left
                ${activeMode === 'belajar' 
                  ? 'bg-walnut text-surface-raised shadow-sm font-semibold' 
                  : 'text-text-muted hover:bg-divider hover:text-text-primary hover:translate-x-1'
                }`}
            >
              <Compass className="w-4 h-4" />
              <span>Belajar</span>
            </button>

            {/* Rangkuman */}
            <button 
              onClick={() => setActiveMode('rangkuman')}
              className={`w-full py-2.5 px-3.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-3 text-left
                ${activeMode === 'rangkuman' 
                  ? 'bg-walnut text-surface-raised shadow-sm font-semibold' 
                  : 'text-text-muted hover:bg-divider hover:text-text-primary hover:translate-x-1'
                }`}
            >
              <FileText className="w-4 h-4" />
              <span>Rangkuman</span>
            </button>

            {/* Latihan Soal */}
            <button 
              onClick={() => setActiveMode('latihan')}
              className={`w-full py-2.5 px-3.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-3 text-left
                ${activeMode === 'latihan' 
                  ? 'bg-walnut text-surface-raised shadow-sm font-semibold' 
                  : 'text-text-muted hover:bg-divider hover:text-text-primary hover:translate-x-1'
                }`}
            >
              <Award className="w-4 h-4" />
              <span>Latihan Soal</span>
            </button>

            {/* Mind Map */}
            <button 
              onClick={() => setActiveMode('mindmap')}
              className={`w-full py-2.5 px-3.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-3 text-left
                ${activeMode === 'mindmap' 
                  ? 'bg-walnut text-surface-raised shadow-sm font-semibold' 
                  : 'text-text-muted hover:bg-divider hover:text-text-primary hover:translate-x-1'
                }`}
            >
              <Share2 className="w-4 h-4" />
              <span>Mind Map</span>
            </button>

            {/* Reset Chat Button - ELEGANT RED HIGHLIGHT */}
            <button 
              onClick={handleResetChat}
              className="w-full py-2.5 px-3.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-3 text-left text-red-500 hover:bg-red-50 hover:translate-x-1 mt-2 border border-dashed border-red-200/50"
            >
              <Trash2 className="w-4 h-4" />
              <span>Reset Chat</span>
            </button>
          </div>

          {/* RAG Upload Area inside sidebar */}
          <div className="flex flex-col gap-2 pt-2 border-t border-divider">
            <label className="text-[10px] uppercase font-bold tracking-wider text-text-muted px-1">Unggah Dokumen (RAG)</label>
            
            <div className="relative border border-dashed border-border rounded-xl bg-surface-raised p-3 flex flex-col items-center justify-center text-center cursor-pointer hover:border-walnut transition-colors group">
              <input 
                type="file" 
                multiple
                accept=".txt,.pdf"
                onChange={handleFileUpload}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <Upload className="w-5 h-5 text-text-muted mb-1.5 group-hover:scale-110 transition-transform" />
              <span className="text-[10px] font-semibold text-text-primary">Unggah berkas PDF/TXT</span>
              <span className="text-[9px] text-text-muted mt-0.5">Maks 200MB</span>
            </div>

            {uploadedDocs.length > 0 && (
              <div className="flex flex-col gap-1.5 max-h-28 overflow-y-auto mt-1 bg-surface-raised border border-border p-2 rounded-xl">
                {uploadedDocs.map((doc, i) => (
                  <div key={i} className="flex justify-between items-center bg-background px-2 py-1.5 rounded-lg border border-border text-[10px] hover:border-walnut transition-colors group/doc">
                    <span 
                      onClick={() => setSelectedPreviewDoc(doc)}
                      className="truncate font-medium text-text-primary max-w-[130px] cursor-pointer hover:underline flex items-center gap-1.5"
                      title="Klik untuk pratinjau konten"
                    >
                      📄 {doc.filename}
                    </span>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <span className="text-[8px] text-text-muted">{doc.size}</span>
                      <button 
                        onClick={() => handleDeleteDoc(doc.filename)}
                        className="text-text-muted hover:text-red-500 opacity-0 group-hover/doc:opacity-100 transition-opacity p-0.5"
                        title="Hapus dokumen"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
                <button 
                  onClick={handleClearDocs}
                  className="text-[9px] text-red-500 font-bold hover:underline self-end mt-1"
                >
                  Hapus Semua
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Premium Upgrade Pro Tier Card */}
        <div className="bg-surface-raised border border-border rounded-2xl p-4 shadow-sm relative overflow-hidden mt-6">
          <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
          <div className="flex items-center gap-2 mb-1.5">
            <Crown className="w-4 h-4 text-primary fill-primary/10" />
            <h5 className="text-xs font-bold text-text-primary">Upgrade ke ScholarPro</h5>
          </div>
          <p className="text-[10px] text-text-muted mb-3 leading-relaxed">
            Akses fitur premium tanpa batas, RAG multi-dokumen, dan AI tercepat.
          </p>
          <button className="w-full py-2 bg-divider border border-border rounded-lg text-[10px] font-bold text-walnut hover:bg-walnut hover:text-surface-raised hover:border-walnut transition-colors">
            Upgrade Sekarang
          </button>
        </div>

      </aside>

      {/* ─── RIGHT WORKSPACE / CHAT PANEL ───────────────────────────────────────── */}
      <main className="flex-1 flex flex-col justify-between overflow-hidden relative">
        <div className="flex-1 overflow-y-auto px-10 py-8 scrollbar-thin">
          
          <AnimatePresence mode="wait">
            
            {/* ── Welcome Screen (If no user-generated messages yet or active mode welcome trigger) ── */}
            {messages.length <= 1 && (
              <motion.div 
                key="welcome-pane"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="max-w-3xl mx-auto flex flex-col gap-10"
              >
                {/* Visual Mascot Header */}
                <div className="flex justify-between items-center gap-8 pt-8">
                  <div className="flex-1">
                    <motion.h2 
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="font-serif text-4xl text-text-primary mb-3.5 leading-tight"
                    >
                      Mau belajar apa hari ini?
                    </motion.h2>
                    <p className="text-sm text-walnut-muted leading-relaxed max-w-md">
                      ScholarBot siap membantu Anda memvisualisasikan peta konsep, menghasilkan kuis cerdas, dan merangkum materi secara instan.
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    <AnimatedMascot />
                  </div>
                </div>

                {/* Visual Progress Cards ("Lanjutkan Belajar") */}
                <div className="flex flex-col gap-4">
                  <h3 className="font-serif text-lg text-text-primary flex items-center gap-2">
                    <History className="w-5 h-5 text-primary" /> Lanjutkan Belajar
                  </h3>
                  
                  <div className="grid grid-cols-3 gap-4">
                    {/* Card 1 */}
                    <motion.div 
                      whileHover={{ y: -4, shadow: "shadow-md" }}
                      className="bg-surface-raised border border-border rounded-2xl p-4 shadow-sm flex flex-col justify-between h-32 cursor-pointer transition-all hover:border-walnut"
                      onClick={() => handleSendMessage("Apa itu Machine Learning?")}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-blue-50 text-blue-700 flex items-center justify-center">
                          <Compass className="w-5 h-5" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-text-primary">Machine Learning</span>
                          <span className="text-[10px] text-text-muted mt-0.5">Progres: {mlProgress}%</span>
                        </div>
                      </div>
                      <div className="w-full">
                        <div className="h-1 bg-divider rounded-full overflow-hidden mb-1.5">
                          <div className="h-full bg-walnut rounded-full transition-all duration-500" style={{ width: `${mlProgress}%` }} />
                        </div>
                        <span className="text-[9px] text-text-muted">Terakhir dipelajari baru saja</span>
                      </div>
                    </motion.div>

                    {/* Card 2 */}
                    <motion.div 
                      whileHover={{ y: -4, shadow: "shadow-md" }}
                      className="bg-surface-raised border border-border rounded-2xl p-4 shadow-sm flex flex-col justify-between h-32 cursor-pointer transition-all hover:border-walnut"
                      onClick={() => handleSendMessage("Buat kuis Stoikiometri Kimia")}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-emerald-50 text-emerald-700 flex items-center justify-center">
                          <BookOpen className="w-5 h-5" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-text-primary">Kimia: Stoikiometri</span>
                          <span className="text-[10px] text-text-muted mt-0.5">Progres: {chemProgress}%</span>
                        </div>
                      </div>
                      <div className="w-full">
                        <div className="h-1 bg-divider rounded-full overflow-hidden mb-1.5">
                          <div className="h-full bg-walnut rounded-full transition-all duration-500" style={{ width: `${chemProgress}%` }} />
                        </div>
                        <span className="text-[9px] text-text-muted">Terakhir dipelajari baru saja</span>
                      </div>
                    </motion.div>

                    {/* Card 3 */}
                    <motion.div 
                      whileHover={{ y: -4, shadow: "shadow-md" }}
                      className="bg-surface-raised border border-border rounded-2xl p-4 shadow-sm flex flex-col justify-between h-32 cursor-pointer transition-all hover:border-walnut"
                      onClick={() => handleSendMessage("Ceritakan Perang Dunia II")}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-amber-50 text-amber-700 flex items-center justify-center">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-text-primary">Perang Dunia II</span>
                          <span className="text-[10px] text-text-muted mt-0.5">Progres: {historyProgress}%</span>
                        </div>
                      </div>
                      <div className="w-full">
                        <div className="h-1 bg-divider rounded-full overflow-hidden mb-1.5">
                          <div className="h-full bg-walnut rounded-full transition-all duration-500" style={{ width: `${historyProgress}%` }} />
                        </div>
                        <span className="text-[9px] text-text-muted">Terakhir dipelajari 3 hari lalu</span>
                      </div>
                    </motion.div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* ── Active Obrolan Area ── */}
            {messages.length > 1 && (
              <motion.div 
                key="chat-pane"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="max-w-3xl mx-auto flex flex-col gap-6 pb-20"
              >
                {/* Active Mode Visual Header info */}
                <div className="flex items-center justify-between border-b border-divider pb-4 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-text-primary uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-primary fill-primary/10" />
                      Mode: {activeMode.toUpperCase()}
                    </span>
                    <span className="text-[10px] border border-border bg-surface-raised px-2.5 py-0.5 rounded-full text-text-muted">
                      {personality}
                    </span>
                  </div>
                  <button 
                    onClick={handleResetChat}
                    className="text-xs text-text-muted hover:text-red-500 font-semibold flex items-center gap-1 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Bersihkan Obrolan
                  </button>
                </div>

                {/* Messages stream */}
                <div className="flex flex-col gap-6">
                  {messages.map((msg, index) => {
                    const isBot = msg.role === 'assistant';
                    
                    return (
                      <motion.div 
                        key={msg.id || index}
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`flex gap-4 ${isBot ? '' : 'flex-row-reverse'}`}
                      >
                        {/* Avatar */}
                        <div className={`w-8 h-8 rounded-full border border-border flex items-center justify-center flex-shrink-0 shadow-sm
                          ${isBot ? 'bg-walnut text-surface-raised font-serif' : 'bg-surface-raised text-text-muted font-bold text-xs'}`}
                        >
                          {isBot ? <Bot className="w-4 h-4 text-surface-raised" /> : <User className="w-4 h-4 text-walnut" />}
                        </div>

                        {/* Content bubble */}
                        <div className="flex flex-col max-w-[70%]">
                          <div className={`p-4 rounded-2xl border text-xs leading-relaxed shadow-sm
                            ${isBot 
                              ? 'bg-surface-raised border-border text-text-body font-serif' 
                              : 'bg-surface border-border text-text-primary'
                            }`}
                          >
                            {/* Simple Markdown support simulator */}
                            {isBot ? (
                              <div className="flex flex-col gap-2">
                                {msg.content.split('\n\n').map((para, pIdx) => {
                                  if (para.startsWith('### ')) {
                                    return <h4 key={pIdx} className="font-bold text-sm text-text-primary font-serif mt-1">{para.replace('### ', '')}</h4>;
                                  }
                                  if (para.startsWith('*   ')) {
                                    return (
                                      <ul key={pIdx} className="list-disc pl-5 flex flex-col gap-1">
                                        {para.split('\n').map((li, lIdx) => (
                                          <li key={lIdx}>{li.replace('*   ', '').replace('**', '').replace('**', '')}</li>
                                        ))}
                                      </ul>
                                    );
                                  }
                                  return <p key={pIdx} dangerouslySetInnerHTML={{__html: para.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}} />;
                                })}
                              </div>
                            ) : (
                              <div>{msg.content}</div>
                            )}
                          </div>

                          {/* ─── RAG SOURCE VISUALIZER & RELEVANCE INDICATOR (v3.2 ROADMAP) ─── */}
                          {isBot && msg.sources && msg.sources.length > 0 && (
                            <div className="mt-2 border border-border bg-surface rounded-xl overflow-hidden shadow-sm max-w-full">
                              <details className="group">
                                <summary className="flex items-center justify-between p-2.5 bg-surface-raised cursor-pointer hover:bg-divider transition-colors select-none text-[10px] font-bold text-walnut">
                                  <div className="flex items-center gap-1.5">
                                    <Sparkles className="w-3.5 h-3.5 text-primary" />
                                    <span>Sumber Referensi Akademis ({msg.sources.length})</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-[8px] px-2 py-0.5 rounded-full bg-walnut/10 text-walnut font-bold">
                                      Relevansi: {Math.min(100, Math.round((msg.sources[0]?.score || 0) * 100))}%
                                    </span>
                                    <ChevronDown className="w-3 h-3 text-text-muted group-open:rotate-180 transition-transform" />
                                  </div>
                                </summary>
                                <div className="p-3 border-t border-divider bg-surface flex flex-col gap-2 max-h-48 overflow-y-auto scrollbar-thin">
                                  {msg.sources.map((src, sIdx) => (
                                    <div key={sIdx} className="p-2.5 rounded-lg border border-border bg-surface-raised/40 hover:border-walnut transition-colors">
                                      <div className="flex justify-between items-center mb-1 text-[9px]">
                                        <span className="font-bold text-text-primary">📄 {src.source}</span>
                                        <span className="text-[8px] font-semibold text-walnut-muted">
                                          Skor Relevansi: {src.score?.toFixed(3)}
                                        </span>
                                      </div>
                                      <p className="text-[9px] leading-relaxed text-text-body font-mono whitespace-pre-wrap bg-background/50 p-2 rounded border border-border/50 max-h-24 overflow-y-auto animate-pulse-subtle">
                                        {src.content}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </details>
                            </div>
                          )}
                          
                          {/* Timestamp and feedback actions */}
                          <div className={`flex items-center gap-3 mt-1.5 text-[9px] text-text-muted ${!isBot ? 'justify-end' : ''}`}>
                            <span>{msg.time}</span>
                            {isBot && (
                              <>
                                <button 
                                  onClick={() => {
                                    navigator.clipboard.writeText(msg.content);
                                  }}
                                  className="hover:text-text-primary transition-colors flex items-center gap-0.5 focus:text-walnut"
                                >
                                  📋 Salin
                                </button>
                                <button 
                                  onClick={() => handleMessageFeedback(msg.id, "like")}
                                  className={`transition-colors flex items-center gap-0.5 ${msg.feedback === 'like' ? 'text-walnut font-bold scale-105' : 'hover:text-text-primary'}`}
                                >
                                  👍 {msg.feedback === 'like' ? 'Berguna!' : 'Berguna'}
                                </button>
                                <button 
                                  onClick={() => handleMessageFeedback(msg.id, "dislike")}
                                  className={`transition-colors flex items-center gap-0.5 ${msg.feedback === 'dislike' ? 'text-red-500 font-bold scale-105' : 'hover:text-text-primary'}`}
                                >
                                  👎 {msg.feedback === 'dislike' ? 'Kurang!' : 'Kurang'}
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}

                  {/* Typing Indicator */}
                  {isTyping && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex gap-4"
                    >
                      <div className="w-8 h-8 rounded-full bg-walnut flex items-center justify-center flex-shrink-0">
                        <Bot className="w-4 h-4 text-surface-raised" />
                      </div>
                      <div className="bg-surface-raised border border-border p-4 rounded-2xl flex items-center gap-1.5 shadow-sm">
                        <span className="w-1.5 h-1.5 bg-walnut-muted rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-1.5 h-1.5 bg-walnut-muted rounded-full animate-bounce" style={{ animationDelay: '200ms' }} />
                        <span className="w-1.5 h-1.5 bg-walnut-muted rounded-full animate-bounce" style={{ animationDelay: '400ms' }} />
                      </div>
                    </motion.div>
                  )}
                  
                  <div ref={chatEndRef} />
                </div>
              </motion.div>
            )}

          </AnimatePresence>

          {/* ─── DYNAMIC INTERACTIVE WIDGET PANELS BASED ON MODE ───────────────── */}
          <AnimatePresence>
            {activeMode === 'rangkuman' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="max-w-3xl mx-auto mt-6"
              >
                <div className="bg-surface-raised border border-border rounded-2xl p-6 shadow-sm flex flex-col gap-4">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary" />
                    <h4 className="font-serif text-lg text-text-primary">Poin Rangkuman Cepat</h4>
                  </div>
                  <div className="flex flex-col gap-2">
                    <details className="group border border-border rounded-xl p-3 bg-background cursor-pointer hover:border-walnut transition-colors">
                      <summary className="text-xs font-semibold text-text-primary flex justify-between items-center list-none">
                        <span>Poin 1: Landasan Utama Konsep</span>
                        <ChevronDown className="w-4 h-4 text-text-muted group-open:rotate-180 transition-transform" />
                      </summary>
                      <p className="text-xs text-text-body mt-2 leading-relaxed">
                        Topik ini bertumpu pada aturan universal yang telah teruji secara eksperimental dan teoretis selama berdekade.
                      </p>
                    </details>
                    <details className="group border border-border rounded-xl p-3 bg-background cursor-pointer hover:border-walnut transition-colors">
                      <summary className="text-xs font-semibold text-text-primary flex justify-between items-center list-none">
                        <span>Poin 2: Alur Metodologis Sistem</span>
                        <ChevronDown className="w-4 h-4 text-text-muted group-open:rotate-180 transition-transform" />
                      </summary>
                      <p className="text-xs text-text-body mt-2 leading-relaxed">
                        Langkah awal dimulai dari klasifikasi input, pengolahan model kognitif, diikuti interpretasi visual.
                      </p>
                    </details>
                  </div>
                </div>
              </motion.div>
            )}

            {activeMode === 'latihan' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="max-w-3xl mx-auto mt-6"
              >
                <InteractiveQuiz 
                  sessionId={sessionId} 
                  onScoreUpdate={(topic, isCorrect) => {
                    const tLower = topic.toLowerCase();
                    if (tLower.includes("machine") || tLower.includes("learning") || tLower.includes("ai")) {
                      setMlProgress(prev => Math.min(100, prev + (isCorrect ? 8 : 2)));
                    } else if (tLower.includes("kimia") || tLower.includes("stoikiometri") || tLower.includes("chem")) {
                      setChemProgress(prev => Math.min(100, prev + (isCorrect ? 8 : 2)));
                    } else if (tLower.includes("perang") || tLower.includes("dunia") || tLower.includes("sejarah") || tLower.includes("history")) {
                      setHistoryProgress(prev => Math.min(100, prev + (isCorrect ? 8 : 2)));
                    }
                  }} 
                />
              </motion.div>
            )}

            {activeMode === 'mindmap' && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="max-w-3xl mx-auto mt-6"
              >
                <InteractiveMindMap topic={messages[messages.length - 1]?.content.includes('Machine Learning') ? 'Machine Learning' : 'Topik Belajar'} />
              </motion.div>
            )}
          </AnimatePresence>

        </div>

        {/* ─── BOTTOM CHAT INPUT ZONE (MATCHING MOCKUP AESTHETIC) ────────────────── */}
        <div className="p-8 border-t border-divider bg-background">
          <div className="max-w-3xl mx-auto flex flex-col gap-4">
            
            {/* Suggestion Chips - flying animations */}
            {messages.length <= 1 && (
              <div className="flex justify-center gap-2 flex-wrap">
                {SUGGESTION_CHIPS.map((chip, idx) => (
                  <motion.button
                    key={idx}
                    onClick={() => handleSendMessage(chip)}
                    whileHover={{ scale: 1.04, backgroundColor: '#FDFCFA' }}
                    whileTap={{ scale: 0.97 }}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + (idx * 0.08) }}
                    className="px-4 py-2 bg-surface-overlay border border-border text-[11px] font-semibold text-walnut-muted rounded-full transition-colors hover:text-text-primary hover:border-border-strong cursor-pointer"
                  >
                    {chip}
                  </motion.button>
                ))}
              </div>
            )}

            {/* Main Chat Input Container */}
            <div className="bg-surface-raised border border-border rounded-2xl p-2 pl-4 pr-2 flex items-center justify-between shadow-md focus-within:border-primary transition-all">
              <input 
                type="text" 
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(chatInput)}
                placeholder="Tanya apa saja tentang pelajaran..."
                className="flex-1 bg-transparent text-xs text-text-primary placeholder-text-subtle py-2.5 focus:outline-none"
              />
              
              {/* Send Button */}
              <motion.button 
                onClick={() => handleSendMessage(chatInput)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="w-10 h-10 rounded-full bg-walnut flex items-center justify-center text-surface-raised shadow-md cursor-pointer hover:bg-walnut-light"
              >
                <Send className="w-4 h-4 fill-current text-surface-raised" />
              </motion.button>
            </div>

            <span className="text-[10px] text-text-subtle text-center">
              ScholarBot dapat membuat kesalahan. Periksa kembali jawaban penting.
            </span>

          </div>
        </div>

      {/* ─── DOCUMENT PREVIEW DIALOG (v3.2 ROADMAP FEATURE) ─── */}
      <AnimatePresence>
        {selectedPreviewDoc && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/35 backdrop-blur-[2px] z-50 flex items-center justify-center p-6"
            onClick={() => setSelectedPreviewDoc(null)}
          >
            <motion.div 
              initial={{ scale: 0.95, y: 15 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 15 }}
              className="bg-surface border border-border w-full max-w-xl rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[80vh]"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="p-5 border-b border-divider bg-surface-raised flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-walnut/10 text-walnut flex items-center justify-center">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-text-primary truncate max-w-[280px]">{selectedPreviewDoc.filename}</h4>
                    <span className="text-[9px] text-text-muted mt-0.5 block">Format: {selectedPreviewDoc.type} • Ukuran: {selectedPreviewDoc.size}</span>
                  </div>
                </div>
                <button 
                  onClick={() => setSelectedPreviewDoc(null)}
                  className="w-8 h-8 rounded-full hover:bg-divider text-text-muted hover:text-text-primary flex items-center justify-center transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Preview Body */}
              <div className="p-6 overflow-y-auto flex-1 bg-surface scrollbar-thin">
                <span className="text-[10px] font-bold text-walnut uppercase tracking-widest block mb-3">Pratinjau Ekstraksi Teks</span>
                <div className="bg-background border border-border rounded-xl p-4 text-xs leading-relaxed text-text-body font-mono whitespace-pre-wrap max-h-80 overflow-y-auto bg-surface-raised/40">
                  {selectedPreviewDoc.preview || "Tidak ada konten teks yang dapat diekstrak atau dokumen kosong."}
                </div>
                {selectedPreviewDoc.preview && selectedPreviewDoc.preview.length >= 800 && (
                  <span className="text-[9px] text-text-subtle mt-2 block text-center italic">
                    (Menampilkan 800 karakter pertama dokumen untuk pratinjau cepat)
                  </span>
                )}
              </div>

              {/* Footer */}
              <div className="p-4 border-t border-divider bg-surface-raised flex justify-end gap-2">
                <button 
                  onClick={() => setSelectedPreviewDoc(null)}
                  className="px-4 py-2 bg-walnut text-surface-raised rounded-xl text-xs font-semibold hover:bg-walnut-light transition-colors"
                >
                  Tutup Pratinjau
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      </main>
    </div>
  );
}
