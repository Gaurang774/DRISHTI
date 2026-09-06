import re

with open('d:/SIH FINAL/prototype-simple/styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Fix Sidebar Logo
css = css.replace('.logo-text-main {\\n    font-size: 1.1rem;\\n    font-weight: 800;\\n    color: var(--text-bright);\\n    letter-spacing: 1px;\\n}', '.logo-text-main {\\n    font-size: 1.25rem;\\n    font-weight: 800;\\n    color: var(--text-bright);\\n    letter-spacing: 1.5px;\\n    line-height: 1;\\n}')
css = css.replace('.logo-text-sub {\\n    font-size: 0.6rem;\\n    color: var(--text-muted);\\n}', '.logo-text-sub {\\n    font-size: 0.6rem;\\n    color: var(--text-muted);\\n    margin-top: 2px;\\n}')
css = css.replace('.logo {\\n    display: flex;\\n    align-items: center;\\n    gap: 0.75rem;\\n    padding: 0 1.25rem;\\n    margin-bottom: 2rem;\\n}', '.logo {\\n    display: flex;\\n    align-items: center;\\n    gap: 0.75rem;\\n    padding: 0 1.25rem;\\n    margin-bottom: 2rem;\\n    width: 100%;\\n}')
css = css.replace('.logo-icon {\\n    font-size: 1.8rem;\\n    color: var(--cyan);\\n    filter: drop-shadow(0 0 8px var(--cyan-glow));\\n    animation: logoPulse 3s ease-in-out infinite;\\n}', '.logo-icon {\\n    font-size: 2.2rem;\\n    color: var(--cyan);\\n    filter: drop-shadow(0 0 8px var(--cyan-glow));\\n}')

# Fix Sidebar Active Tab text color
css = css.replace('.nav-links li.active {\\n    color: var(--text-bright);\\n    background: var(--cyan);\\n    box-shadow: 0 4px 12px rgba(6,182,212,0.3);\\n}', '.nav-links li.active {\\n    color: var(--bg-void);\\n    background: var(--cyan);\\n    box-shadow: 0 4px 12px rgba(6,182,212,0.3);\\n    font-weight: 700;\\n}')

# Fix Camera feeds scaling
css = css.replace('.camera-strip {\\n    display: flex;\\n    gap: 1rem;\\n    overflow-x: auto;\\n    padding-bottom: 0.5rem;\\n}', '.camera-strip {\\n    display: flex;\\n    gap: 1rem;\\n    overflow-x: auto;\\n    padding-bottom: 0.5rem;\\n    height: 220px;\\n}')
css = css.replace('.camera-feed {\\n    position: relative;\\n    width: 320px;\\n    height: 180px;\\n', '.camera-feed {\\n    position: relative;\\n    flex: 0 0 320px;\\n    height: 100%;\\n    display: flex;\\n    flex-direction: column;\\n')
css = css.replace('.cam-view {\\n    position: absolute;\\n    top: 24px; left: 0; right: 0; bottom: 22px;\\n    overflow: hidden;\\n}', '.cam-view {\\n    flex: 1;\\n    position: relative;\\n    overflow: hidden;\\n    min-height: 0;\\n}')
css = css.replace('.cam-img {\\n    width: 100%;\\n    height: 100%;\\n    object-fit: cover;\\n}', '.cam-img {\\n    width: 100%;\\n    height: 100%;\\n    object-fit: cover;\\n    display: block;\\n}')
css = css.replace('.cam-header {\\n    position: absolute;\\n    top: 0; left: 0; right: 0;\\n', '.cam-header {\\n    position: relative;\\n    top: auto; left: auto; right: auto;\\n')
css = css.replace('.cam-footer {\\n    position: absolute;\\n    bottom: 0; left: 0; right: 0;\\n', '.cam-footer {\\n    position: relative;\\n    bottom: auto; left: auto; right: auto;\\n')

# Fix layer filters in map
css = css.replace('.layer-filter-bar {\\n    position: absolute;\\n    top: 1rem;\\n    left: 1rem;\\n    z-index: 450;\\n    display: flex;\\n    gap: 0.4rem;\\n}', '.layer-filter-bar {\\n    position: absolute;\\n    top: 1rem;\\n    left: 1rem;\\n    z-index: 450;\\n    display: flex;\\n    gap: 0.4rem;\\n    flex-wrap: wrap;\\n}')

with open('d:/SIH FINAL/prototype-simple/styles.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("CSS styling fixes applied")
