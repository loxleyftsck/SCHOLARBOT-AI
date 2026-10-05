// Centralized API configuration helper for ScholarBot AI
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

// A free backend may need time to wake. Only probe when the app is opened.
export async function waitForBackend(signal) {
  const deadline = Date.now() + 90000;
  while (!signal.aborted && Date.now() < deadline) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`, {
        signal: AbortSignal.any([signal, AbortSignal.timeout(15000)]),
      });
      if (response.ok) {
        const health = await response.json();
        if (!health.groq_configured) throw new Error('AI belum dikonfigurasi');
        return;
      }
    } catch (error) {
      if (signal.aborted || error.message === 'AI belum dikonfigurasi') throw error;
    }
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  throw new Error('Demo belum tersedia');
}
