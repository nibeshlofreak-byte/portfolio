# 🤖 FormIA - AI-Powered Smart Form Engine & Local LLM Assistant

FormIA is an intelligent web application combining dynamic data-entry forms with local Artificial Intelligence (Ollama with **Qwen 2.5:3b**). It allows users to register, validate, and query profile records while leveraging a private on-device Large Language Model to auto-generate realistic synthetic testing data and perform interactive user analytics.

---

## 🌟 Key Features

- **Local LLM Integration (Ollama + Qwen2.5)**: Runs completely offline without cloud API costs or privacy leaks. Automatically detects and pulls the model if not installed.
- **Smart Form Processing**: Multi-attribute validation for personal identities, employment statuses, and health insurance providers.
- **Automated Synthetic Generation**: Generates contextual, realistic data on-demand using Faker (`es_AR` / international locales) and AI reasoning.
- **Multi-Database Support**:
  - `app.py`: Configured for MySQL with PyMySQL connection pooling.
  - `app2.py`: Configured for enterprise Microsoft SQL Server with native Windows ODBC (`pyodbc`).
- **Interactive AI Assistant Chat**: Chat with the embedded local assistant to query statistics, analyze profiles, and ask questions about submitted data.
- **Responsive Web UI**: Built with HTML5, CSS3, dynamic modals, and responsive JavaScript.

---

## 🏗️ Architecture & Structure

```text
formia-ai-form/
├── app.py               # Main Flask server (MySQL / PyMySQL configuration)
├── app2.py              # Secondary Flask server (SQL Server / pyodbc configuration)
├── requirements.txt     # Python dependencies
├── static/              # CSS stylesheets, animations, and client-side scripts
│   ├── css/style.css
│   └── js/main.js
├── templates/           # Jinja2 templates (Base, Form, AI Assistant, Index)
│   ├── base.html
│   ├── index.html
│   ├── formulario.html
│   └── ia.html
├── app2/                # Supplementary templates and themes for app2
│   ├── static/
│   └── templates/
└── README.md            # Project documentation
```

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.9+
- (Optional for AI queries) [Ollama](https://ollama.ai) installed with `qwen2.5:3b`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
# Launch MySQL version:
python app.py

# Launch SQL Server version:
python app2.py
```

Access the application in your browser at `http://127.0.0.1:5000`.

---

## 🛠️ Tech Stack
- **Backend**: Python, Flask, Jinja2
- **Databases**: MySQL (PyMySQL) / Microsoft SQL Server (pyodbc)
- **Local AI Engine**: Ollama with Qwen2.5 (3B parameters)
- **Synthetic Data**: Faker
- **Frontend**: HTML5, Modern CSS3 Flexbox/Grid, Vanilla JavaScript
