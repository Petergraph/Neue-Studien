import streamlit as st
import requests
import datetime
import pandas as pd
from collections import defaultdict

st.set_page_config(layout="wide")
st.title("Neu registrierte Studien von ClinicalTrials.gov")

# --- Sidebar für Parameter ---
st.sidebar.header("Filter")
days = st.sidebar.slider("Zeitraum (Tage zurück)", min_value=1, max_value=14, value=1)
if st.sidebar.button("Aktualisieren"):
    st.experimental_rerun()

# --- Funktion zum Abrufen der Studien ---
@st.cache_data(ttl=3600)  # Cache für 1 Stunde
def fetch_new_studies(days: int):
    today = datetime.date.today()
    start = today - datetime.timedelta(days=days)
    expr = f"AREA[FirstPosted]RANGE[{start.isoformat()} {today.isoformat()}]"
    params = {
        "expr": expr,
        "fields": "NCTId,Condition,FirstPosted,BriefTitle",
        "min_rnk": 1,
        "max_rnk": 10000,
        "fmt": "json"
    }
    r = requests.get("https://clinicaltrials.gov/api/query/study_fields", params=params)
    r.raise_for_status()
    return r.json()["StudyFieldsResponse"]["StudyFields"]

# --- Daten holen und gruppieren ---
with st.spinner("Hole Daten …"):
    studies = fetch_new_studies(days)
grouped = defaultdict(list)
for s in studies:
    nct = s["NCTId"][0]
    date_fp = s["FirstPosted"][0]
    title = s["BriefTitle"][0]
    conds = s.get("Condition", [])
    for cond in conds:
        grouped[cond].append({"NCTId": nct, "Title": title, "FirstPosted": date_fp})

# --- Anzeige ---
for cond, items in sorted(grouped.items(), key=lambda x: -len(x[1])):
    st.subheader(f"{cond} ({len(items)})")
    df = pd.DataFrame(items)
    st.dataframe(df, height=200)
