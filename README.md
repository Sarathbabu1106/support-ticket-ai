# Support Ticket AI

An AI-powered support ticket analysis system that ingests CSV data, makes it queryable, answers natural language questions, detects anomalies, and exposes functionality via REST API and minimal UI.

---

## 🚀 Setup Instructions

> **Important:** Before re-running the project, delete the existing database to avoid conflicts:
> ```bash
> del tickets.db        # Windows Command Prompt
> # or
> rm tickets.db         # macOS / Linux / Git Bash
> ```

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sarathbabu1106/support-ticket-ai.git
   cd support-ticket-ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare the dataset**
   - Place `support_tickets.csv` in the project root.
   - (Optional but recommended before re-run) Delete old database:
     ```bash
     del tickets.db        # Windows
     # or
     rm tickets.db         # macOS / Linux
     ```
   - Run the loader script to create `tickets.db`:
     ```bash
     python scripts/load_csv.py
     ```

4. **Configure API key**
   - Create a `.env` file in the project root:
     ```env
     OPENROUTER_API_KEY=sk-or-v1-your_real_key_here
     ```
   - Or paste the key directly in `llm.py` if preferred.

5. **Run the backend**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Run the UI**
   ```bash
   streamlit run ui/app_ui.py
   ```

---

## 🏗️ Architecture Overview

### Data Layer
- SQLite database (`tickets.db`) created from `support_tickets.csv`.
- Schema includes ticket metadata: ID, category, priority, status, timestamps, agent, rating, summary.

### LLM Integration
- Natural language queries converted to SQL using OpenRouter free models.
- Post-processing safeguards ensure SQLite compatibility:
  - Case-insensitive filters
  - Removal of unsupported functions

### Backend (FastAPI)
Endpoints:
- `/query` → NL query → SQL → results  
- `/anomalies` → detect abnormal resolution times  
- `/health` → system status  

### Frontend (Streamlit)
- Simple UI for entering natural language queries and viewing results.

---

## 🤖 Model / Tools Used

- **LLM Provider:** OpenRouter  
- **Model Alias:** `openrouter/free` (routes to free models like Mistral or LLaMA automatically)  

**Libraries:**
- FastAPI – REST API  
- Streamlit – UI  
- SQLite3 – database  
- Requests – API calls  
- python-dotenv – environment variable management  

---

## 📊 Example Queries & Outputs

1. **How many tickets are currently open?**
   ```json
   {
     "sql": "SELECT COUNT(*) AS open_tickets_count FROM tickets WHERE LOWER(status) = LOWER('Open');",
     "result": [][111]
   }
   ```

2. **Which agent resolved the most tickets this month?**
   ```json
   {
     "sql": "WITH latest_month AS (SELECT substr(MAX(created_at), 7, 4) || '-' || substr(MAX(created_at), 4, 2) AS ym FROM tickets) SELECT agent_id, COUNT(*) AS resolved_ticket_count FROM tickets WHERE LOWER(status) = LOWER('Resolved') AND substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) = (SELECT ym FROM latest_month) GROUP BY agent_id ORDER BY resolved_ticket_count DESC LIMIT 1;",
     "result": [["AGT-06", 14]]
   }
   ```

3. **Show me all Critical tickets not resolved within 12 hours**
   ```json
   {
     "sql": "SELECT * FROM tickets WHERE LOWER(priority) = LOWER('High') AND resolution_time_hrs > 12;",
     "result": [["TKT-092","18-02-2024 14.42","Technical","High","Resolved",4.9,84.2,"AGT-11",4,"API timeout errors in production"], "..."]
   }
   ```

4. **What is the average customer rating for Technical category tickets?**
   ```json
   {
     "sql": "SELECT AVG(customer_rating) FROM tickets WHERE LOWER(category) = LOWER('Technical');",
     "result": [[3.7403846153846154]]
   }
   ```

5. **Are there any anomalies in resolution times this week?**
   ```json
   {
     "sql": "SELECT ticket_id, created_at, resolution_time_hrs FROM tickets WHERE LOWER(created_at) BETWEEN '2024-02-05' AND '2024-02-11' AND LOWER(resolution_time_hrs) > (SELECT AVG(resolution_time_hrs) FROM tickets WHERE LOWER(created_at) BETWEEN '2024-02-05' AND '2024-02-11');",
     "result": []
   }
   ```

---

## ⚠️ Known Limitations

- **LLM Variability:** SQL generation depends on the model; occasional malformed queries may occur.  
- **SQLite Constraints:** Functions like `STDDEV()` or advanced date handling are not supported; post-processing replaces them with safe alternatives.  
- **Dataset Year:** All ticket dates are from 2024; queries using `strftime('now')` or current year logic will fail.  
- **Free Model Routing:** Using `openrouter/free` means the backend model may change over time, slightly affecting query style or accuracy.  
- **Minimal UI:** Streamlit interface is basic; not production-ready.  

---

## 📝 Notes on Technical Constraints

The assessment required LLM usage for NL → SQL conversion. Allowed options: Ollama (local), Groq free tier, Hugging Face Inference API free tier, or any locally runnable model.

- **Groq:** Account only had access to `whisper-large-v3` (speech-to-text), no text models for SQL.  
- **Hugging Face:** Attempted, but DNS/server/firewall issues blocked access despite a working internet connection.  
- **Local models (Ollama/LM Studio):** Ignored because my system cannot handle large model execution.  

**Final Choice:** OpenRouter free API. It meets the constraint of “no paid services” and provides reliable free LLM access for SQL generation.

---

## 📂 Project Folder Architecture

```text
support-ticket-ai/
│
├── app/                         # FastAPI backend
│   ├── __init__.py
│   ├── main.py                  # Entry point for FastAPI (routes: /query, /anomalies, /health)
│   ├── llm.py                   # LLM integration (OpenRouter API, SQL cleaning)
│   └── db.py                    # SQLite connection & query execution
│
├── scripts/
│   └── load_csv.py              # Script to load support_tickets.csv → tickets.db
│
├── ui/                          # Streamlit frontend
│   └── app_ui.py                # Streamlit app for user queries and results
│
├── data/
│   ├── support_tickets.csv      # Raw dataset
│   └── tickets.db               # SQLite database generated from CSV
│
├── .env                         # Environment variables (OPENROUTER_API_KEY)
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
└── .gitignore                   # Ignore db files, env, cache, etc.
```

---

## 🖥️ Commands to Run the Project

> **Note:** Before re-running the project, delete the existing database to ensure a clean setup:
> ```bash
> del tickets.db        # Windows Command Prompt
> # or
> rm tickets.db         # macOS / Linux / Git Bash
> ```

1. **Clone and enter the repo**
   ```bash
   git clone https://github.com/Sarathbabu1106/support-ticket-ai.git
   cd support-ticket-ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional but recommended before re-run) Delete old database**
   ```bash
   del tickets.db        # Windows
   # or
   rm tickets.db         # macOS / Linux
   ```

4. **Load dataset into SQLite**
   ```bash
   python scripts/load_csv.py
   ```

5. **Run the FastAPI backend**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Run the Streamlit UI**
   ```bash
   streamlit run ui/app_ui.py
   ```
