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
import json
import base64
import xml.etree.ElementTree as ET
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
import httpx

from domain_watcher import refresh_verified_domains, get_domain
from configure_html import HTML_CONTENT

app = FastAPI(title="OmniStream Addon", version="2.8.0")

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
    "version": "2.8.0",
    "name": "OmniStream 🌍 (Multi-Audio + Anime)",
    "description": "Universal High-Speed Multi-Audio Streaming Provider with IMAX, 4K Remux, Kitsu Anime & Nyaa Engine.",
    "logo": "https://omnistream-jpp5.onrender.com/logo.png",
    "background": "https://images.metahub.space/background/medium/tt22084616/img",
    "resources": ["stream", "subtitles"],
    "types": ["movie", "series", "anime"],
    "catalogs": [],
    "idPrefixes": ["tt", "kitsu"],
    "behaviorHints": {
        "configurable": True,
        "configurationRequired": False
    }
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def parse_user_config(config_str: str = None) -> dict:
    defaults = {"h": 1, "m": 1, "i": 1, "a": 1, "nc": 0, "gb": 0, "rd": ""}
    if not config_str:
        return defaults
    try:
        padded = config_str + "=" * ((4 - len(config_str) % 4) % 4)
        padded = padded.replace("-", "+").replace("_", "/")
        raw_json = base64.b64decode(padded).decode("utf-8")
        parsed = json.loads(raw_json)
        defaults.update(parsed)
        return defaults
    except Exception:
        return defaults


@app.get("/configure")
def get_configure_page():
    return HTMLResponse(content=HTML_CONTENT)


@app.get("/")
@app.get("/manifest.json")
@app.get("/{config}/manifest.json")
def get_manifest(config: str = None):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(content=MANIFEST, headers=headers)


@app.get("/subtitles/{type}/{imdb_id}.json")
@app.get("/{config}/subtitles/{type}/{imdb_id}.json")
def get_subtitles(type: str, imdb_id: str, config: str = None):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(content={"subtitles": []}, headers=headers)


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
def is_cam_release(title: str) -> bool:
    """Detects CAM, HDTS, Telesync, and PreDVD releases."""
    cam_patterns = [
        r"\bcam(?:rip)?\b",
        r"\bhdcam\b",
        r"\bhdts\b",
        r"\btelesync\b",
        r"\btelecine\b",
        r"\bpredvd\b",
        r"\bdvdscr\b",
        r"\bhdtc\b",
        r"\bcam-rip\b",
    ]
    t = title.lower()
    return any(re.search(pat, t) for pat in cam_patterns)


def classify_audio_and_priority(title: str, seeders: int, cfg: dict = None) -> tuple[str, int]:
    if cfg is None:
        cfg = {"h": 1, "m": 1, "i": 1, "a": 1}
    t = title.lower()

    # Special Detection: TamilMV Release
    is_tamilmv = "tamilmv" in t or "1tamilmv" in t

    # Priority 1: Indian Regional Audio (Hindi / Tamil / Telugu / Malayalam / Kannada)
    indian_keywords = [
        "hindi", "bollywood", "dd5.1", "dd 5.1", "org dd",
        "tamil", "telugu", "malayalam", "kannada",
        "movierulz", "tamilblasters", "worldfree4u", "vegamovies", "katmoviehd",
        "moviesmod", "hdhub", "tombdoc", "remuxdoc", "filmyzilla", "desiremovies", "bolly4u"
    ]
    is_indian = any(k in t for k in indian_keywords) or is_tamilmv or bool(re.search(r"\b(tam|tel|hin)\b", t))
    if is_indian:
        if is_tamilmv:
            badge = "🇮🇳 [TamilMV / Multi Audio]"
        elif bool(re.search(r"\b(tamil|tam)\b", t)):
            badge = "🇮🇳 [Tamil Audio / Multi]"
        elif bool(re.search(r"\b(telugu|tel)\b", t)):
            badge = "🇮🇳 [Telugu Audio / Multi]"
        elif "malayalam" in t:
            badge = "🇮🇳 [Malayalam Audio / Multi]"
        elif "kannada" in t:
            badge = "🇮🇳 [Kannada Audio / Multi]"
        else:
            badge = "🇮🇳 [Hindi Dubbed / Multi Audio]"
        weight = 200000 if cfg.get("h", 1) else 10000
        return badge, weight + seeders

    # Priority 2: Multi-Audio / Dual Audio Packs (Including Global Netflix / OTT WebRips)
    multi_keywords = [
        "multi audio", "multi-audio", "dual audio", "dual-audio", "multi", "dual", "dubbed",
        "nf.webrip", "amzn.webrip", "dsnp.webrip", "nf webrip"
    ]
    if any(k in t for k in multi_keywords):
        weight = 150000 if cfg.get("m", 1) else 10000
        return "🌐 [Multi-Audio Pack]", weight + seeders

    # Priority 3: 4K IMAX / Massive Remux Beasts (Dolby Vision / Atmos)
    if "IMAX" in title.upper() or "REMUX" in title.upper():
        badge = "🌌 [4K IMAX Enhanced]" if "IMAX" in title.upper() else "💎 [4K UHD Remux Lossless]"
        weight = 100000 if cfg.get("i", 1) else 10000
        return badge, weight + seeders

    # Priority 4: Japanese / Anime
    jap_keywords = ["japanese", "jap", "subbed"]
    if any(k in t for k in jap_keywords):
        weight = 80000 if cfg.get("a", 1) else 10000
        return "🇯🇵 [Japanese / Anime]", weight + seeders

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
        r"^(?:https?://)?(?:www\.)?[a-zA-Z0-9\.\-]+\.(?:land|pm|ws|org|net|com|one|me|top|baby|xyz|solar|lat|click|lease|vip|in|cc|to|pet|dad)\s*[-_–:\s]\s*",
        "",
        raw_title,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def parse_size_str(size_str: str) -> int:
    try:
        parts = size_str.strip().split()
        val = float(parts[0])
        unit = parts[1].upper() if len(parts) > 1 else ""
        if "GIB" in unit or "GB" in unit:
            return int(val * 1024 ** 3)
        elif "MIB" in unit or "MB" in unit:
            return int(val * 1024 ** 2)
        elif "KIB" in unit or "KB" in unit:
            return int(val * 1024)
        return int(val)
    except Exception:
        return 0


async def fetch_nyaa(query: str, client: httpx.AsyncClient):
    """Fetches anime torrents from NyaaSi RSS feed."""
    try:
        url = f"https://nyaa.si/?page=rss&q={urllib.parse.quote(query)}"
        resp = await client.get(url, headers={"User-Agent": USER_AGENT})
        if resp.status_code == 200:
            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            items = []
            if channel is not None:
                for it in channel.findall("item"):
                    title_elem = it.find("title")
                    title = title_elem.text if title_elem is not None and title_elem.text else ""
                    hash_elem = it.find("{https://nyaa.si/xmlns/nyaa}infoHash")
                    info_hash = hash_elem.text.strip().lower() if hash_elem is not None and hash_elem.text else ""
                    seed_elem = it.find("{https://nyaa.si/xmlns/nyaa}seeders")
                    seeders = int(seed_elem.text.strip()) if seed_elem is not None and seed_elem.text else 0
                    size_elem = it.find("{https://nyaa.si/xmlns/nyaa}size")
                    size_str = size_elem.text.strip() if size_elem is not None and size_elem.text else ""
                    size_bytes = parse_size_str(size_str)
                    if info_hash:
                        items.append({
                            "name": title,
                            "infohash": info_hash,
                            "seeders": seeders,
                            "size_bytes": size_bytes,
                        })
            return items
    except Exception as e:
        print(f"[-] Nyaa fetch error for '{query}': {e}")
    return []


async def fetch_apibay(query: str, client: httpx.AsyncClient):
    """Fetches torrents from The Pirate Bay (apibay.org) using direct IMDb ID or keywords."""
    try:
        url = f"https://apibay.org/q.php?q={urllib.parse.quote(query)}"
        resp = await client.get(url, headers={"User-Agent": USER_AGENT})
        if resp.status_code == 200:
            data = resp.json()
            items = []
            if isinstance(data, list):
                for x in data:
                    name = x.get("name", "")
                    if not name or name == "No results returned":
                        continue
                    ih = x.get("info_hash", "").strip().lower()
                    seeders = int(x.get("seeders", 0))
                    size_bytes = int(x.get("size", 0))
                    if ih:
                        items.append({
                            "name": name,
                            "infohash": ih,
                            "seeders": seeders,
                            "size_bytes": size_bytes,
                        })
            return items
    except Exception as e:
        print(f"[-] Apibay error for '{query}': {e}")
    return []


TRACKERS = [
    "tracker:udp://tracker.opentrackr.org:1337/announce",
    "tracker:udp://open.stealth.si:80/announce",
    "tracker:udp://tracker.torrent.eu.org:451/announce",
    "tracker:udp://explodie.org:6969/announce",
    "tracker:udp://tracker.moeking.me:6969/announce",
    "tracker:udp://opentracker.i2p.rocks:6969/announce",
    "tracker:udp://tracker.dler.org:6969/announce",
    "tracker:udp://p4p.arenabg.com:1337/announce",
]


# 4. Stream Route with Global Torrent, IMAX & Kitsu/Nyaa Anime Aggregation
@app.get("/stream/{type}/{imdb_id}.json")
@app.get("/{config}/stream/{type}/{imdb_id}.json")
async def get_streams(type: str, imdb_id: str, config: str = None):
    cfg = parse_user_config(config)
    print(f"\n=======================================================")
    print(f"[+] OmniStream Query: {type.upper()} | ID: {imdb_id} | Config: {cfg}")

    parts = imdb_id.split(":")
    is_kitsu = imdb_id.startswith("kitsu:")
    base_imdb = parts[0]
    season = int(parts[1]) if len(parts) >= 2 and not is_kitsu else 1
    episode = int(parts[2]) if len(parts) >= 3 else (int(parts[1]) if is_kitsu and len(parts) >= 2 else None)

    title_name = ""
    romaji_name = ""
    year = ""

    # Step 1: Resolve Title (Kitsu for Anime Catalogs or Cinemeta for IMDb)
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        if is_kitsu:
            try:
                kitsu_id = parts[1]
                episode = int(parts[2]) if len(parts) >= 3 else 1
                kitsu_url = f"https://kitsu.io/api/edge/anime/{kitsu_id}"
                k_res = await client.get(kitsu_url, headers={"Accept": "application/vnd.api+json", "User-Agent": USER_AGENT})
                if k_res.status_code == 200:
                    attr = k_res.json().get("data", {}).get("attributes", {})
                    title_name = attr.get("canonicalTitle", "")
                    romaji_name = attr.get("titles", {}).get("en_jp", "")
                    year = attr.get("startDate", "")[:4]
                    print(f"[+] Resolved Kitsu Anime: '{title_name}' / '{romaji_name}' ({year}) | Ep: {episode}")
            except Exception as e:
                print(f"[-] Kitsu error: {e}")
        else:
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

    # Build targeted search queries (Including Subtitles, Regional Audio, Anime, IMAX, Remux & 4K)
    search_queries = []
    nyaa_queries = []

    if title_name:
        clean_title = " ".join(re.sub(r"[^\w\s]", " ", title_name).split())
        clean_romaji = " ".join(re.sub(r"[^\w\s]", " ", romaji_name).split()) if romaji_name else ""

        # If title has a colon (e.g. 'Stree 2: Sarkate Ka Aatank' or 'Dune: Part Two')
        primary_title = ""
        if ":" in title_name:
            primary_title = " ".join(re.sub(r"[^\w\s]", " ", title_name.split(":")[0]).split())

        if is_kitsu or type == "anime":
            ep_num = episode if episode is not None else 1
            search_queries.append(f"{clean_title} S01E{ep_num:02d}")
            search_queries.append(f"{clean_title} E{ep_num:02d}")
            search_queries.append(f"{clean_title} {ep_num:02d}")
            search_queries.append(f"{clean_title} Dual Audio")
            search_queries.append(f"{clean_title} Hindi")
            search_queries.append(clean_title)

            nyaa_queries.append(f"{clean_title} {ep_num:02d}")
            nyaa_queries.append(f"{clean_title} Dual Audio")

            if clean_romaji and clean_romaji.lower() != clean_title.lower():
                search_queries.append(f"{clean_romaji} {ep_num:02d}")
                search_queries.append(clean_romaji)
                nyaa_queries.append(f"{clean_romaji} {ep_num:02d}")
        elif type == "series" and season is not None:
            if episode is not None:
                search_queries.append(f"{clean_title} S{season:02d}E{episode:02d}")
                if primary_title:
                    search_queries.append(f"{primary_title} S{season:02d}E{episode:02d}")
            search_queries.append(f"{clean_title} S{season:02d}")
            search_queries.append(f"{clean_title} Hindi")
            search_queries.append(clean_title)
            if primary_title:
                search_queries.append(f"{primary_title} Hindi")
                search_queries.append(primary_title)
        else:
            # Movie queries: Comprehensive Deep Torrent Sweep
            if primary_title:
                search_queries.append(f"{primary_title} Hindi")
                if year:
                    search_queries.append(f"{primary_title} {year}")
                search_queries.append(f"{primary_title} Remux")
                search_queries.append(f"{primary_title} 2160p")
                search_queries.append(primary_title)

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
    else:
        search_queries.append(base_imdb)

    # Step 2: Fetch Torrents in Parallel via Asyncio Gather (torrents-csv + NyaaSi + Apibay)
    raw_torrents = {}
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        # Deduplicate queries while preserving order
        unique_queries = list(dict.fromkeys(search_queries))[:12]
        tasks = [
            client.get(
                f"https://torrents-csv.com/service/search?q={urllib.parse.quote(q)}",
                headers={"User-Agent": USER_AGENT}
            )
            for q in unique_queries
        ]

        # Add NyaaSi tasks for anime
        unique_nyaa = list(dict.fromkeys(nyaa_queries))[:3]
        for nq in unique_nyaa:
            tasks.append(fetch_nyaa(nq, client))

        # Add The Pirate Bay (apibay.org) tasks
        apibay_queries = []
        if not is_kitsu and base_imdb.startswith("tt"):
            apibay_queries.append(base_imdb)
            if clean_title:
                apibay_queries.append(f"{clean_title} Hindi")
                if type == "series" and season is not None:
                    apibay_queries.append(f"{clean_title} S{season:02d}")

        unique_apibay = list(dict.fromkeys(apibay_queries))[:3]
        for aq in unique_apibay:
            tasks.append(fetch_apibay(aq, client))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process torrents-csv responses
        for i, q in enumerate(unique_queries):
            resp = responses[i]
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

        # Process Nyaa responses
        for i, nq in enumerate(unique_nyaa):
            resp = responses[len(unique_queries) + i]
            if isinstance(resp, list):
                print(f"    -> NyaaSi Query '{nq}' returned {len(resp)} anime torrents.")
                for item in resp:
                    ih = item.get("infohash", "").strip().lower()
                    if ih and ih not in raw_torrents:
                        raw_torrents[ih] = item

        # Process The Pirate Bay (Apibay) responses
        offset = len(unique_queries) + len(unique_nyaa)
        for i, aq in enumerate(unique_apibay):
            resp = responses[offset + i]
            if isinstance(resp, list):
                print(f"    -> PirateBay Query '{aq}' returned {len(resp)} torrents.")
                for item in resp:
                    ih = item.get("infohash", "").strip().lower()
                    if ih and ih not in raw_torrents:
                        raw_torrents[ih] = item

    print(f"[+] Total unique torrents collected: {len(raw_torrents)}")

    # Step 3: Classify Language & Calculate Smart Priority with User Config Filters
    exclude_cam = bool(cfg.get("nc", 0))
    max_gb = float(cfg.get("gb", 0))
    max_size_bytes = int(max_gb * (1024 ** 3)) if max_gb > 0 else 0

    streams = []
    for ih, item in raw_torrents.items():
        name = item.get("name", "Unknown Release")
        seeders = int(item.get("seeders", 0))
        size_bytes = int(item.get("size_bytes", 0))

        # Filter 1: Exclude CAM / Telesync / PreDVD if configured
        if exclude_cam and is_cam_release(name):
            continue

        # Filter 2: Max File Size in GB (0 = No limit / full 80GB Remux beasts)
        if max_size_bytes > 0 and size_bytes > max_size_bytes:
            continue

        audio_badge, priority_score = classify_audio_and_priority(name, seeders, cfg)
        quality = detect_quality(name)
        size_str = format_bytes(size_bytes)
        display_name = clean_display_title(name)

        stream_obj = {
            "name": f"OmniStream 🌍\n{quality}",
            "title": f"🎬 {display_name}\n{audio_badge}\n💾 {size_str}  •  ⚡ Seeders: {seeders}",
            "infoHash": ih,
            "fileIdx": 0,
            "sources": TRACKERS,
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
