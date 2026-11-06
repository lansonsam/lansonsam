"""Generate the visual-novel style profile images (light + dark):

  header-{theme}.svg   dialogue scene with today's anime character
  status-{theme}.svg   RPG-like status panel with live GitHub numbers
  quest-{n}-{theme}.svg  three project cards

Usage: python scripts/profile_gen.py <out_dir>
Env:   GITHUB_TOKEN (optional, raises API limits and enables the contribution count)
"""
import base64
import datetime as dt
import html
import io
import json
import os
import sys
import urllib.request

USER = "lansonsam"
TOKEN = os.environ.get("GITHUB_TOKEN")
UA = "lansonsam-profile-readme"

# ---- content you may want to edit -------------------------------------------
LINES = [
    "「今天也在把东西拆开，看看它是怎么运转的。」",
    "「逆向、网络、小工具——一点一点打磨。」",
    "「如果你也喜欢折腾，就留下一颗星吧。」",
]
CLASS = "Reverse Engineer"
SKILLS = [("逆向", 82), ("网络", 74), ("工具", 66), ("二次元", 90)]
QUESTS = [
    ("TrollStore-roothide", "TrollStore Lite for roothide · iOS 17"),
    ("anylink", "SSL VPN server, AnyConnect compatible"),
    ("fuwari", "My personal blog, built on Astro"),
]
# ------------------------------------------------------------------------------

P = {
    "light": dict(bg1="#F7F6FA", bg2="#ECE9F3", line="#DCD8E6", accent="#B4A9D6", accent2="#8C7DBA",
                  text="#4B4858", sub="#8E8AA0", box="#FFFFFF", box_op=".80", bokeh="#C9BFE6",
                  track="#E6E2EF", tag_text="#FFFFFF", blend="multiply"),
    "dark": dict(bg1="#1C1B22", bg2="#141319", line="#2E2B38", accent="#B7ABD9", accent2="#9A8AC8",
                 text="#E7E4EF", sub="#8C88A0", box="#221F2B", box_op=".85", bokeh="#5E527F",
                 track="#2C2937", tag_text="#17161C", blend="normal"),
}
FONT = "'Noto Sans SC','PingFang SC','Microsoft YaHei','Segoe UI','Inter','Helvetica Neue',Arial,sans-serif"
E = html.escape


def req(url, data=None):
    h = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if TOKEN and "api.github.com" in url:
        h["Authorization"] = f"Bearer {TOKEN}"
    r = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(r, timeout=30) as resp:
        return resp.read()


def github_stats():
    s = {"repos": "—", "stars": "—", "followers": "—", "contrib": "—", "lv": 1, "days": 0, "repo_stars": {}}
    try:
        u = json.loads(req(f"https://api.github.com/users/{USER}"))
        created = dt.datetime.fromisoformat(u["created_at"].replace("Z", "+00:00"))
        now = dt.datetime.now(dt.timezone.utc)
        s["days"] = (now - created).days
        s["lv"] = max(1, s["days"] // 365)
        s["followers"] = u["followers"]
        repos = json.loads(req(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner"))
        s["repos"] = u["public_repos"]
        s["stars"] = sum(r["stargazers_count"] for r in repos)
        s["repo_stars"] = {r["name"]: r["stargazers_count"] for r in repos}
    except Exception as e:  # keep going with placeholders
        print("stats error:", e)
    if TOKEN:
        try:
            q = {"query": 'query{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions}}}}' % USER}
            d = json.loads(req("https://api.github.com/graphql", json.dumps(q).encode()))
            s["contrib"] = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
        except Exception as e:
            print("contrib error:", e)
    return s


def anime():
    try:
        from PIL import Image, ImageEnhance, ImageStat
        # Fetch several candidates and keep the palest / least saturated one so it
        # sits well on the lavender-gray palette.
        results = json.loads(req("https://nekos.best/api/v2/neko?amount=8"))["results"]
        best = None
        for m in results:
            try:
                im = Image.open(io.BytesIO(req(m["url"]))).convert("RGB")
            except Exception:
                continue
            _, s, v = ImageStat.Stat(im.resize((64, 96)).convert("HSV")).mean
            score = v - 1.4 * s
            if best is None or score > best[0]:
                best = (score, m, im)
        _, meta, img = best
        img = ImageEnhance.Color(img).enhance(0.82)
        w = 540
        h = round(img.height * w / img.width)
        img = img.resize((w, h), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=84, optimize=True, progressive=True)
        print("anime:", meta["url"], meta.get("artist_name"), meta.get("source_url"))
        return dict(b64=base64.b64encode(buf.getvalue()).decode(), w=w, h=h,
                    artist=meta.get("artist_name") or "unknown", meta=meta)
    except Exception as e:
        print("anime error:", e)
        return None


def text_width(s, size):
    return sum(size if ord(c) > 0x2E7F else size * 0.56 for c in s)


def roman(n):
    out = ""
    for v, r in ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out += r
            n -= v
    return out


# ---------------------------------------------------------------- header -----
def header(t, art, st, today):
    p = P[t]
    W, H = 1200, 420
    slot, size = 6.0, 22
    dur = slot * len(LINES)

    lines_svg = []
    for i, line in enumerate(LINES):
        w = text_width(line, size) + 14
        typing = min(len(line) * 0.09, slot * 0.6)
        a = i * slot / dur
        b = (i * slot + typing) / dur
        c = ((i + 1) * slot - 0.3) / dur
        c2 = min(c + 0.0005, 1)
        kt = ";".join(f"{x:.4f}" for x in (0, a, b, c, c2, 1))
        lines_svg.append(f'''
    <clipPath id="t{i}"><rect x="84" y="312" height="44" width="0">
      <animate attributeName="width" dur="{dur}s" repeatCount="indefinite" values="0;0;{w:.0f};{w:.0f};0;0" keyTimes="{kt}"/>
    </rect></clipPath>
    <text clip-path="url(#t{i})" x="88" y="343" font-size="{size}" fill="{p['text']}" letter-spacing="1">{E(line)}</text>''')

    char = ""
    credit = ""
    if art:
        ix, iy = 660, -16
        char = f'''
  <g mask="url(#mv)"><g mask="url(#mh)">
    <image x="{ix}" y="{iy}" width="{art['w']}" height="{art['h']}" style="mix-blend-mode:{p['blend']}"{' filter="url(#dim)"' if t == 'dark' else ''}
      xlink:href="data:image/jpeg;base64,{art['b64']}"/>
  </g></g>'''
        credit = f'<text x="44" y="412" font-size="10" fill="{p["sub"]}" letter-spacing=".5" opacity=".8">illust. {E(art["artist"])} · nekos.best</text>'

    bokeh = "".join(
        f'<circle class="bk" style="animation-delay:{d}s" cx="{x}" cy="{y}" r="{r}" fill="{p["bokeh"]}" opacity="{o}"/>'
        for x, y, r, o, d in [(120, 210, 46, .18, 0), (330, 60, 22, .22, 1.5), (520, 190, 64, .12, 3),
                               (610, 70, 14, .3, .8), (250, 250, 10, .35, 2.2), (460, 110, 6, .5, 1.1)])
    sparkles = "".join(
        f'<path class="tw" style="animation-delay:{d}s" transform="translate({x} {y}) scale({s})" d="M0 -8 L1.6 -1.6 L8 0 L1.6 1.6 L0 8 L-1.6 1.6 L-8 0 L-1.6 -1.6 Z" fill="{p["accent"]}"/>'
        for x, y, s, d in [(580, 46, .9, 0), (420, 170, .6, 1.3), (160, 140, .7, 2.6), (640, 230, .5, 3.4)])

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{USER}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{p['bg1']}"/><stop offset="1" stop-color="{p['bg2']}"/></linearGradient>
    <linearGradient id="gh" x1="0" x2="1"><stop offset="0" stop-color="#000"/><stop offset=".38" stop-color="#fff"/></linearGradient>
    <linearGradient id="gv" x1="0" y1="0" x2="0" y2="1"><stop offset=".72" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
    <radialGradient id="gr" cx=".56" cy=".42" r=".62"><stop offset=".45" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
    <mask id="mh"><rect x="660" y="0" width="540" height="{H}" fill="url(#{'gr' if t == 'dark' else 'gh'})"/></mask>
    <filter id="dim"><feComponentTransfer><feFuncR type="linear" slope=".86"/><feFuncG type="linear" slope=".85"/><feFuncB type="linear" slope=".9"/></feComponentTransfer></filter>
    <mask id="mv"><rect x="0" y="0" width="{W}" height="{H}" fill="url(#gv)"/></mask>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
  </defs>
  <style>
    text{{font-family:{FONT}}}
    .bk{{animation:float 9s ease-in-out infinite}}
    .tw{{opacity:0;animation:tw 4.5s ease-in-out infinite}}
    .nx{{animation:nx 1.2s ease-in-out infinite}}
    @keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-10px)}}}}
    @keyframes tw{{0%,100%{{opacity:0}}50%{{opacity:.9}}}}
    @keyframes nx{{0%,100%{{transform:translateY(0);opacity:.9}}50%{{transform:translateY(4px);opacity:.4}}}}
  </style>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    {bokeh}
    {sparkles}
    {char}
  </g>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="{p['line']}"/>

  <text x="56" y="70" font-size="12" letter-spacing="6" fill="{p['accent2']}">CHAPTER {roman(st['lv'])}</text>
  <text x="54" y="114" font-size="36" font-weight="300" fill="{p['text']}">Workshop Log</text>
  <text x="56" y="144" font-size="13" letter-spacing="2" fill="{p['sub']}">{today}  ·  DAY {st['days']}</text>
  {credit}

  <rect x="40" y="284" width="1120" height="112" rx="16" fill="{p['box']}" fill-opacity="{p['box_op']}" stroke="{p['line']}"/>
  <rect x="64" y="264" width="148" height="36" rx="10" fill="{p['accent']}"/>
  <text x="138" y="288" text-anchor="middle" font-size="16" font-weight="500" letter-spacing="1" fill="{p['tag_text']}">{USER}</text>
  {''.join(lines_svg)}
  <polygon class="nx" points="1122,366 1136,366 1129,375" fill="{p['accent2']}"/>
  <text x="1158" y="412" text-anchor="end" font-size="10" letter-spacing="3" fill="{p['sub']}" opacity=".8">AUTO    SKIP    LOG    SAVE</text>
</svg>'''


# ---------------------------------------------------------------- status -----
def status(t, st):
    p = P[t]
    W, H = 1200, 250
    bars = []
    for i, (name, v) in enumerate(SKILLS):
        y = 132 + i * 30
        bw = 400 * v / 100
        bars.append(f'''
  <text x="48" y="{y+5}" font-size="14" fill="{p['sub']}">{E(name)}</text>
  <rect x="128" y="{y}" width="400" height="4" rx="2" fill="{p['track']}"/>
  <rect x="128" y="{y}" width="0" height="4" rx="2" fill="{p['accent']}">
    <animate attributeName="width" from="0" to="{bw:.0f}" dur="1.4s" begin="{0.2 + i*0.15:.2f}s" fill="freeze" calcMode="spline" keySplines=".2 .8 .2 1" keyTimes="0;1"/>
  </rect>
  <text x="560" y="{y+5}" text-anchor="end" font-size="12" fill="{p['sub']}">{v}</text>''')
    boxes = []
    items = [("REPOS", "仓库", st["repos"]), ("STARS", "星标", st["stars"]),
             ("FOLLOWERS", "关注者", st["followers"]), ("CONTRIBUTIONS", "今年贡献", st["contrib"])]
    for i, (en, zh, val) in enumerate(items):
        x = 650 + (i % 2) * 260
        y = 110 + (i // 2) * 66
        boxes.append(f'''
  <text x="{x}" y="{y+14}" font-size="10" letter-spacing="3" fill="{p['sub']}">{en}  <tspan letter-spacing="1">{zh}</tspan></text>
  <text x="{x}" y="{y+46}" font-size="28" font-weight="300" fill="{p['text']}">{val}</text>''')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="status">
  <style>text{{font-family:{FONT}}}</style>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="{p['bg1']}" stroke="{p['line']}"/>
  <text x="48" y="54" font-size="12" letter-spacing="6" fill="{p['accent2']}">◇ STATUS</text>
  <text x="48" y="90" font-size="15" fill="{p['text']}">职业 <tspan fill="{p['sub']}" dx="8">{E(CLASS)}</tspan></text>
  <text x="{W-48}" y="64" text-anchor="end" font-size="40" font-weight="200" fill="{p['text']}"><tspan font-size="14" letter-spacing="3" fill="{p['accent2']}">LV.</tspan>{st['lv']}</text>
  <line x1="610" y1="112" x2="610" y2="222" stroke="{p['line']}"/>
  {''.join(bars)}
  {''.join(boxes)}
</svg>'''


# ----------------------------------------------------------------- quest -----
def quest(t, i, name, desc, stars):
    p = P[t]
    W, H = 380, 140
    star = f"★ {stars}" if stars != "" else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{E(name)}">
  <style>text{{font-family:{FONT}}}</style>
  <rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="{p['bg1']}" stroke="{p['line']}"/>
  <text x="28" y="40" font-size="11" letter-spacing="4" fill="{p['accent2']}">VOL.{i}</text>
  <text x="{W-28}" y="40" text-anchor="end" font-size="12" fill="{p['sub']}">{star}</text>
  <text x="28" y="78" font-size="20" font-weight="500" fill="{p['text']}">{E(name)}</text>
  <text x="28" y="104" font-size="13" fill="{p['sub']}">{E(desc)}</text>
  <rect x="28" y="120" width="24" height="2" rx="1" fill="{p['accent']}"/>
</svg>'''


def main(out):
    os.makedirs(out, exist_ok=True)
    st = github_stats()
    art = anime()
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime("%Y.%m.%d")
    files = {}
    for t in P:
        files[f"header-{t}.svg"] = header(t, art, st, today)
        files[f"status-{t}.svg"] = status(t, st)
        for i, (name, desc) in enumerate(QUESTS, 1):
            files[f"quest-{i}-{t}.svg"] = quest(t, i, name, desc, st["repo_stars"].get(name, ""))
    for name, content in files.items():
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(content)
    if art:
        with open(os.path.join(out, "anime.json"), "w", encoding="utf-8") as f:
            json.dump(art["meta"], f, ensure_ascii=False, indent=2)
    print("wrote", len(files), "files to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist")
