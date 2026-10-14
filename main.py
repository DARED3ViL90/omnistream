"""
OmniStream 🌍 - Worldwide Multi-Audio Stremio Addon (Production Cloud Edition)
Powered by open decentralized torrent networks (zero Cloudflare blocks).
Features Smart Priority Sorting: 🇮🇳 Hindi & 🌐 Multi-Audio on top, followed by 4K/UHD Original Audio.
"""

import os
import re
import urllib.parse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import httpx

app = FastAPI(title="OmniStream Addon", version="2.1.0")

# 1. Enable Wildcard CORS for Stremio Web and Native Apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Addon Manifest
MANIFEST = {
    "id": "community.omnistream.core",
    "version": "2.1.0",
    "name": "OmniStream 🌍 (Multi-Audio)",
    "description": "Universal High-Speed Multi-Audio Streaming Provider with Smart Audio Prioritization & 4K UHD Support.",
    "logo": "https://omnistream-jpp5.onrender.com/logo.png",
    "background": "https://images.metahub.space/background/medium/tt22084616/img",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "catalogs": [],
    "idPrefixes": ["tt"],
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


@app.get("/")
@app.get("/manifest.json")
def get_manifest():
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(content=MANIFEST, headers=headers)


@app.get("/logo.png")
def get_logo():
    if os.path.exists("logo.png"):
        return FileResponse("logo.png", media_type="image/png")
    elif os.path.exists(r"C:\Users\AVITA\omnistream_global_logo.png"):
        return FileResponse(r"C:\Users\AVITA\omnistream_global_logo.png", media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "Logo not found"})


# 3. Smart Language Classifier & Flag Tagger
def classify_audio_and_priority(title: str, seeders: int) -> tuple[str, int]:
    t = title.lower()

    # Priority 1: Hindi / Bollywood / Desi Dubs
    hindi_keywords = ["hindi", "hin", "bollywood"]
    if any(k in t for k in hindi_keywords):
        return "🇮🇳 [Hindi Dubbed / Multi Audio]", 100000 + seeders

    # Priority 2: Multi-Audio / Dual Audio
    multi_keywords = ["multi audio", "multi-audio", "dual audio", "dual-audio", "multi"]
    if any(k in t for k in multi_keywords):
        return "🌐 [Multi-Audio Pack]", 80000 + seeders

    # Priority 3: Japanese / Anime
    jap_keywords = ["japanese", "jap", "subbed"]
    if any(k in t for k in jap_keywords):
        return "🇯🇵 [Japanese / Anime]", 60000 + seeders

    # Priority 4: Korean
    kor_keywords = ["korean", "kor"]
    if any(k in t for k in kor_keywords):
        return "🇰🇷 [Korean Audio]", 50000 + seeders

    # Priority 5: Spanish
    span_keywords = ["spanish", "castellano", "latino", "esp"]
    if any(k in t for k in span_keywords):
        return "🇪🇸 [Spanish Audio]", 40000 + seeders

    # Priority 6: French
    french_keywords = ["french", "vf", "vostfr", "fra"]
    if any(k in t for k in french_keywords):
        return "🇫🇷 [French Audio]", 30000 + seeders

    # Priority 7: German
    german_keywords = ["german", "ger", "deutsch"]
    if any(k in t for k in german_keywords):
        return "🇩🇪 [German Audio]", 20000 + seeders

    return "🇺🇸 [English / Original]", 10000 + seeders


def format_bytes(size_bytes: int) -> str:
    try:
        val = int(size_bytes)
        if val >= 1024 ** 3:
            return f"{val / (1024 ** 3):.2f} GB"
        elif val >= 1024 ** 2:
            return f"{val / (1024 ** 2):.1f} MB"
        return f"{val} B"
    except Exception:
        return "Unknown Size"


def detect_quality(title: str) -> str:
    t = title.upper()
    if "2160P" in t or "4K" in t or "UHD" in t:
        return "4K UHD 🌟"
    elif "1080P" in t or "FHD" in t:
        return "1080p FHD ⚡"
    elif "720P" in t or "HD" in t:
        return "720p HD 📺"
    return "HDRip 🎬"


# 4. Stream Route with Cloudflare-Free Torrent Scraping
@app.get("/stream/{type}/{imdb_id}.json")
async def get_streams(type: str, imdb_id: str):
    print(f"\n=======================================================")
    print(f"[+] OmniStream Query: {type.upper()} | ID: {imdb_id}")

    parts = imdb_id.split(":")
    base_imdb = parts[0]
    season = int(parts[1]) if len(parts) >= 2 else None
    episode = int(parts[2]) if len(parts) >= 3 else None

    # Step 1: Resolve Title from Cinemeta
    title_name = ""
    year = ""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            cinemeta_url = f"https://v3-cinemeta.strem.io/meta/{type}/{base_imdb}.json"
            meta_res = await client.get(cinemeta_url, headers={"User-Agent": USER_AGENT})
            if meta_res.status_code == 200:
                meta_data = meta_res.json().get("meta", {})
                title_name = meta_data.get("name", "")
                year = meta_data.get("year", "")
                print(f"[+] Resolved Title: '{title_name}' ({year})")
        except Exception as e:
            print(f"[-] Cinemeta error: {e}")

    # Build targeted search queries
    search_queries = []
    if title_name:
        clean_title = re.sub(r"[^\w\s]", " ", title_name).strip()
        if type == "series" and season is not None:
            if episode is not None:
                search_queries.append(f"{clean_title} S{season:02d}E{episode:02d}")
            search_queries.append(f"{clean_title} S{season:02d}")
            search_queries.append(f"{clean_title} Hindi")
        else:
            search_queries.append(f"{clean_title} Hindi")
            search_queries.append(f"{clean_title} Dual Audio")
            search_queries.append(f"{clean_title}")
    else:
        search_queries.append(base_imdb)

    # Step 2: Fetch Torrents from Cloudflare-Free Network
    raw_torrents = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for q in search_queries[:3]:
            try:
                encoded = urllib.parse.quote(q)
                url = f"https://torrents-csv.com/service/search?q={encoded}"
                resp = await client.get(url, headers={"User-Agent": USER_AGENT})
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("torrents", [])
                    print(f"    -> Query '{q}' returned {len(items)} torrents.")
                    for item in items:
                        ih = item.get("infohash", "").strip().lower()
                        if ih and ih not in raw_torrents:
                            raw_torrents[ih] = item
            except Exception as e:
                print(f"[-] Search query error for '{q}': {e}")

    print(f"[+] Total unique torrents collected: {len(raw_torrents)}")

    # Step 3: Classify Language & Calculate Smart Priority
    streams = []
    for ih, item in raw_torrents.items():
        name = item.get("name", "Unknown Release")
        seeders = int(item.get("seeders", 0))
        size_bytes = int(item.get("size_bytes", 0))

        audio_badge, priority_score = classify_audio_and_priority(name, seeders)
        quality = detect_quality(name)
        size_str = format_bytes(size_bytes)

        stream_obj = {
            "name": f"OmniStream 🌍\n{quality}",
            "title": f"🎬 {name}\n{audio_badge}\n💾 {size_str}  •  ⚡ Seeders: {seeders}",
            "infoHash": ih,
            "fileIdx": 0,
            "_priority": priority_score,
        }
        streams.append(stream_obj)

    # Step 4: Sort by Smart Priority (Hindi 1st, Multi 2nd, Original 3rd)
    streams.sort(key=lambda x: x["_priority"], reverse=True)

    for s in streams:
        del s["_priority"]

    # Top 30 highest-ranked streams
    streams = streams[:30]

    print(f"[+] Returning {len(streams)} Verified Ranked Streams (Hindi on Top)!")
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(content={"streams": streams}, headers=headers)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
