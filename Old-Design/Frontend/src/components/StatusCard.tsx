import { Activity, ShieldAlert } from 'lucide-react';
import { MOCK_COUNTRIES, type CountryData } from '../services/mockData';

interface StatusCardProps {
  hostCountryData: CountryData;
}

export const StatusCard = ({ hostCountryData }: StatusCardProps) => {
    // Find top infected neighbors
    // In mock data, neighbors are strings. We need to look them up.
    // Assuming we pass the full list or look it up.
    // For now, I'll filter MOCK_COUNTRIES based on hostCountryData.neighbors
    
    // Actually, getting full list here might be better, or passing it in.
    // I'll import MOCK_COUNTRIES directly for simplicity.
    
    const relevantNeighbors = MOCK_COUNTRIES.filter(c => 
        hostCountryData.neighbors.includes(c.id)
    ).sort((a, b) => b.severity - a.severity).slice(0, 3);

  return (
    <div className="space-y-4">
      <div className="bg-surface border border-secondary p-4 rounded-sm relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-2 opacity-50"><Activity className="w-12 h-12 text-accent" /></div>
        <h3 className="text-sm font-bold text-text-dim uppercase tracking-wider mb-1">Active Infections ({hostCountryData.name})</h3>
        <p className="text-4xl font-mono text-accent font-bold drop-shadow-[0_0_10px_rgba(239,68,68,0.5)]">
            {hostCountryData.infected.toLocaleString()}
        </p>
        <div className="mt-2 flex items-center gap-2">
            <div className="h-1.5 flex-1 bg-primary rounded-full overflow-hidden">
                <div className="h-full bg-accent w-[15%] animate-pulse"></div>
            </div>
            <span className="text-xs text-accent font-mono">+12%</span>
        </div>
      </div>

      <div className="bg-surface border border-secondary p-4 rounded-sm">
        <div className="flex items-center gap-2 mb-3 border-b border-secondary pb-2">
            <ShieldAlert className="w-4 h-4 text-yellow-500" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">High Risk Neighbors</h3>
        </div>
        
        <div className="space-y-3">
            {relevantNeighbors.map(neighbor => (
                <div key={neighbor.id} className="flex items-center justify-between group cursor-pointer hover:bg-white/5 p-1 rounded transition">
                    <div>
                        <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${neighbor.severity > 70 ? 'bg-red-600 animate-pulse' : 'bg-yellow-500'}`}></span>
                            <span className="text-sm font-mono text-white">{neighbor.name}</span>
                        </div>
                        <span className="text-[10px] text-text-dim pl-4">Severity: {neighbor.severity}/100</span>
                    </div>
                    <div className="text-right">
                        <span className="text-xs font-mono text-accent font-bold">{neighbor.infected.toLocaleString()}</span>
                    </div>
                </div>
            ))}
        </div>
      </div>
    </div>
  );
};
