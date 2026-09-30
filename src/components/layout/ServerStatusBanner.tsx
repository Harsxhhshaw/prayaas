import React, { useState } from 'react';
import { ShieldAlert, RefreshCw, X, CheckCircle2 } from 'lucide-react';
import { useAppStore } from '../../state/AppContext';
import { api } from '../../lib/api';

export const ServerStatusBanner: React.FC = () => {
  const { isLive } = useAppStore();
  const [dismissed, setDismissed] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [pingSuccess, setPingSuccess] = useState<boolean | null>(null);

  if (isLive || dismissed) {
    return null;
  }

  const handleRetry = async () => {
    setRetrying(true);
    try {
      const res = await api.getHealth();
      if (res.isLive && res.data.status === 'ok') {
        setPingSuccess(true);
        setTimeout(() => window.location.reload(), 800);
      } else {
        setPingSuccess(false);
      }
    } catch {
      setPingSuccess(false);
    } finally {
      setRetrying(false);
    }
  };

  return (
    <div className="bg-amber-950/80 border-b border-amber-500/30 px-3 py-1 flex items-center justify-between text-xs font-mono text-amber-200 z-20 shrink-0">
      <div className="flex items-center gap-2">
        <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span>
          <strong className="text-amber-300">DEMO FREEZE MODE:</strong> Running on frozen deterministic snapshot (Raini HAB-002) & benchmark layers. Live optimization/mutations require active backend.
        </span>
      </div>

      <div className="flex items-center gap-2">
        {pingSuccess === false && (
          <span className="text-[10px] text-rose-400">Backend still cold-starting...</span>
        )}
        {pingSuccess === true && (
          <span className="text-[10px] text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Connected!
          </span>
        )}
        <button
          onClick={handleRetry}
          disabled={retrying}
          className="px-2 py-0.5 bg-amber-900/60 hover:bg-amber-800/80 border border-amber-600/40 rounded text-[10px] text-amber-100 flex items-center gap-1 transition-colors"
          title="Retry connecting to backend API"
        >
          <RefreshCw className={`w-2.5 h-2.5 ${retrying ? 'animate-spin' : ''}`} />
          <span>{retrying ? 'Checking...' : 'Check Server'}</span>
        </button>
        <button
          onClick={() => setDismissed(true)}
          className="p-0.5 text-amber-400 hover:text-amber-200 transition-colors"
          title="Dismiss notice"
        >
          <X className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
};
