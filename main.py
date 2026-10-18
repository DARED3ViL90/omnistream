"""
OmniStream 🌍 - Worldwide Multi-Audio Stremio Addon (Production Cloud Edition v3.0.0)
High-Capacity Global Aggregator with IMAX, 4K Remux, TamilMV/TamilBlasters & Anime Engine.

Fixes in v3.0.0:
1. Removed hardcoded 'fileIdx: 0' bug (fixed 10-second PNG/sample loops & wrong episode playback in packs).
2. Added strict release/title validation (stops unrelated movies like Wall Street matching Stree 2).
3. Added strict season/episode filter for TV series.
4. Added Kitsu Romaji + Absolute Episode resolution for Nyaa & AnimeTosho.
5. Added YTS & AnimeTosho high-speed scrapers.
6. Full TamilMV & TamilBlasters priority detection.
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

app = FastAPI(title="OmniStream Addon", version="3.0.0")

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
    "version": "3.0.0",
    "name": "OmniStream 🌍 (Multi-Audio + Anime)",
    "description": "Universal High-Speed Multi-Audio Streaming Provider with IMAX, 4K Remux, Kitsu Anime, TamilBlasters & Nyaa Engine.",
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


@app.get("/debug/{query}")
async def debug_query(query: str):
    debug_info = {}
    async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
        # Test 1: apibay with piratebay headers
        try:
            url = f"https://apibay.org/q.php?q={urllib.parse.quote(query)}"
            headers = {"User-Agent": USER_AGENT, "Referer": "https://thepiratebay.org/", "Origin": "https://thepiratebay.org"}
            r = await client.get(url, headers=headers)
            debug_info["apibay_status"] = r.status_code
            if r.status_code == 200 and isinstance(r.json(), list):
                debug_info["apibay_count"] = len(r.json())
        except Exception as e:
            debug_info["apibay_err"] = str(e)

        # Test 2: thepiratebay10.org HTML scraper
        try:
            url_tpb10 = f"https://thepiratebay10.org/search/{urllib.parse.quote(query)}/1/99/0"
            r10 = await client.get(url_tpb10, headers={"User-Agent": USER_AGENT})
            debug_info["tpb10_status"] = r10.status_code
            hashes = re.findall(r"magnet:\?xt=urn:btih:([a-zA-Z0-9]{40})", r10.text)
            debug_info["tpb10_hashes"] = len(hashes)
        except Exception as e:
            debug_info["tpb10_err"] = str(e)

        # Test 3: tpb.party HTML scraper
        try:
            url_party = f"https://tpb.party/search/{urllib.parse.quote(query)}/1/99/0"
            rp = await client.get(url_party, headers={"User-Agent": USER_AGENT})
            debug_info["party_status"] = rp.status_code
            hashes_p = re.findall(r"magnet:\?xt=urn:btih:([a-zA-Z0-9]{40})", rp.text)
            debug_info["party_hashes"] = len(hashes_p)
        except Exception as e:
            debug_info["party_err"] = str(e)

        # Test 4: torrents-csv
        try:
            url_csv = f"https://torrents-csv.com/service/search?q={urllib.parse.quote(query)}"
            rc = await client.get(url_csv, headers={"User-Agent": USER_AGENT})
            debug_info["csv_status"] = rc.status_code
            debug_info["csv_count"] = len(rc.json().get("torrents", [])) if rc.status_code == 200 else 0
        except Exception as e:
            debug_info["csv_err"] = str(e)

    return debug_info

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

    # Special Detection: TamilMV & TamilBlasters Releases
    is_tamilmv = "tamilmv" in t or "1tamilmv" in t
    is_tamilblasters = "tamilblasters" in t or "1tamilblasters" in t

    # Priority 1: Indian Regional Audio (Hindi / Tamil / Telugu / Malayalam / Kannada)
    indian_keywords = [
        "hindi", "bollywood", "dd5.1", "dd 5.1", "org dd",
        "tamil", "telugu", "malayalam", "kannada",
        "movierulz", "tamilblasters", "worldfree4u", "vegamovies", "katmoviehd",
        "moviesmod", "hdhub", "tombdoc", "remuxdoc", "filmyzilla", "desiremovies", "bolly4u"
    ]
    is_indian = any(k in t for k in indian_keywords) or is_tamilmv or is_tamilblasters or bool(re.search(r"\b(tam|tel|hin)\b", t))
    if is_indian:
        if is_tamilmv:
            badge = "🇮🇳 [TamilMV / Multi Audio]"
        elif is_tamilblasters:
            badge = "🇮🇳 [TamilBlasters / Multi Audio]"
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
        r"^(?:https?://)?(?:www\.)?[a-zA-Z0-9\.\-]+\.(?:land|pm|ws|org|net|com|one|me|top|baby|xyz|solar|lat|click|lease|vip|in|cc|to|pet|dad|tech)\s*[-_–:\s]\s*",
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


# Release / Episode Matching Filters
def is_valid_release(torrent_name: str, media_type: str, title: str, year: str = "", season: int = None, episode: int = None) -> bool:
    """Stops unrelated movies or wrong season/episode releases from creeping in."""
    name_clean = torrent_name.lower().replace(".", " ").replace("_", " ").replace("-", " ")
    raw_name = torrent_name.lower()

    # 1. Exclude sample clips, trailers, promos, extras, and 22-sec notice ads
    junk_patterns = [
        " sample ", "sample mp4", "sample mkv", "sample avi", ".sample.", "-sample.", "_sample_",
        "trailer", "teaser", "promo", "extras", "featurettes", "bonus disc", "notice mp4", "notice.mp4"
    ]
    if any(k in name_clean or k in raw_name for k in junk_patterns):
        return False

    # 2. Check title keyword containment with word boundaries
    clean_title = re.sub(r"[^\w\s]", " ", title.lower()).strip()
    words = [w for w in clean_title.split() if len(w) > 1 and w not in ["the", "and", "part", "movie", "film"]]
    if words:
        matched_words = sum(1 for w in words if re.search(r"\b" + re.escape(w) + r"\b", name_clean))
        if matched_words / len(words) < 0.6:
            return False

    # 3. Series Season & Episode Validation
    if media_type == "series" and season is not None:
        s_target = f"s{season:02d}"
        s_alt = f"season {season}"
        s_alt_dot = f"season.{season}"
        is_target_season = (
            (s_target in raw_name)
            or (s_alt in name_clean)
            or (s_alt_dot in raw_name)
            or ("complete" in raw_name)
            or ("season" not in name_clean and "s0" not in raw_name)
        )
        if not is_target_season:
            return False

        if episode is not None:
            ep_patterns = [f"s{season:02d}e{episode:02d}", f"{season}x{episode:02d}", f"e{episode:02d}"]
            is_matching_ep = any(p in raw_name for p in ep_patterns)
            is_pack = any(k in raw_name for k in ["complete", f"season.{season}", f"season {season}", "batch"])

            if not is_matching_ep and not is_pack:
                other_eps = re.findall(r"(?:s\d{2})?e(\d{2,3})", raw_name)
                if other_eps and f"{episode:02d}" not in other_eps:
                    return False

    return True


def is_valid_anime(torrent_name: str, romaji: str, canonical: str, ep: int = None) -> bool:
    """Verifies anime title and episode matching for Kitsu/Nyaa."""
    name_lower = torrent_name.lower()
    titles = [t for t in [romaji, canonical] if t]
    matched = False
    for t in titles:
        clean = re.sub(r"[^\w\s]", " ", t.lower()).strip()
        words = [w for w in clean.split() if len(w) > 2 and w not in ["the", "and", "part", "season", "anime"]]
        if words:
            if sum(1 for w in words if w in name_lower) / len(words) >= 0.5:
                matched = True
                break
    if not matched:
        return False

    if ep is not None:
        ep_patterns = [
            f" - {ep:02d} ", f" - {ep} ",
            f" {ep:02d} ", f" {ep:02d}.",
            f"e{ep:02d}", f"ep{ep:02d}", f"ep {ep:02d}",
            f"[{ep:02d}]", f"({ep:02d})",
            "batch", "complete"
        ]
        if not any(p in name_lower for p in ep_patterns):
            found_ep = re.findall(r"(?:\s-|\[|\(|ep|e)\s*0*(\d{1,3})(?:\]|\)|\s|\.mkv|\.mp4)", name_lower)
            if found_ep and str(ep) not in found_ep:
                return False
    return True


# Scraper Implementations
async def fetch_nyaa(query: str, client: httpx.AsyncClient):
    """Fetches anime torrents from NyaaSi RSS feed (English-translated c=1_2 category)."""
    try:
        url = f"https://nyaa.si/?page=rss&c=1_2&q={urllib.parse.quote(query)}"
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


async def fetch_animetosho(query: str, client: httpx.AsyncClient):
    """Fetches high-quality anime releases from AnimeTosho API."""
    try:
        url = f"https://feed.animetosho.org/json?q={urllib.parse.quote(query)}"
        resp = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=6.0)
        if resp.status_code == 200:
            data = resp.json()
            items = []
            if isinstance(data, list):
                for x in data:
                    ih = x.get("info_hash", "").strip().lower()
                    if ih:
                        items.append({
                            "name": x.get("title", ""),
                            "infohash": ih,
                            "seeders": int(x.get("seeders", 0)),
                            "size_bytes": int(x.get("total_size", 0)),
                        })
            return items
    except Exception:
        pass
    return []


async def fetch_yts(imdb_id: str, client: httpx.AsyncClient):
    """Fetches verified high-quality 1080p/2160p movies directly by IMDb ID from YTS."""
    if not imdb_id.startswith("tt"):
        return []
    yts_mirrors = [
        "https://yts.mx",
        "https://yts.pm",
        "https://yts.lt",
        "https://yts.bz"
    ]
    for mirror in yts_mirrors:
        try:
            url = f"{mirror}/api/v2/list_movies.json?query_term={imdb_id}"
            resp = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                movies = data.get("movies", [])
                if movies:
                    items = []
                    m = movies[0]
                    movie_title = m.get("title_long", m.get("title", ""))
                    for t in m.get("torrents", []):
                        hash_val = t.get("hash", "").strip().lower()
                        q = t.get("quality", "1080p")
                        size_bytes = int(t.get("size_bytes", 0))
                        seeders = int(t.get("seeds", 0))
                        t_type = t.get("type", "bluray")
                        if hash_val:
                            items.append({
                                "name": f"{movie_title} [{q}] [{t_type.upper()}] [YTS.MX]",
                                "infohash": hash_val,
                                "seeders": seeders,
                                "size_bytes": size_bytes,
                            })
                    return items
        except Exception:
            continue
    return []


async def fetch_apibay(query: str, client: httpx.AsyncClient):
    """Fetches torrents from The Pirate Bay (apibay.org with automatic thepiratebay10.org / tpb.party failover)."""
    items = []
    # 1. Try apibay.org JSON API
    try:
        url = f"https://apibay.org/q.php?q={urllib.parse.quote(query)}"
        resp = await client.get(url, headers={"User-Agent": USER_AGENT, "Referer": "https://thepiratebay.org/"}, timeout=3.5)
        if resp.status_code == 200 and "Just a moment" not in resp.text:
            data = resp.json()
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
                if items:
                    return items
    except Exception:
        pass

    # 2. Mirror Fallback: thepiratebay10.org & tpb.party (100% works on Cloud/Render Datacenter IPs!)
    mirrors = ["https://thepiratebay10.org", "https://tpb.party"]
    for m in mirrors:
        try:
            url = f"{m}/search/{urllib.parse.quote(query)}/1/99/0"
            resp = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=4.0)
            if resp.status_code == 200 and "magnet:" in resp.text:
                html = resp.text
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, flags=re.DOTALL)
                for tr in rows:
                    m_hash = re.search(r'magnet:\?xt=urn:btih:([a-zA-Z0-9]{40})', tr, flags=re.IGNORECASE)
                    if not m_hash:
                        continue
                    ih = m_hash.group(1).lower()
                    m_title = re.search(r'class="detLink"[^>]*>([^<]+)</a>', tr)
                    if not m_title:
                        m_title = re.search(r'title="Details for ([^"]+)"', tr)
                    name = m_title.group(1).strip() if m_title else ""
                    m_seed = re.findall(r'<td[^>]*align="right"[^>]*>(\d+)</td>', tr)
                    seeders = int(m_seed[0]) if m_seed else 10
                    m_size = re.search(r'Size ([^,]+),', tr)
                    size_str = m_size.group(1).strip() if m_size else "1.5 GB"
                    size_bytes = parse_size_str(size_str)
                    if ih and name:
                        items.append({
                            "name": name,
                            "infohash": ih,
                            "seeders": seeders,
                            "size_bytes": size_bytes,
                        })
                if items:
                    print(f"    -> TPB Mirror '{m}' returned {len(items)} torrents for '{query}'!")
                    return items
        except Exception as e:
            print(f"[-] TPB Mirror error for {m}: {e}")
            continue

    return items


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
                episode = int(parts[2]) if len(parts) >= 3 else (int(parts[1]) if len(parts) >= 2 else 1)
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

    # Build targeted search queries
    search_queries = []
    nyaa_queries = []
    apibay_queries = []

    if title_name:
        clean_title = " ".join(re.sub(r"[^\w\s]", " ", title_name).split())
        clean_romaji = " ".join(re.sub(r"[^\w\s]", " ", romaji_name).split()) if romaji_name else ""

        primary_title = ""
        if ":" in title_name:
            primary_title = " ".join(re.sub(r"[^\w\s]", " ", title_name.split(":")[0]).split())

        if is_kitsu or type == "anime":
            ep_num = episode if episode is not None else 1
            # Anime queries (Romaji prioritized for Nyaa/AnimeTosho)
            anime_search_name = clean_romaji if clean_romaji else clean_title
            nyaa_queries.append(f"{anime_search_name} {ep_num:02d}")
            nyaa_queries.append(f"{anime_search_name} {ep_num}")
            nyaa_queries.append(f"{anime_search_name} Dual Audio")
            if clean_romaji and clean_title.lower() != clean_romaji.lower():
                nyaa_queries.append(f"{clean_title} {ep_num:02d}")
                nyaa_queries.append(f"{clean_title} Dual Audio")

            search_queries.append(f"{anime_search_name} {ep_num:02d}")
            search_queries.append(f"{clean_title} Dual Audio")
            search_queries.append(f"{clean_title} Hindi")
        elif type == "series" and season is not None:
            if episode is not None:
                search_queries.append(f"{clean_title} S{season:02d}E{episode:02d}")
                search_queries.append(f"{clean_title} S{season:02d}E{episode:02d} Hindi")
                if primary_title:
                    search_queries.append(f"{primary_title} S{season:02d}E{episode:02d}")
            search_queries.append(f"{clean_title} S{season:02d}")
            search_queries.append(f"{clean_title} S{season:02d} Hindi")
            search_queries.append(f"{clean_title} Hindi")
            if primary_title:
                search_queries.append(f"{primary_title} S{season:02d}")
                search_queries.append(f"{primary_title} Hindi")

            search_queries.append(f"{clean_title} TamilMV")
            search_queries.append(f"{clean_title} TamilBlasters")
            search_queries.append(clean_title)
            if primary_title and primary_title.lower() != clean_title.lower():
                search_queries.append(primary_title)

            apibay_queries.append(f"{clean_title} S{season:02d}")
            if episode is not None:
                apibay_queries.append(f"{clean_title} S{season:02d}E{episode:02d}")
            apibay_queries.append(clean_title)
            if base_imdb.startswith("tt"):
                apibay_queries.append(base_imdb)
        else:
            # Movie queries
            if primary_title:
                search_queries.append(f"{primary_title} Hindi")
                search_queries.append(f"{primary_title} TamilMV")
                search_queries.append(f"{primary_title} TamilBlasters")
                if year:
                    search_queries.append(f"{primary_title} {year}")
                search_queries.append(f"{primary_title} Remux")
                search_queries.append(f"{primary_title} 2160p")

            if year:
                search_queries.append(f"{clean_title} {year} Hindi")
                search_queries.append(f"{clean_title} {year} TamilMV")
                search_queries.append(f"{clean_title} {year} TamilBlasters")
                search_queries.append(f"{clean_title} {year} Remux")
                search_queries.append(f"{clean_title} {year} 2160p")
                search_queries.append(f"{clean_title} {year}")

            search_queries.append(f"{clean_title} Hindi")
            search_queries.append(f"{clean_title} TamilMV")
            search_queries.append(f"{clean_title} TamilBlasters")
            search_queries.append(f"{clean_title} Remux")
            search_queries.append(f"{clean_title} IMAX")
            search_queries.append(f"{clean_title} 2160p")
            search_queries.append(f"{clean_title} Dual Audio")
            search_queries.append(clean_title)

            if base_imdb.startswith("tt"):
                apibay_queries.append(base_imdb)
            apibay_queries.append(f"{clean_title} Hindi")
            apibay_queries.append(clean_title)
    else:
        search_queries.append(base_imdb)
        if base_imdb.startswith("tt"):
            apibay_queries.append(base_imdb)

    # Step 2: Parallel Fetch via Asyncio Gather
    raw_torrents = {}
    async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
        unique_queries = list(dict.fromkeys(search_queries))[:12]
        tasks = [
            client.get(
                f"https://torrents-csv.com/service/search?q={urllib.parse.quote(q)}",
                headers={"User-Agent": USER_AGENT}
            )
            for q in unique_queries
        ]

        # Nyaa tasks for anime
        unique_nyaa = list(dict.fromkeys(nyaa_queries))[:4]
        for nq in unique_nyaa:
            tasks.append(fetch_nyaa(nq, client))
            tasks.append(fetch_animetosho(nq, client))

        # PirateBay (Apibay) tasks
        unique_apibay = list(dict.fromkeys(apibay_queries))[:4]
        for aq in unique_apibay:
            tasks.append(fetch_apibay(aq, client))

        # YTS for movies
        if type == "movie" and base_imdb.startswith("tt"):
            tasks.append(fetch_yts(base_imdb, client))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 1. Process torrents-csv
        for i, q in enumerate(unique_queries):
            resp = responses[i]
            if isinstance(resp, httpx.Response) and resp.status_code == 200:
                try:
                    data = resp.json()
                    items = data.get("torrents", [])
                    for item in items:
                        ih = item.get("infohash", "").strip().lower()
                        if ih and ih not in raw_torrents:
                            raw_torrents[ih] = item
                except Exception:
                    pass

        # 2. Process remaining responses (Nyaa, AnimeTosho, Apibay, YTS)
        for resp in responses[len(unique_queries):]:
            if isinstance(resp, list):
                for item in resp:
                    ih = item.get("infohash", "").strip().lower()
                    if ih and ih not in raw_torrents:
                        raw_torrents[ih] = item

    print(f"[+] Total raw torrents collected: {len(raw_torrents)}")

    # Step 3: Validate and Classify Torrents
    exclude_cam = bool(cfg.get("nc", 0))
    max_gb = float(cfg.get("gb", 0))
    max_size_bytes = int(max_gb * (1024 ** 3)) if max_gb > 0 else 0

    streams = []
    for ih, item in raw_torrents.items():
        name = item.get("name", "Unknown Release")
        seeders = int(item.get("seeders", 0))
        size_bytes = int(item.get("size_bytes", 0))

        # Filter 1: Release & Title Validation (Stops unrelated movies & wrong episodes!)
        if title_name:
            if is_kitsu or type == "anime":
                if not is_valid_anime(name, romaji_name, title_name, episode):
                    continue
            else:
                if not is_valid_release(name, type, title_name, year, season, episode):
                    continue

        # Filter 2: Exclude CAM / Telesync / PreDVD if configured
        if exclude_cam and is_cam_release(name):
            continue

        # Filter 3: Max File Size in GB (0 = No limit)
        if max_size_bytes > 0 and size_bytes > max_size_bytes:
            continue

        # Filter 4: Minimum File Size Protection (Blocks 22-second notice ads, sample clips, and tiny spam)
        if type == "movie" and size_bytes > 0 and size_bytes < 250 * 1024 * 1024:
            continue
        if type in ["series", "anime"] and size_bytes > 0 and size_bytes < 40 * 1024 * 1024:
            continue

        audio_badge, priority_score = classify_audio_and_priority(name, seeders, cfg)
        quality = detect_quality(name)
        size_str = format_bytes(size_bytes)
        display_name = clean_display_title(name)

        # CRITICAL FIX: No 'fileIdx: 0'!
        # Omitting fileIdx allows Stremio's internal video selector to auto-select
        # the main movie file (skipping sample.mp4, pngs, screens) and auto-match
        # the exact episode inside complete season packs!
        stream_obj = {
            "name": f"OmniStream 🌍\n{quality}",
            "title": f"🎬 {display_name}\n{audio_badge}\n💾 {size_str}  •  ⚡ Seeders: {seeders}",
            "infoHash": ih,
            "sources": TRACKERS,
            "_priority": priority_score,
        }
        streams.append(stream_obj)

    # Step 4: Sort by Smart Priority (TamilMV/TamilBlasters/Hindi 1st, Multi 2nd, 4K IMAX/Remux 3rd)
    streams.sort(key=lambda x: x["_priority"], reverse=True)

    for s in streams:
        del s["_priority"]

    # Top 60 highest-ranked verified streams
    streams = streams[:60]

    print(f"[+] Returning {len(streams)} Verified Ranked Streams for Stremio!")
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
