import React, { useMemo, useState } from 'react';
import { 
  Monitor, 
  User, 
  Search, 
  Filter, 
  Cpu, 
  ShieldCheck,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import { cn } from '../lib/utils';

export default function MonitorView() {
  const [query, setQuery] = useState('');
  const [riskOnly, setRiskOnly] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const entities = [
    { id: 'MUM-772', name: 'Mumbai DC - dev_42', type: 'DEVICE', status: 'PROTECTED', risk: 12, lastSeen: 'Active Now' },
    { id: 'BLR-USR-881', name: 'rajesh.m (Admin)', type: 'USER', status: 'MONITORED', risk: 85, lastSeen: '2m ago', alert: true },
    { id: 'DEL-SRV-001', name: 'Delhi Core Database', type: 'DEVICE', status: 'PROTECTED', risk: 4, lastSeen: 'Active Now' },
    { id: 'BLR-LT-092', name: 'Bangalore VM - staging', type: 'DEVICE', status: 'ISOLATED', risk: 92, lastSeen: 'Blocked', alert: true },
    { id: 'CHN-USR-221', name: 'deepika.p', type: 'USER', status: 'PROTECTED', risk: 18, lastSeen: '15m ago' },
  ];
  const selectedEntityRecord = useMemo(
    () => entities.find((entity) => entity.id === selectedEntity) ?? null,
    [selectedEntity]
  );
  const visibleEntities = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return entities.filter((entity) => {
      const matchesQuery = !normalizedQuery || `${entity.id} ${entity.name} ${entity.type} ${entity.status}`.toLowerCase().includes(normalizedQuery);
      const matchesRisk = !riskOnly || entity.risk >= 75 || entity.alert;
      return matchesQuery && matchesRisk;
    });
  }, [query, riskOnly]);

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-3">
            <Monitor className="w-6 h-6 text-indigo-400" />
            Entity Profiling & Activity Monitoring
          </h2>
          <p className="text-xs text-slate-500 mt-1">Real-time behavior tracking for all recognized devices and identities.</p>
        </div>
        <div className="flex gap-3">
           <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input 
              type="text" 
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Filter entities..." 
              className="bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-xs focus:outline-none focus:border-indigo-500/50 w-64"
            />
          </div>
          <button onClick={() => setRiskOnly(!riskOnly)} className={cn("p-2 border rounded-xl transition-colors", riskOnly ? "bg-rose-500/10 border-rose-500/20" : "bg-white/5 border-white/10 hover:bg-white/10")}>
            <Filter className={cn("w-4 h-4", riskOnly ? "text-rose-500" : "text-slate-400")} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6">
        <EntityStat label={selectedEntityRecord ? "Investigating" : "Visible Entities"} value={selectedEntityRecord?.id ?? String(visibleEntities.length)} icon={<Cpu className="w-4 h-4" />} />
        <EntityStat label={selectedEntityRecord ? "Pattern Score" : "High Risk"} value={selectedEntityRecord ? `${selectedEntityRecord.risk}%` : String(visibleEntities.filter((entity) => entity.risk >= 75).length)} icon={<ShieldAlert className="w-4 h-4 text-amber-500" />} tone={selectedEntityRecord?.risk && selectedEntityRecord.risk >= 75 ? "danger" : "default"} />
        <EntityStat label={selectedEntityRecord ? "Last Telemetry" : "Active Sessions"} value={selectedEntityRecord?.lastSeen ?? "442"} icon={<User className="w-4 h-4 text-indigo-400" />} />
        <EntityStat label={selectedEntityRecord ? "Containment" : "Auto-Isolated"} value={selectedEntityRecord?.status ?? String(visibleEntities.filter((entity) => entity.status === 'ISOLATED').length)} icon={<ShieldAlert className="w-4 h-4 text-rose-500" />} tone={selectedEntityRecord?.status === 'ISOLATED' ? "danger" : "default"} />
      </div>

      <div className="bg-[#0c0c0c] border border-white/5 rounded-2xl overflow-hidden shadow-2xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-white/5 text-[10px] uppercase font-bold text-slate-500 tracking-widest bg-white/[0.02]">
              <th className="px-6 py-4">Entity Identity</th>
              <th className="px-6 py-4">Type</th>
              <th className="px-6 py-4">Current Status</th>
              <th className="px-6 py-4">Pattern Score</th>
              <th className="px-6 py-4">Last Telemetry</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {visibleEntities.map((entity) => (
              <tr key={entity.id} className={cn("hover:bg-white/5 transition-colors group", selectedEntity === entity.id && "bg-indigo-500/10")}>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-10 h-10 rounded-xl flex items-center justify-center border",
                      entity.alert ? "bg-rose-500/10 border-rose-500/20 text-rose-500" : "bg-indigo-500/10 border-indigo-500/20 text-indigo-400"
                    )}>
                      {entity.type === 'DEVICE' ? <Monitor className="w-5 h-5" /> : <User className="w-5 h-5" />}
                    </div>
                    <div>
                      <p className="text-xs font-bold text-white mb-0.5">{entity.name}</p>
                      <p className="text-[10px] text-slate-500 font-mono italic">UID: {entity.id}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                   <span className="text-[10px] font-bold text-slate-400 bg-white/5 px-2 py-0.5 rounded uppercase tracking-tighter">
                    {entity.type}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    {entity.status === 'PROTECTED' ? (
                      <ShieldCheck className="w-3 h-3 text-emerald-500" />
                    ) : (
                      <ShieldAlert className={cn("w-3 h-3 text-amber-500", entity.status === 'ISOLATED' && "text-rose-500")} />
                    )}
                    <span className={cn(
                      "text-[10px] font-bold uppercase",
                      entity.status === 'PROTECTED' ? "text-emerald-500" : (entity.status === 'ISOLATED' ? "text-rose-500" : "text-amber-500")
                    )}>
                      {entity.status}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div 
                        className={cn("h-full", entity.risk > 75 ? "bg-rose-500" : "bg-indigo-500")}
                        style={{ width: `${entity.risk}%` }}
                      />
                    </div>
                    <span className={cn("text-[11px] font-bold", entity.risk > 75 ? "text-rose-500" : "text-white")}>
                      {entity.risk}%
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                   <p className="text-[10px] text-slate-400">{entity.lastSeen}</p>
                </td>
                <td className="px-6 py-4 text-right">
                  <button onClick={() => setSelectedEntity(selectedEntity === entity.id ? null : entity.id)} className="p-2 hover:bg-white/10 rounded-lg text-slate-500 hover:text-white transition-all">
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selectedEntityRecord && (
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8 bg-[#0c0c0c] border border-indigo-500/10 rounded-2xl p-6 shadow-xl">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="text-sm font-bold text-white">{selectedEntityRecord.name}</h3>
                <p className="text-[10px] text-slate-500 font-mono mt-1">UID: {selectedEntityRecord.id}</p>
              </div>
              <span className={cn(
                "text-[10px] px-2 py-1 rounded border font-bold",
                selectedEntityRecord.status === 'ISOLATED'
                  ? "text-rose-500 border-rose-500/20 bg-rose-500/10"
                  : selectedEntityRecord.status === 'MONITORED'
                    ? "text-amber-500 border-amber-500/20 bg-amber-500/10"
                    : "text-emerald-500 border-emerald-500/20 bg-emerald-500/10"
              )}>
                {selectedEntityRecord.status}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <InvestigationMetric label="Type" value={selectedEntityRecord.type} />
              <InvestigationMetric label="Pattern Score" value={`${selectedEntityRecord.risk}%`} danger={selectedEntityRecord.risk >= 75} />
              <InvestigationMetric label="Last Telemetry" value={selectedEntityRecord.lastSeen} />
            </div>
            <div className="mt-6 p-4 bg-black/30 border border-white/5 rounded-xl text-[11px] text-slate-300">
              {selectedEntityRecord.status === 'ISOLATED'
                ? 'Containment is active. Outbound traffic is blocked and the entity is held for analyst review.'
                : selectedEntityRecord.status === 'MONITORED'
                  ? 'Enhanced monitoring is active. New telemetry from this identity will be scored at elevated priority.'
                  : 'Entity is within learned behavior baseline. No containment action is currently active.'}
            </div>
          </div>
          <div className="col-span-4 bg-indigo-500/5 border border-indigo-500/10 rounded-2xl p-6">
            <h3 className="text-xs font-bold uppercase tracking-widest text-indigo-300 mb-4">Pinned Values</h3>
            <div className="space-y-3 text-[10px] font-mono">
              <div className="flex justify-between"><span className="text-slate-500">Entity</span><span className="text-white">{selectedEntityRecord.id}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Score</span><span className={selectedEntityRecord.risk >= 75 ? "text-rose-500" : "text-emerald-500"}>{selectedEntityRecord.risk}%</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Telemetry</span><span className="text-white">{selectedEntityRecord.lastSeen}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Containment</span><span className="text-white">{selectedEntityRecord.status}</span></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function EntityStat({ label, value, icon, tone = "default" }: { label: string, value: string, icon: React.ReactNode, tone?: "default" | "danger" }) {
  return (
    <div className="bg-[#0c0c0c] border border-white/5 p-5 rounded-2xl shadow-lg">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 bg-white/5 rounded-lg text-slate-400">
          {icon}
        </div>
        <p className="text-[10px] uppercase font-bold text-slate-500 tracking-widest">{label}</p>
      </div>
      <p className={cn("text-2xl font-bold tracking-tighter truncate", tone === "danger" ? "text-rose-500" : "text-white")}>{value}</p>
    </div>
  );
}

function InvestigationMetric({ label, value, danger = false }: { label: string, value: string, danger?: boolean }) {
  return (
    <div className="p-4 bg-white/5 rounded-xl border border-white/5">
      <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-2">{label}</p>
      <p className={cn("text-sm font-bold", danger ? "text-rose-500" : "text-white")}>{value}</p>
    </div>
  );
}
