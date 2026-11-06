"""Fetch one SFW anime illustration from nekos.best and wrap it in a small SVG card
with the artist credit. Output: dist/anime.svg (+ dist/anime.json for reference)."""
import base64
import html
import io
import json
import os
import sys
import urllib.request

from PIL import Image

API = "https://nekos.best/api/v2/neko"
WIDTH = 400  # rendered card width in px
UA = {"User-Agent": "lansonsam-profile-readme"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main(out_dir):
    meta = json.loads(get(API))["results"][0]
    img = Image.open(io.BytesIO(get(meta["url"]))).convert("RGB")
    h = round(img.height * WIDTH / img.width)
    img = img.resize((WIDTH, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=84, optimize=True, progressive=True)
    b64 = base64.b64encode(buf.getvalue()).decode()

    artist = html.escape(meta.get("artist_name") or "unknown artist")
    cap_h = 34
    total = h + cap_h
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {WIDTH} {total}" width="{WIDTH}" height="{total}">
  <defs><clipPath id="r"><rect width="{WIDTH}" height="{h}" rx="14"/></clipPath></defs>
  <style>
    .cap{{font-family:'Inter','Segoe UI','PingFang SC','Microsoft YaHei',Arial,sans-serif;font-size:12px;fill:#8B8F96;letter-spacing:.4px}}
    .img{{opacity:0;animation:in 1s ease-out forwards}}
    @keyframes in{{to{{opacity:1}}}}
  </style>
  <image class="img" clip-path="url(#r)" width="{WIDTH}" height="{h}" xlink:href="data:image/jpeg;base64,{b64}"/>
  <rect width="{WIDTH}" height="{h}" rx="14" fill="none" stroke="#8B8F96" stroke-opacity=".25"/>
  <text class="cap" x="{WIDTH // 2}" y="{h + 22}" text-anchor="middle">illustration · {artist} · via nekos.best</text>
</svg>'''
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "anime.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    with open(os.path.join(out_dir, "anime.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"ok: {meta['url']} by {meta.get('artist_name')} ({meta.get('source_url')})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dist")
