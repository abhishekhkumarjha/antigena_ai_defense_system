/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Activity, 
  Network, 
  Lock, 
  Search, 
  RefreshCcw, 
  User, 
  Monitor,
  Database,
  BarChart3
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from './lib/utils';
import { getApiStatus, scoreTelemetryEvent, type ApiStatus } from './api';
import { 
  ThreatLevel, 
  ActionType, 
  TelemetryEvent 
} from './types';

// View Components
import DashboardView from './components/DashboardView';
import NetworkView from './components/NetworkView';
import MonitorView from './components/MonitorView';
import LogsView from './components/LogsView';
import AnalyticsView from './components/AnalyticsView';

type View = 'dashboard' | 'network' | 'monitor' | 'logs' | 'analytics';

// Mock Data Generator
const generateMockEvent = (): TelemetryEvent => {
  const id = Math.random().toString(36).substr(2, 9);
  const protocols = ['TCP', 'UDP', 'HTTPS', 'SSH', 'SMB', 'DNS'];
  const sources = [
    '103.21.144.12', // Mumbai Data Center
    '103.1.1.45',    // Bangalore HQ
    '43.252.176.8',  // Delhi Branch
    '112.133.201.5'  // Chennai Node
  ];
  const users = ['ashok.v', 'priya.s', 'raj.k', 'admin_mumbai', 'system_blr'];
  const score = Math.random() * 100;
  
  let threatLevel = ThreatLevel.NORMAL;
  if (score > 90) threatLevel = ThreatLevel.CRITICAL;
  else if (score > 75) threatLevel = ThreatLevel.HIGH_RISK;
  else if (score > 50) threatLevel = ThreatLevel.SUSPICIOUS;

  return {
    id,
    timestamp: new Date().toLocaleTimeString(),
    source: sources[Math.floor(Math.random() * sources.length)],
    destination: `142.250.${Math.floor(Math.random()*255)}.${Math.floor(Math.random()*255)}`,
    protocol: protocols[Math.floor(Math.random() * protocols.length)],
    bytes: Math.floor(Math.random() * 10000),
    score,
    threatLevel,
    entity: {
      id: `ENT-${id}`,
      type: Math.random() > 0.5 ? 'DEVICE' : 'USER',
      name: users[Math.floor(Math.random() * users.length)]
    },
    explanation: score > 50 ? ["Unusual outbound volume", "Non-standard port usage"] : undefined,
    autoAction: score > 80 ? {
      type: ActionType.ENFORCE_POL,
      status: 'ACTIVE',
      timestamp: new Date().toLocaleTimeString()
    } : undefined
  };
};

export default function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<TelemetryEvent | null>(null);
  const [isLive, setIsLive] = useState(true);
  const [apiStatus, setApiStatus] = useState<ApiStatus>({ online: false, modelLoaded: false, label: 'Connecting' });
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (!isLive) return;
    const interval = setInterval(() => {
      const event = generateMockEvent();
      scoreTelemetryEvent(event)
        .then(scoredEvent => setEvents(prev => [scoredEvent, ...prev].slice(0, 50)))
        .catch(() => setEvents(prev => [event, ...prev].slice(0, 50)));
    }, 2000);
    return () => clearInterval(interval);
  }, [isLive]);

  useEffect(() => {
    setEvents(Array.from({ length: 15 }, generateMockEvent));
  }, []);

  useEffect(() => {
    let mounted = true;

    const refreshStatus = async () => {
      const status = await getApiStatus();
      if (mounted) setApiStatus(status);
    };

    refreshStatus();
    const interval = setInterval(refreshStatus, 10000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const getThreatColor = (level: ThreatLevel) => {
    switch (level) {
      case ThreatLevel.CRITICAL: return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
      case ThreatLevel.HIGH_RISK: return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
      case ThreatLevel.SUSPICIOUS: return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
      default: return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    }
  };

  const renderView = () => {
    const query = searchQuery.trim().toLowerCase();
    const visibleEvents = query
      ? events.filter((event) => `${event.source} ${event.destination} ${event.protocol} ${event.entity.name} ${event.threatLevel}`.toLowerCase().includes(query))
      : events;

    switch (currentView) {
      case 'dashboard': return <DashboardView events={visibleEvents} selectedEvent={selectedEvent} setSelectedEvent={setSelectedEvent} getThreatColor={getThreatColor} />;
      case 'network': return <NetworkView events={visibleEvents} />;
      case 'monitor': return <MonitorView />;
      case 'logs': return <LogsView />;
      case 'analytics': return <AnalyticsView />;
      default: return <DashboardView events={events} selectedEvent={selectedEvent} setSelectedEvent={setSelectedEvent} getThreatColor={getThreatColor} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-slate-300 font-sans selection:bg-indigo-500/30">
      <nav className="fixed left-0 top-0 h-full w-20 border-r border-white/5 flex flex-col items-center py-8 gap-10 bg-[#080808] z-50">
        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-[0_0_15px_rgba(79,70,229,0.5)]">
          <Shield className="text-white w-6 h-6" />
        </div>
        <div className="flex flex-col gap-6">
          <NavItem icon={<Activity className="w-5 h-5" />} active={currentView === 'dashboard'} onClick={() => setCurrentView('dashboard')} />
          <NavItem icon={<Network className="w-5 h-5" />} active={currentView === 'network'} onClick={() => setCurrentView('network')} />
          <NavItem icon={<Monitor className="w-5 h-5" />} active={currentView === 'monitor'} onClick={() => setCurrentView('monitor')} />
          <NavItem icon={<Database className="w-5 h-5" />} active={currentView === 'logs'} onClick={() => setCurrentView('logs')} />
          <NavItem icon={<BarChart3 className="w-5 h-5" />} active={currentView === 'analytics'} onClick={() => setCurrentView('analytics')} />
        </div>
        <div className="mt-auto">
          <NavItem icon={<Lock className="w-5 h-5" />} />
        </div>
      </nav>

      <main className="pl-20 min-h-screen">
        <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-[#080808]/80 backdrop-blur-md sticky top-0 z-40">
          <div className="flex items-center gap-4">
            <h1 className="text-sm font-semibold tracking-widest text-white uppercase italic">Antigena // India West-1 Defense</h1>
            <div className={cn(
              "flex items-center gap-2 px-3 py-1 rounded-full border",
              apiStatus.modelLoaded
                ? "bg-emerald-500/10 border-emerald-500/20"
                : apiStatus.online
                  ? "bg-amber-500/10 border-amber-500/20"
                  : "bg-slate-500/10 border-slate-500/20"
            )}>
              <div className={cn(
                "w-1.5 h-1.5 rounded-full animate-pulse",
                apiStatus.modelLoaded ? "bg-emerald-500" : apiStatus.online ? "bg-amber-500" : "bg-slate-500"
              )} />
              <span className={cn(
                "text-[10px] font-mono tracking-tighter uppercase font-bold",
                apiStatus.modelLoaded ? "text-emerald-500" : apiStatus.online ? "text-amber-500" : "text-slate-500"
              )}>{apiStatus.label}</span>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="relative group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-indigo-400 transition-colors" />
              <input
                type="text"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search Indian infrastructure..."
                className="bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-xs focus:outline-none focus:border-indigo-500/50 w-64 transition-all"
              />
            </div>
            <button onClick={() => setIsLive(!isLive)} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
              <RefreshCcw className={cn("w-4 h-4 text-slate-400", isLive && "animate-spin-slow")} />
            </button>
            <div className="w-8 h-8 rounded-full bg-indigo-900/40 border border-indigo-500/30 flex items-center justify-center">
              <User className="w-4 h-4 text-indigo-400" />
            </div>
          </div>
        </header>

        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {renderView()}
          </motion.div>
        </AnimatePresence>
      </main>

      <div className="fixed bottom-0 right-0 w-[500px] h-[500px] bg-indigo-600/5 blur-[120px] rounded-full -z-10" />
      <div className="fixed top-0 left-0 w-[300px] h-[300px] bg-emerald-600/5 blur-[120px] rounded-full -z-10" />
    </div>
  );
}

function NavItem({ icon, active = false, onClick }: { icon: React.ReactNode, active?: boolean, onClick?: () => void }) {
  return (
    <button 
      onClick={onClick}
      className={cn(
        "w-12 h-12 rounded-xl flex items-center justify-center transition-all",
        active 
          ? "bg-indigo-500/10 text-indigo-400 shadow-[inset_0_0_10px_rgba(99,102,241,0.2)] border border-indigo-500/20" 
          : "text-slate-500 hover:text-indigo-400"
      )}
    >
      {icon}
    </button>
  );
}
