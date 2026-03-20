import { useState, useCallback } from 'react';

const API = 'http://localhost:5051';

export default function useSectorData() {
  const [sectors, setSectors] = useState(null);
  const [etfDetail, setEtfDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState('');

  const scanSectors = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/sectors/scan`);
      if (!res.ok) throw new Error(`Sector scan failed (${res.status})`);
      const body = await res.json();
      if (body.error) throw new Error(body.error);
      setSectors(body);
      return body;
    } catch (e) {
      setError(e.message || 'Sector scan failed');
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const analyzeETF = useCallback(async (ticker) => {
    setDetailLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/sectors/analyze/${ticker}`);
      if (!res.ok) throw new Error(`ETF analyze failed (${res.status})`);
      const body = await res.json();
      if (body.error) throw new Error(body.error);
      setEtfDetail(body);
      return body;
    } catch (e) {
      setError(e.message || 'ETF analyze failed');
      throw e;
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const clearDetail = useCallback(() => setEtfDetail(null), []);

  return { sectors, etfDetail, loading, detailLoading, error, scanSectors, analyzeETF, clearDetail };
}
