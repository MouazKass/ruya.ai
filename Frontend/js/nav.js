// --- SHARED SIDE NAVIGATION ---
// Compact right-side pill nav inspired by glassmorphism design

const NAV_ITEMS = [
    {
        id: "dashboard",
        label: "Command Center",
        meta: "Live threat map",
        href: "./index.html",
        icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>`
    },
    {
        id: "outbreaks",
        label: "Outbreak Archive",
        meta: "Historical records",
        href: "./outbreaks.html",
        icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>`
    },
    {
        id: "strategies",
        label: "Agent Strategies",
        meta: "AI response protocols",
        href: "./strategies.html",
        icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`
    }
];

export function initSideNav(activeId) {
    const nav = document.getElementById("side-nav");
    if (!nav) return;

    let html = `<div class="side-nav-inner">`;

    NAV_ITEMS.forEach(item => {
        const isActive = item.id === activeId;
        html += `
            <a href="${item.href}" class="side-nav-item ${isActive ? 'active' : ''}" data-nav-id="${item.id}">
                <div class="side-nav-icon">${item.icon}</div>
                <div class="side-nav-tooltip">
                    <div class="side-nav-tooltip-label">${item.label}</div>
                    <div class="side-nav-tooltip-meta">${item.meta}</div>
                </div>
            </a>`;
    });

    html += `</div>`;
    nav.innerHTML = html;
}
