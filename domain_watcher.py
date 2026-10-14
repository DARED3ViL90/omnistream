"""
Domain Watcher Module for OmniStream 🌍
Automatically extracts verified, active domains for VegaMovies, HDHub4u, TamilMV, etc.
directly from FMHY (FreeMediaHeckYeah) official curated GitHub repository.
Prevents scraping fake clone / adware phishing sites.
"""

import re
import time
import httpx

FMHY_NON_ENGLISH_URL = "https://raw.githubusercontent.com/fmhy/edit/main/docs/non-english.md"
FMHY_VIDEO_URL = "https://raw.githubusercontent.com/fmhy/edit/main/docs/video.md"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Default fallback domains if network fetch fails
_CACHED_DOMAINS = {
    "vegamovies": "https://1vegamovies.baby/",
    "hdhub4u": "https://hdhub4u.bi/",
    "tamilmv": "https://www.1tamilmv.lease/",
}
_LAST_FETCH_TIME = 0
_CACHE_TTL_SECONDS = 6 * 3600  # 6 hours TTL


async def refresh_verified_domains() -> dict[str, str]:
    global _CACHED_DOMAINS, _LAST_FETCH_TIME
    now = time.time()
    
    # Return cached if still fresh
    if _LAST_FETCH_TIME and (now - _LAST_FETCH_TIME < _CACHE_TTL_SECONDS):
        return _CACHED_DOMAINS

    print("[*] DomainWatcher: Fetching latest verified domains from FMHY...")
    discovered = dict(_CACHED_DOMAINS)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(FMHY_NON_ENGLISH_URL, headers={"User-Agent": USER_AGENT})
            if resp.status_code == 200:
                text = resp.text
                matches = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', text)
                for name, link in matches:
                    clean_name = name.lower().strip()
                    clean_link = link.strip().rstrip("/") + "/"
                    
                    if "vegamovies" in clean_name or "vegamovies" in clean_link:
                        if not any(x in clean_link for x in ["telegram", "t.me", "discord"]):
                            discovered["vegamovies"] = clean_link
                    elif "hdhub" in clean_name or "hdhub4u" in clean_link:
                        if not any(x in clean_link for x in ["telegram", "t.me", "discord"]):
                            discovered["hdhub4u"] = clean_link
                    elif "tamilmv" in clean_name or "1tamilmv" in clean_link:
                        if not any(x in clean_link for x in ["telegram", "t.me", "discord"]):
                            discovered["tamilmv"] = clean_link

                _CACHED_DOMAINS = discovered
                _LAST_FETCH_TIME = now
                print(f"[+] DomainWatcher: Updated active domains successfully: {_CACHED_DOMAINS}")
        except Exception as e:
            print(f"[-] DomainWatcher error: {e}. Keeping cached domains.")

    return _CACHED_DOMAINS


def get_domain(service_name: str) -> str:
    """Returns current active domain for a requested service."""
    return _CACHED_DOMAINS.get(service_name.lower(), "")
