const fs = require('fs');
const https = require('https');

// Configuration for API Endpoints
const API_CONFIG = {
    countries: "https://restcountries.com/v3.1/all?fields=name,population,ccn3",
    gdp: "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.CD?format=json&per_page=300&date=2023"
};

// Major cities with fixed coordinates (to ensure they align with the map projection)
const majorCities = [
  // Asia – largest megacities
  { name: "Jakarta", country: "Indonesia", coords: [106.845, -6.2146], pop: 41900000 },   // UN 2025 #1 :contentReference[oaicite:1]{index=1}
  { name: "Dhaka", country: "Bangladesh", coords: [90.4086, 23.7231], pop: 36600000 },    // UN 2025 #2 :contentReference[oaicite:2]{index=2}
  { name: "Tokyo", country: "Japan", coords: [139.6917, 35.6895], pop: 33400000 },       // UN agglomeration estimate :contentReference[oaicite:3]{index=3}
  { name: "New Delhi", country: "India", coords: [77.2167, 28.6667], pop: 30200000 },    // UN 2025 #4 :contentReference[oaicite:4]{index=4}
  { name: "Shanghai", country: "China", coords: [121.4667, 31.1667], pop: 29500000 },    // UN 2025 #5 :contentReference[oaicite:5]{index=5}
  { name: "Guangzhou", country: "China", coords: [113.259, 23.1288], pop: 27600000 },    // UN 2025 #6 :contentReference[oaicite:6]{index=6}
  { name: "Manila", country: "Philippines", coords: [120.9833, 14.6], pop: 24700000 },   // UN 2025 #8 :contentReference[oaicite:7]{index=7}
  { name: "Kolkata", country: "India", coords: [88.3639, 22.5726], pop: 22500000 },      // UN 2025 #9 :contentReference[oaicite:8]{index=8}
  { name: "Seoul", country: "South Korea", coords: [126.978, 37.5665], pop: 22500000 },  // UN 2025 #10 :contentReference[oaicite:9]{index=9}
  { name: "Mumbai", country: "India", coords: [72.8777, 19.0758], pop: 22100000 },       // UN agglomeration estimates :contentReference[oaicite:10]{index=10}
  { name: "Beijing", country: "China", coords: [116.4074, 39.9042], pop: 21000000 },     // UN rankings :contentReference[oaicite:11]{index=11}
  { name: "Bangkok", country: "Thailand", coords: [100.5014, 13.7563], pop: 18100000 },  // UN agglomeration :contentReference[oaicite:12]{index=12}
  { name: "Karachi", country: "Pakistan", coords: [67.0011, 24.8607], pop: 20200000 },   // UN 2025 :contentReference[oaicite:13]{index=13}
  { name: "Lahore", country: "Pakistan", coords: [74.3436, 31.5497], pop: 15100000 },    // UN 2025 :contentReference[oaicite:14]{index=14}
  { name: "Chengdu", country: "China", coords: [104.0657, 30.6595], pop: 10100000 },    // population >10M tier :contentReference[oaicite:15]{index=15}
  { name: "Shenzhen", country: "China", coords: [114.0579, 22.5431], pop: 13700000 },    // population >10M :contentReference[oaicite:16]{index=16}

  // Africa
  { name: "Cairo", country: "Egypt", coords: [31.2357, 30.0444], pop: 25600000 },        // UN 2025 :contentReference[oaicite:17]{index=17}
  { name: "Lagos", country: "Nigeria", coords: [3.3792, 6.5244], pop: 16000000 },       // UN agglomeration >16M :contentReference[oaicite:18]{index=18}
  { name: "Kinshasa", country: "DR Congo", coords: [15.3136, -4.4419], pop: 17000000 },  // UN 2025 :contentReference[oaicite:19]{index=19}
  { name: "Luanda", country: "Angola", coords: [13.2344, -8.8390], pop: 11000000 },     // UN agglomeration >10M :contentReference[oaicite:20]{index=20}

  // North & Latin America
  { name: "São Paulo", country: "Brazil", coords: [-46.6333, -23.5505], pop: 19000000 }, // UN 2025 :contentReference[oaicite:21]{index=21}
  { name: "Mexico City", country: "Mexico", coords: [-99.1332, 19.4326], pop: 17700000 },// UN 2025 :contentReference[oaicite:22]{index=22}
  { name: "Buenos Aires", country: "Argentina", coords: [-58.3816, -34.6037], pop: 14000000 }, // UN agglomeration tier :contentReference[oaicite:23]{index=23}
  { name: "Rio de Janeiro", country: "Brazil", coords: [-43.1729, -22.9068], pop: 9500000 },   // UN agglomeration tier :contentReference[oaicite:24]{index=24}
  { name: "Bogotá", country: "Colombia", coords: [-74.0721, 4.7110], pop: 10600000 },   // UN agglomeration tier :contentReference[oaicite:25]{index=25}

  // Europe / Western cities
  { name: "Moscow", country: "Russia", coords: [37.6173, 55.7558], pop: 14500000 },      // UN agglomeration :contentReference[oaicite:26]{index=26}
  { name: "London", country: "United Kingdom", coords: [-0.1276, 51.5074], pop: 9927000 },// UN agglomeration :contentReference[oaicite:27]{index=27}
  { name: "Paris", country: "France", coords: [2.3522, 48.8566], pop: 11400000 },       // UN agglomeration :contentReference[oaicite:28]{index=28}
  { name: "Istanbul", country: "Turkey", coords: [28.9784, 41.0082], pop: 15000000 },   // UN agglomeration :contentReference[oaicite:29]{index=29}

  // Additional global megacities / large cities
  { name: "Los Angeles", country: "USA", coords: [-118.2437, 34.0522], pop: 12700000 }, // UN agglomeration tier :contentReference[oaicite:30]{index=30}
  { name: "Lima", country: "Peru", coords: [-77.0428, -12.0464], pop: 10500000 },        // UN agglomeration tier :contentReference[oaicite:31]{index=31}
  { name: "Tehran", country: "Iran", coords: [51.3890, 35.6892], pop: 9840000 },        // near megacity tier :contentReference[oaicite:32]{index=32}
  { name: "Hyderabad", country: "India", coords: [78.4867, 17.3850], pop: 11600000 },   // UN agglomeration tier :contentReference[oaicite:33]{index=33}
  { name: "Chennai", country: "India", coords: [80.2707, 13.0827], pop: 12600000 },     // UN agglomeration tier :contentReference[oaicite:34]{index=34}
  { name: "Nanjing", country: "China", coords: [118.7965, 32.0603], pop: 10300000 },    // UN agglomeration tier :contentReference[oaicite:35]{index=35}
  { name: "Ho Chi Minh City", country: "Vietnam", coords: [106.6297, 10.8231], pop: 10000000 } // UN agglomeration tier :contentReference[oaicite:36]{index=36}
];

async function fetchData(url) {
    return new Promise((resolve, reject) => {
        https.get(url, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => resolve(JSON.parse(data)));
        }).on('error', reject);
    });
}

async function generateStats() {
    console.log("🚀 Starting data harvest...");
    
    try {
        const [countryData, gdpDataRaw] = await Promise.all([
            fetchData(API_CONFIG.countries),
            fetchData(API_CONFIG.gdp)
        ]);

        const gdpMap = {};
        // World Bank JSON structure: [metadata, actual_data]
        gdpDataRaw[1].forEach(entry => {
            if (entry.value) {
                // Convert to Billions and store by 3-letter code
                gdpMap[entry.countryiso3code] = Math.round(entry.value / 1e9);
            }
        });

        const stats = {
            countries: {},
            cities: majorCities
        };

        countryData.forEach(c => {
            const id = c.ccn3; // Numeric ISO code matching D3 Map ID
            if (id) {
                stats.countries[id] = {
                    name: c.name.common,
                    pop: c.population,
                    gdp: gdpMap[c.cca3] || 0, // Fallback to 0 if GDP not found
                    infected: 0 // Reset for simulation
                };
            }
        });

        fs.writeFileSync('stats.json', JSON.stringify(stats, null, 2));
        console.log("✅ stats.json generated successfully with live data!");

    } catch (err) {
        console.error("❌ Error fetching data:", err.message);
    }
}

generateStats();