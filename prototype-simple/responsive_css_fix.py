import os

css_file_path = 'd:/SIH FINAL/prototype-simple/styles.css'

with open(css_file_path, 'r', encoding='utf-8') as f:
    css_content = f.read()

# Only append if not already there
if "@media (max-width: 1400px)" not in css_content:
    responsive_css = """
/* ---- RESPONSIVE FIXES FOR SMALLER LAPTOPS ---- */
@media (max-width: 1400px) {
    /* Allow scrolling instead of hiding overflows when things squish */
    .app-container {
        height: auto;
        min-height: 100vh;
    }
    .main-content {
        height: auto;
        min-height: 100vh;
        overflow-y: auto;
        overflow-x: hidden;
    }
    
    /* Make the top bar wrap if text gets too long */
    .top-bar {
        flex-wrap: wrap;
        padding: 1rem 1.5rem 0.5rem 1.5rem;
    }
    
    /* Wrap the KPI strip so cards don't squish */
    .kpi-strip {
        flex-wrap: wrap;
        margin-bottom: 0.5rem;
    }
    
    /* Allow the main grid to wrap its panels */
    .dashboard-core {
        flex-wrap: wrap;
        flex: none;
        height: auto;
    }
    
    /* Instead of fixed widths that crush the map, allow panels to take full width when space is tight */
    .left-panel {
        width: 100%;
        flex: none;
        height: 450px;
        margin-bottom: 1rem;
    }
    
    .center-panel {
        width: 100%;
        flex: none;
        height: 500px;
        margin-bottom: 1rem;
    }
    
    .intel-panel {
        width: 100%;
        flex: none;
        height: 400px;
    }
    
    /* Sidebar adjustments for small screens */
    .sidebar {
        width: 200px;
        padding: 1rem 0;
    }
    
    /* Ensure the camera strip allows scrolling and images fit */
    .camera-feed {
        flex: 0 0 280px;
    }
}
"""
    with open(css_file_path, 'a', encoding='utf-8') as f:
        f.write(responsive_css)
    print("Responsive CSS media queries added successfully.")
else:
    print("Media queries already present.")
