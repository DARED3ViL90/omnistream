import httpx
import base64
import json
import urllib.parse
import time
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

CASTLE_BASE = "https://api.hlowb.com"
PKG = "com.external.castle"
CHANNEL = "IndiaA"
CLIENT = "1"
LANG = "en-US"

HEADERS = {
    "User-Agent": "okhttp/4.9.3",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "Keep-Alive",
    "Referer": CASTLE_BASE
}

_cached_sec_key = None
_sec_key_expiry = 0

def derive_key(security_key_b64: str) -> bytes:
    key_bytes = base64.b64decode(security_key_b64)
    suffix = b"T!BgJB"
    combined = key_bytes + suffix
    if len(combined) < 16:
        combined = combined + b"\x00" * (16 - len(combined))
    return combined[:16]

def decrypt_castle(cipher_text_b64: str, sec_key: str) -> str:
    key = derive_key(sec_key)
    cipher_bytes = base64.b64decode(cipher_text_b64)
    cipher = AES.new(key, AES.MODE_CBC, iv=key)
    decrypted = unpad(cipher.decrypt(cipher_bytes), AES.block_size)
    return decrypted.decode('utf-8', errors='ignore')

async def get_security_key(client: httpx.AsyncClient) -> str:
    global _cached_sec_key, _sec_key_expiry
    now = time.time()
    if _cached_sec_key and now < _sec_key_expiry:
        return _cached_sec_key
    try:
        url = f"{CASTLE_BASE}/v0.1/system/getSecurityKey/1?channel={CHANNEL}&clientType={CLIENT}&lang={LANG}"
        r = await client.get(url, headers=HEADERS, timeout=4.0)
        if r.status_code == 200:
            key = r.json().get("data")
            if key:
                _cached_sec_key = key
                _sec_key_expiry = now + 1800  # Cache for 30 minutes
                return key
    except Exception as e:
        print(f"[-] Castle get_security_key error: {e}")
    return _cached_sec_key or "ZkpBVG0qa2dmSg=="

def get_lang_badge(lang_name: str) -> str:
    l = lang_name.lower()
    if "hindi" in l:
        return "🇮🇳 [Hindi Dubbed / Cloud Stream]"
    elif "tamil" in l:
        return "🇮🇳 [Tamil Dubbed / Cloud Stream]"
    elif "telugu" in l:
        return "🇮🇳 [Telugu Dubbed / Cloud Stream]"
    elif "korean" in l:
        return "🇰🇷 [Korean / Original Audio]"
    elif "english" in l:
        return "🇺🇸 [English Dubbed / Cloud Stream]"
    elif "japanese" in l:
        return "🇯🇵 [Japanese Audio / Cloud Stream]"
    return f"🌐 [{lang_name} Audio / Cloud Stream]"

async def fetch_castle_streams(media_type: str, title: str, year: str = "", season: int = None, episode: int = None) -> list:
    streams = []
    if not title:
        return []

    async with httpx.AsyncClient(timeout=4.5, follow_redirects=True) as client:
        try:
            sec_key = await get_security_key(client)
            if not sec_key:
                return []

            # 1. Search Castle
            clean_title = re.sub(r"[^\w\s]", " ", title).strip()
            params = {
                "channel": CHANNEL,
                "clientType": CLIENT,
                "keyword": clean_title,
                "lang": LANG,
                "mode": "1",
                "packageName": PKG,
                "page": "1",
                "size": "15"
            }
            search_url = f"{CASTLE_BASE}/film-api/v1.1.0/movie/searchByKeyword?{urllib.parse.urlencode(params)}"
            r_search = await client.get(search_url, headers=HEADERS)
            if r_search.status_code != 200:
                return []

            raw_cipher = r_search.text.strip()
            dec_search = decrypt_castle(raw_cipher, sec_key)
            search_data = json.loads(dec_search).get("data", {})
            rows = search_data.get("rows", [])
            if not rows:
                return []

            # Validate title match
            words = [w.lower() for w in clean_title.split() if len(w) > 1 and w.lower() not in ["the", "and", "a"]]
            matched_row = None
            for row in rows:
                r_title = (row.get("title") or row.get("name") or "").lower()
                if words and sum(1 for w in words if w in r_title) / len(words) >= 0.6:
                    matched_row = row
                    break

            if not matched_row:
                matched_row = rows[0]
                r_title = (matched_row.get("title") or "").lower()
                if words and sum(1 for w in words if w in r_title) / len(words) < 0.5:
                    return []

            castle_id = str(matched_row.get("id") or matched_row.get("movieId") or "")
            if not castle_id:
                return []

            # 2. Details
            det_url = f"{CASTLE_BASE}/film-api/v1.9.9/movie?channel={CHANNEL}&clientType={CLIENT}&lang={LANG}&movieId={castle_id}&packageName={PKG}"
            r_det = await client.get(det_url, headers=HEADERS)
            if r_det.status_code != 200:
                return []

            dec_det = decrypt_castle(r_det.text.strip(), sec_key)
            det_data = json.loads(dec_det).get("data", {})
            active_id = castle_id

            if media_type == "series" and season is not None:
                seasons = det_data.get("seasons", [])
                s_entry = next((s for s in seasons if s.get("number") == season), None)
                if s_entry and s_entry.get("movieId") and str(s_entry.get("movieId")) != castle_id:
                    s_movie_id = str(s_entry.get("movieId"))
                    det_url_s = f"{CASTLE_BASE}/film-api/v1.9.9/movie?channel={CHANNEL}&clientType={CLIENT}&lang={LANG}&movieId={s_movie_id}&packageName={PKG}"
                    r_det_s = await client.get(det_url_s, headers=HEADERS)
                    if r_det_s.status_code == 200:
                        dec_det_s = decrypt_castle(r_det_s.text.strip(), sec_key)
                        det_data = json.loads(dec_det_s).get("data", {})
                        active_id = s_movie_id

            episodes = det_data.get("episodes", [])
            target_ep = None
            if media_type == "series":
                target_ep_num = episode if episode is not None else 1
                target_ep = next((e for e in episodes if e.get("number") == target_ep_num), None)
            else:
                target_ep = episodes[0] if episodes else None

            if not target_ep:
                return []

            episode_id = str(target_ep.get("id") or "")
            if not episode_id:
                return []

            tracks = target_ep.get("tracks", [])
            # Priority order: Hindi, Tamil, Telugu, English, Original
            seen_combos = set()

            headers_post = dict(HEADERS)
            headers_post["Content-Type"] = "application/json"

            async def query_video(lang_id, lang_name, res_num, qual_label):
                try:
                    body = {
                        "mode": "1",
                        "appMarket": "GuanWang",
                        "clientType": CLIENT,
                        "woolUser": "true",
                        "apkSignKey": "ED0955EB04E67A1D9F3305B95454FED485261475",
                        "androidVersion": "13",
                        "movieId": active_id,
                        "episodeId": episode_id,
                        "isNewUser": "true",
                        "resolution": str(res_num),
                        "packageName": PKG
                    }
                    if lang_id:
                        body["languageId"] = str(lang_id)

                    video_api_url = f"{CASTLE_BASE}/film-api/v2.0.1/movie/getVideo2?clientType={CLIENT}&packageName={PKG}&channel={CHANNEL}&lang={LANG}"
                    rv = await client.post(video_api_url, headers=headers_post, json=body, timeout=3.5)
                    if rv.status_code == 200:
                        dec_v = decrypt_castle(rv.text.strip(), sec_key)
                        v_data = json.loads(dec_v).get("data", {})
                        if not v_data.get("permissionDenied"):
                            v_url = v_data.get("videoUrl")
                            combo = (v_url, lang_name, res_num)
                            if v_url and combo not in seen_combos:
                                seen_combos.add(combo)
                                badge = get_lang_badge(lang_name)
                                display_title = f"🎬 {title} S{season:02d}E{episode:02d}\n{badge}\n⚡ Direct Cloud Stream • Instant Play" if media_type == "series" else f"🎬 {title} ({year})\n{badge}\n⚡ Direct Cloud Stream • Instant Play"
                                distinct_url = f"{v_url}#audio={urllib.parse.quote(lang_name)}"
                                return {
                                    "name": f"OmniStream 🌍\nCastle CDN ⚡\n{qual_label}",
                                    "title": display_title,
                                    "url": distinct_url,
                                    "behaviorHints": {
                                        "notWebReady": False,
                                        "proxyHeaders": {
                                            "request": {
                                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                                                "Referer": "https://api.hlowb.com"
                                            }
                                        }
                                    }
                                }
                except Exception:
                    pass
                return None

            tasks = []
            if tracks:
                for t in tracks:
                    l_id = t.get("languageId")
                    l_name = t.get("languageName", "Multi")
                    # Try 720p HD and 1080p FHD
                    tasks.append(query_video(l_id, l_name, 3, "1080p FHD 🌟"))
                    tasks.append(query_video(l_id, l_name, 2, "720p HD ⚡"))
            else:
                tasks.append(query_video(None, "Original", 3, "1080p FHD 🌟"))
                tasks.append(query_video(None, "Original", 2, "720p HD ⚡"))

            import asyncio
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, dict) and res.get("url"):
                    streams.append(res)

        except Exception as e:
            print(f"[-] Castle engine error: {e}")

    # Prioritize Hindi streams to the top
    streams.sort(key=lambda s: 0 if "Hindi" in s.get("title", "") else 1)
    return streams
