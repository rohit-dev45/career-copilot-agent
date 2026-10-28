"""Regenerate README visuals from real CLI output on sample data.

Usage: python docs/make_assets.py   (after running the `shortlist` and `post` commands)
All outputs are SVG so they stay text-diffable; raster slides are embedded as JPEG data URIs.
"""
import base64, csv, io, subprocess, sys
from html import escape
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
BG, PANEL, LINE, TXT, MUTED = "#0b1120", "#111a2e", "#1e293b", "#e2e8f0", "#94a3b8"
SKY, VIO, EMR, AMB = "#38bdf8", "#a78bfa", "#34d399", "#fbbf24"
SANS = "Inter, Segoe UI, DejaVu Sans, Arial, sans-serif"
MONO = "JetBrains Mono, Consolas, DejaVu Sans Mono, monospace"


def shortlist_output():
    r = subprocess.run([sys.executable, "-m", "career_copilot", "shortlist", "--jobs",
                        "data/sample_jobs.json", "--tracker", "/tmp/cc-demo-tracker.csv"],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:  # older CLI without --tracker
        r = subprocess.run([sys.executable, "-m", "career_copilot", "shortlist", "--jobs",
                            "data/sample_jobs.json"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout.replace("/tmp/cc-demo-tracker.csv", "output/job-tracker.csv").rstrip().splitlines()


def color_for(line):
    if "prepare-application" in line: return EMR
    if "human-review" in line: return AMB
    if line.strip().startswith("- ") and "skip" in line: return "#f87171"
    if "missing:" in line: return MUTED
    if line.startswith("#"): return SKY
    return TXT


def terminal(lines, cmd, w=980, anim=False):
    lh, top = 26, 92
    h = top + lh * (len(lines) + 1) + 30
    rows = [f'<text x="28" y="{top}" fill="{EMR}">$</text><text x="48" y="{top}" fill="{TXT}">{escape(cmd)}</text>']
    for i, ln in enumerate(lines, 1):
        style = f' class="ln" style="animation-delay:{0.6 + i*0.35:.2f}s"' if anim else ""
        rows.append(f'<text x="28" y="{top + i*lh}" fill="{color_for(ln)}" xml:space="preserve"{style}>{escape(ln)}</text>')
    css = ('<style>.ln{opacity:0;animation:in .3s forwards}@keyframes in{to{opacity:1}}</style>' if anim else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{css}'
            f'<rect width="{w}" height="{h}" rx="14" fill="{BG}" stroke="{LINE}"/>'
            f'<rect width="{w}" height="44" rx="14" fill="{PANEL}"/><rect y="30" width="{w}" height="14" fill="{PANEL}"/>'
            + "".join(f'<circle cx="{26+i*22}" cy="22" r="7" fill="{c}"/>' for i, c in enumerate(["#f87171", AMB, EMR]))
            + f'<text x="{w/2}" y="27" text-anchor="middle" font-family="{SANS}" font-size="14" fill="{MUTED}">career-copilot-agent — bash</text>'
            f'<g font-family="{MONO}" font-size="16">{"".join(rows)}</g></svg>')


def thumb(path, width=300):
    im = Image.open(path).convert("RGB")
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=80, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


def slide_grid(slides):
    tw, gap = 300, 24
    imgs = [thumb(p, tw) for p in slides]
    th = imgs[0][1][1]
    n = len(imgs); w = gap + n * (tw + gap); h = th + 2 * gap + 40
    parts = [f'<rect width="{w}" height="{h}" rx="16" fill="{BG}"/>']
    for i, (uri, _) in enumerate(imgs):
        x = gap + i * (tw + gap)
        parts.append(f'<rect x="{x-2}" y="{gap-2}" width="{tw+4}" height="{th+4}" rx="10" fill="{LINE}"/>'
                     f'<image x="{x}" y="{gap}" width="{tw}" height="{th}" href="{uri}"/>'
                     f'<text x="{x + tw/2}" y="{h-18}" text-anchor="middle" font-family="{SANS}" font-size="15" fill="{MUTED}">slide-{i+1}.png</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(parts)}</svg>'


def tracker_table(path):
    rows = list(csv.reader(open(path, newline="")))
    cols = [0, 1, 2, 4, 5, 6]
    widths = [165, 170, 250, 70, 190, 160]
    rh, w = 40, sum(widths) + 40
    h = 70 + rh * len(rows) + 20
    out = [f'<rect width="{w}" height="{h}" rx="14" fill="{BG}" stroke="{LINE}"/>',
           f'<text x="20" y="38" font-family="{SANS}" font-size="18" font-weight="700" fill="{TXT}">output/job-tracker.csv</text>']
    for r, row in enumerate(rows):
        y = 60 + r * rh
        fill = PANEL if r == 0 else (BG if r % 2 else "#0f172a")
        out.append(f'<rect x="20" y="{y}" width="{w-40}" height="{rh}" fill="{fill}"/>')
        x = 30
        for c, wd in zip(cols, widths):
            val = row[c]; col = SKY if r == 0 else TXT
            if r and c == 5: col = color_for(val) if val != "skip" else "#f87171"
            bold = ' font-weight="700"' if r == 0 else ""
            out.append(f'<text x="{x}" y="{y+26}" font-family="{MONO}" font-size="14" fill="{col}"{bold}>{escape(val)}</text>')
            x += wd
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(out)}</svg>'


def flowchart():
    W, H = 1200, 640
    lanes = [
        ("Jobs", SKY, ["Sample listings", "Score 0–100", "Verify live", "job-tracker.csv"], [False]*4),
        ("Content", VIO, ["Research", "Fact-check gate", "Caption", "Slides", "PDF", "Human approval", "Scheduler"],
         [False, False, False, False, False, True, False]),
        ("Networking", EMR, ["Draft notes", "Length check", "Human sends", "networking-log.csv"], [False, False, True, False]),
    ]
    out = [f'<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
           f'<path d="M0,0L10,5L0,10z" fill="{MUTED}"/></marker></defs>',
           f'<rect width="{W}" height="{H}" rx="20" fill="{BG}"/>',
           f'<text x="40" y="56" font-family="{SANS}" font-size="28" font-weight="800" fill="{TXT}">How the pipelines flow</text>',
           f'<text x="40" y="84" font-family="{SANS}" font-size="15" fill="{MUTED}">Dashed amber = a human step. Nothing is applied, posted or sent automatically.</text>']
    y = 120
    for name, col, steps, human in lanes:
        lh = 150
        out.append(f'<rect x="30" y="{y}" width="{W-60}" height="{lh}" rx="16" fill="{PANEL}" stroke="{col}" stroke-opacity=".35"/>'
                   f'<rect x="30" y="{y}" width="8" height="{lh}" rx="4" fill="{col}"/>'
                   f'<text x="60" y="{y+34}" font-family="{SANS}" font-size="18" font-weight="700" fill="{col}">{name}</text>')
        n = len(steps); avail = W - 120; bw = min(190, (avail - (n-1)*26) / n); gap = (avail - n*bw) / (n-1)
        for i, s in enumerate(steps):
            x = 60 + i * (bw + gap); by = y + 60
            stroke = f'stroke="{AMB}" stroke-dasharray="6 4" stroke-width="2"' if human[i] else f'stroke="{col}" stroke-width="1.5"'
            out.append(f'<rect x="{x:.0f}" y="{by}" width="{bw:.0f}" height="56" rx="12" fill="{BG}" {stroke}/>'
                       f'<text x="{x+bw/2:.0f}" y="{by+34}" text-anchor="middle" font-family="{SANS}" font-size="{15 if bw>140 else 14}" '
                       f'font-weight="600" fill="{AMB if human[i] else TXT}">{escape(s)}</text>')
            if i < n-1:
                out.append(f'<line x1="{x+bw+4:.0f}" y1="{by+28}" x2="{x+bw+gap-4:.0f}" y2="{by+28}" stroke="{MUTED}" stroke-width="2" marker-end="url(#a)"/>')
        y += lh + 22
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(out)}</svg>'


def banner():
    W, H = 1280, 360
    chips = ["Score jobs", "Verify live", "Fact-check", "Carousel PNG + PDF", "Human-in-the-loop"]
    x, cs = 80, []
    for c in chips:
        cw = 22 + len(c) * 10.5
        cs.append(f'<rect x="{x}" y="250" width="{cw:.0f}" height="40" rx="20" fill="{PANEL}" stroke="{SKY}" stroke-opacity=".5"/>'
                  f'<text x="{x+cw/2:.0f}" y="276" text-anchor="middle" font-family="{SANS}" font-size="17" fill="{TXT}">{c}</text>')
        x += cw + 14
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1120"/>'
            f'<stop offset="1" stop-color="#1e1b4b"/></linearGradient><linearGradient id="t" x1="0" x2="1">'
            f'<stop offset="0" stop-color="{SKY}"/><stop offset="1" stop-color="{VIO}"/></linearGradient></defs>'
            f'<rect width="{W}" height="{H}" rx="24" fill="url(#g)"/>'
            f'<circle cx="1120" cy="80" r="180" fill="{VIO}" opacity=".10"/><circle cx="1180" cy="300" r="120" fill="{SKY}" opacity=".10"/>'
            f'<text x="80" y="140" font-family="{SANS}" font-size="64" font-weight="800" fill="url(#t)">Career Copilot Agent</text>'
            f'<text x="82" y="195" font-family="{SANS}" font-size="24" fill="{TXT}">A human-in-the-loop pipeline for job search and LinkedIn content</text>'
            f'{"".join(cs)}</svg>')


def demo(lines, slides):
    """Animated SVG: terminal types out, then the carousel slides cycle. Loops every 16 s."""
    W, H, T = 1000, 560, 16
    term_lines = []
    for i, ln in enumerate(lines):
        t0 = (0.8 + i * 0.45) / T * 100
        term_lines.append(f'<text x="30" y="{110 + i*26}" fill="{color_for(ln)}" xml:space="preserve" '
                          f'style="animation:l{i} {T}s infinite">{escape(ln)}</text>'
                          f'<style>@keyframes l{i}{{0%,{t0:.1f}%{{opacity:0}}{t0+1:.1f}%,46%{{opacity:1}}48%,100%{{opacity:0}}}}</style>')
    imgs = [thumb(p, 330)[0] for p in slides]
    sl = []
    k = len(imgs); seg = 50 / k
    for i, uri in enumerate(imgs):
        a = 50 + i*seg; b = a + seg
        sl.append(f'<style>@keyframes s{i}{{0%,{a:.1f}%{{opacity:0}}{a+1:.1f}%,{b:.1f}%{{opacity:1}}{min(b+1,100):.1f}%,100%{{opacity:0}}}}</style>'
                  f'<image x="{W/2-165}" y="80" width="330" height="412" href="{uri}" style="opacity:0;animation:s{i} {T}s infinite"/>')
    cap = (f'<style>@keyframes c1{{0%,47%{{opacity:1}}49%,100%{{opacity:0}}}}@keyframes c2{{0%,49%{{opacity:0}}51%,100%{{opacity:1}}}}</style>'
           f'<text x="{W/2}" y="530" text-anchor="middle" font-family="{SANS}" font-size="17" fill="{MUTED}" style="animation:c1 {T}s infinite">'
           f'1 · python -m career_copilot shortlist --jobs data/sample_jobs.json</text>'
           f'<text x="{W/2}" y="530" text-anchor="middle" font-family="{SANS}" font-size="17" fill="{MUTED}" style="opacity:0;animation:c2 {T}s infinite">'
           f'2 · python -m career_copilot post → output/post/slide-*.png + carousel.pdf</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" rx="16" fill="{BG}" stroke="{LINE}"/>'
            f'<rect width="{W}" height="44" rx="16" fill="{PANEL}"/><rect y="30" width="{W}" height="14" fill="{PANEL}"/>'
            + "".join(f'<circle cx="{26+i*22}" cy="22" r="7" fill="{c}"/>' for i, c in enumerate(["#f87171", AMB, EMR]))
            + f'<text x="{W/2}" y="27" text-anchor="middle" font-family="{SANS}" font-size="14" fill="{MUTED}">career-copilot-agent demo (sample data)</text>'
            f'<g font-family="{MONO}" font-size="16">{"".join(term_lines)}</g>{"".join(sl)}{cap}</svg>')


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    lines = shortlist_output()
    slides = sorted((ROOT / "output" / "post").glob("slide-*.png"))
    files = {
        "banner.svg": banner(),
        "workflow.svg": flowchart(),
        "shortlist-terminal.svg": terminal(lines, "python -m career_copilot shortlist --jobs data/sample_jobs.json"),
        "carousel-grid.svg": slide_grid(slides),
        "tracker-preview.svg": tracker_table(ROOT / "output" / "job-tracker.csv"),
        "demo.svg": demo(lines, slides),
    }
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"{name}: {len(svg)//1024} KB")
