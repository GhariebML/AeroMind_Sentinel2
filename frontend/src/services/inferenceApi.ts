import type { HighwayEvent } from '../types/highway';

interface HighwayEventsResponse {
  source?: string;
  events?: HighwayEvent[];
}

const DEFAULT_BACKEND_URL = 'http://localhost:5000';

export async function fetchPythonInferenceEvents(): Promise<{ source: string; events: HighwayEvent[] } | null> {
  const candidates = getApiCandidates();

  for (const baseUrl of candidates) {
    try {
      const response = await fetch(`${baseUrl}/api/highway/events`, { cache: 'no-store' });
      if (!response.ok) continue;
      const payload = (await response.json()) as HighwayEventsResponse | HighwayEvent[];
      const events = Array.isArray(payload) ? payload : payload.events;
      if (events?.length) {
        return {
          source: Array.isArray(payload) ? 'python_inference' : payload.source ?? 'python_inference',
          events,
        };
      }
    } catch {
      // Try the next candidate silently; the UI has a strong offline mock fallback.
    }
  }

  return null;
}

function getApiCandidates(): string[] {
  const configured = import.meta.env.VITE_SENTINEL_API_URL as string | undefined;
  const sameOrigin = '';
  return [configured, sameOrigin, DEFAULT_BACKEND_URL].filter((value): value is string => value !== undefined);
}
