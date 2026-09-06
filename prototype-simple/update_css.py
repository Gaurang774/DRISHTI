import re

with open('d:/SIH FINAL/prototype-simple/styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

# 1. Update Layout
css = re.sub(r'\.main-content \{.*?\n\}', '.main-content {\n    flex: 1;\n    display: flex;\n    flex-direction: column;\n    position: relative;\n    overflow: hidden;\n    background: var(--bg-dark);\n}', css, flags=re.DOTALL)

# 2. Update Sidebar
css = re.sub(r'\.sidebar \{[^\}]+\}', '.sidebar {\n    width: 240px;\n    background: linear-gradient(180deg, #0a0f1d 0%, #060a14 100%);\n    border-right: 1px solid var(--border-dim);\n    display: flex;\n    flex-direction: column;\n    padding: 1.5rem 0;\n    z-index: 1000;\n    position: relative;\n    flex-shrink: 0;\n}', css)
css = re.sub(r'\.nav-links li, \.sidebar-bottom li \{[^\}]+\}', '.nav-links li, .sidebar-bottom li {\n    list-style: none;\n    color: var(--text-secondary);\n    font-size: 0.85rem;\n    font-weight: 500;\n    cursor: pointer;\n    padding: 0.8rem 1.25rem;\n    margin: 0.2rem 1rem;\n    border-radius: 8px;\n    transition: var(--transition);\n    display: flex;\n    align-items: center;\n    gap: 0.75rem;\n}\n.nav-links li i, .sidebar-bottom li i {\n    font-size: 1.2rem;\n}', css)
css = css.replace('.nav-links li.active {\n    color: var(--cyan);\n    background: rgba(6, 182, 212, 0.1);\n    box-shadow: inset 0 0 20px rgba(6, 182, 212, 0.05);\n}', '.nav-links li.active {\n    color: var(--text-bright);\n    background: var(--cyan);\n    box-shadow: 0 4px 12px rgba(6,182,212,0.3);\n}')
css = css.replace('.logo {\n    display: flex;\n    flex-direction: column;\n    align-items: center;\n    gap: 0.25rem;\n    margin-bottom: 2rem;\n}', '.logo {\n    display: flex;\n    align-items: center;\n    gap: 0.75rem;\n    padding: 0 1.25rem;\n    margin-bottom: 2rem;\n}\n.logo-text-group {\n    display: flex;\n    flex-direction: column;\n}\n.logo-text-main {\n    font-size: 1.1rem;\n    font-weight: 800;\n    color: var(--text-bright);\n    letter-spacing: 1px;\n}\n.logo-text-sub {\n    font-size: 0.6rem;\n    color: var(--text-muted);\n}')

# 3. Update Top Bar
css = re.sub(r'\/\* ---- TOP COMMAND BAR ---- \*\/\n\.top-bar \{.*?\n\}', '/* ---- TOP COMMAND BAR ---- */\n.top-bar {\n    padding: 1.25rem 1.5rem 0.75rem 1.5rem;\n    display: flex;\n    justify-content: space-between;\n    align-items: center;\n    gap: 1rem;\n}', css, flags=re.DOTALL)
css = css.replace('.top-bar-left {\n    display: flex;\n    flex-direction: column;\n    gap: 0.3rem;\n    flex: 1;\n    min-width: 0;\n}', '.top-bar-left {\n    display: flex;\n    flex-direction: column;\n    gap: 0.3rem;\n    flex: 1;\n    min-width: 0;\n}\n.top-bar-left h1 {\n    font-size: 1.2rem;\n    font-weight: 700;\n    letter-spacing: 0px;\n    text-transform: none;\n}')

# 4. Update KPI Strip
css = re.sub(r'\/\* ---- KPI STRIP ---- \*\/\n\.kpi-strip \{.*?\n\}', '/* ---- KPI STRIP ---- */\n.kpi-strip {\n    display: flex;\n    gap: 0.75rem;\n    padding: 0 1.5rem;\n    flex-wrap: wrap;\n    z-index: 10;\n}', css, flags=re.DOTALL)
css = css.replace('.kpi-card {\n    display: flex;\n    align-items: center;\n    gap: 0.45rem;\n    background: var(--bg-panel);\n    backdrop-filter: blur(16px);\n    border: 1px solid var(--border-dim);\n    border-radius: 8px;\n    padding: 0.35rem 0.65rem;\n    min-width: 105px;\n    flex-shrink: 0;\n    transition: var(--transition);\n}', '.kpi-card {\n    flex: 1;\n    display: flex;\n    align-items: center;\n    gap: 0.75rem;\n    background: rgba(15, 23, 42, 0.6);\n    border: 1px solid rgba(255,255,255,0.05);\n    border-radius: 8px;\n    padding: 0.75rem 1rem;\n    min-width: 160px;\n    transition: var(--transition);\n}')
css = css.replace('.kpi-icon {\n    font-size: 1.15rem;\n', '.kpi-icon {\n    font-size: 1.8rem;\n')
css = css.replace('.kpi-value {\n    font-size: 0.95rem;\n', '.kpi-value {\n    font-size: 1.25rem;\n')

# 5. Dashboard Core Grid
dashboard_css = """
/* ---- DASHBOARD GRID ---- */
.dashboard-core {
    display: flex;
    flex: 1;
    min-height: 0;
    gap: 1rem;
    padding: 1rem 1.5rem;
}
.left-panel {
    width: 320px;
    display: flex;
    flex-direction: column;
    min-height: 0;
}
.center-panel {
    flex: 1;
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08);
    display: flex;
    flex-direction: column;
}
.intel-panel {
    width: 360px;
    position: relative;
    right: auto;
    top: auto;
    bottom: auto;
    height: 100%;
    transform: none;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    background: var(--bg-card);
    border: 1px solid rgba(255,255,255,0.08);
}
"""
css = css + dashboard_css

# 6. Map and Layer Filter Bar inside Center Panel
css = re.sub(r'\/\* ---- LAYER FILTER BAR ---- \*\/\n\.layer-filter-bar \{.*?\n\}', '/* ---- LAYER FILTER BAR ---- */\n.layer-filter-bar {\n    position: absolute;\n    top: 1rem;\n    left: 1rem;\n    z-index: 450;\n    display: flex;\n    gap: 0.4rem;\n}', css, flags=re.DOTALL)
css = css.replace('.layer-pill {\n    background: rgba(255, 255, 255, 0.05);\n', '.layer-pill {\n    background: rgba(15, 23, 42, 0.8);\n    backdrop-filter: blur(8px);\n')

# 7. Live Feed Panel
css = re.sub(r'\.live-feed-panel \{.*?\n\}', '.live-feed-panel {\n    display: flex;\n    flex-direction: column;\n    height: 100%;\n    background: var(--bg-card);\n    border: 1px solid rgba(255,255,255,0.08);\n    border-radius: 12px;\n    overflow: hidden;\n}', css, flags=re.DOTALL)

# 8. Bottom Camera Feeds
css = css.replace('.camera-strip {\n    position: absolute;\n    bottom: 35px;\n    left: 50%;\n    transform: translateX(-50%);\n    z-index: 400;\n    display: flex;\n    gap: 1rem;\n    width: 95%;\n    justify-content: center;\n    pointer-events: none;\n}', '.camera-strip {\n    display: flex;\n    gap: 1rem;\n    overflow-x: auto;\n    padding-bottom: 0.5rem;\n}')
css = css + """
.dashboard-bottom {
    padding: 0 1.5rem 1rem 1.5rem;
    flex-shrink: 0;
}
.bottom-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
}
.bottom-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-bright);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.view-all {
    color: var(--cyan);
    font-size: 0.75rem;
    text-decoration: none;
    display: flex;
    align-items: center;
}
"""

# 9. OSINT Ticker
css = re.sub(r'\.osint-ticker-strip \{.*?\n\}', '.osint-ticker-strip {\n    background: #060a14;\n    border-top: 1px solid var(--border-dim);\n    display: flex;\n    align-items: center;\n    padding: 0.4rem 1.5rem;\n    font-family: var(--font-mono);\n    font-size: 0.65rem;\n    color: var(--text-secondary);\n    flex-shrink: 0;\n}', css, flags=re.DOTALL)
css = css.replace('.ticker-label {\n    background: rgba(6, 182, 212, 0.15);\n    color: var(--cyan);\n', '.ticker-label {\n    color: var(--text-bright);\n    display: flex;\n    align-items: center;\n    gap: 0.4rem;\n')
css = css.replace('.ticker-content {\n    display: flex;\n    gap: 3rem;\n    white-space: nowrap;\n    animation: tickerScroll 25s linear infinite;\n}', '.ticker-content {\n    display: flex;\n    gap: 2rem;\n    margin-left: 2rem;\n    flex: 1;\n}')
css = css + "\\n.ticker-dot { width: 6px; height: 6px; background: var(--low); border-radius: 50%; }\\n.ticker-right { color: var(--text-muted); }\\n"

with open('d:/SIH FINAL/prototype-simple/styles.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("CSS updated successfully")
