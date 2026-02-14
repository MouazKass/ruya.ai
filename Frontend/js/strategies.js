// --- SHARED NAVIGATION ---
import { initSideNav } from './nav.js';

// --- SVG ICONS ---
const ICONS = {
    flight: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></svg>`,
    border: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22V2"/><path d="m5 12 7-7 7 7"/><path d="M2 17h20"/><path d="M2 7h20"/></svg>`,
    trade: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/></svg>`,
    medical: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v4"/><path d="M16 2v4"/><rect x="4" y="4" width="16" height="6" rx="2"/><path d="M12 10v12"/><path d="M6 16h12"/></svg>`,
    satellite: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"/><path d="M4.93 4.93a10 10 0 0 0 0 14.14"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M7.76 7.76a6 6 0 0 0 0 8.48"/><path d="M16.24 7.76a6 6 0 0 1 0 8.48"/></svg>`,
    quarantine: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`,
    vaccine: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m18 2 4 4"/><path d="m17 7 3-3"/><path d="M19 9 8.7 19.3c-1 1-2.5 1-3.4 0l-.6-.6c-1-1-1-2.5 0-3.4L15 5"/><path d="m9 11 4 4"/><path d="m5 19-3 3"/><path d="m14 4 6 6"/></svg>`,
    comms: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
    shield: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
    water: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>`,
    supply: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 17h4V5H2v12h3"/><path d="M20 17h2v-3.34a4 4 0 0 0-1.17-2.83L19 9h-5v8h1"/><circle cx="7.5" cy="17.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>`,
    data: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`
};

// --- ALL AGENT STRATEGIES ---
const AGENT_STRATEGIES = [
    {
        id: "travel-ban",
        category: "Travel",
        name: "Air Travel Suspension",
        icon: ICONS.flight,
        severity: "critical",
        triggerCondition: "Infection rate > 5% in source region",
        description: "Immediately ground all commercial and charter flights originating from high-infection regions. Cargo flights continue under enhanced screening protocols.",
        reasoning: [
            "Airborne pathogens propagate fastest through commercial aviation corridors.",
            "With infection rates exceeding 5%, the probability of infected passengers exceeds 85% per flight.",
            "Historical precedent: early flight bans in past pandemics reduced cross-border spread by up to 72%.",
            "Economic modeling suggests temporary air travel suspension costs less than treating an uncontrolled domestic outbreak."
        ],
        impact: "High",
        estimatedCost: "$2.4B / week",
        successRate: "78%",
        timeToEffect: "24-48 hours"
    },
    {
        id: "border-seal",
        category: "Security",
        name: "Land Border Lockdown",
        icon: ICONS.border,
        severity: "critical",
        triggerCondition: "Infection rate > 5% in adjacent nation",
        description: "Deploy military and security forces to seal all land crossings. Only authorized humanitarian and essential supply convoys permitted through designated checkpoints.",
        reasoning: [
            "Uncontrolled migration vectors have been identified along border corridors.",
            "Land crossings are the second-highest transmission channel after air travel.",
            "Adjacent nations with >5% infection rates present immediate geographic risk.",
            "Sealing borders enables controlled screening of all incoming individuals."
        ],
        impact: "Very High",
        estimatedCost: "$800M / week",
        successRate: "82%",
        timeToEffect: "12-24 hours"
    },
    {
        id: "trade-halt",
        category: "Economic",
        name: "Trade Import Embargo",
        icon: ICONS.trade,
        severity: "critical",
        triggerCondition: "Infection rate > 5% in trade partner",
        description: "Halt all physical trade imports from critically affected nations. Digital services and financial transactions remain unaffected.",
        reasoning: [
            "Viral persistence on cargo surfaces has been detected for up to 72 hours post-packaging.",
            "Import logistics workers represent a high-risk exposure group with multiplier transmission potential.",
            "Supply chain contamination could bypass standard immigration screening entirely.",
            "Diverting trade to unaffected partners mitigates both health and long-term economic risk."
        ],
        impact: "Moderate",
        estimatedCost: "$5.1B / week",
        successRate: "65%",
        timeToEffect: "48-72 hours"
    },
    {
        id: "medical-aid",
        category: "Medical",
        name: "Humanitarian Medical Dispatch",
        icon: ICONS.medical,
        severity: "elevated",
        triggerCondition: "Infection rate 1–5% and healthcare capacity failing",
        description: "Deploy mobile medical units, field hospitals, and emergency pharmaceutical supplies to affected regions to prevent healthcare system collapse.",
        reasoning: [
            "Healthcare collapse in neighboring regions accelerates refugee flows toward UAE borders.",
            "Proactive aid reduces the total cost of containment by an estimated 40%.",
            "Establishes diplomatic goodwill for future cooperation on containment strategies.",
            "Field data from medical teams provides superior real-time intelligence on pathogen evolution."
        ],
        impact: "High",
        estimatedCost: "$340M / deployment",
        successRate: "71%",
        timeToEffect: "3-5 days"
    },
    {
        id: "surveillance",
        category: "Intelligence",
        name: "Enhanced Satellite Surveillance",
        icon: ICONS.satellite,
        severity: "moderate",
        triggerCondition: "Infection rate 0.1–1% with anomalous patterns",
        description: "Redirect satellite and SIGINT assets to monitor population movements, mass gatherings, and potential quarantine breaches in regions of concern.",
        reasoning: [
            "Anomalous movement patterns often precede confirmed outbreak escalation by 5-10 days.",
            "Satellite imagery can detect mass burials, hospital overcrowding, and refugee movements before official reporting.",
            "Signals intelligence provides early warning of government cover-ups or reporting delays.",
            "Data feeds directly into the AI prediction model, improving forecast accuracy by 23%."
        ],
        impact: "Low",
        estimatedCost: "$12M / week",
        successRate: "89%",
        timeToEffect: "6-12 hours"
    },
    {
        id: "quarantine",
        category: "Containment",
        name: "Domestic Quarantine Zones",
        icon: ICONS.quarantine,
        severity: "critical",
        triggerCondition: "Domestic cases exceed 10,000",
        description: "Establish designated quarantine zones in affected domestic regions with enforced stay-at-home orders, restricted movement, and mandatory testing.",
        reasoning: [
            "Containing domestic clusters early prevents exponential spread through community transmission.",
            "Quarantine zones reduce R0 by an average of 1.8 within the first week of enforcement.",
            "Contact tracing is 4x more effective within defined geographic boundaries.",
            "Enables targeted resource allocation rather than nationwide lockdowns."
        ],
        impact: "Very High",
        estimatedCost: "$1.8B / week",
        successRate: "76%",
        timeToEffect: "24of hours"
    },
    {
        id: "vaccine-push",
        category: "Medical",
        name: "Emergency Vaccination Campaign",
        icon: ICONS.vaccine,
        severity: "elevated",
        triggerCondition: "Vaccine available and infection rate rising",
        description: "Launch mass vaccination campaign targeting high-risk populations first: healthcare workers, elderly, immunocompromised, and border personnel.",
        reasoning: [
            "Vaccinating healthcare workers first preserves the medical system's capacity to treat infected patients.",
            "Ring vaccination around confirmed cases has historically contained outbreaks 3x faster than mass approaches.",
            "Early vaccination reduces severity of illness even if infection occurs, lowering ICU burden by 60%.",
            "Public vaccination campaigns also serve as confidence-building measures that reduce panic-driven behaviors."
        ],
        impact: "Very High",
        estimatedCost: "$2.1B total",
        successRate: "84%",
        timeToEffect: "2-4 weeks"
    },
    {
        id: "comms-campaign",
        category: "Communication",
        name: "Public Information Campaign",
        icon: ICONS.comms,
        severity: "moderate",
        triggerCondition: "Any active pathogen threat",
        description: "Deploy multi-channel public awareness campaign across broadcast, digital, and mobile platforms with real-time updates, hygiene guidance, and misinformation countermeasures.",
        reasoning: [
            "Informed populations demonstrate 35% higher compliance with health directives.",
            "Countering misinformation early prevents panic-driven resource hoarding and healthcare system overload.",
            "Transparent communication maintains public trust, which is critical for long-term strategy compliance.",
            "Digital channels enable instant updates as the pathogen situation evolves."
        ],
        impact: "Moderate",
        estimatedCost: "$45M / campaign",
        successRate: "62%",
        timeToEffect: "Immediate"
    },
    {
        id: "maritime-screen",
        category: "Maritime",
        name: "Port Screening Protocol",
        icon: ICONS.water,
        severity: "elevated",
        triggerCondition: "Infection rate > 1% in maritime trade partners",
        description: "Implement mandatory health screening for all crew and passengers at UAE ports. Cargo undergoes UV-C decontamination before entry to domestic supply chain.",
        reasoning: [
            "Maritime crews spend extended periods in confined spaces, creating ideal transmission environments.",
            "Ship-to-shore transfer is a documented pathway for pathogen introduction in coastal nations.",
            "Port screening can be implemented without fully halting maritime trade, preserving economic flow.",
            "UV-C decontamination neutralizes 99.7% of known surface pathogens on cargo containers."
        ],
        impact: "Moderate",
        estimatedCost: "$180M / month",
        successRate: "74%",
        timeToEffect: "48 hours"
    },
    {
        id: "supply-stockpile",
        category: "Logistics",
        name: "Strategic Resource Stockpiling",
        icon: ICONS.supply,
        severity: "moderate",
        triggerCondition: "Any active pathogen with R0 > 2",
        description: "Activate emergency procurement of medical supplies, PPE, ventilators, and pharmaceutical reserves. Establish distributed regional stockpiles for rapid deployment.",
        reasoning: [
            "Global supply chains collapse within 2-3 weeks of a major pandemic declaration.",
            "Pre-positioned stockpiles enable 48-hour response times vs. 2-week procurement cycles.",
            "Diversified storage locations prevent single-point-of-failure in resource distribution.",
            "Historical analysis shows nations with pre-positioned reserves had 40% lower fatality rates."
        ],
        impact: "High",
        estimatedCost: "$3.2B initial",
        successRate: "88%",
        timeToEffect: "1-2 weeks"
    },
    {
        id: "cyber-shield",
        category: "Cyber",
        name: "Critical Infrastructure Protection",
        icon: ICONS.shield,
        severity: "elevated",
        triggerCondition: "Engineered pathogen markers detected",
        description: "Activate enhanced cybersecurity protocols for healthcare, utilities, and communication infrastructure. Deploy counter-intelligence teams to investigate pathogen origin.",
        reasoning: [
            "Engineered pathogens may be accompanied by coordinated cyber attacks on health infrastructure.",
            "Healthcare systems under pandemic stress are 5x more vulnerable to ransomware attacks.",
            "Protecting communication infrastructure ensures public information channels remain operational.",
            "Counter-intelligence gathering is critical for understanding the full threat vector of engineered agents."
        ],
        impact: "High",
        estimatedCost: "$95M / month",
        successRate: "81%",
        timeToEffect: "6-12 hours"
    },
    {
        id: "data-sharing",
        category: "Intelligence",
        name: "International Data Sharing Protocol",
        icon: ICONS.data,
        severity: "moderate",
        triggerCondition: "Multi-region outbreak detected",
        description: "Establish real-time epidemiological data exchange with WHO, neighboring nations, and allied intelligence services. Feed data into AI prediction models for improved forecasting.",
        reasoning: [
            "Cross-border data sharing improves outbreak prediction accuracy by 35-50%.",
            "Standardized data formats enable faster identification of mutation patterns.",
            "Collaborative intelligence reduces duplication of effort across nations.",
            "AI models trained on multi-source data produce intervention recommendations 20% earlier."
        ],
        impact: "Moderate",
        estimatedCost: "$8M / month",
        successRate: "91%",
        timeToEffect: "24-48 hours"
    }
];

// --- RENDER ---
function renderStrategies() {
    const grid = document.getElementById("strategies-grid");

    grid.innerHTML = AGENT_STRATEGIES.map((s, i) => {
        const sevColor = s.severity === "critical" ? "var(--danger-color)"
            : s.severity === "elevated" ? "var(--warning-color)"
                : "var(--accent-color)";

        const reasoningHTML = s.reasoning.map(r =>
            `<div class="reasoning-point">
                <span>${r}</span>
            </div>`
        ).join("");

        return `
        <div class="strategy-card" style="animation-delay:${i * 60}ms; border-left: 3px solid ${sevColor}">
            <div class="strategy-card-top">
                <div class="strategy-card-title">
                    <span class="strategy-category" style="color:${sevColor}">${s.category.toUpperCase()}</span>
                    <h3>${s.name}</h3>
                </div>
            </div>

            <div class="strategy-trigger">
                <span>Trigger: ${s.triggerCondition}</span>
            </div>

            <p class="strategy-desc">${s.description}</p>

            <div class="strategy-reasoning">
                <div class="reasoning-title">Strategic Reasoning</div>
                ${reasoningHTML}
            </div>

            <div class="strategy-metrics-row">
                <div class="strategy-metric">
                    <span class="sm-label">Impact</span>
                    <span class="sm-value">${s.impact}</span>
                </div>
                <div class="strategy-metric">
                    <span class="sm-label">Est. Cost</span>
                    <span class="sm-value">${s.estimatedCost}</span>
                </div>
                <div class="strategy-metric">
                    <span class="sm-label">Success Rate</span>
                    <span class="sm-value" style="color:var(--success-color)">${s.successRate}</span>
                </div>
                <div class="strategy-metric">
                    <span class="sm-label">Time to Effect</span>
                    <span class="sm-value">${s.timeToEffect}</span>
                </div>
            </div>
        </div>`;
    }).join("");
}

// --- INIT ---
renderStrategies();
initSideNav("strategies");
