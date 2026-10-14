"""
OmniStream 🌍 - Worldwide Multi-Audio Stremio Addon (Production Cloud Edition v2.4.0)
High-Capacity Global Aggregator with IMAX & 4K Remux Engine.
Priority Order:
1. 🇮🇳 [TamilMV / Hindi Dubbed] (Highest Seeders at Top)
2. 🌐 [Multi-Audio & Dual Audio Packs]
3. 🌌 [4K IMAX & 70GB+ Remux Dolby Vision Beasts]
4. 🇯🇵 [Anime / Japanese Dual Audio]
5. 🇺🇸 [Original High-Seeder 4K UHD Streams]
"""

import os
import re
import urllib.parse
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import httpx

from domain_watcher import refresh_verified_domains, get_domain

app = FastAPI(title="OmniStream Addon", version="2.4.0")

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
    "version": "2.4.0",
    "name": "OmniStream 🌍 (Multi-Audio)",
    "description": "Universal High-Speed Multi-Audio Streaming Provider with IMAX, 4K Remux & Smart Prioritization.",
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


@app.get("/domains")
async def get_domains():
    domains = await refresh_verified_domains()
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(content={"status": "online", "verified_domains": domains}, headers=headers)


# 3. Smart Language Classifier & Flag Tagger
def classify_audio_and_priority(title: str, seeders: int) -> tuple[str, int]:
    t = title.lower()

    # Special Detection: TamilMV Release
    is_tamilmv = "tamilmv" in t or "1tamilmv" in t

    # Priority 1: Hindi / Bollywood / TamilMV Hindi Dubs
    hindi_keywords = [
        "hindi", "hin", "bollywood", "dd5.1", "dd 5.1", "org dd",
        "worldfree4u", "vegamovies", "katmoviehd", "moviesmod", "hdhub",
        "tombdoc", "remuxdoc", "filmyzilla", "desiremovies", "bolly4u"
    ]
    if any(k in t for k in hindi_keywords) or (is_tamilmv and any(x in t for x in ["hin", "hindi", "multi"])):
        badge = "🇮🇳 [TamilMV / Hindi Dubbed]" if is_tamilmv else "🇮🇳 [Hindi Dubbed / Multi Audio]"
        return badge, 200000 + seeders

    # Priority 2: Multi-Audio / Dual Audio Packs
    multi_keywords = ["multi audio", "multi-audio", "dual audio", "dual-audio", "multi", "dual", "dubbed"]
    if any(k in t for k in multi_keywords):
        return "🌐 [Multi-Audio Pack]", 150000 + seeders

    # Priority 3: 4K IMAX / Massive Remux Beasts (Dolby Vision / Atmos)
    if "IMAX" in title.upper() or "REMUX" in title.upper():
        badge = "🌌 [4K IMAX Enhanced]" if "IMAX" in title.upper() else "💎 [4K UHD Remux Lossless]"
        return badge, 100000 + seeders

    # Priority 4: Japanese / Anime
    jap_keywords = ["japanese", "jap", "subbed"]
    if any(k in t for k in jap_keywords):
        return "🇯🇵 [Japanese / Anime]", 80000 + seeders

    # Priority 5: Korean
    kor_keywords = ["korean", "kor"]
    if any(k in t for k in kor_keywords):
        return "🇰🇷 [Korean Audio]", 60000 + seeders

    # Priority 6: Spanish / French / German
    if any(k in t for k in ["spanish", "latino", "esp"]):
        return "🇪🇸 [Spanish Audio]", 40000 + seeders
    if any(k in t for k in ["french", "vf", "vostfr"]):
        return "🇫🇷 [French Audio]", 30000 + seeders
    if any(k in t for k in ["german", "ger", "deutsch"]):
        return "🇩🇪 [German Audio]", 20000 + seeders

    # Default: Original / English Audio (Highest Seeders First)
    return "🇺🇸 [English / Original]", 50000 + seeders


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
    if "IMAX" in t:
        return "4K IMAX 🌌"
    elif "REMUX" in t:
        return "4K REMUX 💎"
    elif "2160P" in t or "4K" in t or "UHD" in t:
        return "4K UHD 🌟"
    elif "1080P" in t or "FHD" in t:
        return "1080p FHD ⚡"
    elif "720P" in t or "HD" in t:
        return "720p HD 📺"
    return "HDRip 🎬"


def clean_display_title(raw_title: str) -> str:
    """Removes ugly domain prefixes like 'www.1tamilmv.land - ' from stream titles."""
    cleaned = re.sub(
        r"^(?:https?://)?(?:www\.)?[a-zA-Z0-9\.\-]+\.(?:land|pm|ws|org|net|com|one|me|top|baby|xyz|solar|lat|click|lease|vip|in|cc|to)\s*[-_–:\s]\s*",
        "",
        raw_title,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


# 4. Stream Route with Global Torrent & IMAX Aggregation
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

    # Build targeted search queries (Including Year, Hindi, IMAX, Remux & 4K)
    search_queries = []
    if title_name:
        clean_title = " ".join(re.sub(r"[^\w\s]", " ", title_name).split())

        if type == "series" and season is not None:
            if episode is not None:
                search_queries.append(f"{clean_title} S{season:02d}E{episode:02d}")
            search_queries.append(f"{clean_title} S{season:02d}")
            search_queries.append(f"{clean_title} Hindi")
            search_queries.append(clean_title)
        else:
            # Movie queries: Targeted with Year, Hindi, IMAX, Remux, 2160p
            if year:
                search_queries.append(f"{clean_title} {year} Hindi")
                search_queries.append(f"{clean_title} {year} Remux")
                search_queries.append(f"{clean_title} {year} IMAX")
                search_queries.append(f"{clean_title} {year} 2160p")
                search_queries.append(f"{clean_title} {year}")

            search_queries.append(f"{clean_title} Hindi")
            search_queries.append(f"{clean_title} Remux")
            search_queries.append(f"{clean_title} IMAX")
            search_queries.append(f"{clean_title} 2160p")
            search_queries.append(f"{clean_title} Dual Audio")
            search_queries.append(clean_title)

            # Subtitle handling (e.g. 'Spider-Man: Brand New Day')
            if ":" in title_name:
                sub_parts = title_name.split(":")
                sub_part = " ".join(re.sub(r"[^\w\s]", " ", sub_parts[1]).split())
                search_queries.append(sub_part)
    else:
        search_queries.append(base_imdb)

    # Step 2: Fetch Torrents in Parallel via Asyncio Gather
    raw_torrents = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Deduplicate queries while preserving order
        unique_queries = list(dict.fromkeys(search_queries))[:8]
        tasks = [
            client.get(
                f"https://torrents-csv.com/service/search?q={urllib.parse.quote(q)}",
                headers={"User-Agent": USER_AGENT}
            )
            for q in unique_queries
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for q, resp in zip(unique_queries, responses):
            if isinstance(resp, httpx.Response) and resp.status_code == 200:
                try:
                    data = resp.json()
                    items = data.get("torrents", [])
                    print(f"    -> Parallel Query '{q}' returned {len(items)} torrents.")
                    for item in items:
                        ih = item.get("infohash", "").strip().lower()
                        if ih and ih not in raw_torrents:
                            raw_torrents[ih] = item
                except Exception:
                    pass

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
        display_name = clean_display_title(name)

        stream_obj = {
            "name": f"OmniStream 🌍\n{quality}",
            "title": f"🎬 {display_name}\n{audio_badge}\n💾 {size_str}  •  ⚡ Seeders: {seeders}",
            "infoHash": ih,
            "fileIdx": 0,
            "_priority": priority_score,
        }
        streams.append(stream_obj)

    # Step 4: Sort by Smart Priority (TamilMV/Hindi 1st, Multi 2nd, 4K IMAX/Remux 3rd, Highest Seeders Top)
    streams.sort(key=lambda x: x["_priority"], reverse=True)

    for s in streams:
        del s["_priority"]

    # Top 60 highest-ranked streams (Massive Library Output!)
    streams = streams[:60]

    print(f"[+] Returning {len(streams)} Verified Ranked Streams (IMAX & TamilMV prioritized)!")
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
