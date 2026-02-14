import { useState } from 'react';
import { Layout } from './components/Layout';
import  WorldMap  from './components/WorldMap';
import { StatusCard } from './components/StatusCard';
import { AgentSuggestions } from './components/AgentSuggestions';
import { CountryDetail } from './components/CountryDetail';
import { MOCK_COUNTRIES, AGENT_SUGGESTIONS } from './services/mockData';
import type { CountryData } from './services/mockData';

function App() {
  const [selectedCountry, setSelectedCountry] = useState<CountryData | null>(
    MOCK_COUNTRIES.find(c => c.id === 'ARE') || null
  );

  const handleCountrySelect = (data: any) => {
      // The data passed from WorldMap includes the transient "Safe" data properties
      // so we can just use it directly.
      const countryData: CountryData = {
          id: data.id,
          name: data.name,
          infected: data.infected || 0,
          severity: data.severity || 0,
          neighbors: data.neighbors || [],
          traffic: data.traffic || 0,
          trafficBreakdown: data.trafficBreakdown || { flights: 0, trucks: 0, sea: 0 },
          coordinates: data.coordinates || [0,0]
      };
      
      setSelectedCountry(countryData);
  };

  // Assuming 'ARE' (UAE) is the host
  const hostCountry = MOCK_COUNTRIES.find(c => c.id === 'ARE') || MOCK_COUNTRIES[0];

  return (
    <Layout
      sidebar={
        <div className="space-y-6 pb-20"> {/* Added padding bottom for scrolling */}
          <StatusCard hostCountryData={hostCountry} />

          <AgentSuggestions suggestions={AGENT_SUGGESTIONS} />
        </div>
      }
      content={
        <div className="relative w-full h-full">
            <WorldMap 
                onSelectCountry={handleCountrySelect} 
                selectedCountryId={selectedCountry?.id || null} 
            />
            
            {/* Overlay Detail Card */}
            {selectedCountry && (
                <div className="absolute bottom-6 left-6 right-6 md:left-auto md:right-6 md:w-96 z-20">
                    <CountryDetail 
                        country={selectedCountry} 
                        onClose={() => setSelectedCountry(null)} 
                    />
                </div>
            )}
        </div>
      }
    />
  );
}

export default App;
