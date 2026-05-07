export enum ThreatLevel {
  NORMAL = 'NORMAL',
  SUSPICIOUS = 'SUSPICIOUS',
  HIGH_RISK = 'HIGH_RISK',
  CRITICAL = 'CRITICAL'
}

export enum ActionType {
  BLOCK_CONNECTION = 'BLOCK_CONNECTION',
  ENFORCE_POL = 'ENFORCE_PATTERN_OF_LIFE',
  QUARANTINE = 'QUARANTINE',
  THROTTLE = 'THROTTLE',
  ALERT = 'ALERT'
}

export interface TelemetryEvent {
  id: string;
  timestamp: string;
  source: string;
  destination: string;
  protocol: string;
  bytes: number;
  score: number;
  threatLevel: ThreatLevel;
  entity: {
    id: string;
    type: 'DEVICE' | 'USER' | 'CLOUD_API';
    name: string;
  };
  explanation?: string[];
  autoAction?: {
    type: ActionType;
    status: 'ACTIVE' | 'PENDING' | 'COMPLETED';
    timestamp: string;
  };
}

export interface ModelMetrics {
  auc: number;
  precision: number;
  recall: number;
  drift: number;
  activeDevices: number;
}
