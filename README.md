# 🌌 Nikoly Beatriz – Full-Stack Developer Portfolio

Welcome to the personal software engineering portfolio of **Nikoly Beatriz Schmaeller Loch**. This repository contains the source code for the interactive cosmic-themed portfolio web application and houses the core production-ready projects developed across backend architectures, local AI integrations, desktop POS software, and mobile eSports platforms.

---

## 🚀 Live Featured Projects

### 1. [PharmaPOS – Multi-Branch POS & FEFO Analytics](projects/pharmacy-pos/)
- **Domain**: Pharmaceutical Inventory, Cashier POS & Business Intelligence
- **Stack**: Python, Tkinter, Matplotlib, SQLite, MySQL, Bcrypt
- **Highlights**:
  - Independent multi-branch stock synchronization.
  - Strict **FEFO (First Expired, First Out)** algorithmic inventory deduction.
  - Role-based security (RBAC) with cryptographic password salting.
  - Real-time BI dashboard with interactive Matplotlib sales trends and KPI metrics.
  - Custom thermal ticket printing engine with batch tracking.

### 2. [FormIA – AI-Powered Smart Form & Local LLM Assistant](projects/formia-ai-form/)
- **Domain**: Dynamic Forms, Local AI, Synthetic Data Generation
- **Stack**: Python, Flask, Ollama, Qwen2.5 (3B), MySQL, SQL Server, Faker, JavaScript
- **Highlights**:
  - On-device local LLM inference using Ollama with Qwen2.5 (zero external API latency or costs).
  - Multi-database engine compatibility (MySQL PyMySQL & Microsoft SQL Server pyodbc).
  - Synthetic test profile generation using locale-aware Faker models.
  - Embedded conversational AI assistant for profile data querying and record validation.

### 3. [Lotus – Gaming & eSports Tournament Platform](projects/lotus-esports/)
- **Domain**: Gaming Hub, eSports Tournament Brackets & Streaming Simulation
- **Stack**: Python, Flet (Flutter UI engine), FastAPI, Uvicorn, MySQL, Pydantic, HTTPX
- **Highlights**:
  - Responsive cross-platform interface (Desktop & Android) with custom midnight-gamer aesthetics.
  - Dynamic tournament bracket creator with DatePicker and participant limit counters.
  - Dual authentication: asynchronous FastAPI REST backend when online, cryptographic SHA-256 fallback store when offline.
  - Live stream viewer simulation with interactive reactions, chats, and community feed.

---

## 🎓 Teacher & Academic Evaluator Portal

The portfolio includes a dedicated **Academic Evaluator Portal** designed specifically for professors and academic evaluators to inspect projects, assign scores (1 to 10), and submit detailed technical feedback.

### 🔑 Demo Teacher Credentials
- **Access URL**: `/login` (via the **Teacher Portal** navigation button)
- **Username**: `professor`
- **Password**: `prof2026`
- **Role**: Academic Faculty Evaluator

### 📋 Features in Evaluator Dashboard (`/evaluator`):
- **Candidate Overview**: Student profile, academic degree progress (TSDS - 2nd Year).
- **Interactive Project Rubric**: Submit architectural design notes, code quality reviews, and general comments for any project.
- **Persistent Feedback Log**: Evaluations are stored in the database with timestamps, scores, and status tags (`Outstanding`, `Approved`, `Needs Revision`).
- **Review Management**: Delete or update previous evaluations.

---

- **Backend**: Python 3.9+, Flask, Flask-SQLAlchemy, Jinja2
- **Databases**: SQLite (zero-config default), MySQL (production configuration)
- **Frontend**: Responsive HTML5, Modern CSS3 Flexbox/Grid, Cosmic Glow Effects, Vanilla JavaScript
- **Environment**: Virtualenv, Python-dotenv, Git version control

---

## 💻 Local Setup & Running

### 1. Clone Repository
```bash
git clone https://github.com/nibeshlofreak-byte/portfolio.git
cd portfolio
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Web Application
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your browser. Default projects will be automatically seeded into SQLite on startup.

---

## 📬 Contact & Connect

- **Email**: [nikolybeatrizschmaellerloxh@gmail.com](mailto:nikolybeatrizschmaellerloxh@gmail.com)
- **GitHub**: [github.com/nibeshlofreak-byte](https://github.com/nibeshlofreak-byte)
- **LinkedIn**: [linkedin.com/in/nikolybeatriz](https://www.linkedin.com/in/nikolybeatriz)

---
*© 2026 Nikoly Beatriz Schmaeller Loch. All rights reserved.*
