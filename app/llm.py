import os
import re
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def clean_and_fix_sql(sql: str) -> str:
    """Post-processing safeguards for SQLite compatibility and data quirks."""
    # 1. Case insensitivity for text columns
    target_columns = ["status", "priority", "category"]
    for col in target_columns:
        pattern = re.compile(rf"\b({col})\s*=\s*(['\"][^'\"]+['\"])", re.IGNORECASE)
        sql = pattern.sub(rf"LOWER(\1) = LOWER(\2)", sql)

    # 2. Strip invalid strftime('now') filters
    sql = re.sub(r"\s*AND\s+substr\(created_at,\s*7,\s*4\)\s*=\s*strftime\('%Y',\s*'now'\)", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*AND\s+substr\(created_at,\s*4,\s*2\)\s*=\s*strftime\('%m',\s*'now'\)", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"WHERE\s+substr\(created_at,\s*7,\s*4\)\s*=\s*strftime\('%Y',\s*'now'\)\s*AND\s*", "WHERE ", sql, flags=re.IGNORECASE)

    # 3. Handle unsupported STDDEV() function
    if "STDDEV(" in sql.upper():
        sql = re.sub(r"\+?\s*2\s*\*\s*STDDEV\([^)]+\)", "* 1.5", sql, flags=re.IGNORECASE)
        sql = re.sub(r"STDDEV\([^)]+\)", "0", sql, flags=re.IGNORECASE)

    return sql


def llm_to_sql(nl_query: str) -> str:
    # Fail-safe check if key is missing
    if not OPENROUTER_API_KEY:
        return "SELECT * FROM tickets LIMIT 5; -- Error: OPENROUTER_API_KEY not found in .env"

    prompt = f"""
    Convert the natural language query into a valid SQLite SQL statement.
    
    Table Name: tickets
    Columns & Formats:
    - ticket_id (TEXT): Unique ID
    - created_at (TEXT): Stored as 'DD-MM-YYYY HH.MM' (Dataset dates are from 2024, e.g. '05-02-2024 11.14')
    - category (TEXT): 'General', 'Billing', 'Technical'
    - priority (TEXT): 'Low', 'Medium', 'High'
    - status (TEXT): 'Open', 'Resolved', 'Pending', 'Closed'
    - response_time_hrs (REAL)
    - resolution_time_hrs (REAL)
    - agent_id (TEXT): 'AGT-01', 'AGT-02', etc.
    - customer_rating (INTEGER)
    - issue_summary (TEXT)

    CRITICAL RULES:
    1. Case Insensitivity: ALWAYS wrap text comparisons in LOWER() (e.g., LOWER(status) = LOWER('resolved')).
    2. SQLite Function Limitations: SQLite DOES NOT support STDDEV() or VARIANCE(). Use AVG() or simple multipliers instead.
    3. Date Filters: DO NOT use strftime('%Y', 'now') or date('now') because dataset dates are from 2024, NOT the current year.
    4. Output Format: Return ONLY the raw SQL query. No markdown backticks (```), comments, or explanations.

    Natural language query: {nl_query}
    SQL:
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Support Ticket AI"
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json={
                "model": "openrouter/free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
            },
            timeout=30,
        )
        data = response.json()

        if "error" in data:
            print(f"[OpenRouter API Error]: {data['error']}")
            return f"SELECT * FROM tickets LIMIT 5; -- API error: {data['error'].get('message')}"

        if "choices" in data and len(data["choices"]) > 0:
            sql_response = data["choices"][0]["message"]["content"].strip()

            # Clean markdown code formatting
            if sql_response.startswith("```"):
                lines = sql_response.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                sql_response = "\n".join(lines).strip()

            # Apply post-processing safeguards
            sql_response = clean_and_fix_sql(sql_response)

            return sql_response

        return f"SELECT * FROM tickets LIMIT 5; -- Fallback, empty response: {data}"

    except Exception as e:
        return f"SELECT * FROM tickets LIMIT 5; -- Fallback, exception: {e}"