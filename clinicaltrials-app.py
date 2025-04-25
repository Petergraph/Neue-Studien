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

# --- Funktion zum Abrufen der Studien über API V2 ---
@st.cache_data(ttl=3600)
def fetch_new_studies(days: int):
    """
    Ruft alle Studien ab, deren "First Posted"-Datum in den letzten `days` Tagen liegt
    über die Version 2 API (Legacy v1 ist seit Juni 2024 abgeschaltet).
    """
    today = datetime.date.today()
    start = today - datetime.timedelta(days=days)
    url = "https://clinicaltrials.gov/api/v2/studies"
    # Suche über searchExpr mit AREA[FirstPosted]RANGE im ISO-Format
    search_expr = f"AREA[FirstPosted]RANGE[{start.isoformat()},{today.isoformat()}]"
    params = {
        "searchExpr": search_expr,
        "pageSize": 1000,
        "format": "json"
    }
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        return data.get("studies", [])
    except requests.HTTPError as e:
        st.error(f"Fehler beim Abrufen der Daten: {e}")
        return []

# --- Daten holen und gruppieren ---
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
        grouped[cond].append({"NCTId": nct, "Title": title, "FirstPosted": date_fp})

# Anzeige sortiert nach Anzahl Studien pro Condition
for cond, items in sorted(grouped.items(), key=lambda x: -len(x[1])):
    st.subheader(f"{cond} ({len(items)})")
    df = pd.DataFrame(items)
    st.dataframe(df, height=200)
