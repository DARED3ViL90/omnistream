"""
OmniStream 🌍 - Worldwide Multi-Audio Stremio Addon (Gradio Template for Hugging Face)
100% Free - No Docker Required!
"""

import os
import re
import urllib.parse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import httpx
import gradio as gr

# 1. FastAPI App Initialization
app = FastAPI(title="OmniStream Addon", version="2.0.0")

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
    "description": "Worldwide Torrent Provider with Smart Language Prioritization (🇮🇳 Hindi & 🌐 Multi-Audio on top, followed by 4K/UHD Original Audio).",
    "logo": "https://huggingface.co/front/assets/huggingface_logo.svg",
    "resources": ["stream"],
    "types": ["movie", "series"],
    "catalogs": [],
    "idPrefixes": ["tt"],
}


@app.get("/manifest.json")
def get_manifest():
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(content=MANIFEST, headers=headers)


# 3. Audio Classifier & Smart Priority
def classify_audio_and_priority(title: str, seeders: int) -> tuple[str, int]:
    t = title.lower()
    
    # Priority 1: Hindi / Bollywood / Desi Dubs
    hindi_keywords = ["hindi", "hin", "bollywood"]
    if any(k in t for k in hindi_keywords):
        return "🇮🇳 [Hindi Dubbed / Multi]", 10000 + seeders

    # Priority 2: Multi-Audio / Dual Audio
    multi_keywords = ["multi audio", "multi-audio", "dual audio", "dual-audio", "multi"]
    if any(k in t for k in multi_keywords):
        return "🌐 [Multi-Audio Pack]", 8000 + seeders

    # Priority 3: Japanese / Anime
    jap_keywords = ["japanese", "jap", "subbed"]
    if any(k in t for k in jap_keywords):
        return "🇯🇵 [Japanese / Anime]", 6000 + seeders

    # Priority 4: Korean
    kor_keywords = ["korean", "kor"]
    if any(k in t for k in kor_keywords):
        return "🇰🇷 [Korean Audio]", 5000 + seeders

    # Priority 5: Spanish
    span_keywords = ["spanish", "castellano", "latino", "esp"]
    if any(k in t for k in span_keywords):
        return "🇪🇸 [Spanish Audio]", 4000 + seeders

    # Priority 6: French
    french_keywords = ["french", "vf", "vostfr", "fra"]
    if any(k in t for k in french_keywords):
        return "🇫🇷 [French Audio]", 3000 + seeders

    # Priority 7: German
    german_keywords = ["german", "ger", "deutsch"]
    if any(k in t for k in german_keywords):
        return "🇩🇪 [German Audio]", 2000 + seeders

    return "🇺🇸 [English / Original]", 1000 + seeders


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


# 4. Stream Route with Tracker Aggregation
@app.get("/stream/{type}/{imdb_id}.json")
async def get_streams(type: str, imdb_id: str):
    parts = imdb_id.split(":")
    base_imdb = parts[0]
    season = int(parts[1]) if len(parts) >= 2 else None
    episode = int(parts[2]) if len(parts) >= 3 else None

    title_name = ""
    year = ""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            cinemeta_url = f"https://v3-cinemeta.strem.io/meta/{type}/{base_imdb}.json"
            meta_res = await client.get(cinemeta_url)
            if meta_res.status_code == 200:
                meta_data = meta_res.json().get("meta", {})
                title_name = meta_data.get("name", "")
                year = meta_data.get("year", "")
        except Exception:
            pass

    search_queries = []
    if base_imdb:
        search_queries.append(base_imdb)

    if title_name:
        clean_title = re.sub(r"[^\w\s]", " ", title_name).strip()
        if type == "series" and season is not None:
            if episode is not None:
                search_queries.append(f"{clean_title} S{season:02d}E{episode:02d} Hindi")
                search_queries.append(f"{clean_title} S{season:02d}E{episode:02d}")
            search_queries.append(f"{clean_title} S{season:02d} Hindi")
            search_queries.append(f"{clean_title} S{season:02d}")
        else:
            search_queries.append(f"{clean_title} Hindi")
            search_queries.append(f"{clean_title} Dual Audio")
            search_queries.append(f"{clean_title} Multi")
            search_queries.append(f"{clean_title}")

    raw_torrents = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for query in search_queries[:4]:
            try:
                encoded_q = urllib.parse.quote(query)
                search_url = f"https://apibay.org/q.php?q={encoded_q}"
                resp = await client.get(search_url)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        for item in data:
                            ih = item.get("info_hash", "").strip().lower()
                            if ih and ih != "0000000000000000000000000000000000000000":
                                raw_torrents[ih] = item
            except Exception:
                pass

    streams = []
    for ih, item in raw_torrents.items():
        name = item.get("name", "Unknown Release")
        seeders = int(item.get("seeders", 0))
        size_bytes = int(item.get("size", 0))

        audio_badge, priority_score = classify_audio_and_priority(name, seeders)
        quality = detect_quality(name)
        size_str = format_bytes(size_bytes)
        
        streams.append({
            "name": f"OmniStream 🌍\n{quality}",
            "title": f"🎬 {name}\n{audio_badge}\n💾 {size_str}  •  ⚡ Seeders: {seeders}",
            "infoHash": ih,
            "fileIdx": 0,
            "_priority": priority_score
        })

    streams.sort(key=lambda x: x["_priority"], reverse=True)

    for s in streams:
        del s["_priority"]

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(content={"streams": streams[:25]}, headers=headers)


# 5. Gradio Web Dashboard for the Space Homepage
with gr.Blocks(title="OmniStream 🌍", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🌍 OmniStream - Stremio Addon Server")
    gr.Markdown("""
    ### ✅ Status: 24/7 Live & Active!
    
    **How to install in Stremio:**
    1. Copy your Space URL and add `/manifest.json` at the end:
       `https://<your-space-name>.hf.space/manifest.json`
    2. Paste into Stremio Addons search bar.
    3. Click **Install**!
    """)

# Mount Gradio onto the FastAPI app so both work simultaneously
app = gr.mount_gradio_app(app, demo, path="/")
