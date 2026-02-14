import { X, Users, Thermometer, Truck, Plane, Ship } from 'lucide-react';
import type { CountryData } from '../services/mockData';

interface CountryDetailProps {
  country: CountryData | null;
  onClose: () => void;
}

export const CountryDetail = ({ country, onClose }: CountryDetailProps) => {
  if (!country) return null;

  return (
    <div className="bg-surface border-2 border-accent/50 p-4 rounded-sm animate-in fade-in slide-in-from-left-4 duration-300 shadow-[0_0_20px_rgba(239,68,68,0.2)] relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
        <Users className="w-24 h-24" />
      </div>

      <div className="flex items-center justify-between mb-4 border-b border-secondary/50 pb-2 relative z-10">
        <h2 className="text-lg font-bold text-white uppercase tracking-wider">{country.name}</h2>
        <button onClick={onClose} className="text-text-dim hover:text-white">
            <X className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-background/50 p-2 rounded border border-secondary">
            <div className="flex items-center gap-2 text-text-dim text-xs mb-1">
                <Users className="w-3 h-3" />
                <span>Infected</span>
            </div>
            <span className="text-lg font-mono text-accent font-bold">{country.infected.toLocaleString()}</span>
        </div>
        <div className="bg-background/50 p-2 rounded border border-secondary">
             <div className="flex items-center gap-2 text-text-dim text-xs mb-1">
                <Thermometer className="w-3 h-3" />
                <span>Severity</span>
            </div>
            <div className="flex items-center gap-2">
                <span className={`text-lg font-mono font-bold ${country.severity > 50 ? 'text-accent' : 'text-yellow-500'}`}>
                    {country.severity}
                </span>
                <span className="text-[10px] text-text-dim">/100</span>
            </div>
        </div>
      </div>

       <div className="bg-background/50 p-2 rounded border border-secondary mb-4">
            <h4 className="text-xs font-bold text-text-dim uppercase mb-2">Incoming Traffic</h4>
            <div className="grid grid-cols-3 gap-2">
                <div className="flex flex-col items-center p-2 bg-surface rounded border border-secondary/50">
                    <Plane className="w-4 h-4 text-blue-400 mb-1" />
                    <span className="text-xs text-text-dim">Flights</span>
                    <span className="text-sm font-mono font-bold text-white">{country.trafficBreakdown?.flights?.toLocaleString() || 0}</span>
                </div>
                <div className="flex flex-col items-center p-2 bg-surface rounded border border-secondary/50">
                    <Truck className="w-4 h-4 text-green-400 mb-1" />
                    <span className="text-xs text-text-dim">My</span>
                    <span className="text-sm font-mono font-bold text-white">{country.trafficBreakdown?.trucks?.toLocaleString() || 0}</span>
                </div>
                <div className="flex flex-col items-center p-2 bg-surface rounded border border-secondary/50">
                    <Ship className="w-4 h-4 text-cyan-400 mb-1" />
                    <span className="text-xs text-text-dim">Sea</span>
                    <span className="text-sm font-mono font-bold text-white">{country.trafficBreakdown?.sea?.toLocaleString() || 0}</span>
                </div>
            </div>
            
            <div className="flex items-center gap-2 text-text-dim text-[10px] mt-2 justify-end">
                 <span>Total:</span>
                 <span className="font-mono text-white">{country.traffic.toLocaleString()}</span>
            </div>
        </div>

      <div>
        <h4 className="text-xs font-bold text-text-dim uppercase mb-2">Bordering Neighbors</h4>
        <div className="flex flex-wrap gap-1">
            {country.neighbors.map(n => (
                <span key={n} className="text-[10px] bg-primary px-2 py-1 rounded border border-secondary text-text-dim hover:text-white cursor-help">
                    {n}
                </span>
            ))}
        </div>
      </div>
    </div>
  );
};
