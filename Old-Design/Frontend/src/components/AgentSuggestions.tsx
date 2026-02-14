import { AlertOctagon, Plane, ShoppingBag, Shield, Activity } from 'lucide-react';
import type { AgentSuggestion } from '../services/mockData';

interface AgentSuggestionsProps {
  suggestions: AgentSuggestion[];
}

export const AgentSuggestions = ({ suggestions }: AgentSuggestionsProps) => {
  const getIcon = (type: string) => {
    switch (type) {
      case 'FLIGHT': return <Plane className="w-4 h-4" />;
      case 'TRADE': return <ShoppingBag className="w-4 h-4" />;
      case 'BORDER': return <Shield className="w-4 h-4" />;
      case 'MEDICAL': return <Activity className="w-4 h-4" />;
      default: return <AlertOctagon className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between border-b border-secondary pb-2 mb-4">
        <h3 className="text-sm font-bold text-text-dim uppercase tracking-wider">Agent Intelligence</h3>
        <span className="text-[10px] bg-primary px-2 py-0.5 rounded text-accent animate-pulse">AI ACTIVE</span>
      </div>

      <div className="space-y-3">
        {suggestions.map((suggestion) => (
          <div key={suggestion.id} className="bg-surface border border-secondary p-3 rounded-sm relative overflow-hidden transition hover:border-accent/50 group">
            {/* Severity Indicator */}
            <div className={`absolute left-0 top-0 bottom-0 w-1 ${suggestion.severity === 'HIGH' ? 'bg-accent' : 'bg-yellow-500'}`}></div>
            
            <div className="pl-3">
                <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2 text-xs font-mono text-white">
                        {getIcon(suggestion.type)}
                        <span className="font-bold">{suggestion.type} PROTOCOL</span>
                    </div>
                     <span className="text-[10px] text-text-dim border border-secondary px-1 rounded">{suggestion.targetCountry}</span>
                </div>
                
                <p className="text-xs text-text-dim mb-3">
                    {suggestion.description}
                </p>

                {/* Action Button (Action Card logic embedded) */}
                <button 
                  className="w-full bg-primary hover:bg-accent hover:text-white text-text text-xs font-mono py-2 rounded border border-secondary transition-all flex items-center justify-center gap-2 group-hover:shadow-[0_0_10px_rgba(239,68,68,0.3)]"
                  onClick={() => alert(`Initiating protocol: ${suggestion.actionLabel} for ${suggestion.targetCountry}`)}
                >
                    <span>[{suggestion.actionLabel}]</span>
                    <span className="w-1.5 h-1.5 bg-current rounded-full animate-pulse"></span>
                </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
