import { ActionType, TelemetryEvent, ThreatLevel } from './types';

const DEFAULT_API_URL = import.meta.env.PROD
  ? 'https://antigena-ai-defense-system.onrender.com'
  : 'http://localhost:8000';
const API_BASE_URL = (
  import.meta.env.VITE_ANTIGENA_API_URL ??
  import.meta.env.VITE_API_URL ??
  DEFAULT_API_URL
).replace(/\/$/, '');
const FEATURE_COUNT = 42;

interface PredictionResponse {
  anomaly_score: number;
  label: 'normal' | 'anomaly';
  confidence: number;
  explanation?: {
    explanation?: string;
    top_features?: Array<{ feature: string; importance: number; direction?: string }>;
  } | null;
  individual_models?: Record<string, { score: number; prediction: number }>;
  timestamp: string;
}

interface HealthResponse {
  status: string;
  model_loaded: boolean;
  timestamp: string;
}

export interface ApiStatus {
  online: boolean;
  modelLoaded: boolean;
  label: string;
}

export interface RuntimeMetrics {
  total_decisions: number;
  anomaly_count: number;
  anomaly_rate: number;
  avg_anomaly_score: number;
  drift_score: number;
  drift_status: string;
  model_loaded: boolean;
  model_type: string;
  training: {
    status: string;
    last_run: string | null;
    message: string;
  };
}

export interface AuditEvent {
  timestamp: string;
  source?: string;
  label: string;
  anomaly_score: number;
  confidence: number;
  explanation?: {
    top_features?: Array<{ feature: string; importance: number; direction?: string }>;
  };
}

export async function getApiStatus(): Promise<ApiStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed with ${response.status}`);
    }

    const health = (await response.json()) as HealthResponse;
    return {
      online: true,
      modelLoaded: health.model_loaded,
      label: health.model_loaded ? 'Model Connected' : 'API Online',
    };
  } catch {
    return {
      online: false,
      modelLoaded: false,
      label: 'Simulation Mode',
    };
  }
}

export async function scoreTelemetryEvent(event: TelemetryEvent): Promise<TelemetryEvent> {
  const features = buildFeatureVector(event);

  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      features,
      timestamp: new Date().toISOString(),
      source: event.source,
    }),
  });

  if (!response.ok) {
    throw new Error(`Prediction failed with ${response.status}`);
  }

  const prediction = (await response.json()) as PredictionResponse;
  const score = Math.round(prediction.anomaly_score * 1000) / 10;

  return {
    ...event,
    timestamp: new Date(prediction.timestamp).toLocaleTimeString(),
    score,
    threatLevel: toThreatLevel(score, prediction.label),
    explanation: buildExplanation(prediction),
    autoAction: prediction.label === 'anomaly' ? buildAction(score) : undefined,
  };
}

export async function triggerModelRetraining() {
  const response = await fetch(`${API_BASE_URL}/models/train`, { method: 'POST' });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || `Retraining failed with ${response.status}`);
  }

  return response.json() as Promise<{ message: string; status: string; model_loaded?: boolean }>;
}

export async function getRuntimeMetrics(): Promise<RuntimeMetrics> {
  const response = await fetch(`${API_BASE_URL}/metrics`);
  if (!response.ok) {
    throw new Error(`Metrics failed with ${response.status}`);
  }
  return response.json();
}

export async function getRecentAuditEvents(limit = 100): Promise<AuditEvent[]> {
  const response = await fetch(`${API_BASE_URL}/events/recent?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Audit events failed with ${response.status}`);
  }
  const payload = (await response.json()) as { events: AuditEvent[] };
  return payload.events;
}

export async function getGlobalImportance(): Promise<Record<string, number>> {
  const response = await fetch(`${API_BASE_URL}/explain/global`);
  if (!response.ok) {
    throw new Error(`Importance failed with ${response.status}`);
  }
  const payload = (await response.json()) as { feature_importance: Record<string, number> };
  return payload.feature_importance;
}

export function downloadCsv(filename: string, rows: Array<Record<string, string | number | undefined>>) {
  if (!rows.length) return;

  const headers = Object.keys(rows[0]);
  const csv = [
    headers.join(','),
    ...rows.map((row) => headers.map((header) => escapeCsv(row[header])).join(',')),
  ].join('\n');

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function buildFeatureVector(event: TelemetryEvent): number[] {
  const sourceParts = event.source.split('.').map(Number);
  const destinationParts = event.destination.split('.').map(Number);
  const protocolMap: Record<string, number> = {
    TCP: 1,
    UDP: 2,
    HTTPS: 3,
    SSH: 4,
    SMB: 5,
    DNS: 6,
  };

  const seed = [
    event.bytes,
    event.score,
    protocolMap[event.protocol] ?? 0,
    ...sourceParts,
    ...destinationParts,
  ];

  while (seed.length < FEATURE_COUNT) {
    const index = seed.length;
    const previous = seed[index - 1] ?? event.bytes;
    seed.push(((previous * 31 + index * 17) % 10000) / 10);
  }

  return seed.slice(0, FEATURE_COUNT);
}

function toThreatLevel(score: number, label: string): ThreatLevel {
  if (score >= 95) return ThreatLevel.CRITICAL;
  if (score >= 80) return ThreatLevel.HIGH_RISK;
  if (label === 'anomaly' || score >= 50) return ThreatLevel.SUSPICIOUS;
  return ThreatLevel.NORMAL;
}

function buildExplanation(prediction: PredictionResponse): string[] {
  if (prediction.explanation?.top_features?.length) {
    return prediction.explanation.top_features.map((feature) => `${feature.feature}: ${feature.direction ?? 'elevated'} influence`);
  }

  if (!prediction.individual_models) {
    return prediction.label === 'anomaly' ? ['Model ensemble detected abnormal behavior'] : ['Traffic matches learned baseline'];
  }

  return Object.entries(prediction.individual_models).map(([name, model]) => {
    const modelName = name.replace(/_/g, ' ');
    return `${modelName}: ${(model.score * 100).toFixed(1)}% anomaly signal`;
  });
}

function buildAction(score: number) {
  const type = score >= 90 ? ActionType.QUARANTINE : score >= 75 ? ActionType.ENFORCE_POL : ActionType.ALERT;

  return {
    type,
    status: 'ACTIVE' as const,
    timestamp: new Date().toLocaleTimeString(),
  };
}

function escapeCsv(value: string | number | undefined) {
  const text = String(value ?? '');
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}
