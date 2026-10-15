"""
OmniStream 🌍 - Cyber-Cinema Web Configuration Interface
Production-grade Glassmorphism Web App for Stremio Configuration.
"""

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OmniStream 🌍 | Configure Stremio Addon</title>
  <link rel="icon" type="image/png" href="/logo.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Outfit:wght@300;400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #07090E;
      --card-bg: rgba(15, 20, 31, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --card-hover: rgba(255, 255, 255, 0.14);
      --cyan: #00F0FF;
      --cyan-glow: rgba(0, 240, 255, 0.35);
      --purple: #A855F7;
      --purple-glow: rgba(168, 85, 247, 0.35);
      --emerald: #10B981;
      --text-main: #F3F4F6;
      --text-muted: #9CA3AF;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg);
      color: var(--text-main);
      font-family: 'Outfit', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      padding: 40px 20px 80px;
      overflow-x: hidden;
      position: relative;
    }

    /* Ambient Cosmic Lighting */
    body::before {
      content: "";
      position: fixed;
      top: -20%;
      left: 20%;
      width: 600px;
      height: 600px;
      background: radial-gradient(circle, var(--purple-glow) 0%, transparent 70%);
      filter: blur(100px);
      z-index: -1;
      pointer-events: none;
    }
    body::after {
      content: "";
      position: fixed;
      bottom: -10%;
      right: 15%;
      width: 700px;
      height: 700px;
      background: radial-gradient(circle, var(--cyan-glow) 0%, transparent 70%);
      filter: blur(120px);
      z-index: -1;
      pointer-events: none;
    }

    .container {
      max-width: 680px;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    /* Header */
    .header {
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 14px;
      margin-bottom: 12px;
    }

    .logo-wrapper {
      position: relative;
      width: 108px;
      height: 108px;
      border-radius: 26px;
      padding: 4px;
      background: linear-gradient(135deg, var(--cyan), var(--purple));
      box-shadow: 0 0 35px var(--cyan-glow);
      animation: float 4s ease-in-out infinite;
    }

    @keyframes float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-8px); }
    }

    .logo-img {
      width: 100%;
      height: 100%;
      border-radius: 22px;
      object-fit: cover;
      background: #000;
      display: block;
    }

    .title-row {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: center;
    }

    .title {
      font-size: 34px;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(90deg, #FFFFFF, var(--cyan));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(168, 85, 247, 0.18);
      border: 1px solid rgba(168, 85, 247, 0.4);
      color: #D8B4FE;
      letter-spacing: 0.5px;
    }

    .subtitle {
      color: var(--text-muted);
      font-size: 15px;
      max-width: 460px;
      line-height: 1.5;
    }

    /* Glass Cards */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 24px;
      backdrop-filter: blur(20px);
      transition: all 0.25s ease;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .card:hover {
      border-color: var(--card-hover);
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }

    .card-title {
      font-size: 16px;
      font-weight: 700;
      color: #FFFFFF;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .card-title span {
      font-size: 18px;
    }

    /* Toggles & Checkboxes */
    .option-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      gap: 16px;
    }

    .option-row:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }

    .option-info {
      display: flex;
      flex-direction: column;
      gap: 3px;
    }

    .option-label {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-main);
    }

    .option-desc {
      font-size: 12px;
      color: var(--text-muted);
    }

    /* Custom Switch */
    .switch {
      position: relative;
      display: inline-block;
      width: 44px;
      height: 24px;
      flex-shrink: 0;
    }

    .switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }

    .slider {
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: rgba(255, 255, 255, 0.12);
      transition: .3s;
      border-radius: 24px;
      border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .slider:before {
      position: absolute;
      content: "";
      height: 18px;
      width: 18px;
      left: 2px;
      bottom: 2px;
      background-color: #FFFFFF;
      transition: .3s;
      border-radius: 50%;
    }

    input:checked + .slider {
      background: linear-gradient(90deg, var(--cyan), var(--purple));
      border-color: transparent;
      box-shadow: 0 0 10px var(--cyan-glow);
    }

    input:checked + .slider:before {
      transform: translateX(20px);
    }

    /* Select Inputs */
    .custom-select, .custom-input {
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: var(--text-main);
      padding: 10px 14px;
      border-radius: 12px;
      font-family: inherit;
      font-size: 13px;
      outline: none;
      transition: border 0.2s ease;
      width: 100%;
    }

    .custom-select:focus, .custom-input:focus {
      border-color: var(--cyan);
      box-shadow: 0 0 12px var(--cyan-glow);
    }

    /* Providers Pill Grid */
    .pill-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #E2E8F0;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--emerald);
      box-shadow: 0 0 8px var(--emerald);
    }

    /* Actions Section */
    .install-box {
      display: flex;
      flex-direction: column;
      gap: 14px;
      margin-top: 10px;
    }

    .btn-primary {
      background: linear-gradient(90deg, #00D2FF 0%, #7928CA 100%);
      color: #FFFFFF;
      border: none;
      padding: 16px 24px;
      border-radius: 16px;
      font-family: inherit;
      font-size: 16px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 4px 25px rgba(0, 210, 255, 0.4);
      transition: all 0.25s ease;
      text-align: center;
      text-decoration: none;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }

    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 35px rgba(121, 40, 202, 0.5);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #E2E8F0;
      padding: 13px 20px;
      border-radius: 14px;
      font-family: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(255, 255, 255, 0.2);
    }

    .url-preview {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      background: rgba(0, 0, 0, 0.45);
      padding: 10px 14px;
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      color: var(--text-muted);
      overflow-x: auto;
      white-space: nowrap;
    }

    .toast {
      position: fixed;
      bottom: 24px;
      background: #10B981;
      color: #FFFFFF;
      padding: 12px 24px;
      border-radius: 999px;
      font-weight: 600;
      font-size: 14px;
      box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
      opacity: 0;
      transform: translateY(20px);
      transition: all 0.3s ease;
      pointer-events: none;
      z-index: 99;
    }

    .toast.show {
      opacity: 1;
      transform: translateY(0);
    }

    .footer {
      text-align: center;
      margin-top: 20px;
      color: #64748B;
      font-size: 12px;
    }
  </style>
</head>
<body>

  <div class="container">
    <!-- Header -->
    <div class="header">
      <div class="logo-wrapper">
        <img src="/logo.png" alt="OmniStream Logo" class="logo-img">
      </div>
      <div class="title-row">
        <h1 class="title">OmniStream 🌍</h1>
        <span class="badge">v2.8.0 PRO</span>
      </div>
      <p class="subtitle">Universal Stremio Addon with 4K IMAX, 80GB Remux, Nyaa Anime, The Pirate Bay & Smart Prioritization.</p>
    </div>

    <!-- Card 1: Priorities -->
    <div class="card">
      <div class="card-title">
        <span>🇮🇳</span> Smart Language Prioritization
      </div>
      <div class="option-row">
        <div class="option-info">
          <div class="option-label">Rank 1: TamilMV & Indian Audio</div>
          <div class="option-desc">Hindi Dubbed, Tamil, Telugu, Malayalam releases placed at the very top.</div>
        </div>
        <label class="switch">
          <input type="checkbox" id="prioritize_hindi" checked onchange="updateConfig()">
          <span class="slider"></span>
        </label>
      </div>

      <div class="option-row">
        <div class="option-info">
          <div class="option-label">Rank 2: Multi-Audio & Dual Audio Packs</div>
          <div class="option-desc">Multi-language tracks and Netflix/Prime global WebRips.</div>
        </div>
        <label class="switch">
          <input type="checkbox" id="multi_audio" checked onchange="updateConfig()">
          <span class="slider"></span>
        </label>
      </div>

      <div class="option-row">
        <div class="option-info">
          <div class="option-label">Rank 3: 4K IMAX & 70GB+ Remux Beasts</div>
          <div class="option-desc">Dolby Vision & TrueHD Atmos 7.1 home-theatre master files highlighted.</div>
        </div>
        <label class="switch">
          <input type="checkbox" id="imax_remux" checked onchange="updateConfig()">
          <span class="slider"></span>
        </label>
      </div>

      <div class="option-row">
        <div class="option-info">
          <div class="option-label">Rank 4: Anime Engine (NyaaSi & Kitsu)</div>
          <div class="option-desc">Direct integration with Nyaa.si and Kitsu.io anime catalogs.</div>
        </div>
        <label class="switch">
          <input type="checkbox" id="anime_engine" checked onchange="updateConfig()">
          <span class="slider"></span>
        </label>
      </div>
    </div>

    <!-- Card 2: Filters -->
    <div class="card">
      <div class="card-title">
        <span>🎬</span> Quality & Stream Filters
      </div>

      <div class="option-row">
        <div class="option-info">
          <div class="option-label">Clean Cinema Mode</div>
          <div class="option-desc">Filter out low-quality CAM, Telesync, and HDTS theatre recordings.</div>
        </div>
        <label class="switch">
          <input type="checkbox" id="exclude_cam" onchange="updateConfig()">
          <span class="slider"></span>
        </label>
      </div>

      <div class="option-row">
        <div class="option-info">
          <div class="option-label">Maximum Stream File Size</div>
          <div class="option-desc">Cap stream size to prevent Smart TV storage or buffering issues.</div>
        </div>
        <div style="width: 170px;">
          <select id="max_gb" class="custom-select" onchange="updateConfig()">
            <option value="0" selected>No Limit (80GB+ 💎)</option>
            <option value="40">40 GB (High-End)</option>
            <option value="20">20 GB (TV Sweetspot)</option>
            <option value="10">10 GB (Fast Streaming)</option>
            <option value="5">5 GB (Lightweight)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Card 3: Active Engines -->
    <div class="card">
      <div class="card-title">
        <span>⚡</span> Active Global Indexers (All Online)
      </div>
      <div class="pill-grid">
        <div class="pill"><span class="dot"></span> Global DHT Swarm (torrents-csv)</div>
        <div class="pill"><span class="dot"></span> The Pirate Bay (apibay.org)</div>
        <div class="pill"><span class="dot"></span> NyaaSi Anime (nyaa.si)</div>
        <div class="pill"><span class="dot"></span> Kitsu Anime Catalog</div>
        <div class="pill"><span class="dot"></span> 8 Turbo Announce Trackers</div>
        <div class="pill"><span class="dot"></span> FMHY Verified Mirror Watcher</div>
      </div>
    </div>

    <!-- Card 4: Optional Debrid -->
    <div class="card">
      <div class="card-title">
        <span>🚀</span> Cloud Debrid / Real-Debrid (Optional)
      </div>
      <div class="option-desc" style="margin-top:-6px;">
        Leave blank for 100% Free Peer-to-Peer torrent streaming. If you have a Real-Debrid API key, paste it here for 1Gbps direct cached playback.
      </div>
      <input type="password" id="debrid_key" class="custom-input" placeholder="Real-Debrid API Token (Optional)" oninput="updateConfig()">
    </div>

    <!-- Card 5: Install Actions -->
    <div class="card install-box">
      <div class="card-title">
        <span>🍿</span> Ready to Watch
      </div>
      <div class="url-preview" id="manifest_url">Generating URL...</div>
      <a href="#" id="install_btn" class="btn-primary">
        ⚡ Install Addon in Stremio
      </a>
      <button class="btn-secondary" onclick="copyManifestUrl()">
        📋 Copy Manifest URL (for Android TV / Web)
      </button>
    </div>

    <div class="footer">
      OmniStream 🌍 Core Engine • Built by OfficialTanishSharma • 24/7 Cloud Deployed
    </div>
  </div>

  <div class="toast" id="toast">Manifest URL copied to clipboard!</div>

  <script>
    function getBaseHost() {
      return window.location.origin;
    }

    function buildConfigString() {
      const config = {
        h: document.getElementById('prioritize_hindi').checked ? 1 : 0,
        m: document.getElementById('multi_audio').checked ? 1 : 0,
        i: document.getElementById('imax_remux').checked ? 1 : 0,
        a: document.getElementById('anime_engine').checked ? 1 : 0,
        nc: document.getElementById('exclude_cam').checked ? 1 : 0,
        gb: parseInt(document.getElementById('max_gb').value) || 0,
        rd: document.getElementById('debrid_key').value.trim()
      };

      // Base64 encode JSON
      const jsonStr = JSON.stringify(config);
      return btoa(jsonStr).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    function updateConfig() {
      const host = getBaseHost();
      const cfg = buildConfigString();
      const manifestUrl = `${host}/${cfg}/manifest.json`;
      const stremioDeepLink = `stremio://${host.replace(/^https?:\/\//, '')}/${cfg}/manifest.json`;

      document.getElementById('manifest_url').innerText = manifestUrl;
      document.getElementById('install_btn').href = stremioDeepLink;
    }

    function copyManifestUrl() {
      const url = document.getElementById('manifest_url').innerText;
      navigator.clipboard.writeText(url).then(() => {
        const toast = document.getElementById('toast');
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2500);
      });
    }

    // Init on load
    window.onload = updateConfig;
  </script>
</body>
</html>
"""
