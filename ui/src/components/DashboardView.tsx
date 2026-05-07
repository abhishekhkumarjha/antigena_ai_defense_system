import React, { useState } from 'react';
import { 
  Zap, 
  Lock, 
  Activity, 
  Cpu, 
  Binary, 
  ShieldAlert, 
  ShieldCheck, 
  ArrowRight, 
  Monitor, 
  User, 
  MoreVertical 
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  CartesianGrid, 
  XAxis, 
  YAxis, 
  Tooltip, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  Radar, 
  LineChart, 
  Line 
} from 'recharts';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../lib/utils';
import { TelemetryEvent, ThreatLevel } from '../types';

interface DashboardViewProps {
  events: TelemetryEvent[];
  selectedEvent: TelemetryEvent | null;
  setSelectedEvent: (e: TelemetryEvent | null) => void;
  getThreatColor: (level: ThreatLevel) => string;
}

export default function DashboardView({ events, selectedEvent, setSelectedEvent, getThreatColor }: DashboardViewProps) {
  const [traceOpen, setTraceOpen] = useState(false);

  return (
    <div className="p-8 grid grid-cols-12 gap-6">
      {/* Top Row: Quick Stats */}
      <section className="col-span-12 grid grid-cols-4 gap-6">
        <StatCard label="Anomaly Threshold" value="92.4%" trend="+0.2" icon={<Zap className="w-4 h-4" />} chart={<MiniLine color="#6366f1" />} />
        <StatCard label="Containment Rate" value="100%" trend="Stable" icon={<Lock className="w-4 h-4" />} chart={<MiniLine color="#10b981" />} />
        <StatCard label="Network Entropy" value="0.45" trend="-0.03" icon={<Activity className="w-4 h-4" />} chart={<MiniLine color="#f59e0b" />} />
        <StatCard label="Active Models" value="12" trend="Optimized" icon={<Cpu className="w-4 h-4" />} chart={<MiniLine color="#ec4899" />} />
      </section>

      {/* Middle Row: Live Feed */}
      <section className="col-span-8 space-y-6">
        <div className="bg-[#0c0c0c] border border-white/5 rounded-2xl overflow-hidden shadow-2xl">
          <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              <h3 className="text-xs font-bold uppercase tracking-widest text-white">Live Telemetry Ingestion</h3>
            </div>
            <div className="flex items-center gap-3 text-[10px] text-slate-500 font-bold uppercase">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-500" /> Critical</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Verified</span>
            </div>
          </div>
          <div className="h-[400px] overflow-y-auto font-mono scrollbar-hide">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-[#0c0c0c] z-10 text-[10px] uppercase text-slate-500 font-bold tracking-widest border-b border-white/5">
                <tr>
                  <th className="px-6 py-3">Timestamp</th>
                  <th className="px-6 py-3">Entity</th>
                  <th className="px-6 py-3">Traffic Pair</th>
                  <th className="px-6 py-3">Score</th>
                  <th className="px-6 py-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence initial={false}>
                  {events.map((event) => (
                    <motion.tr 
                      key={event.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0 }}
                      onClick={() => setSelectedEvent(event)}
                      className={cn("group cursor-pointer hover:bg-white/5 transition-colors border-b border-white/5", selectedEvent?.id === event.id && "bg-indigo-500/10")}
                    >
                      <td className="px-6 py-3 text-[11px] text-slate-400">{event.timestamp}</td>
                      <td className="px-6 py-3">
                        <div className="flex items-center gap-2">
                          {event.entity.type === 'DEVICE' ? <Monitor className="w-3 h-3 text-slate-500" /> : <User className="w-3 h-3 text-slate-500" />}
                          <span className="text-xs text-white">{event.entity.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-3 text-[11px] text-slate-400 group-hover:text-indigo-300 transition-colors">
                        {event.source} <ArrowRight className="inline w-3 h-3 mx-1 opacity-40 text-slate-500" /> {event.destination}
                      </td>
                      <td className="px-6 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1 bg-white/5 rounded-full overflow-hidden">
                            <motion.div className={cn("h-full", event.score > 75 ? "bg-rose-500" : "bg-indigo-500")} initial={{ width: 0 }} animate={{ width: `${event.score}%` }} />
                          </div>
                          <span className={cn("text-[11px] font-bold", event.score > 75 ? "text-rose-500" : "text-white")}>{event.score.toFixed(1)}</span>
                        </div>
                      </td>
                      <td className="px-6 py-3 text-right">
                        <span className={cn("text-[9px] px-2 py-0.5 rounded-full border uppercase font-bold", getThreatColor(event.threatLevel))}>{event.threatLevel}</span>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="bg-[#0c0c0c] border border-white/5 rounded-2xl p-6">
            <h3 className="text-xs font-bold uppercase tracking-widest text-white mb-6 flex items-center gap-2"><Binary className="w-4 h-4 text-pink-400" /> Performance Analysis</h3>
            <div className="h-48"><ResponsiveContainer><AreaChart data={ROC_DATA}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#ffffff05" /><XAxis dataKey="fpr" tick={{fontSize: 10}} stroke="#ffffff20" /><YAxis tick={{fontSize: 10}} stroke="#ffffff20" /><Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid #ffffff10', fontSize: '10px' }} /><Area type="monotone" dataKey="tpr" stroke="#ec4899" fill="#ec4899" fillOpacity={0.1} /></AreaChart></ResponsiveContainer></div>
          </div>
          <div className="bg-[#0c0c0c] border border-white/5 rounded-2xl p-6">
            <h3 className="text-xs font-bold uppercase tracking-widest text-white mb-6 flex items-center gap-2"><Activity className="w-4 h-4 text-orange-400" /> Entropy Radar</h3>
            <div className="h-48"><ResponsiveContainer><RadarChart data={ENTROPY_DATA} cx="50%" cy="50%" outerRadius="80%"><PolarGrid stroke="#ffffff10" /><PolarAngleAxis dataKey="subject" tick={{fontSize: 8, fill: '#64748b'}} /><Radar name="A" dataKey="A" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} /><Radar name="B" dataKey="B" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} /></RadarChart></ResponsiveContainer></div>
          </div>
        </div>
      </section>

      {/* Right Column: Alert Detail */}
      <section className="col-span-4 space-y-6">
        <AnimatePresence mode="wait">
          {selectedEvent ? (
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className="bg-[#111] border border-white/10 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
               <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-3xl rounded-full -translate-y-1/2 translate-x-1/2" />
               <div className="flex justify-between items-start mb-6">
                 <div><h3 className="text-sm font-bold text-white mb-1">Incident Detail</h3><p className="text-[10px] text-slate-500 font-mono tracking-tight underline">ID: {selectedEvent.id}</p></div>
                 <button onClick={() => setSelectedEvent(null)} className="text-slate-500 hover:text-white"><MoreVertical className="w-4 h-4" /></button>
               </div>
               <div className="space-y-6">
                 <div className="flex gap-4">
                   <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center border", getThreatColor(selectedEvent.threatLevel))}><ShieldAlert className="w-6 h-6" /></div>
                   <div><div className="text-[10px] uppercase font-bold text-slate-500 mb-1">Risk Score</div><div className="text-4xl font-bold text-white tracking-tighter">{selectedEvent.score.toFixed(1)}</div></div>
                 </div>
                 <div className="p-4 bg-white/5 rounded-xl border border-white/5 space-y-3">
                   <div className="text-[10px] uppercase tracking-widest text-slate-400 font-bold border-b border-white/5 pb-2">Analysis Factors</div>
                   {selectedEvent.explanation?.map((e, i) => (<div key={i} className="flex items-center gap-2 text-[11px] text-slate-300"><div className="w-1 h-1 rounded-full bg-indigo-500" />{e}</div>))}
                 </div>
                 <div className="space-y-3">
                    <div className="text-[10px] uppercase tracking-widest text-slate-400 font-bold">Auto-Response Audit</div>
                    <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5">
                       <div className="flex items-center gap-3">
                         <div className="p-2 bg-emerald-500/10 rounded-lg"><ShieldCheck className="w-4 h-4 text-emerald-500" /></div>
                         <div><p className="text-[10px] text-emerald-500 font-bold uppercase">Pattern Enforcement</p><p className="text-[9px] text-slate-500">Active protection applied</p></div>
                       </div>
                       <span className="text-[9px] px-2 py-0.5 rounded bg-white/5 text-slate-400">ACTIVE</span>
                    </div>
                 </div>
                 <button onClick={() => setTraceOpen(!traceOpen)} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-xl text-xs font-bold transition-all shadow-lg shadow-indigo-600/20">
                  {traceOpen ? 'Hide Full Trace' : 'Analyze Full Trace'}
                 </button>
                 {traceOpen && (
                  <div className="p-4 bg-black/30 rounded-xl border border-indigo-500/10 font-mono text-[10px] text-slate-400 space-y-2">
                    <div className="flex justify-between"><span>Source</span><span className="text-white">{selectedEvent.source}</span></div>
                    <div className="flex justify-between"><span>Destination</span><span className="text-white">{selectedEvent.destination}</span></div>
                    <div className="flex justify-between"><span>Protocol</span><span className="text-white">{selectedEvent.protocol}</span></div>
                    <div className="flex justify-between"><span>Bytes</span><span className="text-white">{selectedEvent.bytes}</span></div>
                    <div className="flex justify-between"><span>Action</span><span className="text-white">{selectedEvent.autoAction?.type ?? 'MONITOR'}</span></div>
                  </div>
                 )}
               </div>
            </motion.div>
          ) : (
            <div className="bg-[#0c0c0c] border border-dashed border-white/10 rounded-2xl p-12 text-center flex flex-col items-center justify-center min-h-[300px]">
              <Activity className="w-8 h-8 text-slate-700 mb-4" /><p className="text-xs text-slate-500 uppercase tracking-widest font-bold">Awaiting Input</p>
            </div>
          )}
        </AnimatePresence>

        <div className="bg-[#0c0c0c] border border-white/5 rounded-2xl p-6 shadow-xl space-y-6">
          <h3 className="text-xs font-bold uppercase tracking-widest text-white flex items-center gap-2"><CPU className="w-4 h-4 text-indigo-400" /> System Health</h3>
          <div className="space-y-4">
            <SystemIndicator label="Ingestion Engine" status="HEALTHY" stats="12.4k EPS" />
            <SystemIndicator label="ML Pipeline" status="OPTIMIZED" stats="4.2ms Latency" />
          </div>
        </div>
      </section>
    </div>
  );
}

function StatCard({ label, value, trend, icon, chart }: { label: string, value: string, trend: string, icon: React.ReactNode, chart: React.ReactNode }) {
  return (
    <div className="bg-[#0c0c0c] border border-white/5 p-5 rounded-2xl relative shadow-lg hover:border-white/10 transition-colors group">
      <div className="flex justify-between items-start mb-4">
        <div className="p-2 bg-white/5 rounded-lg text-slate-400 group-hover:text-indigo-400 transition-colors">{icon}</div>
        <div className="text-[10px] font-bold text-emerald-500 font-mono italic">{trend}</div>
      </div>
      <div>
        <p className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mb-1">{label}</p>
        <p className="text-2xl font-bold text-white tracking-tighter">{value}</p>
      </div>
      <div className="absolute right-4 bottom-4 h-12 w-24">{chart}</div>
    </div>
  );
}

function MiniLine({ color }: { color: string }) {
  const data = Array.from({length: 10}, () => Math.random() * 10);
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data.map((v, i) => ({v, i}))}><Line type="monotone" dataKey="v" stroke={color} strokeWidth={2} dot={false} animate={true} /></LineChart>
    </ResponsiveContainer>
  );
}

function SystemIndicator({ label, status, stats }: { label: string, status: string, stats: string }) {
  return (
    <div className="flex items-center justify-between">
      <div className="space-y-1">
        <p className="text-[11px] font-bold text-white">{label}</p>
        <p className="text-[10px] text-slate-500 font-mono tracking-tighter">{stats}</p>
      </div>
      <div className="text-right">
        <div className="text-[10px] font-bold text-emerald-500 uppercase tracking-tighter border border-emerald-500/20 bg-emerald-500/5 px-2 py-0.5 rounded">{status}</div>
      </div>
    </div>
  );
}

const ROC_DATA = [{ fpr: 0, tpr: 0 }, { fpr: 0.1, tpr: 0.65 }, { fpr: 0.2, tpr: 0.85 }, { fpr: 0.3, tpr: 0.92 }, { fpr: 0.5, tpr: 0.95 }, { fpr: 0.7, tpr: 0.98 }, { fpr: 1.0, tpr: 1.0 }];

const ENTROPY_DATA = [
  { subject: 'SMB', A: 120, B: 110, fullMark: 150 },
  { subject: 'TCP', A: 98, B: 130, fullMark: 150 },
  { subject: 'DNS', A: 86, B: 130, fullMark: 150 },
  { subject: 'HTTP', A: 99, B: 100, fullMark: 150 },
  { subject: 'SSH', A: 85, B: 90, fullMark: 150 },
  { subject: 'VOL', A: 65, B: 85, fullMark: 150 },
];

const CPU = ({ className }: { className?: string }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
  >
    <rect width="16" height="16" x="4" y="4" rx="2" /><path d="M9 9h6v6H9z" /><path d="M15 2v2" /><path d="M15 20v2" /><path d="M2 15h2" /><path d="M2 9h2" /><path d="M20 15h2" /><path d="M20 9h2" /><path d="M9 2v2" /><path d="M9 20v2" />
  </svg>
);
