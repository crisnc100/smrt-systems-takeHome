import AsyncStorage from '@react-native-async-storage/async-storage';

export type EvidenceSnippet = { date?: string; revenue?: number };

const QUERY_MODE_KEY = 'QUERY_MODE';

export type QueryMode = 'classic' | 'ai';

export type ChatResponse = {
  answer_text?: string; // may be absent when error is returned
  tables_used?: string[];
  sql?: string;
  rows_scanned?: number;
  data_snippets?: EvidenceSnippet[];
  validations?: { name: string; status: 'pass' | 'fail' }[];
  confidence?: number;
  follow_ups?: string[];
  chart_suggestion?: { [k: string]: any };
  error?: string;
  suggestion?: string;
  query_mode?: QueryMode;
};

export async function getBaseUrl(): Promise<string> {
  try {
    const stored = await AsyncStorage.getItem('API_BASE_URL');
    return stored || 'http://localhost:8000';
  } catch {
    return 'http://localhost:8000';
  }
}

export async function setBaseUrl(url: string): Promise<void> {
  await AsyncStorage.setItem('API_BASE_URL', url);
}

export async function getQueryMode(): Promise<QueryMode> {
  try {
    const stored = await AsyncStorage.getItem(QUERY_MODE_KEY);
    return stored === 'ai' ? 'ai' : 'classic';
  } catch {
    return 'classic';
  }
}

export async function setQueryMode(mode: QueryMode): Promise<void> {
  await AsyncStorage.setItem(QUERY_MODE_KEY, mode);
}

export async function callChat(message: string, filters: any = {}, mode?: QueryMode): Promise<ChatResponse> {
  const base = await getBaseUrl();
  const queryMode = mode ?? await getQueryMode();
  const res = await fetch(`${base}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, filters, query_mode: queryMode })
  });
  const data = await res.json();
  if (typeof data === 'object' && data !== null) {
    (data as any).query_mode = queryMode;
  }
  return data;
}

export async function refreshData(): Promise<any> {
  const base = await getBaseUrl();
  const res = await fetch(`${base}/datasource/refresh`, { method: 'POST' });
  return res.json();
}

export async function callReport(type: 'revenue_by_month' | 'top_customers', filters: any = {}): Promise<any> {
  const base = await getBaseUrl();
  const res = await fetch(`${base}/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, filters })
  });
  return res.json();
}

export async function runSelfCheck(): Promise<any> {
  const base = await getBaseUrl();
  const res = await fetch(`${base}/debug/test-queries`);
  return res.json();
}

export async function getDataStatus(): Promise<any> {
  const base = await getBaseUrl();
  const res = await fetch(`${base}/debug/data-status`);
  return res.json();
}
