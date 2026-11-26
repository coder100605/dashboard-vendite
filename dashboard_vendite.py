import os
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard Vendite", layout="wide")
st.title("Dashboard Vendite e Redditivita'")

NOME_FILE = "vendite.csv"

def crea_dati_di_prova():
    np.random.seed(42)
    n = 2000

    sottocategorie = {
        "Chairs": "Furniture", "Tables": "Furniture", "Bookcases": "Furniture",
        "Paper": "Office Supplies", "Binders": "Office Supplies", "Storage": "Office Supplies",
        "Phones": "Technology", "Accessories": "Technology", "Machines": "Technology",
    }
    stati = {
        "California": "West", "Washington": "West", "Texas": "South",
        "Florida": "South", "New York": "East", "Pennsylvania": "East",
        "Illinois": "Central", "Ohio": "East", "Michigan": "Central",
    }

    sub = np.random.choice(list(sottocategorie.keys()), n)
    stato = np.random.choice(list(stati.keys()), n)
    date_ordine = pd.to_datetime("2021-01-01") + pd.to_timedelta(
        np.random.randint(0, 4 * 365, n), unit="D"
    )
    vendite = np.round(np.random.uniform(10, 1500, n), 2)

    df = pd.DataFrame({
        "Order Date": date_ordine.strftime("%Y-%m-%d"),
        "Ship Date": (date_ordine + pd.to_timedelta(np.random.randint(1, 8, n), unit="D")).strftime("%Y-%m-%d"),
        "Category": [sottocategorie[s] for s in sub],
        "Sub-Category": sub,
        "Sales": vendite,
        "Profit": np.round(vendite * np.random.uniform(-0.2, 0.4, n), 2),
        "Region": [stati[s] for s in stato],
        "State": stato,
        "Quantity": np.random.randint(1, 10, n),
    })
    df = pd.concat([df, df.sample(15, random_state=1)], ignore_index=True)
    df.loc[df.sample(10, random_state=2).index, "Profit"] = np.nan
    return df

SIGLE_STATI = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}

@st.cache_data
def carica_e_pulisci():
    if os.path.exists(NOME_FILE):
        try:
            df = pd.read_csv(NOME_FILE)
        except UnicodeDecodeError:
            df = pd.read_csv(NOME_FILE, encoding="latin-1")
        fonte = "file " + NOME_FILE
    else:
        df = crea_dati_di_prova()
        fonte = "dati di prova (non ho trovato " + NOME_FILE + ")"

    report = {"fonte": fonte, "righe_iniziali": len(df)}

    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")

    report["nulli"] = df.isnull().sum()
    report["duplicati"] = int(df.duplicated().sum())

    df = df.drop_duplicates()
    df = df.dropna(subset=["Order Date", "Sales"])
    df["Profit"] = df["Profit"].fillna(0)

    df["Year"] = df["Order Date"].dt.year

    report["righe_finali"] = len(df)
    return df, report

df, report = carica_e_pulisci()

st.sidebar.header("Filtri")

categorie = st.sidebar.multiselect(
    "Categoria", sorted(df["Category"].unique()), default=sorted(df["Category"].unique())
)
regioni = st.sidebar.multiselect(
    "Regione", sorted(df["Region"].unique()), default=sorted(df["Region"].unique())
)
anni = st.sidebar.multiselect(
    "Anno", sorted(df["Year"].unique()), default=sorted(df["Year"].unique())
)

df_f = df[
    df["Category"].isin(categorie)
    & df["Region"].isin(regioni)
    & df["Year"].isin(anni)
]

if df_f.empty:
    st.warning("Nessun dato con questi filtri. Cambia la selezione a sinistra.")
    st.stop()

with st.expander("Report pulizia dati (Parte 1)"):
    st.write("Fonte dati:", report["fonte"])
    st.write("Righe iniziali:", report["righe_iniziali"])
    st.write("Righe duplicate rimosse:", report["duplicati"])
    st.write("Valori nulli per colonna (prima della pulizia):")
    st.write(report["nulli"])
    st.write("Righe finali:", report["righe_finali"])

col1, col2, col3 = st.columns(3)
col1.metric("Vendite totali", f"{df_f['Sales'].sum():,.0f} €")
col2.metric("Profitto totale", f"{df_f['Profit'].sum():,.0f} €")
col3.metric("Quantita' venduta", f"{df_f['Quantity'].sum():,}")

st.subheader("1) Vendite e profitti per anno")
per_anno = df_f.groupby("Year")[["Sales", "Profit"]].sum().reset_index()

grafico_anno = px.bar(
    per_anno, x="Year", y=["Sales", "Profit"], barmode="group",
    labels={"value": "Euro (€)", "Year": "Anno", "variable": ""},
)
grafico_anno.update_xaxes(type="category")
st.plotly_chart(grafico_anno, width="stretch")
st.dataframe(per_anno.round(2), width="stretch")

st.subheader("2) Top 5 sottocategorie per vendite")
top5 = (
    df_f.groupby("Sub-Category")["Sales"].sum()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)
grafico_top5 = px.bar(
    top5, x="Sales", y="Sub-Category", orientation="h",
    labels={"Sales": "Vendite (€)", "Sub-Category": "Sottocategoria"},
)
grafico_top5.update_yaxes(autorange="reversed")
st.plotly_chart(grafico_top5, width="stretch")

st.subheader("3) Mappa interattiva delle vendite per stato")
per_stato = df_f.groupby("State")["Sales"].sum().reset_index()
per_stato["Sigla"] = per_stato["State"].map(SIGLE_STATI)

mancanti = per_stato[per_stato["Sigla"].isna()]["State"].tolist()
if mancanti:
    st.info("Stati non riconosciuti (esclusi dalla mappa): " + ", ".join(mancanti))
per_stato = per_stato.dropna(subset=["Sigla"])

mappa = px.choropleth(
    per_stato,
    locations="Sigla",
    locationmode="USA-states",
    color="Sales",
    scope="usa",
    hover_name="State",
    color_continuous_scale="Blues",
    labels={"Sales": "Vendite (€)"},
)
st.plotly_chart(mappa, width="stretch")
