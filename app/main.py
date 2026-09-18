from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from app.db import get_db_connection
from app.llm import llm_to_sql

app = FastAPI()

class QueryRequest(BaseModel):
    nl_query: str

@app.post("/query")
def query_tickets(request: QueryRequest):
    sql = llm_to_sql(request.nl_query)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()
        return {"sql": sql, "result": rows}
    except Exception as e:
        return {"sql": sql, "result": {"error": str(e)}}

@app.get("/anomalies")
def anomalies():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM tickets", conn)
        conn.close()

        anomalies = {}

        # Critical unresolved tickets
        anomalies["critical_unresolved_count"] = int(
            df[(df['priority'] == "Critical") & (df['status'] != "Resolved")].shape[0]
        )

        # Unresolved >24h
        df['created_at'] = pd.to_datetime(df['created_at'], errors="coerce")
        unresolved_old = df[(df['status'] != "Resolved") &
                            ((pd.Timestamp.now() - df['created_at']).dt.total_seconds()/3600 > 24)]
        anomalies["unresolved_older_than_24h_count"] = int(unresolved_old.shape[0])

        # Long resolution times
        if df['resolution_time_hrs'].notnull().any():
            mean = df['resolution_time_hrs'].mean(skipna=True)
            std = df['resolution_time_hrs'].std(skipna=True)
            long_res = df[df['resolution_time_hrs'] > mean + 2*std]
            anomalies["long_resolution_count"] = int(long_res.shape[0])
        else:
            anomalies["long_resolution_count"] = 0

        # ✅ Always return JSON
        return {"anomalies": anomalies}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}
