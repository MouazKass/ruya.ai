import { scaleLinear } from 'd3-scale';

export interface CountryData {
  id: string; // ISO3
  name: string;
  infected: number;
  severity: number; // 0-100
  neighbors: string[]; // List of ISO3
  traffic: number; // Incoming traffic volume
  trafficBreakdown: {
    flights: number;
    trucks: number;
    sea: number;
  };
  coordinates: [number, number]; // [Longitude, Latitude] for marker
}

export interface AgentSuggestion {
  id: string;
  type: 'TRADE' | 'FLIGHT' | 'BORDER' | 'MEDICAL';
  targetCountry: string;
  description: string;
  actionLabel: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
}

export const MOCK_COUNTRIES: CountryData[] = [
  { id: 'CHN', name: 'China', infected: 145000, severity: 85, neighbors: ['MNG', 'RUS', 'IND', 'NPL', 'PAK'], traffic: 50000, trafficBreakdown: { flights: 30000, trucks: 10000, sea: 10000 }, coordinates: [104.1954, 35.8617] },
  { id: 'IND', name: 'India', infected: 89000, severity: 72, neighbors: ['CHN', 'PAK', 'NPL', 'BGD'], traffic: 45000, trafficBreakdown: { flights: 25000, trucks: 15000, sea: 5000 }, coordinates: [78.9629, 20.5937] },
  { id: 'USA', name: 'United States', infected: 42000, severity: 45, neighbors: ['CAN', 'MEX'], traffic: 80000, trafficBreakdown: { flights: 60000, trucks: 15000, sea: 5000 }, coordinates: [-95.7129, 37.0902] },
  { id: 'BRA', name: 'Brazil', infected: 35000, severity: 60, neighbors: ['ARG', 'BOL', 'PER'], traffic: 20000, trafficBreakdown: { flights: 10000, trucks: 5000, sea: 5000 }, coordinates: [-51.9253, -14.2350] },
  { id: 'RUS', name: 'Russia', infected: 12000, severity: 30, neighbors: ['CHN', 'MNG', 'KAZ', 'FIN'], traffic: 15000, trafficBreakdown: { flights: 5000, trucks: 8000, sea: 2000 }, coordinates: [105.3188, 61.5240] },
  { id: 'ARE', name: 'United Arab Emirates', infected: 120, severity: 5, neighbors: ['SAU', 'OMN'], traffic: 100000, trafficBreakdown: { flights: 80000, trucks: 5000, sea: 15000 }, coordinates: [53.8478, 23.4241] }, // Host
  { id: 'SAU', name: 'Saudi Arabia', infected: 500, severity: 15, neighbors: ['ARE', 'YEM', 'JOR', 'IRQ', 'KWT'], traffic: 30000, trafficBreakdown: { flights: 10000, trucks: 15000, sea: 5000 }, coordinates: [45.0792, 23.8859] },
  { id: 'IRN', name: 'Iran', infected: 15000, severity: 65, neighbors: ['IRQ', 'TUR', 'PAK', 'AFG'], traffic: 12000, trafficBreakdown: { flights: 2000, trucks: 8000, sea: 2000 }, coordinates: [53.6880, 32.4279] },
  { id: 'IRQ', name: 'Iraq', infected: 8000, severity: 55, neighbors: ['IRN', 'TUR', 'SYR', 'JOR', 'SAU', 'KWT'], traffic: 5000, trafficBreakdown: { flights: 1000, trucks: 3000, sea: 1000 }, coordinates: [43.6793, 33.2232] },
  { id: 'GBR', name: 'United Kingdom', infected: 25000, severity: 40, neighbors: ['IRL'], traffic: 60000, trafficBreakdown: { flights: 40000, trucks: 10000, sea: 10000 }, coordinates: [-3.4360, 55.3781] },
  { id: 'FRA', name: 'France', infected: 18000, severity: 35, neighbors: ['ESP', 'DEU', 'ITA', 'BEL', 'CHE'], traffic: 55000, trafficBreakdown: { flights: 25000, trucks: 20000, sea: 10000 }, coordinates: [2.2137, 46.2276] },
  { id: 'DEU', name: 'Germany', infected: 15000, severity: 30, neighbors: ['FRA', 'POL', 'CZE', 'AUT', 'CHE'], traffic: 50000, trafficBreakdown: { flights: 20000, trucks: 25000, sea: 5000 }, coordinates: [10.4515, 51.1657] },
  { id: 'ITA', name: 'Italy', infected: 22000, severity: 58, neighbors: ['FRA', 'CHE', 'AUT', 'SVN'], traffic: 40000, trafficBreakdown: { flights: 15000, trucks: 15000, sea: 10000 }, coordinates: [12.5674, 41.8719] },
  { id: 'JPN', name: 'Japan', infected: 9000, severity: 25, neighbors: [], traffic: 70000, trafficBreakdown: { flights: 40000, trucks: 5000, sea: 25000 }, coordinates: [138.2529, 36.2048] },
  { id: 'EGY', name: 'Egypt', infected: 3000, severity: 40, neighbors: ['LBY', 'SDN', 'ISR'], traffic: 25000, trafficBreakdown: { flights: 10000, trucks: 5000, sea: 10000 }, coordinates: [30.8025, 26.8206] },
  { id: 'TUR', name: 'Turkey', infected: 11000, severity: 50, neighbors: ['GRC', 'BGR', 'GEO', 'ARM', 'IRN', 'IRQ', 'SYR'], traffic: 35000, trafficBreakdown: { flights: 15000, trucks: 10000, sea: 10000 }, coordinates: [35.2433, 38.9637] },
];

export const GLOBAL_STATS = {
  totalInfected: 345000,
  activeOutbreaks: 12,
  riskLevel: 'HIGH',
};

export const AGENT_SUGGESTIONS: AgentSuggestion[] = [
  {
    id: '1',
    type: 'FLIGHT',
    targetCountry: 'China',
    description: 'High infection rate detected in outgoing passengers. Recommend immediate suspension of all commercial flights.',
    actionLabel: 'Halt Flights',
    severity: 'HIGH',
  },
  {
    id: '2',
    type: 'TRADE',
    targetCountry: 'India',
    description: 'Contaminated cargo shipments identified. Suggest halting non-essential trade imports.',
    actionLabel: 'Stop Trade',
    severity: 'MEDIUM',
  },
  {
    id: '3',
    type: 'BORDER',
    targetCountry: 'Iran',
    description: 'Increased border crossing from infected regions. Recommend tightening border control.',
    actionLabel: 'Reinforce Border',
    severity: 'HIGH',
  },
];

// Color scale for severity
export const getSeverityColor = scaleLinear<string>()
  .domain([0, 50, 100])
  .range(['#10b981', '#fbbf24', '#ef4444']); // Green -> Amber -> Red
