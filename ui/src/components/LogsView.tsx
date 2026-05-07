import React, { useEffect, useMemo, useState } from 'react';
import { 
  Database, 
  Search, 
  Download, 
  Trash2, 
  Clock, 
  Info,
  Terminal,
  FileCode
} from 'lucide-react';
import { cn } from '../lib/utils';
import { downloadCsv, getRecentAuditEvents } from '../api';

interface LogRow {
  id: number;
  type: string;
  level: string;
  message: string;
  time: string;
}

export default function LogsView() {
  const [query, setQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('All Events');
  const [logs, setLogs] = useState<LogRow[]>([
    { id: 1, type: 'MODEL', level: 'INFO', message: 'Isolation Forest threshold recalibrated to 0.94', time: '19:14:02' },
    { id: 2, type: 'AUTH', level: 'SUCCESS', message: 'User admin_svc authenticated from 192.168.1.10', time: '19:12:45' },
    { id: 3, type: 'NETWORK', level: 'WARN', message: 'Unusual outbound DNS volume detected for ENT-99sjak', time: '19:10:12' },
    { id: 4, type: 'SYSTEM', level: 'INFO', message: 'Database maintenance completed: 4.2M records indices updated', time: '19:05:00' },
    { id: 5, type: 'CONTAINMENT', level: 'ACTION', message: 'Auto-isolation triggered for ENT-l73ks (Risk: 94%)', time: '18:58:32' },
    { id: 6, type: 'MODEL', level: 'DRIFT', message: 'Concept drift detected in SMTP traffic pattern', time: '18:45:10' },
  ]);
  const [selectedLog, setSelectedLog] = useState<number | null>(null);

  useEffect(() => {
    let mounted = true;

    const refreshLogs = async () => {
      try {
        const events = await getRecentAuditEvents(100);
        if (!mounted || !events.length) return;
        setLogs(events.map((event, index) => ({
          id: index + 1,
          type: event.label === 'anomaly' ? 'CONTAINMENT' : 'MODEL',
          level: event.label === 'anomaly' ? 'ACTION' : 'INFO',
          message: `${event.label.toUpperCase()} score ${(event.anomaly_score * 100).toFixed(1)}% from ${event.source ?? 'unknown'} (${event.explanation?.top_features?.[0]?.feature ?? 'feature baseline'})`,
          time: new Date(event.timestamp).toLocaleTimeString(),
        })).reverse());
      } catch {
        // Keep bundled sample logs when the API is offline.
      }
    };

    refreshLogs();
    const interval = window.setInterval(refreshLogs, 8000);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  const filteredLogs = useMemo(() => {
    const filterMap: Record<string, string | null> = {
      'All Events': null,
      'Model Logs': 'MODEL',
      'Auth Events': 'AUTH',
      Containment: 'CONTAINMENT',
      'System State': 'SYSTEM',
    };
    const typeFilter = filterMap[activeFilter];
    const normalizedQuery = query.trim().toLowerCase();

    return logs.filter((log) => {
      const matchesType = !typeFilter || log.type === typeFilter;
      const matchesQuery = !normalizedQuery || `${log.type} ${log.level} ${log.message} ${log.time}`.toLowerCase().includes(normalizedQuery);
      return matchesType && matchesQuery;
    });
  }, [activeFilter, logs, query]);

  const exportLogs = () => {
    downloadCsv('antigena-logs.csv', filteredLogs);
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-3">
            <Database className="w-6 h-6 text-indigo-400" />
            Audit Ledger & Historical Logs
          </h2>
          <p className="text-xs text-slate-500 mt-1">Immutable record of all model decisions, system events, and active responses.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={exportLogs} className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-xs font-bold hover:bg-white/10 transition-colors">
            <Download className="w-4 h-4" />
            Export CSV
          </button>
          <button onClick={() => setLogs([])} className="p-2 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-500 hover:bg-rose-500/20 transition-all">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-3 space-y-6">
          <div className="bg-[#0c0c0c] border border-white/5 rounded-2xl p-6 shadow-xl">
             <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-6 flex items-center gap-2">
              <Terminal className="w-3 h-3" />
              Quick Filters
            </h3>
            <div className="space-y-2">
              {['All Events', 'Model Logs', 'Auth Events', 'Containment', 'System State'].map((label) => (
                <FilterItem
                  key={label}
                  label={label}
                  count={label === 'All Events' ? logs.length : logs.filter((log) => filterMatches(label, log.type)).length}
                  active={activeFilter === label}
                  onClick={() => setActiveFilter(label)}
                />
              ))}
            </div>
          </div>

          <div className="bg-[#0c0c0c] border border-white/5 rounded-2xl p-6 shadow-xl">
             <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-6 flex items-center gap-2">
              <Clock className="w-3 h-3" />
              Retention Policy
            </h3>
            <div className="p-4 bg-indigo-500/5 border border-indigo-500/10 rounded-xl text-[10px] text-indigo-300 leading-relaxed font-mono italic">
              Active: 180 Days<br/>
              Archive: 7 Years<br/>
              Status: COMPLIANT (CERT-In)
            </div>
          </div>
        </div>

        <div className="col-span-9 bg-[#0c0c0c] border border-white/5 rounded-2xl overflow-hidden shadow-2xl flex flex-col">
          <div className="px-6 py-4 border-b border-white/5 flex items-center gap-4 bg-white/[0.01]">
            <Search className="w-4 h-4 text-slate-500" />
            <input 
              type="text" 
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Query logs (regex supported)..." 
              className="bg-transparent border-none focus:outline-none text-xs text-white flex-1"
            />
            <FileCode onClick={exportLogs} className="w-4 h-4 text-indigo-400 opacity-50 cursor-pointer hover:opacity-100" />
          </div>
          <div className="flex-1 overflow-y-auto font-mono text-[11px] p-2 bg-black/40">
             {filteredLogs.map((log) => (
                <div key={log.id} className={cn("flex gap-4 p-2 hover:bg-white/5 rounded transition-colors group", selectedLog === log.id && "bg-indigo-500/10")}>
                  <span className="text-slate-600 w-16">{log.time}</span>
                  <span className={cn(
                    "font-bold w-20",
                    log.level === 'WARN' ? "text-amber-500" : (log.level === 'ACTION' ? "text-rose-500" : "text-indigo-400")
                  )}>
                    [{log.type}]
                  </span>
                  <span className="text-slate-300 flex-1">{log.message}</span>
                  <Info onClick={() => setSelectedLog(selectedLog === log.id ? null : log.id)} className="w-3 h-3 text-slate-700 group-hover:text-slate-400 cursor-pointer opacity-0 group-hover:opacity-100" />
                </div>
             ))}
             {selectedLog && (
              <div className="m-2 p-3 bg-indigo-500/5 border border-indigo-500/10 rounded text-indigo-200">
                Selected event #{selectedLog} is pinned for investigation.
              </div>
             )}
             <div className="p-2 text-slate-700 italic border-t border-white/5 mt-4">
              -- {filteredLogs.length ? 'END OF TRACE' : 'NO MATCHING EVENTS'} --
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function filterMatches(label: string, type: string) {
  return (
    (label === 'Model Logs' && type === 'MODEL') ||
    (label === 'Auth Events' && type === 'AUTH') ||
    (label === 'Containment' && type === 'CONTAINMENT') ||
    (label === 'System State' && type === 'SYSTEM')
  );
}

function FilterItem({ label, count, active = false, onClick }: { label: string, count: number, active?: boolean, onClick: () => void }) {
  return (
    <button onClick={onClick} className={cn(
      "flex items-center justify-between p-2 rounded-lg cursor-pointer transition-all",
      "w-full",
      active ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20" : "text-slate-500 hover:text-slate-300 hover:bg-white/5"
    )}>
      <span className="text-[11px] font-bold">{label}</span>
      <span className="text-[10px] font-mono opacity-50">{count}</span>
    </button>
  );
}
