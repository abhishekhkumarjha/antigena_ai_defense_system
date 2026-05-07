import React, { useState } from 'react';
import { 
  Network, 
  Map as MapIcon, 
  Globe, 
  ArrowRight,
  Server,
  Cloud
} from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../lib/utils';
import { TelemetryEvent } from '../types';
import { downloadCsv } from '../api';

interface NetworkViewProps {
  events: TelemetryEvent[];
}

export default function NetworkView({ events }: NetworkViewProps) {
  const [mapMode, setMapMode] = useState<'topology' | 'table'>('topology');

  const exportFlows = () => {
    downloadCsv('antigena-flows.csv', events.map((event) => ({
      timestamp: event.timestamp,
      source: event.source,
      destination: event.destination,
      protocol: event.protocol,
      bytes: event.bytes,
      score: event.score,
      level: event.threatLevel,
    })));
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white flex items-center gap-3">
          <Network className="w-6 h-6 text-indigo-400" />
          Network Topology & Flow Analysis
        </h2>
        <div className="flex gap-2">
          <button onClick={() => setMapMode(mapMode === 'topology' ? 'table' : 'topology')} className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-xs font-bold hover:bg-white/10 transition-colors">
            {mapMode === 'topology' ? 'Show Flow Table' : 'Show Topology'}
          </button>
          <button onClick={exportFlows} className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/20">
            Export Flows
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-8 bg-[#0c0c0c] border border-white/5 rounded-2xl p-6 min-h-[500px] relative overflow-hidden">
          <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:20px_20px]" />
          
          <div className="relative z-10 h-full flex flex-col">
            <div className="flex justify-between mb-8">
              <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-lg p-3 inline-flex items-center gap-2">
                <Globe className="w-4 h-4 text-indigo-400" />
                <span className="text-[10px] uppercase font-bold tracking-widest text-indigo-300">Global Origin Analysis</span>
              </div>
            </div>

            {mapMode === 'topology' ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="relative">
                <div className="w-24 h-24 bg-indigo-600/20 border border-indigo-500/30 rounded-full flex items-center justify-center animate-pulse">
                  <Server className="w-8 h-8 text-indigo-400" />
                </div>
                {/* Simulated connection lines */}
                {Array.from({length: 6}).map((_, i) => (
                  <motion.div 
                    key={i}
                    className="absolute top-1/2 left-1/2 h-px bg-gradient-to-r from-indigo-500 to-transparent origin-left"
                    initial={{ width: 0, rotate: i * 60 }}
                    animate={{ width: 200 }}
                    transition={{ duration: 1, delay: i * 0.1 }}
                  >
                    <motion.div 
                      className="absolute right-0 w-2 h-2 bg-indigo-400 rounded-full blur-[2px]"
                      animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                  </motion.div>
                ))}
              </div>
            </div>
            ) : (
            <div className="flex-1 overflow-y-auto border border-white/5 rounded-xl bg-black/20">
              <table className="w-full text-left font-mono text-[10px]">
                <thead className="text-slate-500 uppercase border-b border-white/5">
                  <tr>
                    <th className="p-3">Source</th>
                    <th className="p-3">Destination</th>
                    <th className="p-3">Proto</th>
                    <th className="p-3">Bytes</th>
                    <th className="p-3">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {events.slice(0, 12).map((event) => (
                    <tr key={event.id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="p-3 text-white">{event.source}</td>
                      <td className="p-3 text-slate-400">{event.destination}</td>
                      <td className="p-3 text-indigo-300">{event.protocol}</td>
                      <td className="p-3 text-slate-400">{event.bytes}</td>
                      <td className={cn("p-3 font-bold", event.score > 75 ? "text-rose-500" : "text-emerald-500")}>{event.score.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            )}

            <div className="mt-auto grid grid-cols-3 gap-4">
               <FlowStat label="Total Inbound" value="4.2 GB" />
               <FlowStat label="Peak Throughput" value="850 Mbps" />
               <FlowStat label="Active Streams" value="1,240" />
            </div>
          </div>
        </div>

        <div className="col-span-4 space-y-6">
          <div className="bg-[#0c0c0c] border border-white/5 rounded-2xl p-6">
            <h3 className="text-xs font-bold uppercase tracking-widest text-white mb-6">Top Regional Destinations (Asia)</h3>
            <div className="space-y-4">
              <DestinationRow ip="13.233.124.12" country="IND" traffic="4.2 GB" score={12} />
              <DestinationRow ip="18.139.22.45" country="SGP" traffic="2.1 GB" score={8} />
              <DestinationRow ip="52.193.18.2" country="JPN" traffic="850 MB" score={45} />
              <DestinationRow ip="43.252.176.8" country="IND" traffic="600 MB" score={22} />
              <DestinationRow ip="20.42.161.124" country="CHN" traffic="320 MB" score={78} risk />
            </div>
          </div>

          <div className="bg-indigo-600/5 border border-indigo-500/10 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-indigo-500/10 rounded-lg">
                <Cloud className="w-4 h-4 text-indigo-400" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-widest text-indigo-300">Cloud Sync Status</h3>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Real-time synchronization with AWS CloudTrail and Azure Sentinel is currently operational. 
              VPC Flow logs are being ingested with 42ms median latency.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function FlowStat({ label, value }: { label: string, value: string }) {
  return (
    <div className="p-4 bg-white/5 rounded-xl border border-white/5">
      <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter mb-1">{label}</p>
      <p className="text-lg font-bold text-white tracking-tighter">{value}</p>
    </div>
  );
}

function DestinationRow({ ip, country, traffic, score, risk = false }: { ip: string, country: string, traffic: string, score: number, risk?: boolean }) {
  return (
    <div className="flex items-center justify-between group cursor-pointer">
      <div className="flex items-center gap-3">
        <div className="text-[10px] font-mono text-slate-500 bg-white/5 px-1.5 py-0.5 rounded uppercase">{country}</div>
        <div>
          <p className="text-[11px] font-mono text-white group-hover:text-indigo-400 transition-colors">{ip}</p>
          <p className="text-[9px] text-slate-600">{traffic} total volume</p>
        </div>
      </div>
      <div className={cn(
        "text-[10px] font-bold px-2 py-0.5 rounded",
        risk ? "text-rose-500 bg-rose-500/10" : "text-emerald-500 bg-emerald-500/10"
      )}>
        {score}
      </div>
    </div>
  );
}
