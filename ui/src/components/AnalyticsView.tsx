import React, { useEffect, useMemo, useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Target, 
  AlertCircle,
  Binary,
  Cpu,
  RefreshCcw,
  Workflow
} from 'lucide-react';
import { 
  ComposedChart,
  Bar,
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend,
  Scatter
} from 'recharts';
import { cn } from '../lib/utils';
import { getGlobalImportance, getRuntimeMetrics, triggerModelRetraining, type RuntimeMetrics } from '../api';

export default function AnalyticsView() {
  const [isRetraining, setIsRetraining] = useState(false);
  const [trainingMessage, setTrainingMessage] = useState('Idle');
  const [lastRun, setLastRun] = useState('Sun 02:00 UTC');
  const [metrics, setMetrics] = useState<RuntimeMetrics | null>(null);
  const [importance, setImportance] = useState<Record<string, number>>({});

  useEffect(() => {
    let mounted = true;

    const refreshAnalytics = async () => {
      try {
        const [runtimeMetrics, featureImportance] = await Promise.all([
          getRuntimeMetrics(),
          getGlobalImportance(),
        ]);
        if (!mounted) return;
        setMetrics(runtimeMetrics);
        setImportance(featureImportance);
        setTrainingMessage(runtimeMetrics.training.message);
        setLastRun(runtimeMetrics.training.last_run ? new Date(runtimeMetrics.training.last_run).toLocaleString() : 'Not run');
        setIsRetraining(runtimeMetrics.training.status === 'queued' || runtimeMetrics.training.status === 'running');
      } catch {
        if (mounted) setTrainingMessage('API analytics unavailable');
      }
    };

    refreshAnalytics();
    const interval = window.setInterval(refreshAnalytics, 8000);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  const modelStats = [
    { name: 'Isolation Forest', healthy: true, load: 12, alerts: 140 },
    { name: 'One-Class SVM', healthy: true, load: 8, alerts: 12 },
    { name: 'Simple Ensemble', healthy: Boolean(metrics?.model_loaded ?? true), load: isRetraining ? 71 : 18, alerts: metrics?.anomaly_count ?? 152 },
    { name: 'Drift Evaluator', healthy: metrics?.drift_status !== 'review' && !isRetraining, load: Math.round((metrics?.drift_score ?? 0.1) * 100), alerts: 0, error: isRetraining ? 'Retraining queued...' : `Drift ${metrics?.drift_status ?? 'stable'}` },
  ];
  const featureRows = useMemo(() => Object.entries(importance).slice(0, 5), [importance]);

  const handleRetraining = async () => {
    setIsRetraining(true);
    setTrainingMessage('Queueing retraining job...');

    try {
      const result = await triggerModelRetraining();
      setTrainingMessage(result.message);
      setLastRun(new Date().toLocaleString());

      window.setTimeout(() => {
        setIsRetraining(false);
        setTrainingMessage('Retraining completed');
      }, 10000);
    } catch (error) {
      setIsRetraining(false);
      setTrainingMessage(error instanceof Error ? error.message : 'Retraining failed');
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-3">
            <BarChart3 className="w-6 h-6 text-indigo-400" />
            Model Intelligence & Analytics
          </h2>
          <p className="text-xs text-slate-500 mt-1">Deep analysis of detection performance, false positive rates, and concept drift.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleRetraining}
            disabled={isRetraining}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 disabled:bg-indigo-600/50 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/20"
          >
            <RefreshCcw className={cn("w-4 h-4", isRetraining && "animate-spin")} />
            {isRetraining ? 'Retraining...' : 'Trigger Retraining'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 grid grid-cols-4 gap-6">
          <AnalyticsStat label="Model Decisions" value={String(metrics?.total_decisions ?? 0)} trend="Live" icon={<Target className="w-4 h-4" />} />
          <AnalyticsStat label="Anomaly Rate" value={`${(((metrics?.anomaly_rate ?? 0) * 100)).toFixed(1)}%`} trend={metrics?.drift_status === 'review' ? '+Drift' : 'Stable'} icon={<Workflow className="w-4 h-4 text-indigo-400" />} />
          <AnalyticsStat label="Avg Score" value={(metrics?.avg_anomaly_score ?? 0).toFixed(2)} trend="Rolling" icon={<BarChart3 className="w-4 h-4 text-pink-400" />} />
          <AnalyticsStat label="Drift Score" value={(metrics?.drift_score ?? 0).toFixed(2)} trend={metrics?.drift_status === 'review' ? '+Review' : 'Stable'} icon={<TrendingUp className="w-4 h-4 text-emerald-400" />} />
        </div>

        <div className="col-span-8 bg-[#0c0c0c] border border-white/5 rounded-2xl p-6 shadow-xl">
           <h3 className="text-xs font-bold uppercase tracking-widest text-white mb-6 flex items-center gap-2">
            <Binary className="w-4 h-4 text-pink-400" />
            True Positive vs False Positive Trends
          </h3>
          <div className="h-[350px]">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={ANALYTICS_DATA}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#ffffff05" />
                <XAxis dataKey="name" tick={{fontSize: 10}} stroke="#ffffff20" />
                <YAxis tick={{fontSize: 10}} stroke="#ffffff20" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111', border: '1px solid #ffffff10', fontSize: '10px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '10px', paddingTop: '20px' }} />
                <Bar dataKey="detections" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={30} name="True Positives" />
                <Line type="monotone" dataKey="fp" stroke="#ec4899" strokeWidth={2} name="False Positives" />
                <Scatter dataKey="drift" fill="#f59e0b" name="Pattern Drift" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-span-4 space-y-6">
          <div className="bg-[#0c0c0c] border border-white/5 rounded-2xl p-6 shadow-xl">
            <h3 className="text-xs font-bold uppercase tracking-widest text-white mb-6">Model Cluster Status</h3>
            <div className="space-y-4">
              {modelStats.map((model, i) => (
                <div key={i} className="p-4 bg-white/[0.02] border border-white/5 rounded-xl space-y-3">
                  <div className="flex justify-between items-center">
                    <p className="text-xs font-bold text-white">{model.name}</p>
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      model.healthy ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]"
                    )} />
                  </div>
              {model.healthy ? (
                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                      <span>LOAD: {model.load}%</span>
                      <span>ALERTS: {model.alerts}</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-[10px] text-rose-500/80 italic">
                      <AlertCircle className="w-3 h-3" />
                      {model.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-indigo-600/5 border border-indigo-500/10 rounded-2xl p-6">
             <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-indigo-500/10 rounded-lg">
                <Cpu className="w-4 h-4 text-indigo-400" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-widest text-indigo-300">Retraining Queue</h3>
            </div>
            <div className="text-[10px] text-slate-500 space-y-2">
              <div className="flex justify-between">
                <span>Last Queue Event:</span>
                <span className="text-white font-mono">{lastRun}</span>
              </div>
              <div className="flex justify-between">
                <span>Status:</span>
                <span className="text-white font-mono">{trainingMessage}</span>
              </div>
            </div>
          </div>

          <div className="bg-[#0c0c0c] border border-white/5 rounded-2xl p-6 shadow-xl">
            <h3 className="text-xs font-bold uppercase tracking-widest text-white mb-4">Top Decision Features</h3>
            <div className="space-y-3">
              {featureRows.length ? featureRows.map(([feature, value]) => (
                <div key={feature} className="flex items-center justify-between text-[10px] font-mono">
                  <span className="text-slate-400 truncate pr-3">{feature}</span>
                  <span className="text-indigo-300">{value.toFixed(2)}</span>
                </div>
              )) : (
                <p className="text-[10px] text-slate-500">Waiting for live decisions.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AnalyticsStat({ label, value, trend, icon }: { label: string, value: string, trend: string, icon: React.ReactNode }) {
  return (
    <div className="bg-[#0c0c0c] border border-white/5 p-5 rounded-2xl">
      <div className="flex justify-between items-start mb-4">
        <div className="p-2 bg-white/5 rounded-lg text-slate-400">{icon}</div>
        <div className={cn(
          "text-[10px] font-bold font-mono",
          trend.startsWith('+') ? "text-emerald-500" : (trend === 'Stable' || trend === 'Live' || trend === 'Rolling' ? "text-slate-500" : "text-rose-500")
        )}>{trend}</div>
      </div>
      <p className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mb-1">{label}</p>
      <p className="text-2xl font-bold text-white tracking-tighter">{value}</p>
    </div>
  );
}

const ANALYTICS_DATA = [
  { name: 'Mon', detections: 140, fp: 12, drift: 2 },
  { name: 'Tue', detections: 120, fp: 10, drift: 5 },
  { name: 'Wed', detections: 230, fp: 45, drift: 10 },
  { name: 'Thu', detections: 180, fp: 14, drift: 8 },
  { name: 'Fri', detections: 150, fp: 11, drift: 4 },
  { name: 'Sat', detections: 90, fp: 2, drift: 1 },
  { name: 'Sun', detections: 85, fp: 1, drift: 1 },
];
