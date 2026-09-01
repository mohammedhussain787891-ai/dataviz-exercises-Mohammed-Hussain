from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CO2 Dashboard", page_icon="🌱", layout="wide")

METRICS = {"Total CO2 (Mt)": "CO2_Mt", "CO2 per capita": "CO2_per_capita"}


@st.cache_data
def load_data():
    df = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "co2_emissions.csv")
    df["Date"] = pd.to_datetime(df["Year"].astype(str) + "-01-01")
    return df


df = load_data()

st.title("🌱 CO2 Emissions Explorer")
st.caption("Source: Our World in Data — ourworldindata.org/co2-emissions")

with st.sidebar:
    st.header("Filters")
    region = st.selectbox("Region", ["All"] + sorted(df["Region"].unique()))
    pool = df if region == "All" else df[df["Region"] == region]
    options = sorted(pool["Country"].unique())
    countries = st.multiselect("Countries", options, default=options[:3])
    dmin, dmax = df["Date"].min().date(), df["Date"].max().date()
    dates = st.date_input("Date range", (dmin, dmax), min_value=dmin, max_value=dmax)
    metric_label = st.radio("Metric", list(METRICS))
    highlight = st.checkbox("Show only top emitter highlighted")

metric = METRICS[metric_label]

if not countries:
    st.warning("Select at least one country.")
    st.stop()
if len(dates) != 2:
    st.warning("Select a start and an end date.")
    st.stop()

start, end = pd.Timestamp(dates[0]), pd.Timestamp(dates[1])
filtered = df[df["Country"].isin(countries) & df["Date"].between(start, end)]

if filtered.empty:
    st.warning("No records match the current filters.")
    st.stop()

st.caption(f"{len(countries)} countries | {region} | {start.year}–{end.year} | {metric_label}")

first_year, last_year = filtered["Year"].min(), filtered["Year"].max()
last = filtered[filtered["Year"] == last_year]
total_last = last[metric].sum()
total_first = filtered[filtered["Year"] == first_year][metric].sum()
pct = (total_last - total_first) / total_first * 100 if total_first else 0
top_emitter = filtered.groupby("Country")[metric].sum().idxmax()

# Avoid colour clutter: once more than 3 countries are selected (or the user
# asks for it), only the top emitter keeps an accent colour and the rest go grey.
ACCENT, MUTED = "#1f77b4", "#d9d9d9"
focus = highlight or len(countries) > 3

k1, k2, k3 = st.columns(3)
k1.metric(f"Total {metric_label} ({last_year})", f"{total_last:,.1f}")
k2.metric(f"Change {first_year}→{last_year}", f"{pct:+.1f}%")
k3.metric(f"Top emitter ({last_year})", top_emitter)

col_left, col_right = st.columns([2, 1])

with col_left:
    if focus:
        colours = {c: (ACCENT if c == top_emitter else MUTED) for c in countries}
        fig = px.line(
            filtered, x="Year", y=metric, color="Country",
            color_discrete_map=colours,
            title=f"{top_emitter} leads {metric_label.lower()}, {start.year}–{end.year}",
        )
        tip = filtered[(filtered["Country"] == top_emitter) & (filtered["Year"] == last_year)]
        fig.add_scatter(
            x=tip["Year"], y=tip[metric], mode="text", text=[top_emitter],
            textposition="middle right", showlegend=False,
        )
        fig.update_layout(showlegend=False)
    else:
        fig = px.line(
            filtered, x="Year", y=metric, color="Country",
            title=f"{metric_label}, {start.year}–{end.year}",
        )
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    rank = last.sort_values(metric, ascending=False)
    if focus:
        bar_colours = {c: (ACCENT if c == top_emitter else MUTED) for c in countries}
    else:
        bar_colours = {top_emitter: ACCENT}
    fig2 = px.bar(
        rank, x=metric, y="Country", orientation="h",
        color="Country", color_discrete_map=bar_colours,
        title=f"{top_emitter} tops the {last_year} ranking",
    )
    fig2.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(fig2, use_container_width=True)
