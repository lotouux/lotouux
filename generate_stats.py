#!/usr/bin/env python3
"""Gera assets/stats/stats.svg (painel TULIP // SYSTEM STATS) com dados públicos do GitHub.
Só usa a biblioteca padrão do Python. Variáveis de ambiente opcionais:
  GH_USER      (padrão: lotouux)
  GITHUB_TOKEN (aumenta o limite da API; no GitHub Actions já vem pronto)
  STATS_OUT    (padrão: assets/stats/stats.svg)
"""
import json, os, sys, urllib.request, urllib.error

USER = os.environ.get("GH_USER", "lotouux")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT = os.environ.get("STATS_OUT", "assets/stats/stats.svg")
FF = 'font-family="Courier New, monospace"'
BAR_COLORS = ["#F0A1C5", "#E98AB8", "#D87FAD", "#A982B8", "#A95E91"]


def api(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "tulip-os-stats"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.load(r)


def collect():
    user = api(f"https://api.github.com/users/{USER}")
    repos, page = [], 1
    while page <= 10:
        chunk = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += chunk
        if len(chunk) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]

    langs = {}
    for r in own:
        try:
            for name, size in api(r["languages_url"]).items():
                langs[name] = langs.get(name, 0) + size
        except urllib.error.URLError:
            pass

    commits = "--"
    try:
        commits = f'{api(f"https://api.github.com/search/commits?q=author:{USER}")["total_count"]:,}'
    except (urllib.error.URLError, KeyError):
        pass

    return {
        "commits": commits,
        "repos": str(user["public_repos"]),
        "followers": str(user["followers"]),
        "following": str(user["following"]),
        "joined": user["created_at"][:4],
        "langs": langs,
    }


def t(x, y, s, fill, size, bold=False, anchor="start"):
    b = ' font-weight="bold"' if bold else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}" {FF} font-size="{size}"{b}>{s}</text>'


def render(d):
    langs = sorted(d["langs"].items(), key=lambda kv: -kv[1])
    total = sum(v for _, v in langs) or 1
    top = [(n, 100 * v / total) for n, v in langs[:5]]
    tiles = [(d["commits"], "COMMITS"), (d["repos"], "REPOS"), (d["followers"], "FOLLOWERS"),
             (d["following"], "FOLLOWING"), (str(len(langs)), "LANGUAGES"), (d["joined"], "JOINED")]

    p = []
    # cabeçalho (igual ao inventário)
    p.append('<line x1="2" y1="57" x2="858" y2="57" stroke="#D87FAD" stroke-width="1.5"/>')
    for cx, col in ((26, "#D87FAD"), (47, "#A982B8"), (68, "#6E3A52")):
        p.append(f'<circle cx="{cx}" cy="29" r="6" fill="{col}"/>')
    p.append(f'<text x="430" y="35" text-anchor="middle" fill="#F0A1C5" {FF} font-size="17" font-weight="bold" letter-spacing="1.8">TULIP // SYSTEM STATS</text>')
    p.append(t(832, 35, "♥", "#D87FAD", 18, False, "middle"))

    # seção 01: métricas
    p.append(t(23, 82, "✦", "#E98AB8", 14, True))
    p.append(t(45, 82, "01 // ACTIVITY", "#E98AB8", 14, True))
    p.append(t(417, 82, f"[ {len(tiles)} METRICS ]", "#D8D8E0", 11, False, "end"))
    p.append('<line x1="45" y1="92" x2="417" y2="92" stroke="#6E3A52" stroke-width="1"/>')
    for i, (val, label) in enumerate(tiles):
        x = 37 + (i % 3) * 130
        y = 101 + (i // 3) * 88
        p.append(f'<rect x="{x}" y="{y}" width="116" height="78" rx="6" fill="#211B29" stroke="#8A4D69" stroke-width="1.3"/>')
        p.append(t(x + 58, y + 37, val, "#F0A1C5", 24, True, "middle"))
        p.append(t(x + 58, y + 60, label, "#E9A0C1", 9.5, True, "middle"))

    # seção 02: linguagens
    p.append(t(443, 82, "✦", "#E98AB8", 14, True))
    p.append(t(465, 82, "02 // TOP LANGUAGES", "#E98AB8", 14, True))
    p.append(t(837, 82, f"[ TOP {len(top)} ]", "#D8D8E0", 11, False, "end"))
    p.append('<line x1="465" y1="92" x2="837" y2="92" stroke="#6E3A52" stroke-width="1"/>')
    for i, (name, pct) in enumerate(top):
        y = 112 + i * 34
        p.append(t(465, y + 10, name.upper()[:11], "#E9A0C1", 11, True))
        filled = max(1, round(pct / 100 * 20))
        for s in range(20):
            col = BAR_COLORS[i % len(BAR_COLORS)] if s < filled else "#2B2233"
            p.append(f'<rect x="{560 + s * 12}" y="{y}" width="9" height="13" rx="2" fill="{col}"/>')
        p.append(t(837, y + 11, f"{pct:.1f}%", "#D8D8E0", 10.5, False, "end"))

    # divisórias e rodapé
    p.append('<line x1="430" y1="67" x2="430" y2="283" stroke="#8A4D69" stroke-width="1.2"/>')
    fy = 293
    p.append(f'<line x1="18" y1="{fy}" x2="842" y2="{fy}" stroke="#8A4D69" stroke-width="1"/>')
    p.append(f'<rect x="14" y="{fy+13}" width="6" height="6" fill="#D87FAD"/>')
    p.append(f'<rect x="22" y="{fy+21}" width="6" height="6" fill="#A982B8"/>')
    p.append(f'<rect x="14" y="{fy+29}" width="6" height="6" fill="#6E3A52"/>')
    p.append(t(42, fy + 29, "STATS STATUS: SYNCED // AUTO-UPDATED DAILY", "#E98AB8", 12))
    p.append(f'<line x1="540" y1="{fy+24}" x2="760" y2="{fy+24}" stroke="#8A4D69" stroke-width="1"/>')
    p.append(f'<rect x="775" y="{fy+9}" width="70" height="30" rx="15" fill="#17151D" stroke="#D87FAD" stroke-width="1.4"/>')
    p.append(f'<circle cx="791" cy="{fy+24}" r="4" fill="#28D989"/>')
    p.append(t(817, fy + 28, "ACTIVE", "#28D989", 10, False, "middle"))
    H = fy + 48

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{H}" viewBox="0 0 860 {H}" role="img" aria-label="TULIP OS GitHub stats">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="860" y2="{H}" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#111019"/><stop offset="100%" stop-color="#1D1722"/></linearGradient>
<linearGradient id="border" x1="0" y1="0" x2="860" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0%" stop-color="#D87FAD"/><stop offset="50%" stop-color="#A95E91"/><stop offset="100%" stop-color="#E99BC4"/></linearGradient>
</defs>
<rect x="1.5" y="1.5" width="857" height="{H-3}" rx="15" fill="url(#bg)" stroke="url(#border)" stroke-width="2.5"/>
{chr(10).join(p)}
</svg>
'''


def main():
    try:
        data = collect()
    except Exception as e:  # não gera arquivo quebrado: o workflow falha e nada é commitado
        print(f"erro ao coletar dados: {e}", file=sys.stderr)
        sys.exit(1)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(data))
    print("ok:", OUT, {k: v for k, v in data.items() if k != "langs"}, "| linguagens:", len(data["langs"]))


if __name__ == "__main__":
    main()
