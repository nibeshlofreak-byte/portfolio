# 🎮 Lotus - Gaming & eSports Tournament Platform

Lotus is a full-featured cross-platform application for gamers, tournament organizers, and eSports fans built with **Python & Flet** (powered by Flutter's UI engine) backed by a private **FastAPI & MySQL** backend with offline-first authentication fallback.

---

## 🌟 Visual Identity & Design System
- **Gaming Dark Theme**: Deep Midnight Navy background (`#090D1A`, `#131B2E`)
- **Primary Brand Accent**: High-voltage Neon Fuchsia (`#FF1493`) with glow effects
- **Typography & Details**: Crisp White (`#FFFFFF`) and Muted Slate Blue (`#8E9BB5`)
- **Status Accents**: Neon Cyberpunk Green (`#00FFA3`) and official game badges (Valorant, EA Sports FC, League of Legends)

---

## 🚀 Key Modules & Capabilities

1. **Authentication Portal**:
   - Dynamic toggle between Gamertag/Email and secure password.
   - Dual-mode: Connects to local FastAPI backend when online, falls back gracefully to a cryptographically hashed local offline auth store.

2. **Dashboard & Feed**:
   - Hero spotlight for major tournament championships with prize pool statistics.
   - Quick-access grid: Events, Live Streams, Community, and Team Chats.
   - Persistent Bottom Navigation: `[Home, Tournaments, Schedule, Live, Social]`.

3. **Tournament & Bracket Manager**:
   - Event creation wizard: Title, Game selection, Platform (PC, PlayStation, Xbox, Crossplay), and participant limits with haptic counters.
   - Interactive calendar with DatePicker integration.
   - Real-time tournament registration with Gamertag and Discord Tag verification.

4. **Live Stream Hub**:
   - Live stream player simulation with dynamic viewer counters and interactive reaction likes.
   - Real-time tournament chat feed.

5. **Community Hub**:
   - Interactive social feed for gaming updates, team recruitment, and highlight shares.

---

## 🏗️ Architecture & Structure

```text
lotus-esports/
├── assets/                  # Brand logos, icons, and artwork
├── api_server.py            # FastAPI REST backend for user registration and auth
├── api_client.py            # Async HTTP client interfacing with backend
├── auth_errors.py           # Custom exception definitions
├── auth_store.py            # MySQL database queries and credential validations
├── offline_auth.py          # Offline cryptographic fallback authentication store
├── database.sql             # MySQL database schema initialization script
├── main.py                  # Core Flet application and interactive UI screens
├── pyproject.toml           # Project metadata & Flet packaging configurations
├── requirements.txt         # Dependencies list
└── README.md                # System documentation
```

---

## 🛠️ Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Backend API (Optional for networked mode)
```bash
# Windows
start_lotus_api.bat
# Or manually with uvicorn:
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### 3. Run the Client App
```bash
python main.py
```

---

## 💻 Tech Stack
- **UI Engine**: Python Flet (Flutter rendering engine)
- **API Server**: FastAPI, Uvicorn, Pydantic
- **Database**: MySQL Connector / SQLite local fallback
- **Security**: SHA-256 + cryptographic salting
- **Networking**: HTTPX asynchronous client
