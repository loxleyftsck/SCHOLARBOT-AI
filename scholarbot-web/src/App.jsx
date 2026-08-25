import { useState, useEffect, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { AnswerBody, parseCitationIds } from './markdown';
import dagre from 'dagre';
import ReactFlow, { Background, Controls, MarkerType, Handle, Position, useNodesState, useEdgesState } from 'reactflow';
import 'reactflow/dist/style.css';
import { API_BASE_URL } from './config';

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
  Bot, 
  User, 
  Award,
  Sparkles,
  ArrowRight,
  Maximize2,
  Minimize2,
  GitFork,
  ChevronDown,
  RefreshCw,
  X,
  Search,
  Edit3
} from 'lucide-react';

// ─── STATIC DATA & ASSETS ──────────────────────────────────────────────────────

const PERSONALITIES = {
  "😊 Santai & Friendly": "Menjelaskan materi dengan bahasa santai, penuh analogi kehidupan sehari-hari.",
  "🎓 Formal Tutor": "Bahasa formal akademis, referensi ilmiah, terstruktur, dan sangat mendalam.",
  "⚡ Gen Z Mode": "Gaya bicara gaul, no cap, literally, slay fr fr agar belajar lebih chill dan engaging.",
  "💼 Expert Consultant": "Analisis mendalam, perspektif multi-dimensi, framework berpikir, dan actionable insights."
};

const SUGGESTION_CHIPS = [
  "Jelaskan Teorema Pythagoras",
  "Rangkum Perang Dunia II",
  "Apa itu Machine Learning?",
  "Buat soal Stoikiometri Kimia"
];



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
      {/* Premium Ambient Radial Glow */}
      <motion.div 
        className="absolute inset-0 rounded-full bg-[radial-gradient(circle,rgba(139,105,20,0.12)_0%,transparent_70%)] pointer-events-none"
        animate={{ scale: [0.85, 1.15, 0.85], opacity: [0.6, 1, 0.6] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      />

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

// Custom Node Component for React Flow representing the walnut-themed nodes
function CustomMindMapNode({ data, selected }) {
  const isRoot = data.type === 'root';
  const isBranch = data.type === 'branch';

  return (
    <div
      className={`px-4 py-2.5 rounded-full border text-xs font-semibold shadow-md transition-all flex items-center gap-2 min-w-[140px] max-w-[200px] text-center justify-center relative
        ${isRoot 
          ? 'bg-walnut text-surface-raised border-walnut-muted' 
          : isBranch
            ? 'bg-surface-raised border-border text-text-body hover:border-walnut'
            : 'bg-background border-border-light text-text-muted hover:border-primary-light font-medium'
        }
        ${selected ? 'ring-2 ring-primary ring-offset-2 border-primary' : ''}
      `}
    >
      {!isRoot && (
        <Handle 
          type="target" 
          position={Position.Top} 
          style={{ background: '#8B6914', border: 'none', width: '6px', height: '6px' }} 
        />
      )}
      
      {isRoot && <Sparkles className="w-3.5 h-3.5 fill-current text-primary-light shrink-0 animate-pulse" />}
      <span className="truncate w-full select-none">{data.label}</span>
      
      <Handle 
        type="source" 
        position={Position.Bottom} 
        style={{ background: '#8B6914', border: 'none', width: '6px', height: '6px' }} 
      />
    </div>
  );
}

// React Flow static node types declaration
const nodeTypes = {
  customNode: CustomMindMapNode
};

// Helper function to layout elements using Dagre for a balanced hierarchical tree
function getLayoutedElements(nodes, edges) {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: 'TB', ranksep: 60, nodesep: 40 });
  g.setDefaultEdgeLabel(() => ({}));

  nodes.forEach((node) => {
    g.setNode(node.id, { width: 160, height: 40 });
  });

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  try {
    dagre.layout(g);
  } catch (e) {
    console.error("Dagre layout error:", e);
  }

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = g.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition ? nodeWithPosition.x - 80 : Math.random() * 200,
        y: nodeWithPosition ? nodeWithPosition.y - 20 : Math.random() * 200,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

// Interactive Mind Map Component
function InteractiveMindMap({ 
  topic = "Machine Learning",
  nodesData = [],
  edgesData = [],
  isLoading = false,
  isExpanding = false,
  onExpandNode,
  onRegenerate
}) {
  const [activeNode, setActiveNode] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isMaximized, setIsMaximized] = useState(false);

  // Close full screen on escape keypress
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsMaximized(false);
      }
    };
    if (isMaximized) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  // Sync with prop updates and calculate Dagre layout
  useEffect(() => {
    if (!nodesData || !Array.isArray(nodesData) || nodesData.length === 0) {
      setNodes([]);
      setEdges([]);
      return;
    }

    // Filter valid elements
    const validNodes = nodesData.filter(node => node && node.id !== undefined && node.id !== null);
    const validEdges = Array.isArray(edgesData)
      ? edgesData.filter(edge => edge && edge.source !== undefined && edge.source !== null && edge.target !== undefined && edge.target !== null)
      : [];

    const rawNodes = validNodes.map(node => ({
      id: node.id.toString(),
      type: 'customNode',
      data: { 
        label: node.label, 
        type: node.type, 
        desc: node.desc || node.description 
      }
    }));

    const rawEdges = validEdges.map(edge => ({
      id: `e-${edge.source}-${edge.target}`,
      source: edge.source.toString(),
      target: edge.target.toString(),
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#C5BAB0', strokeWidth: 2, strokeDasharray: '4 4' },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#C5BAB0',
        width: 10,
        height: 10
      }
    }));

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(rawNodes, rawEdges);
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [nodesData, edgesData, setNodes, setEdges]);

  // Clear activeNode if it's no longer present
  useEffect(() => {
    if (activeNode) {
      const exists = nodesData.some(n => n.id.toString() === activeNode.id.toString());
      if (!exists) {
        setActiveNode(null);
      }
    }
  }, [nodesData, activeNode]);

  const onNodeClick = (event, node) => {
    setActiveNode(node);
  };

  const selectedNodeLabel = activeNode?.data?.label || activeNode?.label;
  const selectedNodeDesc = activeNode?.data?.desc || activeNode?.desc || activeNode?.description;
  const selectedNodeType = activeNode?.data?.type || activeNode?.type;

  const mindMapContent = (
    <div 
      className="w-full bg-surface-raised border border-border rounded-2xl p-6 shadow-sm overflow-hidden relative flex flex-col justify-between transition-all duration-300 min-h-[360px]"
    >
      <div className="flex justify-between items-center mb-4">
        <div>
          <h4 className="font-serif text-lg text-text-primary flex items-center gap-2">
            <Share2 className="w-5 h-5 text-primary" /> Visual Mind Map: <span className="text-walnut font-sans text-base font-semibold">{topic}</span>
          </h4>
          <p className="text-xs text-text-muted">Klik node untuk melihat deskripsi dan mengeksplorasi subtopik</p>
        </div>
        <div className="flex items-center gap-4">
          {/* Node Expansion Button */}
          <button 
            onClick={() => {
              if (activeNode && onExpandNode) {
                onExpandNode(activeNode.id, selectedNodeLabel);
              }
            }}
            disabled={!activeNode || isExpanding}
            className={`text-xs font-semibold flex items-center gap-1 hover:underline transition-opacity
              ${!activeNode ? 'opacity-40 cursor-not-allowed' : 'text-primary hover:text-walnut'}
              ${isExpanding ? 'animate-pulse' : ''}
            `}
            title="Kembangkan cabang subtopik ini"
          >
            {isExpanding ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Mengekspansi...
              </>
            ) : (
              <>
                <GitFork className="w-3.5 h-3.5" /> Eksplorasi Cabang
              </>
            )}
          </button>

          {/* Full Screen Toggle Button */}
          <button 
            onClick={() => setIsMaximized(true)}
            className="text-xs font-semibold flex items-center gap-1 hover:underline text-text-primary hover:text-walnut transition-all"
            title="Perbesar tampilan peta konsep"
          >
            <Maximize2 className="w-3.5 h-3.5" /> Perbesar Layar
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="relative w-full bg-background rounded-xl border border-border overflow-hidden h-[400px]">
        {isLoading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center bg-background z-30">
            <motion.div 
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
              className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full mb-3"
            />
            <p className="text-sm font-medium text-text-body">Merajut Peta Konsep AI...</p>
            <p className="text-xs text-text-muted mt-1">Menyusun keterkaitan antar subtopik</p>
          </div>
        ) : nodesData.length === 0 ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center bg-background z-30">
            <Sparkles className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
            <p className="text-sm font-medium text-text-body">Belum ada peta konsep</p>
            <p className="text-xs text-text-muted mt-1">Ketikkan topik belajar Anda atau klik tombol di bawah untuk membuat baru</p>
            {onRegenerate && (
              <button 
                onClick={() => onRegenerate(topic)}
                className="mt-3 px-3 py-1.5 bg-walnut hover:bg-walnut-muted text-surface-raised rounded-full text-xs font-semibold"
              >
                Generate Sekarang
              </button>
            )}
          </div>
        ) : (
          <>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              onNodeClick={onNodeClick}
              fitView
              fitViewOptions={{ padding: 0.15 }}
              className="w-full h-full"
            >
              <Background color="#FAF6F0" gap={16} size={1} />
              <Controls showInteractive={false} className="!bg-surface-raised !border-border !rounded-lg !shadow-sm" />
            </ReactFlow>

            {/* Description Panel overlay */}
            <AnimatePresence>
              {activeNode && (
                <motion.div 
                  className="absolute bottom-2 left-2 right-2 bg-surface-raised border border-border rounded-xl p-3 shadow-md z-20 flex justify-between items-start gap-4"
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 15 }}
                >
                  <div className="flex-1 min-w-0">
                    <span className="text-[9px] uppercase font-bold tracking-widest text-primary-light">
                      {(nodeType => {
                        if (nodeType === 'root') return 'TOPIK UTAMA';
                        if (nodeType === 'branch') return 'CABANG UTAMA';
                        return 'SUB-CABANG';
                      })(selectedNodeType)}
                    </span>
                    <h5 className="font-semibold text-text-primary text-sm mt-0.5 truncate">{selectedNodeLabel}</h5>
                    <p className="text-xs text-text-body mt-1 leading-relaxed line-clamp-2">
                      {selectedNodeDesc || 'Tidak ada deskripsi tersedia.'}
                    </p>
                  </div>
                  <div className="flex flex-col gap-2 items-end shrink-0">
                    <button 
                      onClick={() => setActiveNode(null)}
                      className="text-[10px] font-bold text-text-muted hover:text-text-primary uppercase tracking-wider"
                    >
                      Tutup
                    </button>
                    <button
                      onClick={() => {
                        if (onExpandNode) {
                          onExpandNode(activeNode.id, selectedNodeLabel);
                        }
                      }}
                      disabled={isExpanding}
                      className="text-[10px] font-bold text-primary hover:text-walnut hover:underline flex items-center gap-1 uppercase tracking-wider disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {isExpanding ? (
                        <>
                          <RefreshCw className="w-2.5 h-2.5 animate-spin" /> Eksplorasi...
                        </>
                      ) : (
                        <>
                          <GitFork className="w-2.5 h-2.5" /> Eksplorasi
                        </>
                      )}
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </div>
    </div>
  );

  if (isMaximized) {
    return createPortal(
      <>
        {/* Backdrop blurred overlay */}
        <div 
          className="fixed inset-0 bg-text-primary/45 backdrop-blur-md z-[999] transition-opacity duration-300 cursor-pointer"
          onClick={() => setIsMaximized(false)}
        />
        {/* Maximized card container */}
        <div 
          className="fixed inset-4 md:inset-10 z-[1000] shadow-2xl border-2 border-walnut bg-surface-overlay rounded-2xl p-6 overflow-hidden flex flex-col justify-between animate-in fade-in zoom-in-95 duration-200"
        >
          {/* Header */}
          <div className="flex justify-between items-center mb-4 shrink-0">
            <div>
              <h4 className="font-serif text-lg text-text-primary flex items-center gap-2">
                <Share2 className="w-5 h-5 text-primary" /> Visual Mind Map: <span className="text-walnut font-sans text-base font-semibold">{topic}</span>
              </h4>
              <p className="text-xs text-text-muted">Klik node untuk melihat deskripsi dan mengeksplorasi subtopik</p>
            </div>
            <div className="flex items-center gap-4">
              {/* Node Expansion Button */}
              <button 
                onClick={() => {
                  if (activeNode && onExpandNode) {
                    onExpandNode(activeNode.id, selectedNodeLabel);
                  }
                }}
                disabled={!activeNode || isExpanding}
                className={`text-xs font-semibold flex items-center gap-1 hover:underline transition-all duration-200
                  ${!activeNode ? 'opacity-40 cursor-not-allowed' : 'text-primary hover:text-walnut'}
                  ${isExpanding ? 'animate-pulse' : ''}
                `}
                title="Kembangkan cabang subtopik ini"
              >
                {isExpanding ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Mengekspansi...
                  </>
                ) : (
                  <>
                    <GitFork className="w-3.5 h-3.5" /> Eksplorasi Cabang
                  </>
                )}
              </button>

              {/* Full Screen Minimize Button */}
              <button 
                onClick={() => setIsMaximized(false)}
                className="text-xs font-semibold flex items-center gap-1 hover:underline text-text-primary hover:text-walnut transition-all"
                title="Kembalikan ukuran normal (Esc)"
              >
                <Minimize2 className="w-3.5 h-3.5" /> Kecilkan Layar
              </button>
            </div>
          </div>

          {/* Canvas Wrapper */}
          <div className="relative w-full flex-1 bg-background rounded-xl border border-border overflow-hidden">
            {isLoading ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center bg-background z-30">
                <motion.div 
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                  className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full mb-3"
                />
                <p className="text-sm font-medium text-text-body">Merajut Peta Konsep AI...</p>
                <p className="text-xs text-text-muted mt-1">Menyusun keterkaitan antar subtopik</p>
              </div>
            ) : nodesData.length === 0 ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center bg-background z-30">
                <Sparkles className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
                <p className="text-sm font-medium text-text-body">Belum ada peta konsep</p>
              </div>
            ) : (
              <>
                <ReactFlow
                  nodes={nodes}
                  edges={edges}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  nodeTypes={nodeTypes}
                  onNodeClick={onNodeClick}
                  fitView
                  fitViewOptions={{ padding: 0.15 }}
                  className="w-full h-full"
                >
                  <Background color="#FAF6F0" gap={16} size={1} />
                  <Controls showInteractive={false} className="!bg-surface-raised !border-border !rounded-lg !shadow-sm" />
                </ReactFlow>

                {/* Description Panel overlay */}
                <AnimatePresence>
                  {activeNode && (
                    <motion.div 
                      className="absolute bottom-4 left-4 right-4 bg-surface-raised border border-border rounded-xl p-4 shadow-lg z-20 flex justify-between items-start gap-4"
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 15 }}
                    >
                      <div className="flex-1 min-w-0">
                        <span className="text-[9px] uppercase font-bold tracking-widest text-primary-light">
                          {(nodeType => {
                            if (nodeType === 'root') return 'TOPIK UTAMA';
                            if (nodeType === 'branch') return 'CABANG UTAMA';
                            return 'SUB-CABANG';
                          })(selectedNodeType)}
                        </span>
                        <h5 className="font-semibold text-text-primary text-sm mt-0.5 truncate">{selectedNodeLabel}</h5>
                        <p className="text-xs text-text-body mt-1 leading-relaxed line-clamp-2">
                          {selectedNodeDesc || 'Tidak ada deskripsi tersedia.'}
                        </p>
                      </div>
                      <div className="flex flex-col gap-2 items-end shrink-0">
                        <button 
                          onClick={() => setActiveNode(null)}
                          className="text-[10px] font-bold text-text-muted hover:text-text-primary uppercase tracking-wider"
                        >
                          Tutup
                        </button>
                        <button
                          onClick={() => {
                            if (onExpandNode) {
                              onExpandNode(activeNode.id, selectedNodeLabel);
                            }
                          }}
                          disabled={isExpanding}
                          className="text-[10px] font-bold text-primary hover:text-walnut hover:underline flex items-center gap-1 uppercase tracking-wider disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          {isExpanding ? (
                            <>
                              <RefreshCw className="w-2.5 h-2.5 animate-spin" /> Eksplorasi...
                            </>
                          ) : (
                            <>
                              <GitFork className="w-2.5 h-2.5" /> Eksplorasi
                            </>
                          )}
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </>
            )}
          </div>
        </div>
      </>,
      document.body
    );
  }

  return mindMapContent;
}


// Interactive Latihan Soal (Quiz generator) with animations
function InteractiveQuiz({ sessionId, onScoreUpdate }) {
  const [currentStep, setCurrentStep] = useState(0); // 0: start, 1: question 1, 2: score
  const [selectedAns, setSelectedAns] = useState(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [score, setScore] = useState(0);
  const [quizData, setQuizData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Defensively parse quiz options to array format (BUG-03)
  const optionsList = useMemo(() => {
    if (!quizData || !quizData.options) return [];
    
    // If it's already an array
    if (Array.isArray(quizData.options)) {
      return quizData.options.map((opt) => {
        if (typeof opt === 'string') {
          return { key: opt, text: opt };
        }
        if (typeof opt === 'object' && opt !== null) {
          return { 
            key: opt.key || opt.id || '', 
            text: opt.text || opt.val || opt.value || '' 
          };
        }
        return { key: '', text: String(opt) };
      });
    }
    
    // If LLM returned options as a key-value dictionary (e.g. {"A": "Option text"})
    if (typeof quizData.options === 'object' && quizData.options !== null) {
      return Object.entries(quizData.options).map(([key, val]) => {
        if (typeof val === 'object' && val !== null) {
          return { 
            key: val.key || val.id || key, 
            text: val.text || val.val || val.value || '' 
          };
        }
        return { key, text: String(val) };
      });
    }
    
    return [];
  }, [quizData]);

  const fetchQuizQuestion = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/quiz?session_id=${sessionId}`);
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
      await fetch(`${API_BASE_URL}/api/quiz/submit`, {
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
              {optionsList.map((opt) => {
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
  const [user_name, setUserName] = useState(() => localStorage.getItem('scholarbot_user_name') || 'Budi');
  const [isEditingName, setIsEditingName] = useState(false);
  const [tempName, setTempName] = useState(user_name);

  const handleSaveName = () => {
    const trimmed = tempName.trim();
    if (trimmed) {
      setUserName(trimmed);
      localStorage.setItem('scholarbot_user_name', trimmed);
    } else {
      setTempName(user_name);
    }
    setIsEditingName(false);
  };
  const [sessionId] = useState(() => {
    const saved = sessionStorage.getItem("scholarbot_session_id");
    if (saved) return saved;
    const fresh = `sess-${Math.random().toString(36).substring(2, 11)}`;
    sessionStorage.setItem("scholarbot_session_id", fresh);
    return fresh;
  });

  // Gamification progress states
  const [mlProgress, setMlProgress] = useState(78);
  const [chemProgress, setChemProgress] = useState(45);
  const [historyProgress, setHistoryProgress] = useState(60);
  
  // Chat input
  const [chatInput, setChatInput] = useState('');
  // Citation system: which message's source panel is open, and which source is spotlighted
  const [openSourcePanels, setOpenSourcePanels] = useState([]);
  const [activeCitation, setActiveCitation] = useState(null); // { msgId, id }

  const handleCitationClick = (msgId, id) => {
    setOpenSourcePanels(prev => (prev.includes(msgId) ? prev : [...prev, msgId]));
    setActiveCitation({ msgId, id });
    // Wait for the panel to expand before scrolling the card into view
    setTimeout(() => {
      document.getElementById(`src-${msgId}-${id}`)?.scrollIntoView({
        block: 'nearest',
        behavior: 'smooth'
      });
    }, 60);
  };
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
  
  // Document search states
  const [docSearchQuery, setDocSearchQuery] = useState('');
  const [docSearchResults, setDocSearchResults] = useState([]);
  const [isDocSearching, setIsDocSearching] = useState(false);

  useEffect(() => {
    setDocSearchQuery('');
    setDocSearchResults([]);
    setIsDocSearching(false);
  }, [selectedPreviewDoc]);

  // Mindmap dynamic states
  const [mindmapTopic, setMindmapTopic] = useState('Machine Learning');
  const [mindmapNodes, setMindmapNodes] = useState([
    { id: '1', label: 'Machine Learning', type: 'root', desc: 'Topik utama yang sedang kita bedah bersama.' },
    { id: '2', label: 'Supervised', type: 'branch', desc: 'Belajar dari data berlabel. Contoh: Regresi & Klasifikasi.' },
    { id: '3', label: 'Unsupervised', type: 'branch', desc: 'Mencari struktur tersembunyi tanpa label. Contoh: Clustering.' },
    { id: '4', label: 'Reinforcement', type: 'branch', desc: 'Sistem belajar mandiri menggunakan reward & punishment.' }
  ]);
  const [mindmapEdges, setMindmapEdges] = useState([
    { source: '1', target: '2' },
    { source: '1', target: '3' },
    { source: '1', target: '4' }
  ]);
  const [isGeneratingMindMap, setIsGeneratingMindMap] = useState(false);
  const [isExpandingMindMap, setIsExpandingMindMap] = useState(false);

  // Helper to resolve actual study topic from history, ignoring meta commands
  const getActualTopic = (fallbackTopic) => {
    const userMessages = messages.filter(m => m.role === 'user');
    for (let i = userMessages.length - 1; i >= 0; i--) {
      const msg = userMessages[i].content.trim();
      const lower = msg.toLowerCase();
      const isMetaOnly = [
        "mindmap", 
        "mind map", 
        "peta konsep", 
        "buat jadi", 
        "kuis", 
        "soal", 
        "latihan", 
        "reactflow",
        "pendekatan reactflow"
      ].some(cmd => lower === cmd || lower === `buat ${cmd}` || lower === `buatkan ${cmd}` || lower === `buatkan saya ${cmd}` || lower === `coba pakai ${cmd}`);
      
      const containsMeta = ["mindmap", "mind map", "peta konsep", "buat jadi", "reactflow"].some(cmd => lower.includes(cmd));
      
      if (isMetaOnly) {
        continue;
      }
      
      if (containsMeta) {
        const cleaned = msg.replace(/(buat jadi|buatkan|buat|coba pakai|pendekatan|reactflow|mindmap|mind map|peta konsep)/gi, "").trim();
        if (cleaned.length > 2 && cleaned.length < 50) {
          return cleaned;
        }
        continue;
      }
      
      if (msg.length > 2 && msg.length < 60) {
        return msg;
      }
    }
    return fallbackTopic || 'Machine Learning';
  };

  const handleGenerateMindMap = async (topic) => {
    if (!topic || !topic.trim()) return;
    setIsGeneratingMindMap(true);
    
    // Sanitize input topic using getActualTopic helper
    const sanitizedTopic = getActualTopic(topic);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/mindmap/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: sanitizedTopic, session_id: sessionId })
      });
      if (!response.ok) throw new Error("Gagal generate peta konsep");
      const data = await response.json();
      if (data.nodes && data.edges) {
        const rootNode = data.nodes.find(n => n.type === 'root');
        const finalTopic = rootNode ? rootNode.label : sanitizedTopic;
        setMindmapTopic(finalTopic);
        setMindmapNodes(data.nodes);
        setMindmapEdges(data.edges);
      }
    } catch (err) {
      console.warn("Gagal membuat mindmap, menggunakan fallback:", err);
      setMindmapTopic(sanitizedTopic);
      setMindmapNodes([
        { id: '1', label: sanitizedTopic, type: 'root', desc: `Topik utama tentang ${sanitizedTopic}.` },
        { id: '2', label: 'Konsep Dasar', type: 'branch', desc: 'Dasar-dasar dan fundamental penting.' },
        { id: '3', label: 'Penerapan Praktis', type: 'branch', desc: 'Bagaimana konsep ini diterapkan di dunia nyata.' },
        { id: '4', label: 'Tantangan Utama', type: 'branch', desc: 'Hambatan dan tantangan dalam mempelajari topik ini.' }
      ]);
      setMindmapEdges([
        { source: '1', target: '2' },
        { source: '1', target: '3' },
        { source: '1', target: '4' }
      ]);
    } finally {
      setIsGeneratingMindMap(false);
    }
  };

  const handleExpandMindMapNode = async (nodeId, nodeLabel) => {
    if (isExpandingMindMap) return;
    setIsExpandingMindMap(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/mindmap/expand`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: mindmapTopic,
          node_id: nodeId,
          node_label: nodeLabel,
          existing_nodes: mindmapNodes,
          existing_edges: mindmapEdges,
          session_id: sessionId
        })
      });
      if (!response.ok) throw new Error("Gagal mengekspansi subtopik");
      const data = await response.json();
      if (data.nodes && data.edges) {
        const existingIds = new Set(mindmapNodes.map(n => n.id.toString()));
        const newNodes = data.nodes.filter(n => !existingIds.has(n.id.toString()));
        
        setMindmapNodes(prev => [...prev, ...newNodes]);
        setMindmapEdges(prev => [...prev, ...data.edges]);
      }
    } catch (err) {
      console.warn("Gagal mengekspansi subtopik, menggunakan fallback:", err);
      const newId1 = `sub-${nodeId}-${Date.now()}-1`;
      const newId2 = `sub-${nodeId}-${Date.now()}-2`;
      setMindmapNodes(prev => [
        ...prev,
        { id: newId1, label: `Detail ${nodeLabel}`, type: 'sub-branch', desc: `Detail lebih lanjut mengenai subtopik ${nodeLabel}.` },
        { id: newId2, label: `Studi Kasus`, type: 'sub-branch', desc: `Studi kasus nyata tentang penerapan ${nodeLabel}.` }
      ]);
      setMindmapEdges(prev => [
        ...prev,
        { source: nodeId, target: newId1 },
        { source: nodeId, target: newId2 }
      ]);
    } finally {
      setIsExpandingMindMap(false);
    }
  };

  // Automatically generate or update mind map when activeMode is changed to mindmap
  useEffect(() => {
    if (activeMode === 'mindmap') {
      const userMessages = messages.filter(m => m.role === 'user');
      if (userMessages.length > 0) {
        const lastUserMsg = userMessages[userMessages.length - 1].content;
        handleGenerateMindMap(lastUserMsg);
      } else {
        handleGenerateMindMap('Machine Learning');
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeMode]);

  
  // Ref for auto scroll
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Load session from backend on mount
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}`);
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

    if (activeMode === 'mindmap') {
      handleGenerateMindMap(textToSend);
    }

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

    const MAX_RETRIES = 1;
    let lastError = null;

    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout

        const response = await fetch(`${API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: controller.signal,
          body: JSON.stringify({
            message: textToSend,
            session_id: sessionId,
            personality: personality,
            user_name: user_name,
            mode: activeMode
          })
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Server error: ${response.status}`);
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

        return; // Success — exit retry loop

      } catch (error) {
        lastError = error;
        console.warn(`[Chat] Attempt ${attempt + 1} failed:`, error.message);

        if (attempt < MAX_RETRIES) {
          // Brief delay before retry
          await new Promise(resolve => setTimeout(resolve, 1500));
          continue;
        }
      }
    }

    // All retries exhausted — show contextual error
    setIsTyping(false);

    let errorContent;
    if (lastError?.name === 'AbortError') {
      errorContent = '⏳ Waktu permintaan habis. Server LLM mungkin sedang sibuk — coba kirim ulang pesan Anda.';
    } else if (lastError?.message?.includes('Failed to fetch') || lastError?.message?.includes('NetworkError') || lastError?.message?.includes('ERR_CONNECTION_REFUSED')) {
      // Backend not reachable at all
      errorContent = `⚠️ Hubungan terputus. Pastikan FastAPI backend Anda berjalan di ${API_BASE_URL} dengan menjalankan command:\n\`uvicorn api:app --reload\` di folder \`scholarbot\`.`;
    } else {
      errorContent = `⚠️ Gagal mendapatkan respons: ${lastError?.message || 'Unknown error'}. Coba kirim ulang pesan Anda.`;
    }

    setMessages(prev => [...prev, {
      id: `err-${Date.now()}`,
      role: "assistant",
      content: errorContent,
      time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
    }]);
  };

  // In-document search handler
  const handleDocSearch = async () => {
    if (!docSearchQuery.trim() || !selectedPreviewDoc) return;
    setIsDocSearching(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/session/${sessionId}/search-doc?query=${encodeURIComponent(docSearchQuery)}&filename=${encodeURIComponent(selectedPreviewDoc.filename)}`);
      if (res.ok) {
        const data = await res.json();
        setDocSearchResults(data.results || []);
      }
    } catch (e) {
      console.warn("Gagal melakukan pencarian dokumen:", e);
    } finally {
      setIsDocSearching(false);
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
      await fetch(`${API_BASE_URL}/api/session/${sessionId}/message/feedback`, {
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
      await fetch(`${API_BASE_URL}/api/session/${sessionId}/reset`, {
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
        const response = await fetch(`${API_BASE_URL}/api/upload`, {
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
      const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/doc/${encodeURIComponent(filename)}`, {
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
      await fetch(`${API_BASE_URL}/api/session/${sessionId}/clear-docs`, {
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
            <div className="w-11 h-11 rounded-xl bg-surface-raised border border-border flex items-center justify-center shadow-sm text-walnut">
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
          <div className="group flex items-center gap-3 p-3 bg-surface-raised border border-border rounded-2xl shadow-sm relative transition-all duration-300 hover:border-walnut/40">
            <div className="w-9 h-9 rounded-full bg-divider border border-border text-walnut flex items-center justify-center font-serif text-lg font-semibold shrink-0">
              {user_name[0]?.toUpperCase() || 'S'}
            </div>
            <div className="flex-1 min-w-0">
              {isEditingName ? (
                <input
                  type="text"
                  value={tempName}
                  onChange={(e) => setTempName(e.target.value)}
                  onBlur={handleSaveName}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveName();
                    if (e.key === 'Escape') {
                      setTempName(user_name);
                      setIsEditingName(false);
                    }
                  }}
                  className="w-full bg-background border border-walnut rounded px-1.5 py-0.5 text-xs text-text-primary focus:outline-none font-semibold"
                  autoFocus
                  maxLength={15}
                />
              ) : (
                <div className="flex items-center gap-1.5">
                  <span 
                    onClick={() => {
                      setTempName(user_name);
                      setIsEditingName(true);
                    }}
                    className="text-xs font-semibold text-text-primary leading-tight truncate cursor-pointer hover:text-walnut hover:underline flex items-center gap-1"
                    title="Klik untuk mengubah nama"
                  >
                    Halo, {user_name}!
                  </span>
                  <button
                    onClick={() => {
                      setTempName(user_name);
                      setIsEditingName(true);
                    }}
                    className="opacity-0 group-hover:opacity-100 text-text-muted hover:text-walnut transition-opacity p-0.5"
                    title="Ubah nama"
                  >
                    <Edit3 className="w-3 h-3" />
                  </button>
                </div>
              )}
              <span className="text-[10px] text-text-muted mt-0.5 block">Semangat belajar hari ini!</span>
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
            <motion.button 
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveMode('belajar')}
              className={`w-full py-2.5 px-3.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-3 text-left
                ${activeMode === 'belajar' 
                  ? 'bg-walnut text-surface-raised shadow-sm font-semibold' 
                  : 'text-text-muted hover:bg-divider hover:text-text-primary'
                }`}
            >
              <Compass className="w-4 h-4" />
              <span>Belajar</span>
            </motion.button>

            {/* Rangkuman */}
            <motion.button 
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveMode('rangkuman')}
              className={`w-full py-2.5 px-3.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-3 text-left
                ${activeMode === 'rangkuman' 
                  ? 'bg-walnut text-surface-raised shadow-sm font-semibold' 
                  : 'text-text-muted hover:bg-divider hover:text-text-primary'
                }`}
            >
              <FileText className="w-4 h-4" />
              <span>Rangkuman</span>
            </motion.button>

            {/* Latihan Soal */}
            <motion.button 
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveMode('latihan')}
              className={`w-full py-2.5 px-3.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-3 text-left
                ${activeMode === 'latihan' 
                  ? 'bg-walnut text-surface-raised shadow-sm font-semibold' 
                  : 'text-text-muted hover:bg-divider hover:text-text-primary'
                }`}
            >
              <Award className="w-4 h-4" />
              <span>Latihan Soal</span>
            </motion.button>

            {/* Mind Map */}
            <motion.button 
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setActiveMode('mindmap')}
              className={`w-full py-2.5 px-3.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-3 text-left
                ${activeMode === 'mindmap' 
                  ? 'bg-walnut text-surface-raised shadow-sm font-semibold' 
                  : 'text-text-muted hover:bg-divider hover:text-text-primary'
                }`}
            >
              <Share2 className="w-4 h-4" />
              <span>Mind Map</span>
            </motion.button>

            {/* Reset Chat Button - ELEGANT RED HIGHLIGHT */}
            <motion.button 
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleResetChat}
              className="w-full py-2.5 px-3.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-3 text-left text-red-500 hover:bg-red-50 mt-2 border border-dashed border-red-200/50"
            >
              <Trash2 className="w-4 h-4" />
              <span>Reset Chat</span>
            </motion.button>
          </div>

          {/* RAG Upload Area inside sidebar */}
          <div className="flex flex-col gap-2 pt-2 border-t border-divider">
            <label className="text-[10px] uppercase font-bold tracking-wider text-text-muted px-1">Unggah Dokumen (RAG)</label>
            
            <motion.div 
              whileHover={{ scale: 1.015, borderColor: '#4A3728' }}
              whileTap={{ scale: 0.985 }}
              className="relative border border-dashed border-border rounded-xl bg-surface-raised p-3 flex flex-col items-center justify-center text-center cursor-pointer transition-colors group"
            >
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
            </motion.div>

            {uploadedDocs.length > 0 && (
              <div className="flex flex-col gap-1.5 max-h-28 overflow-y-auto mt-1 bg-surface-raised border border-border p-2 rounded-xl scrollbar-thin">
                <AnimatePresence initial={false}>
                  {uploadedDocs.map((doc) => (
                    <motion.div 
                      key={doc.filename}
                      initial={{ opacity: 0, height: 0, y: -4 }}
                      animate={{ opacity: 1, height: 'auto', y: 0 }}
                      exit={{ opacity: 0, height: 0, y: -4 }}
                      transition={{ duration: 0.2 }}
                      className="flex justify-between items-center bg-background px-2 py-1.5 rounded-lg border border-border text-[10px] hover:border-walnut transition-colors group/doc overflow-hidden"
                    >
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
                    </motion.div>
                  ))}
                </AnimatePresence>
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
                      whileHover={{ y: -6 }}
                      whileTap={{ scale: 0.98 }}
                      className="bg-gradient-to-tr from-surface-raised to-surface/20 border border-border rounded-2xl p-4 shadow-sm flex flex-col justify-between h-32 cursor-pointer transition-all duration-300 hover:border-primary/50 hover:shadow-[0_12px_24px_rgba(139,105,20,0.06)]"
                      onClick={() => handleSendMessage("Apa itu Machine Learning?")}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-blue-50/70 border border-blue-100 text-blue-700 flex items-center justify-center">
                          <Compass className="w-5 h-5" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-text-primary">Machine Learning</span>
                          <span className="text-[10px] text-text-muted mt-0.5">Progres: {mlProgress}%</span>
                        </div>
                      </div>
                      <div className="w-full">
                        <div className="h-1 bg-divider rounded-full overflow-hidden mb-1.5">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${mlProgress}%` }}
                            transition={{ type: "spring", stiffness: 60, damping: 12, delay: 0.1 }}
                            className="h-full bg-gradient-to-r from-walnut to-primary rounded-full" 
                          />
                        </div>
                        <span className="text-[9px] text-text-muted">Terakhir dipelajari baru saja</span>
                      </div>
                    </motion.div>

                    {/* Card 2 */}
                    <motion.div 
                      whileHover={{ y: -6 }}
                      whileTap={{ scale: 0.98 }}
                      className="bg-gradient-to-tr from-surface-raised to-surface/20 border border-border rounded-2xl p-4 shadow-sm flex flex-col justify-between h-32 cursor-pointer transition-all duration-300 hover:border-primary/50 hover:shadow-[0_12px_24px_rgba(139,105,20,0.06)]"
                      onClick={() => handleSendMessage("Buat kuis Stoikiometri Kimia")}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-emerald-50/70 border border-emerald-100 text-emerald-700 flex items-center justify-center">
                          <BookOpen className="w-5 h-5" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-text-primary">Kimia: Stoikiometri</span>
                          <span className="text-[10px] text-text-muted mt-0.5">Progres: {chemProgress}%</span>
                        </div>
                      </div>
                      <div className="w-full">
                        <div className="h-1 bg-divider rounded-full overflow-hidden mb-1.5">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${chemProgress}%` }}
                            transition={{ type: "spring", stiffness: 60, damping: 12, delay: 0.2 }}
                            className="h-full bg-gradient-to-r from-walnut to-primary rounded-full" 
                          />
                        </div>
                        <span className="text-[9px] text-text-muted">Terakhir dipelajari baru saja</span>
                      </div>
                    </motion.div>

                    {/* Card 3 */}
                    <motion.div 
                      whileHover={{ y: -6 }}
                      whileTap={{ scale: 0.98 }}
                      className="bg-gradient-to-tr from-surface-raised to-surface/20 border border-border rounded-2xl p-4 shadow-sm flex flex-col justify-between h-32 cursor-pointer transition-all duration-300 hover:border-primary/50 hover:shadow-[0_12px_24px_rgba(139,105,20,0.06)]"
                      onClick={() => handleSendMessage("Ceritakan Perang Dunia II")}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-amber-50/70 border border-amber-100 text-amber-700 flex items-center justify-center">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-text-primary">Perang Dunia II</span>
                          <span className="text-[10px] text-text-muted mt-0.5">Progres: {historyProgress}%</span>
                        </div>
                      </div>
                      <div className="w-full">
                        <div className="h-1 bg-divider rounded-full overflow-hidden mb-1.5">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${historyProgress}%` }}
                            transition={{ type: "spring", stiffness: 60, damping: 12, delay: 0.3 }}
                            className="h-full bg-gradient-to-r from-walnut to-primary rounded-full" 
                          />
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
                        initial={{ opacity: 0, y: 20, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ type: "spring", stiffness: 130, damping: 15 }}
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
                              ? 'bg-gradient-to-br from-surface-raised to-surface/30 border-border text-text-body font-serif shadow-[0_4px_16px_rgba(44,36,23,0.02)]' 
                              : 'bg-surface border-border text-text-primary shadow-[0_2px_8px_rgba(44,36,23,0.02)]'
                            }`}
                          >
                            {/* Simple Markdown support simulator */}
                            {isBot ? (
                              <AnswerBody
                                content={msg.content}
                                sourceCount={msg.sources?.length || 0}
                                activeId={activeCitation?.msgId === msg.id ? activeCitation.id : null}
                                onCite={(id) => handleCitationClick(msg.id, id)}
                              />
                            ) : (
                              <div>{msg.content}</div>
                            )}
                          </div>

                          {/* ─── RAG SOURCE VISUALIZER & RELEVANCE INDICATOR (v3.2 ROADMAP) ─── */}
                          {isBot && msg.sources && msg.sources.length > 0 && (() => {
                            const citedIds = parseCitationIds(msg.content, msg.sources.length);
                            return (
                            <div className="mt-2 border border-border bg-surface rounded-xl overflow-hidden shadow-sm max-w-full">
                              <details
                                className="group"
                                open={openSourcePanels.includes(msg.id)}
                                onToggle={(e) => setOpenSourcePanels(prev => (
                                  e.target.open
                                    ? (prev.includes(msg.id) ? prev : [...prev, msg.id])
                                    : prev.filter(id => id !== msg.id)
                                ))}
                              >
                                <summary className="flex items-center justify-between p-2.5 bg-surface-raised cursor-pointer hover:bg-divider transition-colors select-none text-[10px] font-bold text-walnut">
                                  <div className="flex items-center gap-1.5">
                                    <Sparkles className="w-3.5 h-3.5 text-primary" />
                                    <span>Sumber Referensi Akademis ({msg.sources.length})</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-[8px] px-2 py-0.5 rounded-full bg-walnut/10 text-walnut font-bold">
                                      {citedIds.length > 0
                                        ? `${citedIds.length} dikutip di jawaban`
                                        : 'Belum ada kutipan inline'}
                                    </span>
                                    <span className="text-[8px] px-2 py-0.5 rounded-full bg-walnut/10 text-walnut font-bold">
                                      Relevansi: {Math.min(100, Math.round((msg.sources[0]?.score || 0) * 100))}%
                                    </span>
                                    <ChevronDown className="w-3 h-3 text-text-muted group-open:rotate-180 transition-transform" />
                                  </div>
                                </summary>
                                <div className="p-3 border-t border-divider bg-surface flex flex-col gap-2 max-h-48 overflow-y-auto scrollbar-thin">
                                  {msg.sources.map((src, sIdx) => {
                                    const citeId = src.id ?? sIdx + 1;
                                    const isCited = citedIds.includes(citeId);
                                    // Dimming only reads as a contrast when something IS cited.
                                    // Answers with no inline markers at all (quiz mode, for one)
                                    // were showing every source greyed out as if nothing matched.
                                    const isDimmed = citedIds.length > 0 && !isCited;
                                    const isActive = activeCitation?.msgId === msg.id && activeCitation.id === citeId;
                                    return (
                                    <div
                                      key={sIdx}
                                      id={`src-${msg.id}-${citeId}`}
                                      className={`p-2.5 rounded-lg border bg-surface-raised/40 transition-colors
                                        ${isActive ? 'border-walnut ring-1 ring-walnut' : 'border-border hover:border-walnut'}
                                        ${isDimmed ? 'opacity-60' : ''}`}
                                    >
                                      <div className="flex justify-between items-center mb-1 text-[9px]">
                                        <span className="flex items-center gap-1.5 font-bold text-text-primary">
                                          <span className="inline-flex items-center justify-center min-w-[15px] h-[15px] px-1 rounded-full bg-walnut text-surface-raised text-[8px] leading-none">
                                            {citeId}
                                          </span>
                                          📄 {src.source}
                                          {typeof src.chunk_index === 'number' && (
                                            <span className="font-normal text-text-muted">· bagian {src.chunk_index + 1}</span>
                                          )}
                                        </span>
                                        <span className="text-[8px] font-semibold text-walnut-muted">
                                          {citedIds.length === 0 ? '' : isCited ? 'Dikutip · ' : 'Tidak dikutip · '}
                                          Skor {src.score?.toFixed(3)}
                                        </span>
                                      </div>
                                      <p className="text-[9px] leading-relaxed text-text-body font-mono whitespace-pre-wrap bg-background/50 p-2 rounded border border-border/50 max-h-24 overflow-y-auto">
                                        {src.content}
                                      </p>
                                    </div>
                                    );
                                  })}
                                </div>
                              </details>
                            </div>
                            );
                          })()}
                          
                          {/* Timestamp and feedback actions */}
                          <div className={`flex items-center gap-3 mt-1.5 text-[9px] text-text-muted ${!isBot ? 'justify-end' : ''}`}>
                            <span>{msg.time}</span>
                            {isBot && (
                              <>
                                <motion.button 
                                  whileHover={{ scale: 1.04 }}
                                  whileTap={{ scale: 0.92 }}
                                  onClick={() => {
                                    navigator.clipboard.writeText(msg.content);
                                  }}
                                  className="hover:text-text-primary transition-colors flex items-center gap-0.5 focus:text-walnut"
                                >
                                  📋 Salin
                                </motion.button>
                                <motion.button 
                                  whileHover={{ scale: 1.05 }}
                                  whileTap={{ scale: 0.88 }}
                                  onClick={() => handleMessageFeedback(msg.id, "like")}
                                  className={`transition-colors flex items-center gap-0.5 ${msg.feedback === 'like' ? 'text-walnut font-bold scale-105' : 'hover:text-text-primary'}`}
                                >
                                  👍 {msg.feedback === 'like' ? 'Berguna!' : 'Berguna'}
                                </motion.button>
                                <motion.button 
                                  whileHover={{ scale: 1.05 }}
                                  whileTap={{ scale: 0.88 }}
                                  onClick={() => handleMessageFeedback(msg.id, "dislike")}
                                  className={`transition-colors flex items-center gap-0.5 ${msg.feedback === 'dislike' ? 'text-red-500 font-bold scale-105' : 'hover:text-text-primary'}`}
                                >
                                  👎 {msg.feedback === 'dislike' ? 'Kurang!' : 'Kurang'}
                                </motion.button>
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
                <InteractiveMindMap 
                  topic={mindmapTopic}
                  nodesData={mindmapNodes}
                  edgesData={mindmapEdges}
                  isLoading={isGeneratingMindMap}
                  isExpanding={isExpandingMindMap}
                  onExpandNode={handleExpandMindMapNode}
                  onRegenerate={handleGenerateMindMap}
                />
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
                {/* Search Bar */}
                <div className="mb-5 bg-surface-raised border border-border p-3.5 rounded-xl flex flex-col gap-2.5 shadow-sm">
                  <span className="text-[10px] font-bold text-walnut uppercase tracking-widest">Pencarian Konsep Dalam Dokumen</span>
                  <div className="flex gap-2">
                    <input 
                      type="text" 
                      value={docSearchQuery}
                      onChange={(e) => setDocSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleDocSearch()}
                      placeholder="Cari kata kunci, topik, atau konsep..."
                      className="flex-1 bg-background border border-border rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-walnut placeholder-text-subtle"
                    />
                    <button 
                      onClick={handleDocSearch}
                      disabled={isDocSearching}
                      className="px-4 py-2 bg-walnut hover:bg-walnut-light text-surface-raised rounded-xl text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-50"
                    >
                      {isDocSearching ? (
                        <span className="animate-spin rounded-full h-3 w-3 border-b-2 border-surface-raised" />
                      ) : (
                        <Search className="w-3.5 h-3.5" />
                      )}
                      <span>Cari</span>
                    </button>
                  </div>
                  
                  {docSearchResults.length > 0 && (
                    <div className="flex flex-col gap-2 max-h-40 overflow-y-auto mt-2 scrollbar-thin border-t border-divider pt-2">
                      <span className="text-[9px] font-bold text-secondary">DITEMUKAN {docSearchResults.length} BAGIAN YANG RELEVAN:</span>
                      {docSearchResults.map((res, rIdx) => (
                        <div key={rIdx} className="p-2.5 rounded-lg border border-border bg-background hover:border-walnut transition-colors">
                          <div className="flex justify-between items-center mb-1 text-[8px] font-semibold text-text-muted">
                            <span>Bagian #{res.chunk_index + 1}</span>
                            <span className="text-walnut">Relevansi: {Math.round(res.score * 100)}%</span>
                          </div>
                          <p className="text-[9px] leading-relaxed text-text-body font-mono whitespace-pre-wrap">
                            {res.content}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                  {docSearchQuery && docSearchResults.length === 0 && !isDocSearching && (
                    <span className="text-[9px] text-text-subtle italic">Tidak ada kecocokan. Coba konsep lainnya.</span>
                  )}
                </div>

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
