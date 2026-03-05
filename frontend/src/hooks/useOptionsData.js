import { useCallback, useState } from 'react';

const API = 'http://localhost:5051';

export default function useOptionsData() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const analyze = useCallback(async (payload) => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/options/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Analyze failed (${res.status})`);
      const body = await res.json();
      setData(body);
      return body;
    } catch (e) {
      setError(e.message || 'Request failed');
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, analyze };
}
