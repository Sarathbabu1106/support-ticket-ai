import streamlit as st
import requests

st.title("Support Ticket AI")

query = st.text_input("Ask a question about tickets:")
if st.button("Submit"):
    res = requests.post("http://127.0.0.1:8000/query", json={"nl_query": query})
    st.json(res.json())

if st.button("Show anomalies"):
    res = requests.get("http://127.0.0.1:8000/anomalies")
    st.json(res.json())

if st.button("Health check"):
    res = requests.get("http://127.0.0.1:8000/health")
    st.json(res.json())
