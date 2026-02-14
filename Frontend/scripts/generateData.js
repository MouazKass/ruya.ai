import fs from 'fs';

const statsPath = './stats.json';
const data = JSON.parse(fs.readFileSync(statsPath, 'utf8'));

// Configuration
const INFECTION_RATES = {
    EPICENTER: 0.08,    // 8% infected
    HIGH_TRAFFIC: 0.03, // 3% infected
    NEIGHBOR: 0.015,     // 1.5% infected
    REMOTE: 0.001       // 0.1% infected
};

// Target Country IDs (ISO 3166-1 numeric)
const EPICENTERS = ["156"]; // China
const HUBS = ["840", "826", "276", "250", "380", "392", "724", "643"]; // USA, UK, DE, FR, IT, JP, ES, RU
const MID_EAST = ["784", "682", "512", "414", "368", "048"]; // UAE, KSA, OMN, KWT, IRQ, BHR

function infect(id, rate) {
    if (data.countries[id]) {
        const pop = data.countries[id].pop;
        // Add randomness: +/- 30%
        const finalRate = rate * (0.7 + Math.random() * 0.6); 
        data.countries[id].infected = Math.floor(pop * finalRate);
        data.countries[id].gdp = Math.floor(Math.random() * 500 + 50); // Dummy GDP if 0
    }
}

console.log("Generating Pandemic Scenario...");

// 1. Epicenters
EPICENTERS.forEach(id => infect(id, INFECTION_RATES.EPICENTER));

// 2. Global Hubs
HUBS.forEach(id => infect(id, INFECTION_RATES.HIGH_TRAFFIC));

// 3. Middle East (Focus Region)
MID_EAST.forEach(id => infect(id, INFECTION_RATES.NEIGHBOR));

// 4. Random Scatter
Object.keys(data.countries).forEach(id => {
    // 20% chance of random infection for non-focused countries
    if (Math.random() < 0.2 && data.countries[id].infected === 0) {
        infect(id, INFECTION_RATES.REMOTE);
    }
    
    // Ensure UAE is interesting but not apocalypse yet
    if (id === "784") {
        data.countries[id].infected = 15420; // Specific realistic number
        data.countries[id].gdp = 415;
    }
});

fs.writeFileSync(statsPath, JSON.stringify(data, null, 2));
console.log("stats.json updated with synthetic data.");
