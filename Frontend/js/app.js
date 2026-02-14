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
    
    init: function(data) {
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
    get: function(id) { return this.countries[id] || null; }
};

// --- 2. AI STRATEGY ENGINE ---
const STRATEGIES = {
    TRADE: { 
        id: "s-trade", type: "Economic", icon: "📉", 
        desc: (name) => `Halt all trade imports from ${name}.`,
        reason: "Viral persistence on surfaces detected in cargo."
    },
    FLIGHTS: { 
        id: "s-air", type: "Travel", icon: "✈️", 
        desc: (name) => `Ground all commercial flights from ${name}.`,
        reason: "Passenger transmission probability > 85%."
    },
    BORDERS: { 
        id: "s-border", type: "Security", icon: "🚧", 
        desc: (name) => `Seal land borders with ${name}.`,
        reason: "Uncontrolled migration vectors identified."
    },
    AID: { 
        id: "s-aid", type: "Medical", icon: "�", 
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
            id: "s-monitor", type: "Intel", icon: "�", 
            desc: (n) => `Increase satellite surveillance on ${n}.`,
            reason: "Anomalous movement patterns detected."
        });
    } else {
        suggestions.push({
            id: "s-calm", type: "Status", icon: "✅",
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

const g = svg.append("g"); 
const routesLayer = svg.append("g"); 

const projection = d3.geoNaturalEarth1().translate([width / 2, height / 2]);
const path = d3.geoPath().projection(projection);

const zoom = d3.zoom().scaleExtent([1, 12]).on("zoom", (e) => {
    g.attr("transform", e.transform);
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
    if(!sourceFeature) return;

    const sourceCentroid = d3.geoCentroid(sourceFeature);
    const targetIds = Object.keys(DB.countries).filter(id => id !== sourceId);
    
    const flightTargets = [];
    const shipTargets = [];
    
    for(let i=0; i < Math.min(4, targetIds.length); i++) {
        const rid = targetIds[Math.floor(Math.random()*targetIds.length)];
        if(DB.features[rid]) flightTargets.push(DB.features[rid]);
    }
    for(let i=0; i < Math.min(3, targetIds.length); i++) {
        const rid = targetIds[Math.floor(Math.random()*targetIds.length)];
        if(DB.features[rid]) shipTargets.push(DB.features[rid]);
    }

    flightTargets.forEach(target => {
        const geoPath = {type: "LineString", coordinates: [sourceCentroid, d3.geoCentroid(target)]};
        const pathNode = routesLayer.append("path").datum(geoPath).attr("class", "route-line flight-path").attr("d", path);
        animateVehicle(pathNode, "plane-icon", "var(--flight-color)", 2500);
    });

    shipTargets.forEach(target => {
        const [portX, portY] = projection(sourceCentroid);
        routesLayer.append("text").attr("x", portX).attr("y", portY).attr("class", "port-icon").attr("text-anchor", "middle").attr("dy", ".35em").style("font-size", "14px").text("⚓");

        const geoPath = {type: "LineString", coordinates: [sourceCentroid, d3.geoCentroid(target)]};
        const pathNode = routesLayer.append("path").datum(geoPath).attr("class", "route-line ship-path").attr("d", path);
        animateVehicle(pathNode, "ship-icon", "var(--ship-color)", 6000);
    });
}

function animateVehicle(pathSelection, iconId, color, duration) {
    const pathEl = pathSelection.node();
    const vehicle = routesLayer.append("g");
    
    if (iconId === 'plane-icon') {
        vehicle.append("path")
            .attr("d", "M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z")
            .attr("fill", color)
            .attr("transform", "scale(0.8) rotate(90 12 12) translate(-12 -12)");
    } else {
         vehicle.append("path")
            .attr("d", "M-10 0 L10 0 L7 6 L-7 6 Z M-3 0 L-3 -6 L3 -6 L3 0")
            .attr("fill", color)
            .attr("transform", "scale(0.8)");
    }

    transition();
    function transition() {
        vehicle.transition().duration(duration).ease(d3.easeLinear).attrTween("transform", translateAlong(pathEl)).on("end", transition);
    }

    function translateAlong(path) {
        const l = path.getTotalLength();
        return function(d, i, a) {
            return function(t) {
                const p = path.getPointAtLength(t * l);
                const pBefore = path.getPointAtLength(Math.max(0, t * l - 1));
                const angle = Math.atan2(p.y - pBefore.y, p.x - pBefore.x) * 180 / Math.PI;
                return "translate(" + p.x + "," + p.y + ") rotate(" + angle + ")";
            };
        };
    }
}

const UAE_ID = "784";
const DISEASE_INFO = {
    name: "Crimson Fever",
    symptoms: ["High Fever", "Respiratory Distress", "Hemoptysis"],
    R0: 4.5
};

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
    animateTextJQ("status-count", formatNum(uaeStats.infected));
    $("#status-label").text("DOMESTIC CASES").css("color", status.color);

    const $alerts = $("#alerts-container");
    const $actions = $("#actions-container");
    const $recList = $("#rec-list");

    let intelHTML = `
        <div style="margin-bottom:15px;">
            <div class="rec-head" style="color:var(--accent-color)">PATHOGEN: ${DISEASE_INFO.name}</div>
            <div class="rec-body" style="font-size:0.75rem">Symptoms: ${DISEASE_INFO.symptoms.join(", ")}</div>
        </div>
        <div class="rec-head">TOP EXTERNAL THREATS</div>
    `;
    
    topThreats.forEach(t => {
        intelHTML += `
            <div class="risk-item" style="border-left: 2px solid var(--danger-color); padding-left:8px; margin-bottom:5px;">
                <div style="display:flex; justify-content:space-between;">
                    <span>${t.name}</span>
                    <span style="color:var(--danger-color)">${formatNum(t.infected)}</span>
                </div>
            </div>`;
    });
    $alerts.html(intelHTML);
    $(".panel-title", $recList).text("Intel & Situation Report");

    let actionsHTML = "";
    strategies.forEach(s => {
        actionsHTML += `
            <div class="action-card" onclick="triggerAction('${s.id}', '${s.target}')">
                <div style="display:flex; align-items:center; gap:10px; width:100%">
                    <span class="action-icon">${s.icon}</span>
                    <div style="flex:1">
                        <div class="rec-head" style="margin-bottom:2px; font-size:0.8rem; color:var(--text-secondary)">SUGGESTION: ${s.type} Protocol</div>
                        <div class="action-text">${s.desc(s.target)}</div>
                    </div>
                    <div style="background:var(--bg-color); padding:5px 10px; border-radius:4px; font-size:0.7rem; border:1px solid var(--text-secondary); cursor:pointer;">
                        INITIATE
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
window.triggerAction = function(strategyId, targetName) {
    const $card = $(event.target).closest(".action-card");
    const $btn = $card.find("div:last-child"); // The button div
    
    $card.css("border-color", "var(--success-color)");
    $btn.css("background", "var(--success-color)").css("color", "#fff").text("EXECUTING...");
    
    setTimeout(() => {
         $btn.text("AUTHORIZED");
         $card.css("opacity", "0.6");
    }, 1500);
    
    console.log(`Command Center: User authorized ${strategyId} for ${targetName}`);
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
    $("#metric-r0").text((1.2 + Math.random()).toFixed(2));
    $("#metric-cfr").text((2 + Math.random()*3).toFixed(1) + "%");
    $("#metric-load").text(Math.floor(60 + Math.random()*35) + "%");
    $("#symptom-list").html(`
        <div class="symptom-row"><div style="width:100px;">Fever</div><div class="sym-bar-bg"><div class="sym-bar-fill" style="width:88%"></div></div><div>88%</div></div>
        <div class="symptom-row"><div style="width:100px;">Cough</div><div class="sym-bar-bg"><div class="sym-bar-fill" style="width:65%"></div></div><div>65%</div></div>
    `);
    
    const keys = Object.keys(DB.countries);
    let nHtml = "";
    for(let i=0; i<3; i++) {
        let c = DB.countries[keys[Math.floor(Math.random()*keys.length)]];
        if(c) nHtml += `<div class="risk-item"><span>${c.name}</span><span style="color:var(--danger-color)">${formatNum(c.infected)} cases</span></div>`;
    }
    $("#neighbor-list").html(nHtml);
}

function showTooltip(e, t) { 
    let x = e.pageX; if(x > window.innerWidth-120) x -= 120;
    $tooltip.css({ opacity: 1, left: x + "px", top: (e.pageY - 10) + "px" }).text(t);
}
function hideTooltip() { $tooltip.css("opacity", 0); }

function formatNum(n) { 
    if(n >= 1000000) return (n/1000000).toFixed(1) + "M";
    if(n >= 1000) return (n/1000).toFixed(1) + "k";
    return n; 
}

function animateText(id, txt) { 
    // Legacy support or just use jQuery version below.
    animateTextJQ(id, txt);
}

function animateTextJQ(id, txt) {
    const $el = $("#" + id);
    $el.stop().animate({ opacity: 0 }, 150, function() {
        $(this).text(txt).animate({ opacity: 1 }, 150);
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
