import $ from 'jquery';

// --- 1. DATA INFRASTRUCTURE ---
const config = {
    mapUrl: "https://unpkg.com/world-atlas@2.0.2/countries-110m.json",
    statsUrl: "stats.json"
};

let DB = {
    countries: {},
    cities: [],
    features: {},
    global: { pop: 0, infected: 0, gdp: 0 },

    init: function (data) {
        this.countries = data.countries;
        this.cities = data.cities;
        this.global = { pop: 0, infected: 0, gdp: 0 };

        Object.keys(this.countries).forEach(id => {
            const c = this.countries[id];
            this.global.pop += c.pop;
            this.global.infected += c.infected;
            this.global.gdp += c.gdp;
        });
    },
    get: function (id) { return this.countries[id] || null; }
};

// --- 2. AI STRATEGY ENGINE ---
const SVG_ICONS = {
    trade: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/></svg>`,
    flight: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></svg>`,
    border: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22V2"/><path d="m5 12 7-7 7 7"/><path d="M2 17h20"/><path d="M2 7h20"/></svg>`,
    medical: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v4"/><path d="M16 2v4"/><rect x="4" y="4" width="16" height="6" rx="2"/><path d="M12 10v12"/><path d="M6 16h12"/></svg>`,
    satellite: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"/><path d="M4.93 4.93a10 10 0 0 0 0 14.14"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M7.76 7.76a6 6 0 0 0 0 8.48"/><path d="M16.24 7.76a6 6 0 0 1 0 8.48"/></svg>`,
    checkOk: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`
};

const STRATEGIES = {
    TRADE: {
        id: "s-trade", type: "Economic", icon: SVG_ICONS.trade,
        desc: (name) => `Halt all trade imports from ${name}.`,
        reason: "Viral persistence on surfaces detected in cargo."
    },
    FLIGHTS: {
        id: "s-air", type: "Travel", icon: SVG_ICONS.flight,
        desc: (name) => `Ground all commercial flights from ${name}.`,
        reason: "Passenger transmission probability > 85%."
    },
    BORDERS: {
        id: "s-border", type: "Security", icon: SVG_ICONS.border,
        desc: (name) => `Seal land borders with ${name}.`,
        reason: "Uncontrolled migration vectors identified."
    },
    AID: {
        id: "s-aid", type: "Medical", icon: SVG_ICONS.medical,
        desc: (name) => `Dispatch medical aid package to ${name}.`,
        reason: "Healthcare collapse imminent. Humanitarian crisis."
    }
};

function generateIntel(name, infected, pop) {
    const rate = infected / pop;
    const suggestions = [];

    // Logic for generating strategies based on infection severity
    if (rate > 0.05) { // Critical (>5%)
        suggestions.push(STRATEGIES.FLIGHTS);
        suggestions.push(STRATEGIES.BORDERS);
        suggestions.push(STRATEGIES.TRADE);
    } else if (rate > 0.01) { // High (>1%)
        suggestions.push(STRATEGIES.FLIGHTS);
        suggestions.push(STRATEGIES.AID);
    } else if (rate > 0.001) { // Moderate
        suggestions.push({
            id: "s-monitor", type: "Intel", icon: SVG_ICONS.satellite,
            desc: (n) => `Increase satellite surveillance on ${n}.`,
            reason: "Anomalous movement patterns detected."
        });
    } else {
        suggestions.push({
            id: "s-calm", type: "Status", icon: SVG_ICONS.checkOk,
            desc: (n) => `Maintain standard protocols for ${n}.`,
            reason: "No significant threat vectors."
        });
    }
    return suggestions;
}

function determineStatus(infected, pop) {
    const rate = infected / pop;
    if (rate > 0.05) return { level: "CRITICAL", color: "var(--danger-color)" };
    if (rate > 0.01) return { level: "ELEVATED", color: "var(--warning-color)" };
    return { level: "STABLE", color: "var(--success-color)" };
}

// --- 3. D3 & RENDER LOGIC ---
let width = window.innerWidth, height = window.innerHeight;
let activeCountry = d3.select(null);
let isNightMode = false;

const svg = d3.select("#map-wrapper").append("svg").attr("viewBox", [0, 0, width, height]).on("click", resetView);
const defs = svg.append("defs");

// Plane Icon Path
defs.append("path").attr("id", "plane-icon")
    .attr("d", "M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z")
    .attr("transform", "scale(0.8) rotate(90 12 12) translate(-12 -12)");

// --- INFECTION ZONE RADIAL GRADIENTS ---
// Severity tiers: stable (low), elevated (medium), critical (high)
const severityTiers = [
    { id: "infection-gradient-stable", r: 220, g: 38, b: 38, centerOpacity: 0.25 },
    { id: "infection-gradient-elevated", r: 239, g: 68, b: 68, centerOpacity: 0.45 },
    { id: "infection-gradient-critical", r: 255, g: 0, b: 0, centerOpacity: 0.65 }
];

severityTiers.forEach(tier => {
    const grad = defs.append("radialGradient")
        .attr("id", tier.id)
        .attr("cx", "50%").attr("cy", "50%")
        .attr("r", "50%");
    grad.append("stop")
        .attr("offset", "0%")
        .attr("stop-color", `rgb(${tier.r},${tier.g},${tier.b})`)
        .attr("stop-opacity", tier.centerOpacity);
    grad.append("stop")
        .attr("offset", "60%")
        .attr("stop-color", `rgb(${tier.r},${tier.g},${tier.b})`)
        .attr("stop-opacity", tier.centerOpacity * 0.4);
    grad.append("stop")
        .attr("offset", "100%")
        .attr("stop-color", `rgb(${tier.r},${tier.g},${tier.b})`)
        .attr("stop-opacity", 0);
});

const g = svg.append("g");
const infectionLayer = svg.append("g"); // Infection circles above countries
const routesLayer = svg.append("g");

const projection = d3.geoNaturalEarth1().translate([width / 2, height / 2]);
const path = d3.geoPath().projection(projection);

const zoom = d3.zoom().scaleExtent([1, 12]).on("zoom", (e) => {
    g.attr("transform", e.transform);
    infectionLayer.attr("transform", e.transform);
    routesLayer.attr("transform", e.transform);
    g.selectAll("path.country").attr("stroke-width", 0.5 / e.transform.k);
    g.selectAll(".city-marker").attr("r", 5 / Math.sqrt(e.transform.k));
    routesLayer.selectAll("path.route-line").attr("stroke-width", 1 / e.transform.k);
});
svg.call(zoom);

// Tooltip via jQuery
const $tooltip = $("#tooltip");

// LOADING SEQUENCE
Promise.all([
    d3.json(config.mapUrl),
    d3.json(config.statsUrl)
]).then(([worldData, statsData]) => {

    DB.init(statsData);

    const countries = topojson.feature(worldData, worldData.objects.countries).features;
    countries.forEach(c => { DB.features[c.id] = c; });

    projection.fitSize([width, height], topojson.feature(worldData, worldData.objects.countries));

    g.selectAll("path").data(countries)
        .enter().append("path").attr("d", path).attr("class", "country")
        .on("click", clickedCountry)
        .on("mouseover", (e, d) => {
            const country = DB.get(d.id);
            showTooltip(e, country ? country.name : "Territory");
        })
        .on("mouseout", hideTooltip);

    g.selectAll(".city-marker").data(DB.cities)
        .enter().append("circle").attr("class", "city-marker")
        .attr("cx", d => projection(d.coords)[0]).attr("cy", d => projection(d.coords)[1]).attr("r", 4)
        .on("click", clickedCity)
        .on("mouseover", (e, d) => showTooltip(e, d.name))
        .on("mouseout", hideTooltip);

    // Draw infection zones after map is ready
    drawInfectionZones();

    // 5. Set Initial View (Target: UAE)
    const uaeId = "784";
    const uaeFeature = DB.features[uaeId];

    if (uaeFeature) {
        // Trigger selection visuals
        activeCountry = g.selectAll("path.country").filter(d => d.id === uaeId).classed("active", true);
        updateView('country', uaeId);
        drawConnections(uaeId);

        // Zoom to Middle East Region (approximate bounds for UAE focus)
        // D3 Geo bounds might be tight, so we scale out slightly from the country's centroid
        const [[x0, y0], [x1, y1]] = path.bounds(uaeFeature);
        const cw = x1 - x0;
        const ch = y1 - y0;
        const x = (x0 + x1) / 2;
        const y = (y0 + y1) / 2;
        // Reduced scale factor from 0.9 to 0.4 to zoom out and show more context
        const scale = Math.min(3, 0.4 / Math.max(cw / width, ch / height));
        const translate = [width / 2 - scale * x, height / 2 - scale * y];

        svg.transition().duration(2000).call(
            zoom.transform,
            d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
        );
    } else {
        updateView('global', null);
    }

}).catch(error => {
    console.error("Error loading Pandemic Command Center data:", error);
});
// --- INFECTION ZONE VISUALIZATION ---

function drawInfectionZones() {
    infectionLayer.selectAll("*").remove();

    // Find max infected for radius scaling
    const allInfected = Object.values(DB.countries).map(c => c.infected).filter(v => v > 0);
    if (allInfected.length === 0) return;
    const maxInfected = d3.max(allInfected);

    // Sqrt scale: infection count → pixel radius (5px to 60px)
    const radiusScale = d3.scaleSqrt()
        .domain([0, maxInfected])
        .range([5, 60]);

    Object.keys(DB.countries).forEach(id => {
        const country = DB.countries[id];
        if (country.infected <= 0) return;

        const feature = DB.features[id];
        if (!feature) return;

        const centroid = d3.geoCentroid(feature);
        const [cx, cy] = projection(centroid);

        // Determine severity tier based on infection rate
        const rate = country.infected / country.pop;
        let gradientId;
        if (rate > 0.05) {
            gradientId = "infection-gradient-critical";
        } else if (rate > 0.01) {
            gradientId = "infection-gradient-elevated";
        } else {
            gradientId = "infection-gradient-stable";
        }

        const r = radiusScale(country.infected);

        // Draw the infection circle
        infectionLayer.append("circle")
            .attr("class", "infection-zone")
            .attr("cx", cx)
            .attr("cy", cy)
            .attr("r", r)
            .attr("fill", `url(#${gradientId})`)
            .attr("pointer-events", "none");
    });
}

// --- INTERACTION ---


function clickedCountry(event, d) {
    event.stopPropagation();
    activeCountry.classed("active", false);
    activeCountry = d3.select(this).classed("active", true);
    updateView('country', d.id);
    drawConnections(d.id);
}

function clickedCity(event, d) {
    event.stopPropagation();
    activeCountry.classed("active", false);
    updateView('city', d);
    drawConnections(d.countryId);
}

function resetView() {
    activeCountry.classed("active", false);
    updateView('global', null);
    routesLayer.selectAll("*").remove();
}

function drawConnections(sourceId) {
    routesLayer.selectAll("*").remove();
    const sourceFeature = DB.features[sourceId];
    if (!sourceFeature) return;

    const sourceCentroid = d3.geoCentroid(sourceFeature);
    const targetIds = Object.keys(DB.countries).filter(id => id !== sourceId);

    const flightTargets = [];
    const shipTargets = [];

    for (let i = 0; i < Math.min(6, targetIds.length); i++) {
        const rid = targetIds[Math.floor(Math.random() * targetIds.length)];
        if (DB.features[rid]) flightTargets.push(DB.features[rid]);
    }
    for (let i = 0; i < Math.min(5, targetIds.length); i++) {
        const rid = targetIds[Math.floor(Math.random() * targetIds.length)];
        if (DB.features[rid]) shipTargets.push(DB.features[rid]);
    }

    flightTargets.forEach(target => {
        let start = sourceCentroid;
        let end = d3.geoCentroid(target);

        // If UAE is selected, flights are Incoming (Other -> UAE)
        if (sourceId === UAE_ID) {
            start = d3.geoCentroid(target);
            end = sourceCentroid;
        }

        const geoPath = { type: "LineString", coordinates: [start, end] };
        const pathNode = routesLayer.append("path").datum(geoPath).attr("class", "route-line flight-path").attr("d", path);
        animateVehicle(pathNode, "plane-icon", "var(--flight-color)", 2500);
    });

    // shipTargets.forEach(target => {
    //     const [portX, portY] = projection(sourceCentroid);
    //     routesLayer.append("text").attr("x", portX).attr("y", portY).attr("class", "port-icon").attr("text-anchor", "middle").attr("dy", ".35em").style("font-size", "14px").text("⚓");

    //     const geoPath = { type: "LineString", coordinates: [sourceCentroid, d3.geoCentroid(target)] };
    //     const pathNode = routesLayer.append("path").datum(geoPath).attr("class", "route-line ship-path").attr("d", path);
    //     animateVehicle(pathNode, "ship-icon", "var(--ship-color)", 6000);
    // });
}

function animateVehicle(pathSelection, iconId, color, duration) {
    const pathEl = pathSelection.node();
    const vehicle = routesLayer.append("g");

    if (iconId === 'plane-icon') {
        vehicle.append("path")
            .attr("d", "M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z")
            .attr("fill", color)
            .attr("transform", "scale(0.3) rotate(90 12 12) translate(-12 -12)");
    } else {
        vehicle.append("path")
            .attr("d", "M-10 0 L10 0 L7 6 L-7 6 Z M-3 0 L-3 -6 L3 -6 L3 0")
            .attr("fill", color)
            .attr("transform", "scale(0.3)");
    }

    transition();
    function transition() {
        vehicle.transition().duration(duration).ease(d3.easeLinear).attrTween("transform", translateAlong(pathEl, 0.975)).on("end", transition);
    }

    function translateAlong(path, stopAt = 0.8) {
        const l = path.getTotalLength();
        const maxLength = l * stopAt;

        return function () {
            return function (t) {
                const currentLength = t * maxLength;
                const p = path.getPointAtLength(currentLength);
                const pBefore = path.getPointAtLength(Math.max(0, currentLength - 1));
                const angle = Math.atan2(p.y - pBefore.y, p.x - pBefore.x) * 180 / Math.PI;

                return "translate(" + p.x + "," + p.y + ") rotate(" + angle + ")";
            };
        };
    }

}

const UAE_ID = "784";

// --- PATHOGEN DATABASE (Multiple Pathogens for Carousel) ---
const PATHOGENS = [
    {
        name: "Crimson Fever",
        icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/></svg>`,
        symptoms: ["High Fever", "Respiratory Distress", "Hemoptysis"],
        R0: 4.5,
        severity: "CRITICAL",
        origin: "Southeast Asia",
        notes: "Airborne pathogen with 72-hour incubation. Rapid mutation observed."
    },
    {
        name: "Nox Virus",
        icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 15c6.667-6 13.333 0 20-6"/><path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/><path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"/><path d="M17 6l-2.5-2.5"/><path d="M14 8l-1-3"/><path d="M7 18l2.5 2.5"/><path d="M10 16l1 3"/></svg>`,
        symptoms: ["Neurological Decline", "Vision Loss", "Seizures"],
        R0: 2.8,
        severity: "ELEVATED",
        origin: "Central Africa",
        notes: "Vector-borne via mosquito. Crosses blood-brain barrier in 48 hours."
    },
    {
        name: "Strain Omega-7",
        icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><path d="M8.5 2h7"/><path d="M7 16.5h10"/></svg>`,
        symptoms: ["Organ Failure", "Internal Hemorrhaging", "Cyanosis"],
        R0: 6.1,
        severity: "CRITICAL",
        origin: "Unknown",
        notes: "Engineered markers detected. WHO Level-4 containment required."
    },
    {
        name: "Pale Rot",
        icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/></svg>`,
        symptoms: ["Skin Lesions", "Chronic Fatigue", "Immune Suppression"],
        R0: 1.9,
        severity: "MODERATE",
        origin: "Eastern Europe",
        notes: "Fungal-viral hybrid. Resistant to standard antivirals."
    }
];

let currentPathogenIndex = 0;
let carouselInterval = null;

// Initialize Sidebar once (Idempotent-ish, redraws static UAE sidebar)
function initCommandCenter() {
    const uae = DB.get(UAE_ID);
    if (!uae) return;

    // 1. Identify Top Threats (Highest infected countries excluding UAE)
    const threats = Object.values(DB.countries)
        .filter(c => c.id !== UAE_ID)
        .sort((a, b) => b.infected - a.infected)
        .slice(0, 3);

    // 2. Generate Strategies based on threats
    const strategies = [];
    threats.forEach(t => {
        if (t.infected > 100000) {
            strategies.push({ ...STRATEGIES.FLIGHTS, target: t.name });
            strategies.push({ ...STRATEGIES.TRADE, target: t.name });
        } else if (t.infected > 50000) {
            strategies.push({ ...STRATEGIES.BORDERS, target: t.name });
        }
    });
    // Limit to 4 actionable strategies
    const activeStrategies = strategies.slice(0, 4);

    updateCommandSidebar(uae, threats, activeStrategies);
}

function updateCommandSidebar(uaeStats, topThreats, strategies) {
    const $panel = $("#status-panel");
    const status = determineStatus(uaeStats.infected, uaeStats.pop);

    $panel.css("border-left-color", status.color);
    animateTextJQ("status-count", formatNum(uaeStats.infected), 0);
    $("#status-label").text("DOMESTIC CASES").css("color", status.color);

    const $alerts = $("#alerts-container");
    const $actions = $("#actions-container");
    const $recList = $("#rec-list");

    // --- BUILD PATHOGEN CAROUSEL ---
    let carouselHTML = `<div class="pathogen-carousel">`;

    // Slides
    carouselHTML += `<div class="carousel-track">`;
    PATHOGENS.forEach((p, i) => {
        const sevColor = p.severity === "CRITICAL" ? "var(--danger-color)"
            : p.severity === "ELEVATED" ? "var(--warning-color)"
                : "var(--success-color)";
        carouselHTML += `
            <div class="carousel-slide ${i === 0 ? 'active' : ''}" data-index="${i}">
                <div class="rec-head" style="color:var(--accent-color); display:flex; align-items:center; gap:8px;">
                    <span style="font-size:1.1rem">${p.icon}</span>
                    PATHOGEN: ${p.name}
                    <span class="pathogen-severity" style="background:${sevColor}">${p.severity}</span>
                </div>
                <div class="rec-body" style="font-size:0.75rem; margin-top:4px;">Symptoms: ${p.symptoms.join(", ")}</div>
                <div class="rec-body" style="font-size:0.75rem; margin-top:4px;">R0: <strong style="color:var(--warning-color)">${p.R0}</strong> · Origin: <strong>${p.origin}</strong></div>
                <div class="rec-body" style="font-size:0.7rem; margin-top:6px; font-style:italic; color:var(--text-secondary);">${p.notes}</div>
            </div>`;
    });
    carouselHTML += `</div>`;

    // Dots
    carouselHTML += `<div class="carousel-dots">`;
    PATHOGENS.forEach((_, i) => {
        carouselHTML += `<span class="carousel-dot ${i === 0 ? 'active' : ''}" data-index="${i}"></span>`;
    });
    carouselHTML += `</div>`;
    carouselHTML += `</div>`;

    // Threats section
    carouselHTML += `<div class="rec-head" style="margin-top:12px;">TOP EXTERNAL THREATS</div>`;

    topThreats.forEach(t => {
        carouselHTML += `
            <div class="risk-item">
                <div style="display:flex; justify-content:space-between; width:100%">
                    <span>${t.name}</span>
                    <span style="color:var(--danger-color)">${formatNum(t.infected)}</span>
                </div>
            </div>`;
    });
    $alerts.html(carouselHTML);
    $(".panel-title", $recList).text("Intel & Situation Report");

    // --- CAROUSEL LOGIC ---
    // Dot click handlers
    $(".carousel-dot").on("click", function () {
        const idx = parseInt($(this).data("index"));
        switchPathogenSlide(idx);
        resetCarouselTimer();
    });

    // Start auto-rotation
    resetCarouselTimer();

    let actionsHTML = "";
    strategies.forEach(s => {
        actionsHTML += `
            <div class="action-card">
                <div style="display:flex; align-items:center; gap:10px; width:100%">
                    <span class="action-icon">${s.icon}</span>
                    <div style="flex:1">
                        <div class="rec-head" style="margin-bottom:2px; font-size:0.8rem; color:var(--text-secondary)">SUGGESTION: ${s.type} Protocol</div>
                        <div class="action-text">${s.desc(s.target)}</div>
                    </div>
                    <div class="action-btns">
                        <div class="action-btn action-btn-yes" onclick="triggerAction('${s.id}', '${s.target}', true, event)">YES</div>
                        <div class="action-btn action-btn-no" onclick="triggerAction('${s.id}', '${s.target}', false, event)">NO</div>
                    </div>
                </div>
            </div>`;
    });

    if (strategies.length === 0) {
        actionsHTML = `<div class="rec-item"><div class="rec-body">No immediate external threats requiring intervention. Monitor global vectors.</div></div>`;
    }

    $actions.html(actionsHTML);
    $(".panel-title", $("#action-list")).text("Strategic Response");
}

// --- CAROUSEL HELPERS ---
function switchPathogenSlide(toIndex) {
    currentPathogenIndex = toIndex;
    $(".carousel-slide").removeClass("active");
    $(".carousel-dot").removeClass("active");
    $(`.carousel-slide[data-index="${toIndex}"]`).addClass("active");
    $(`.carousel-dot[data-index="${toIndex}"]`).addClass("active");
}

function resetCarouselTimer() {
    if (carouselInterval) clearInterval(carouselInterval);
    carouselInterval = setInterval(() => {
        const next = (currentPathogenIndex + 1) % PATHOGENS.length;
        switchPathogenSlide(next);
    }, 5000);
}

function updateView(type, data) {
    let stats = {};
    let name = "", sub = "";

    // Bottom Panel Logic (Dynamic Exploration)
    if (type === 'global') {
        stats = DB.global;
        name = "Global View"; sub = "Aggregate Data";
        $("#news-action").removeClass("visible");
    }
    else if (type === 'country') {
        const cData = DB.get(data);
        if (!cData) { stats = { pop: 0, infected: 0, gdp: 0 }; name = "Unknown Territory"; }
        else { stats = cData; name = cData.name; }
        sub = "Nation Status";
        $("#news-action").addClass("visible");
    }
    else if (type === 'city') {
        const country = DB.get(data.countryId) || { infected: 0, pop: 1 };
        const infectionRate = country.infected / country.pop;
        stats = { pop: data.pop, infected: Math.floor(data.pop * infectionRate * 1.2), gdp: 0 };
        name = data.name; sub = "Major Urban Center";
        $("#news-action").addClass("visible");
    }

    // Update Bottom Panel ONLY
    animateText("dash-name", name);
    animateText("dash-sub", sub);
    animateText("val-1", formatNum(stats.pop));
    animateText("val-2", stats.gdp ? "$" + stats.gdp + " B" : "---");
    animateText("val-3", formatNum(stats.infected));

    const status = determineStatus(stats.infected, stats.pop || 1);
    animateTextJQ("val-4", status.level);
    $("#val-4").css("color", status.color);

    // Ensure Static Sidebar is Initialized
    if (DB.countries[UAE_ID]) {
        initCommandCenter();
    }
}

// Remove old updateSidebar function as it is replaced by updateCommandSidebar
// window.triggerAction remains same but updated for context description
window.triggerAction = function (strategyId, targetName, approved, event) {
    const $card = $(event.target).closest(".action-card");
    const $btns = $card.find(".action-btns");

    if (approved) {
        $card.css("border-color", "var(--success-color)");
        $btns.html(`<span class="action-btn-status" style="color:var(--success-color)">AUTHORIZED</span>`);
        setTimeout(() => $card.css("opacity", "0.5"), 1200);
        console.log(`Command Center: User APPROVED ${strategyId} for ${targetName}`);
    } else {
        $card.css("border-color", "var(--danger-color)");
        $btns.html(`<span class="action-btn-status" style="color:var(--danger-color)">REJECTED</span>`);
        setTimeout(() => $card.css("opacity", "0.35"), 1200);
        console.log(`Command Center: User REJECTED ${strategyId} for ${targetName}`);
    }
};

// jQuery Events
$("#status-panel").on("click", () => {
    $("#status-modal").addClass("visible");
    populateModal();
});
$("#close-modal").on("click", () => $("#status-modal").removeClass("visible"));

function populateModal() {
    const title = $("#dash-name").text();
    $("#modal-region-name").text(title);
    $("#metric-air").text(Math.floor(120 + Math.random() * 380));
    $("#metric-sea").text(Math.floor(40 + Math.random() * 160));
    $("#metric-land").text(Math.floor(200 + Math.random() * 800));
    $("#symptom-list").html(`
        <div class="symptom-row"><div style="width:100px;">Fever</div><div class="sym-bar-bg"><div class="sym-bar-fill" style="width:88%"></div></div><div>88%</div></div>
        <div class="symptom-row"><div style="width:100px;">Cough</div><div class="sym-bar-bg"><div class="sym-bar-fill" style="width:65%"></div></div><div>65%</div></div>
    `);

    // UAE regional neighbors by ISO numeric ID
    const UAE_NEIGHBORS = ["682", "512", "364", "368", "414", "634", "048"];
    const neighbors = UAE_NEIGHBORS
        .map(id => DB.get(id))
        .filter(c => c !== null)
        .sort((a, b) => b.infected - a.infected)
        .slice(0, 3);

    let nHtml = "";
    neighbors.forEach(c => {
        nHtml += `<div class="risk-item"><span>${c.name}</span><span style="color:var(--danger-color)">${formatNum(c.infected)} cases</span></div>`;
    });
    $("#neighbor-list").html(nHtml);
}

function showTooltip(e, t) {
    let x = e.pageX; if (x > window.innerWidth - 120) x -= 120;
    $tooltip.css({ opacity: 1, left: x + "px", top: (e.pageY - 10) + "px" }).text(t);
}
function hideTooltip() { $tooltip.css("opacity", 0); }

function formatNum(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
    if (n >= 1000) return (n / 1000).toFixed(1) + "k";
    return n;
}

function animateText(id, txt) {
    // Legacy support or just use jQuery version below.
    animateTextJQ(id, txt);
}

function animateTextJQ(id, txt, timeDelay = 150) {
    const $el = $("#" + id);
    $el.stop().animate({ opacity: 0 }, timeDelay, function () {
        $(this).text(txt).animate({ opacity: 1 }, timeDelay);
    });
}

$("#btn-theme").on("click", () => {
    isNightMode = !isNightMode;
    $("body").attr("data-theme", isNightMode ? "night" : "day");
    $("#theme-icon").text(isNightMode ? "☀" : "☾");
});
$("#btn-reset").on("click", resetView);

$(window).on("resize", () => {
    width = window.innerWidth;
    height = window.innerHeight;
    svg.attr("viewBox", [0, 0, width, height]);
});
