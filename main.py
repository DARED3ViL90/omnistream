"""
OmniStream 🌍 - Worldwide Multi-Audio Stremio Addon (Render Cloud Production)
Aggregates global torrent networks, identifies audio languages, tags national flags,
and enforces Smart Priority Sorting (🇮🇳 Hindi & 🌐 Multi-Audio on top, followed by 4K/UHD Original Audio).
"""

import os
import re
import urllib.parse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import httpx

app = FastAPI(title="OmniStream Addon", version="2.0.0")

# 1. Enable Wildcard CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Stremio v3 Manifest
MANIFEST = {
    "id": "community.omnistream.core",
    "version": "2.0.0",
    "name": "OmniStream 🌍 (Multi-Audio)",
    "description": "Universal High-Speed Multi-Audio Streaming Provider with Smart Audio Prioritization & 4K UHD Support.",
    "logo": "https://omnistream-jpp5.onrender.com/logo.png",
    "background": "https://images.metahub.space/background/medium/tt22084616/img",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "catalogs": [],
    "idPrefixes": ["tt"],
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


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
    elif os.path.exists(r"C:\Users\AVITA\desistream_logo.png"):
        return FileResponse(r"C:\Users\AVITA\desistream_logo.png", media_type="image/png")
    return JSONResponse(status_code=404, content={"error": "Logo not found"})


@app.get("/debug/{type}/{imdb_id}")
async def debug_endpoint(type: str, imdb_id: str):
    results = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r1 = await client.get(f"https://torrentio.strem.fun/stream/{type}/{imdb_id}.json", headers={"User-Agent": USER_AGENT})
            results["torrentio"] = {"status": r1.status_code, "body_preview": r1.text[:300]}
        except Exception as e:
            results["torrentio"] = {"error": str(e)}
        try:
            r2 = await client.get(f"https://v3-cinemeta.strem.io/meta/{type}/{imdb_id}.json", headers={"User-Agent": USER_AGENT})
            results["cinemeta"] = {"status": r2.status_code, "name": r2.json().get("meta", {}).get("name")}
        except Exception as e:
            results["cinemeta"] = {"error": str(e)}
    return results


# 3. Smart Language Classifier & Flag Tagger
def classify_audio_and_priority(title: str) -> tuple[str, int]:
    t = title.lower()

    # Priority 1: Hindi / Bollywood / Desi Dubs
    hindi_keywords = ["hindi", "hin", "bollywood", "🇮🇳"]
    if any(k in t for k in hindi_keywords):
        return "🇮🇳 [Hindi Dubbed / Multi Audio]", 100000

    # Priority 2: Multi-Audio / Dual Audio
    multi_keywords = ["multi audio", "multi-audio", "dual audio", "dual-audio", "multi"]
    if any(k in t for k in multi_keywords):
        return "🌐 [Multi-Audio Pack]", 80000

    # Priority 3: Japanese / Anime
    jap_keywords = ["japanese", "jap", "subbed", "🇯🇵"]
    if any(k in t for k in jap_keywords):
        return "🇯🇵 [Japanese / Anime]", 60000

    # Priority 4: Korean
    kor_keywords = ["korean", "kor", "🇰🇷"]
    if any(k in t for k in kor_keywords):
        return "🇰🇷 [Korean Audio]", 50000

    # Priority 5: Spanish
    span_keywords = ["spanish", "castellano", "latino", "esp", "🇪🇸"]
    if any(k in t for k in span_keywords):
        return "🇪🇸 [Spanish Audio]", 40000

    # Priority 6: French
    french_keywords = ["french", "vf", "vostfr", "fra", "🇫🇷"]
    if any(k in t for k in french_keywords):
        return "🇫🇷 [French Audio]", 30000

    # Priority 7: German
    german_keywords = ["german", "ger", "deutsch", "🇩🇪"]
    if any(k in t for k in german_keywords):
        return "🇩🇪 [German Audio]", 20000

    return "🇺🇸 [English / Original]", 10000


def detect_quality(title: str) -> str:
    t = title.upper()
    if "2160P" in t or "4K" in t or "UHD" in t:
        return "4K UHD 🌟"
    elif "1080P" in t or "FHD" in t:
        return "1080p FHD ⚡"
    elif "720P" in t or "HD" in t:
        return "720p HD 📺"
    return "HDRip 🎬"


# 4. Stream Route with Global Torrent Aggregation
@app.get("/stream/{type}/{imdb_id}.json")
async def get_streams(type: str, imdb_id: str):
    print(f"\n=======================================================")
    print(f"[+] OmniStream Query: {type.upper()} | ID: {imdb_id}")

    streams = []
    seen_hashes = set()

    # Step 1: Query Global Upstream Network (with full Hindi prioritization)
    async with httpx.AsyncClient(timeout=12.0) as client:
        # A. Query Global Stream Aggregator
        try:
            upstream_url = f"https://torrentio.strem.fun/stream/{type}/{imdb_id}.json"
            resp = await client.get(upstream_url, headers={"User-Agent": USER_AGENT})
            if resp.status_code == 200:
                data = resp.json()
                raw_streams = data.get("streams", [])
                print(f"[+] Global Network returned {len(raw_streams)} streams.")

                for s in raw_streams:
                    ih = s.get("infoHash", "").strip().lower()
                    if not ih or ih in seen_hashes:
                        continue
                    seen_hashes.add(ih)

                    raw_title = s.get("title", "")
                    audio_badge, base_priority = classify_audio_and_priority(raw_title)
                    quality = detect_quality(raw_title)

                    # Extract seeders if present in title
                    seed_match = re.search(r"[👤⚡]\s*(\d+)", raw_title)
                    seeders = int(seed_match.group(1)) if seed_match else 0

                    # Combine base language priority with seeders
                    total_priority = base_priority + seeders

                    stream_obj = {
                        "name": f"OmniStream 🌍\n{quality}",
                        "title": f"{raw_title}\n{audio_badge}",
                        "infoHash": ih,
                        "fileIdx": s.get("fileIdx", 0),
                        "sources": s.get("sources", []),
                        "_priority": total_priority,
                    }
                    if "behaviorHints" in s:
                        stream_obj["behaviorHints"] = s["behaviorHints"]

                    streams.append(stream_obj)
        except Exception as e:
            print(f"[-] Upstream fetch error: {e}")

        # B. Fallback / Supplementary Query via Apibay / Cinemeta for rare desi releases
        try:
            parts = imdb_id.split(":")
            base_imdb = parts[0]
            cinemeta_url = f"https://v3-cinemeta.strem.io/meta/{type}/{base_imdb}.json"
            meta_res = await client.get(cinemeta_url, headers={"User-Agent": USER_AGENT})
            if meta_res.status_code == 200:
                name = meta_res.json().get("meta", {}).get("name", "")
                if name:
                    q = urllib.parse.quote(f"{name} Hindi")
                    apibay_res = await client.get(f"https://apibay.org/q.php?q={q}", headers={"User-Agent": USER_AGENT})
                    if apibay_res.status_code == 200:
                        items = apibay_res.json()
                        if isinstance(items, list):
                            for it in items[:5]:
                                ih = it.get("info_hash", "").strip().lower()
                                if ih and ih not in seen_hashes and ih != "0000000000000000000000000000000000000000":
                                    seen_hashes.add(ih)
                                    t_name = it.get("name", "")
                                    s_count = int(it.get("seeders", 0))
                                    streams.append({
                                        "name": f"OmniStream 🇮🇳\n{detect_quality(t_name)}",
                                        "title": f"🎬 {t_name}\n🇮🇳 [Hindi Dubbed / Multi Audio]\n⚡ Seeders: {s_count}",
                                        "infoHash": ih,
                                        "fileIdx": 0,
                                        "_priority": 100000 + s_count,
                                    })
        except Exception as e:
            print(f"[-] Desi fallback fetch error: {e}")

    # Step 2: Sort by Smart Priority (Hindi 1st, Multi 2nd, Original 3rd)
    streams.sort(key=lambda x: x["_priority"], reverse=True)

    # Clean up internal sorting key
    for s in streams:
        del s["_priority"]

    # Limit to top 30 best ranked streams
    streams = streams[:30]

    print(f"[+] Returning {len(streams)} Optimized Ranked Streams (Hindi on Top)!")
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
