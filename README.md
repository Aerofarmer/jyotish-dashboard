# 🕉️ Jyotish Vedic Dashboard

> **Free, open-source Vedic astrology software** — Kundli, Panchang, Transit, Dasha, Daily Predictions, and a full interactive calendar. Runs entirely on your machine; no subscription, no ads.

---

## ✨ Features

| Section | What you get |
|---|---|
| **Kundli (Birth Chart)** | North-Indian & Navamsa D9 canvas chart · planet positions · dignity · nakshatra |
| **Panchang** | Tithi · Nakshatra · Yoga · Karana · Vara · Tarabala · Chandra Bala · Abhijit Muhurta |
| **Transit Chart** | Live planetary positions · nakshatra → natal-house warning map · danger/warning/positive alerts |
| **Vimshottari Dasha** | Full Mahadasha → Antardasha → Pratyantardasha tree with timeline bar |
| **Daily Predictions** | Overall score · मन की बात (emotional state) · Love · Career · Major changes · Enemy/Friend of the day · Planet-by-planet forecast |
| **Prediction Calendar** | Month view with per-day quality dots (Excellent→Difficult) · click any day for deep panchang detail · navigate to that day's predictions |
| **Sky panel** | Sunrise · Sunset · Moonrise · Moonset · Solar noon · Day length · Rahu Kaal · Gulika Kaal · Yamaghanta · Moon phase |
| **Save charts** | Store multiple Kundlis locally; load/delete from the home screen |
| **Auto location** | IP-based city pre-fill · geocode by city name · browser GPS button |

All calculations use the **Lahiri ayanamsa** (sidereal zodiac, Whole Sign houses) via **Swiss Ephemeris** — the same engine used by professional Jyotish software.

---

## 🖥️ Screenshots

```
Home / Birth form          Kundli chart              Transit warnings
┌──────────────┐          ┌──────────────┐           ┌──────────────┐
│ ॐ Jyotish   │          │ North-Indian │           │ 0 Danger     │
│ Vedic Dash  │          │ 4×4 grid     │           │ 3 Warning    │
│             │          │ canvas chart │           │ 2 Positive   │
│ [Birth form]│          │              │           │ [Nak table]  │
└──────────────┘          └──────────────┘           └──────────────┘

Prediction Calendar                     Day detail panel
┌──────────────────────────────┐        ┌────────────────────────┐
│ < May 2026 >                 │        │ 11 May 2026  Monday    │
│ Sun Mon Tue Wed Thu Fri Sat  │        │ ★ 9/10  Excellent      │
│  ●   ●   ●   ●   ●   ●   ●  │  ───▶  │ Vara: Friday   Good    │
│ Good Exc Cau Good Exc Mod G  │        │ Tithi: Navami  Neutral │
│ [click any day]              │        │ Nakshatra: Swati Good  │
└──────────────────────────────┘        │ Sunrise 05:29 · ...    │
                                        │ [Predictions →]        │
                                        └────────────────────────┘
```

---

## 🚀 Quick Start — 3 Ways

### Option 1 · Local Python (recommended for development)

```bash
# 1. Clone
git clone https://github.com/Aerofarmer/jyotish-dashboard.git
cd jyotish-dashboard

# 2. Set up environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure (optional — app works without API keys)
cp .env.example .env
# edit .env if you want OpenCage geocoding (free tier)

# 4. Download Swiss Ephemeris data
mkdir -p ephe
cd ephe
wget https://www.astro.com/ftp/swisseph/ephe/seas_18.se1
wget https://www.astro.com/ftp/swisseph/ephe/semo_18.se1
wget https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1
cd ..

# 5. Run
SE_EPHE_PATH=./ephe python run.py
# Opens http://localhost:5001 automatically
```

### Option 2 · Docker (recommended for servers / one-command deploy)

```bash
# 1. Clone
git clone https://github.com/Aerofarmer/jyotish-dashboard.git
cd jyotish-dashboard

# 2. Copy env file
cp .env.example .env
# (edit .env to add your FLASK_SECRET_KEY at minimum)

# 3. Build and run
docker compose up -d

# App is now at http://localhost:5000
# Logs:
docker compose logs -f
```

> Docker automatically downloads the Swiss Ephemeris files on first build.  
> Data is persisted in a named volume so rebuilds are fast.

### Option 3 · Linux Desktop (Ubuntu / Debian — installs as a launcher icon)

```bash
git clone https://github.com/Aerofarmer/jyotish-dashboard.git
cd jyotish-dashboard
chmod +x install.sh && ./install.sh
# Adds "Jyotish Dashboard" to your app menu
# Double-click to launch — opens in your browser automatically
```

---

## 🔄 Sync / Update (all methods)

```bash
# Pull latest changes
git pull origin main

# Local Python — restart the app
SE_EPHE_PATH=./ephe python run.py

# Docker — rebuild and restart
docker compose up -d --build

# Linux desktop — re-run install script (safe to re-run)
./install.sh
```

---

## 🌐 API Keys — What's required?

| Key | Required? | What it enables | Get it free |
|---|---|---|---|
| `FLASK_SECRET_KEY` | **Yes** | Session security (any random string) | Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `OPENCAGE_API_KEY` | No | Better geocoding accuracy | [opencagedata.com](https://opencagedata.com) — 2500 req/day free |
| `TIMEZONEDB_API_KEY` | No | Timezone fallback | [timezonedb.com](https://timezonedb.com) — free |
| `PROKERALA_*` | No | Supplemental panchang | [api.prokerala.com](https://api.prokerala.com) |

**Without any API keys:** geocoding uses Nominatim (OpenStreetMap, no key needed), timezone is computed offline via `timezonefinder`. The app is fully functional.

---

## 🏗️ Architecture

```
jyotish-dashboard/
├── app/
│   ├── astrology/
│   │   ├── calculator.py   # Planet positions, lagna, nakshatra (pyswisseph)
│   │   ├── dasha.py        # Vimshottari Dasha engine
│   │   ├── panchang.py     # 5-limb panchang + muhurta + sky (ephem)
│   │   ├── predictions.py  # Daily prediction engine
│   │   └── store.py        # JSON chart persistence
│   ├── api/
│   │   └── external.py     # Geocoding, IP location
│   ├── templates/          # Jinja2 HTML templates
│   ├── static/
│   │   ├── css/style.css   # Light Vedic theme
│   │   └── js/chart.js     # Canvas North-Indian chart renderer
│   └── routes.py           # Flask routes + API endpoints
├── ephe/                   # Swiss Ephemeris data files (downloaded separately)
├── data/                   # Saved charts (local JSON, git-ignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── run.py
```

**Tech stack:** Python 3.11 · Flask · pyswisseph · ephem · Bootstrap 5 · Canvas 2D · Nominatim · Docker

---

## 🖥️ API Endpoints (self-hosted)

| Endpoint | Description |
|---|---|
| `GET /api/sky` | Sunrise, sunset, moon times, Rahu Kaal for a location |
| `GET /api/month-scores` | Per-day panchang quality scores for the calendar |
| `GET /api/day-detail` | Full panchang + sky + breakdown for a single date |
| `GET /api/geocode` | City name → lat/lon + timezone |
| `GET /api/panchang` | Full panchang JSON for any date |

---

## 📋 Requirements

- **Python 3.10+** (3.11 recommended)
- **C compiler** (for pyswisseph): `sudo apt install gcc` on Debian/Ubuntu
- **Swiss Ephemeris files** — downloaded during install (3 files, ~30 MB total)
- **Internet** — only for geocoding and IP location; all astro calculations are offline

---

## 🔐 Privacy

All calculations happen **locally on your machine**. Birth data is stored only in your browser session (cleared when you close the tab) or in `data/charts.json` on your own disk. Nothing is sent to any external server except:
- Nominatim (OpenStreetMap) for city → coordinates lookup
- ip-api.com for auto-detecting your city on the home page (no account needed)

---

## 📜 License

MIT — free to use, modify, and self-host. Attribution appreciated.

---

## 🙏 Credits

- **Swiss Ephemeris** by Astrodienst AG — planet position engine
- **pyswisseph** — Python bindings
- **ephem** — sunrise/moonrise calculations
- **Nominatim / OpenStreetMap** — geocoding
- **Bootstrap 5** + **Bootstrap Icons** — UI framework
