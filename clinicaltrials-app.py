import streamlit as st
import requests
import datetime
import pandas as pd
from collections import defaultdict

st.set_page_config(layout="wide")
st.title("Neu registrierte Studien von ClinicalTrials.gov")

# --- Sidebar für Parameter ---
st.sidebar.header("Filter")
days = st.sidebar.slider(
    "Zeitraum (Tage zurück)",
    min_value=1,
    max_value=14,
    value=1
)
if st.sidebar.button("Aktualisieren"):
    st.experimental_rerun()

# --- Funktion zum Abrufen der Studien über API V1 ---
@st.cache_data(ttl=3600)
def fetch_new_studies(days: int):
    """
    Ruft alle Studien ab, deren "First Posted"-Datum in den letzten `days` Tagen liegt
    über die Version 1 API (study_fields endpoint).
    """
    studies = []
    today = datetime.date.today()
    start = today - datetime.timedelta(days=days)
    # Baue Suche mit RANGE und US-Datum
    search_range = f"AREA[FirstPosted]RANGE[{start.strftime('%m/%d/%Y')},{today.strftime('%m/%d/%Y')}]"
    params = {
        # searchExpr für V1 API
        "searchExpr": search_range,
        "fields": "NCTId,Condition,FirstPosted,BriefTitle",
        "min_rnk": 1,
        "max_rnk": 10000,
        "fmt": "json"
    }
    try:
        r = requests.get(
            "https://clinicaltrials.gov/api/query/study_fields",
            params=params
        )
        r.raise_for_status()
        data = r.json()
        return data.get("StudyFieldsResponse", {}).get("StudyFields", [])
    except requests.HTTPError as e:
        st.error(f"Fehler beim Abrufen der Daten: {e}")
        return []

# --- Daten holen und gruppieren ---
with st.spinner("Hole Daten …"):
    studies = fetch_new_studies(days)

with st.spinner("Hole Daten …"):
    studies = fetch_new_studies(days)

grouped = defaultdict(list)
for s in studies:
    ps = s.get("protocolSection", {})
    idmod = ps.get("identificationModule", {})
    nct = idmod.get("nctId", "")
    date_fp = idmod.get("firstSubmittedDate", "")
    title = idmod.get("officialTitle", "")
    conditions = (
        ps.get("conditionsModule", {})
          .get("conditionList", {})
          .get("condition", [])
    )
    for cond in conditions:
        grouped[cond].append({
            "NCTId": nct,
            "Title": title,
            "FirstPosted": date_fp
        })

# --- Anzeige sortiert nach Anzahl Studien pro Condition ---
for cond, items in sorted(grouped.items(), key=lambda x: -len(x[1])):
    st.subheader(f"{cond} ({len(items)})")
    df = pd.DataFrame(items)
    st.dataframe(df, height=200)
