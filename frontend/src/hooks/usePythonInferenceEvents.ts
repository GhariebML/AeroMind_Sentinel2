import { useEffect, useState } from 'react';
import { fetchPythonInferenceEvents } from '../services/inferenceApi';
import type { HighwayEvent } from '../types/highway';

export function usePythonInferenceEvents(enabled: boolean, refreshMs = 2500) {
  const [events, setEvents] = useState<HighwayEvent[] | null>(null);
  const [source, setSource] = useState('browser_simulation');
  const [connectedState, setConnectedState] = useState(false);

  useEffect(() => {
    if (!enabled) return undefined;

    let alive = true;
    const load = async () => {
      const result = await fetchPythonInferenceEvents();
      if (!alive) return;
      if (result) {
        setEvents(result.events);
        setSource(result.source);
        setConnectedState(result.source !== 'mock');
      } else {
        setConnectedState(false);
      }
    };

    void load();
    const interval = window.setInterval(load, refreshMs);
    return () => {
      alive = false;
      window.clearInterval(interval);
    };
  }, [enabled, refreshMs]);

  return { events: enabled ? events : null, source: enabled ? source : 'browser_simulation', connected: enabled && connectedState };
}
