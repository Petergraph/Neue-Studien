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

# --- Funktion zum Abrufen der Studien über die KORREKTE API ---
@st.cache_data(ttl=3600)
def fetch_new_studies(days: int):
    today = datetime.date.today()
    start = today - datetime.timedelta(days=days)
    
    # Korrektes Datumsformat und API-Syntax
    search_expr = f'AREA[FirstPosted]RANGE["{start.isoformat()}","{today.isoformat()}"]'  # ISO-Format YYYY-MM-DD
    
    params = {
        "expr": search_expr,
        "fields": "NCTId,Condition,BriefTitle,FirstPosted",
        "min_rnk": 1,
        "max_rnk": 1000,  # Maximalwert laut API-Dokumentation
        "fmt": "json"
    }
    
    try:
        # Verwende die klassische API-Endpunkt
        r = requests.get(
            "https://classic.clinicaltrials.gov/api/query/study_fields",  # Korrektes Endpoint
            params=params
        )
        r.raise_for_status()
        data = r.json()
        return data.get("StudyFieldsResponse", {}).get("StudyFields", [])
    except Exception as e:
        st.error(f"API-Fehler: {str(e)}")
        return []

# --- Datenverarbeitung ---
with st.spinner("Hole Daten …"):
    studies = fetch_new_studies(days)

# Datenaufbereitung
study_list = []
for study in studies:
    try:
        study_list.append({
            "NCTId": study.get("NCTId", [""])[0],
            "Titel": study.get("BriefTitle", [""])[0],
            "Erstveröffentlichung": study.get("FirstPosted", [""])[0],
            "Bedingungen": ", ".join(study.get("Condition", []))
        })
    except Exception as e:
        st.error(f"Datenfehler: {str(e)}")

df = pd.DataFrame(study_list)

# --- Anzeige ---
if not df.empty:
    st.dataframe(
        df,
        column_config={
            "NCTId": "Studien-ID",
            "Titel": "Titel",

