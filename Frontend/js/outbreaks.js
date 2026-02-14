// --- SHARED NAVIGATION ---
import { initSideNav } from './nav.js';

// --- OUTBREAK DATA ---
const OUTBREAKS = [
    {
        id: "ob-1",
        name: "Crimson Fever",
        year: "2026",
        origin: "Southeast Asia",
        status: "active",
        severity: "critical",
        totalCases: "14.2M",
        fatalities: "312K",
        R0: 4.5,
        duration: "Ongoing",
        description: "Airborne respiratory pathogen with rapid mutation rate. Currently spreading across multiple continents.",
        icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/></svg>`
    },
    {
        id: "ob-2",
        name: "Nox Virus",
        year: "2025",
        origin: "Central Africa",
        status: "active",
        severity: "elevated",
        totalCases: "2.8M",
        fatalities: "89K",
        R0: 2.8,
        duration: "Ongoing",
        description: "Neurotropic virus transmitted via mosquito vectors. Crosses the blood-brain barrier within 48 hours of infection.",
        icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 15c6.667-6 13.333 0 20-6"/><path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/><path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"/><path d="M17 6l-2.5-2.5"/><path d="M14 8l-1-3"/><path d="M7 18l2.5 2.5"/><path d="M10 16l1 3"/></svg>`
    },
    {
        id: "ob-3",
        name: "Strain Omega-7",
        year: "2026",
        origin: "Unknown",
        status: "active",
        severity: "critical",
        totalCases: "890K",
        fatalities: "156K",
        R0: 6.1,
        duration: "Ongoing",
        description: "Suspected engineered pathogen with WHO Level-4 containment classification. Extremely high fatality rate.",
        icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><path d="M8.5 2h7"/><path d="M7 16.5h10"/></svg>`
    },
    {
        id: "ob-4",
        name: "Pale Rot",
        year: "2024",
        origin: "Eastern Europe",
        status: "contained",
        severity: "moderate",
        totalCases: "420K",
        fatalities: "8.1K",
        R0: 1.9,
        duration: "14 months",
        description: "Fungal-viral hybrid resistant to standard antivirals. Successfully contained through aggressive quarantine protocols.",
        icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/></svg>`
    },
    {
        id: "ob-5",
        name: "Azure Plague",
        year: "2023",
        origin: "South America",
        status: "contained",
        severity: "elevated",
        totalCases: "1.6M",
        fatalities: "42K",
        R0: 3.2,
        duration: "9 months",
        description: "Waterborne bacterial pathogen causing severe gastrointestinal hemorrhaging. Vaccine developed in record time.",
        icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>`
    },
    {
        id: "ob-6",
        name: "Iron Cough",
        year: "2022",
        origin: "Northern India",
        status: "contained",
        severity: "critical",
        totalCases: "8.3M",
        fatalities: "198K",
        R0: 5.4,
        duration: "18 months",
        description: "Highly contagious respiratory illness with metallic-tasting hemoptysis. Global lockdowns enacted across 47 nations.",
        icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 16.98h1a2 2 0 0 0 1.75-2.97l-1.9-3.52"/><path d="M12 16.98H6a2 2 0 0 1-1.75-2.97L9 5.7a2 2 0 0 1 3.5 0l4.75 8.31"/><circle cx="12" cy="17" r="5"/></svg>`
    },
    {
        id: "ob-7",
        name: "Phantom Flu",
        year: "2021",
        origin: "West Africa",
        status: "contained",
        severity: "moderate",
        totalCases: "560K",
        fatalities: "3.2K",
        R0: 2.1,
        duration: "6 months",
        description: "Influenza variant with unusually long asymptomatic transmission window. Contained through early contact tracing.",
        icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>`
    },
    {
        id: "ob-8",
        name: "Scarlet Wilt",
        year: "2020",
        origin: "Mediterranean Basin",
        status: "contained",
        severity: "elevated",
        totalCases: "3.1M",
        fatalities: "67K",
        R0: 3.8,
        duration: "11 months",
        description: "Plant-to-human zoonotic pathogen causing rapid dermal necrosis. First documented cross-kingdom viral transmission.",
        icon: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.9C15.5 4.9 17 3.5 19 2c1 2 2 4.5 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>`
    }
];

// --- RENDER CARDS ---
function renderOutbreaks(filter = "all") {
    const grid = document.getElementById("outbreaks-grid");
    const filtered = filter === "all"
        ? OUTBREAKS
        : OUTBREAKS.filter(o => {
            if (filter === "critical") return o.severity === "critical";
            return o.status === filter;
        });

    grid.innerHTML = filtered.map(o => {
        const sevColor = o.severity === "critical" ? "var(--danger-color)"
            : o.severity === "elevated" ? "var(--warning-color)"
                : "var(--success-color)";
        const statusColor = o.status === "active" ? "var(--danger-color)" : "var(--success-color)";
        const statusLabel = o.status === "active" ? "ACTIVE" : "CONTAINED";

        return `
        <div class="outbreak-card" data-status="${o.status}" data-severity="${o.severity}">
            <div class="outbreak-card-header">
                <div class="outbreak-icon">${o.icon}</div>
                <div class="outbreak-card-title">
                    <h3>${o.name}</h3>
                    <span class="outbreak-year">${o.year} · ${o.origin}</span>
                </div>
                <span class="outbreak-status-badge" style="background:${statusColor}">${statusLabel}</span>
            </div>

            <p class="outbreak-desc">${o.description}</p>

            <div class="outbreak-metrics">
                <div class="outbreak-metric">
                    <span class="metric-label">Cases</span>
                    <span class="metric-value">${o.totalCases}</span>
                </div>
                <div class="outbreak-metric">
                    <span class="metric-label">Fatalities</span>
                    <span class="metric-value" style="color:var(--danger-color)">${o.fatalities}</span>
                </div>
                <div class="outbreak-metric">
                    <span class="metric-label">R0</span>
                    <span class="metric-value" style="color:${sevColor}">${o.R0}</span>
                </div>
                <div class="outbreak-metric">
                    <span class="metric-label">Duration</span>
                    <span class="metric-value">${o.duration}</span>
                </div>
            </div>

            <div class="outbreak-severity-bar">
                <div class="severity-fill" style="width:${(o.R0 / 7) * 100}%; background:${sevColor}"></div>
            </div>
        </div>`;
    }).join("");
}

// --- FILTERS ---
document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        renderOutbreaks(btn.dataset.filter);
    });
});

// --- STATS ---
function updateStats() {
    document.getElementById("total-outbreaks").textContent = OUTBREAKS.length;
    document.getElementById("contained-count").textContent = OUTBREAKS.filter(o => o.status === "contained").length;
    document.getElementById("active-count").textContent = OUTBREAKS.filter(o => o.status === "active").length;
}

// --- INIT ---
renderOutbreaks();
updateStats();
initSideNav("outbreaks");
