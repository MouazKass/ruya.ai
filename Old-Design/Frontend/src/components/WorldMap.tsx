import { memo, useState } from 'react';
import { ComposableMap, Geographies, Geography, ZoomableGroup, Line } from 'react-simple-maps';
import { Plus, Minus, Crosshair } from 'lucide-react';
import { MOCK_COUNTRIES, getSeverityColor } from '../services/mockData';

// Map Topology URL
const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

interface WorldMapProps {
  onSelectCountry: (geo: any) => void;
  selectedCountryId: string | null;
}

const UAE_COORDS: [number, number] = [53.8478, 23.4241];
// Major hubs for random traffic simulation
const HUB_COORDS: { [key: string]: [number, number] } = {
    'USA': [-95.7129, 37.0902],
    'GBR': [-3.4360, 55.3781],
    'DEU': [10.4515, 51.1657],
    'CHN': [104.1954, 35.8617],
    'JPN': [138.2529, 36.2048]
};

const WorldMap = ({ onSelectCountry, selectedCountryId }: WorldMapProps) => {
  // Initial zoom focused on Middle East
  const [position, setPosition] = useState({ coordinates: [50, 25], zoom: 4 });

  const handleZoomIn = () => {
    if (position.zoom >= 8) return;
    setPosition((pos) => ({ ...pos, zoom: pos.zoom * 1.5 }));
  };

  const handleZoomOut = () => {
    if (position.zoom <= 1) return;
    setPosition((pos) => ({ ...pos, zoom: pos.zoom / 1.5 }));
  };

  const handleHomeParams = () => {
    setPosition({ coordinates: [53.8478, 23.4241], zoom: 4 }); // UAE coords
    // Optionally select UAE too if desired, but zoom is the main thing here.
    // Let's find UAE geo and select it? We need the geo object. 
    // For now, just reset view. User can click UAE or we can force select if we had the ID.
    // Actually user said "UAE should always be selectable". 
  };

  const handleMoveEnd = (position: { coordinates: [number, number]; zoom: number }) => {
    setPosition(position);
  };

  // Helper to find country data by any means necessary
  const findCountryData = (geo: any) => {
    const isoCode = geo.properties.ISO_A3 || geo.id;
    const name = geo.properties.name;
    
    return MOCK_COUNTRIES.find(c => 
        c.id === isoCode || 
        c.name === name || 
        (c.name === "United States" && name === "United States of America") // Common mismatch
    ); 
  };

  const getCountryColor = (geo: any) => {
    const countryData = findCountryData(geo);
    const isSelected = countryData && selectedCountryId === countryData.id;
    
    if (isSelected) {
        return '#e2e8f0'; // White/Silver for selected (Target Acquired)
    }
    
    if (countryData) {
      return getSeverityColor(countryData.severity);
    }
    return '#1e293b'; // Default surface color for non-infected
  };

  return (
    <div className="w-full h-full bg-background relative overflow-hidden group">
      {/* Ocean Grid Background */}
      <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none"></div>
      
      {/* Radar Sweep Animation */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center overflow-hidden">
        <div className="w-[200%] h-[200%] bg-[conic-gradient(from_0deg,transparent_0deg,transparent_300deg,rgba(255,255,255,0.05)_360deg)] animate-radar-spin opacity-30 rounded-full"></div>
      </div>

      {/* Zoom Controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
        <button 
            onClick={handleHomeParams}
            className="p-2 bg-surface/80 backdrop-blur border border-slate-400/50 rounded text-slate-200 hover:bg-white/10 transition shadow-[0_0_10px_rgba(255,255,255,0.2)]"
            title="Reset to Target (UAE)"
        >
            <Crosshair className="w-4 h-4" />
        </button>
        <button 
            onClick={handleZoomIn}
            className="p-2 bg-surface/80 backdrop-blur border border-secondary rounded text-text hover:bg-white/10 transition"
        >
            <Plus className="w-4 h-4" />
        </button>
        <button 
            onClick={handleZoomOut}
            className="p-2 bg-surface/80 backdrop-blur border border-secondary rounded text-text hover:bg-white/10 transition"
        >
            <Minus className="w-4 h-4" />
        </button>
      </div>

      <ComposableMap projectionConfig={{ scale: 200 }} className="w-full h-full relative z-0">
         <defs>
             <radialGradient id="pulseGradient">
                 <stop offset="10%" stopColor="#ef4444" stopOpacity="0.8" />
                 <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
             </radialGradient>
         </defs>

         {/* Zoomable Group for interactivity. */}
        <ZoomableGroup 
            zoom={position.zoom} 
            center={position.coordinates as [number, number]} 
            onMoveEnd={handleMoveEnd}
            minZoom={1} 
            maxZoom={8}
        >
          <Geographies geography={GEO_URL}>
            {({ geographies }: { geographies: any[] }) =>
              geographies.map((geo) => {
                const countryData = findCountryData(geo);
                const isSelected = countryData && selectedCountryId === countryData.id;
                
                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    onClick={() => {
                        // Create transient data for safe countries if needed
                        const targetData = countryData || {
                            id: geo.properties.ISO_A3 || geo.id,
                            name: geo.properties.name || "Unknown Region",
                            infected: 0,
                            severity: 0,
                            neighbors: [],
                            traffic: 0,
                            trafficBreakdown: { flights: 0, trucks: 0, sea: 0 },
                            coordinates: [0,0] // Not needed for detail view really
                        };

                        // Select the country (always allowed now)
                        if (selectedCountryId !== targetData.id) {
                            console.log("Target Acquired:", targetData.id);
                            // Merge geo and targetData, ensuring targetData properties take precedence
                            onSelectCountry({ ...geo, ...targetData });
                        }
                    }}
                    style={{
                      default: {
                        fill: getCountryColor(geo),
                        stroke: isSelected ? "#f8fafc" : "#0f172a",
                        strokeWidth: isSelected ? 1.5 : 0.5,
                        outline: "none",
                        transition: "all 250ms",
                        filter: isSelected ? "drop-shadow(0 0 10px rgba(255,255,255,0.6))" : "none",
                        zIndex: isSelected ? 10 : 1
                      },
                      hover: {
                        fill: isSelected ? "#f8fafc" : (countryData ? "#ef4444" : "#334155"),
                        stroke: "#f8fafc",
                        strokeWidth: 0.75,
                        outline: "none",
                        cursor: "pointer",
                        zIndex: 20
                      },
                      pressed: {
                        fill: "#f8fafc",
                        outline: "none"
                      }
                    }}
                  />
                );
              })
            }
          </Geographies>

          {/* Flight Paths */}
          {selectedCountryId && (() => {
               const selectedCountry = MOCK_COUNTRIES.find(c => c.id === selectedCountryId);
               const startCoords = selectedCountry?.coordinates || [0,0];
               const isUAE = selectedCountryId === 'ARE';
               
               // Generate lines
               const lines = [];

               if (isUAE) {
                   // INCOMING: From all infected countries TO UAE
                   MOCK_COUNTRIES.forEach(country => {
                       if (country.id !== 'ARE' && country.infected > 1000) { // Threshold for visual clutter
                           lines.push({
                               from: country.coordinates,
                               to: UAE_COORDS,
                               color: "#ef4444", // Red for threat
                               width: 2,
                               opacity: 0.8
                           });
                       }
                   });
               } else {
                   // OUTGOING: From Selected TO UAE (Threat/Contact)
                   lines.push({
                       from: startCoords,
                       to: UAE_COORDS,
                       color: "#06b6d4", // Cyan for contact with target
                       width: 2,
                       opacity: 0.9
                   });

                   // OUTGOING: From Selected TO Random Hubs (Neutral)
                   Object.keys(HUB_COORDS).forEach(hubId => {
                       if (hubId !== selectedCountryId && Math.random() > 0.5) { // Randomize slightly
                           lines.push({
                               from: startCoords,
                               to: HUB_COORDS[hubId],
                               color: "#94a3b8", // Slate for neutral
                               width: 1,
                               opacity: 0.4
                           });
                       }
                   });
               }

               return lines.map((line, index) => (
                   <g key={index}>
                       {/* Curvature for visual appeal - slightly curved lines if possible? 
                           react-simple-maps Line is geodesic by default (straight on globe, curved on map). 
                           Let's stick to default Line for now. */}
                       
                       {/* 1. The Flight Corridor (Static Track) */}
                       <Line
                            from={line.from}
                            to={line.to}
                            stroke={line.color}
                            strokeWidth={1}
                            strokeOpacity={0.2}
                            strokeDasharray="4 4"
                            strokeLinecap="round"
                       />

                       {/* 2. The Plane (Moving Tracer) */}
                       {/* We clone the line but make it a moving dash */}
                       <Line
                            from={line.from}
                            to={line.to}
                            stroke={line.color}
                            strokeWidth={line.width + 1}
                            strokeOpacity={1}
                            strokeLinecap="round"
                            className="animate-plane-tracer"
                            style={{ 
                                animationDuration: `${2 + Math.random()}s` // Randomize speed slightly
                            }} 
                       />
                   </g>
               ));
          })()}

         </ZoomableGroup>
      </ComposableMap>
      
      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-surface/80 backdrop-blur p-2 rounded border border-secondary text-xs font-mono pointer-events-none">
        <div className="flex items-center gap-2 mb-1">
            <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
            <span>CRITICAL</span>
        </div>
        <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-emerald-500 rounded-full"></span>
            <span>SAFE</span>
        </div>
        <div className="flex items-center gap-2 mt-1 pt-1 border-t border-secondary/50">
            <span className="w-3 h-3 bg-slate-200 rounded-full shadow-[0_0_5px_white]"></span>
            <span>TARGET</span>
        </div>
      </div>
    </div>
  );
};

export default memo(WorldMap);
