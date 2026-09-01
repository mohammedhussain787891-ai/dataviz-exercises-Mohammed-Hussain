#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lecture 9 — Streamlit Foundations | Exercise
World Happiness Dashboard

Purpose (single-purpose rule, BBD):
    Helps a UN policy analyst see which countries lead on happiness and
    which countries are happier or unhappier than their wealth (GDP) predicts.

Run locally:   streamlit run lecture09_exercise.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="World Happiness", page_icon="🌍", layout="wide")

# ── Data ──────────────────────────────────────────────────────────────────
# Path relative to this file so it works locally AND on Streamlit Cloud,
# regardless of the working directory.
DATA = Path(__file__).resolve().parent.parent / "data" / "world_happiness_2023.csv"

df = pd.read_csv(DATA)
df.columns = ['Country', 'Region', 'Score', 'GDP', 'Social_Support',
              'Life_Expectancy', 'Freedom', 'Generosity', 'Corruption']

# Expected happiness from GDP (global linear fit). The residual = how much
# happier (+) or unhappier (-) a country is than its wealth predicts.
slope, intercept = np.polyfit(df['GDP'], df['Score'], 1)
df['Expected'] = slope * df['GDP'] + intercept
df['Residual'] = df['Score'] - df['Expected']

# ── Sidebar filters ───────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    regions = ['All'] + sorted(df['Region'].unique().tolist())
    selected_region = st.selectbox("Region", regions)
    top_n = st.slider("Show top N", 5, 25, 15)

filtered = df if selected_region == 'All' else df[df['Region'] == selected_region]

# ── Header ────────────────────────────────────────────────────────────────
st.title("🌍 World Happiness Dashboard")
st.caption("Source: World Happiness Report 2023 | Kaggle")

# KPI row — BBD: big numbers at the top, readable in 5 seconds
col1, col2, col3 = st.columns(3)
col1.metric("Countries", len(filtered))
col2.metric("Avg Score", f"{filtered['Score'].mean():.2f}",
            f"{filtered['Score'].mean() - df['Score'].mean():+.2f} vs global")
col3.metric("Happiest", filtered.nlargest(1, 'Score')['Country'].values[0])

st.divider()

# ── Row 1: rankings + scatter ─────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Rankings")
    top = filtered.nlargest(top_n, 'Score').sort_values('Score')

    fig1 = px.bar(top, x='Score', y='Country', orientation='h',
                  color_discrete_sequence=['#2E75B6'],  # highlight colour
                  labels={'Score': 'Score (0–10)', 'Country': ''})
    fig1.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                       xaxis=dict(range=[0, 8.5]), font=dict(family='Arial', size=12),
                       margin=dict(l=10, r=10, t=5, b=10))
    fig1.update_traces(marker_line_width=0)
    st.plotly_chart(fig1, width='stretch')

with col_right:
    st.subheader("Score vs GDP")
    fig2 = px.scatter(filtered, x='GDP', y='Score', hover_name='Country',
                      color_discrete_sequence=['#E63946'])
    fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                       font=dict(family='Arial', size=12),
                       margin=dict(l=10, r=10, t=5, b=10))
    st.plotly_chart(fig2, width='stretch')

st.divider()

# ── Row 2: STEP 5 — diverging chart (over/under-performers vs GDP) ─────────
# Diverging colour: values go above AND below a meaningful midpoint (0 = the
# happiness GDP predicts). Blue = happier than wealth predicts, red = unhappier.
st.subheader("Happier or unhappier than GDP predicts?")
st.caption("Residual = actual happiness − happiness expected from GDP. "
           "Midpoint (0) is the expectation line.")

# Most extreme over- and under-performers within the current filter
extremes = pd.concat([
    filtered.nlargest(8, 'Residual'),
    filtered.nsmallest(8, 'Residual'),
]).drop_duplicates('Country').sort_values('Residual')

limit = float(filtered['Residual'].abs().max()) + 0.2

fig3 = px.bar(extremes, x='Residual', y='Country', orientation='h',
              color='Residual',
              color_continuous_scale='RdBu',      # diverging
              color_continuous_midpoint=0,        # centred on the midpoint
              range_color=[-limit, limit],
              labels={'Residual': 'Happiness vs GDP expectation', 'Country': ''})

fig3.update_layout(plot_bgcolor='white', paper_bgcolor='white',
                   font=dict(family='Arial', size=12),
                   xaxis=dict(range=[-limit, limit], zeroline=True,
                              zerolinecolor='#444444', zerolinewidth=2),
                   coloraxis_showscale=False,
                   margin=dict(l=10, r=10, t=10, b=10))
fig3.update_traces(marker_line_width=0)

# Label the midpoint in an annotation (required by the exercise)
fig3.add_annotation(x=0, y=1.04, xref='x', yref='paper',
                    text="◀ unhappier   |   GDP expectation (0)   |   happier ▶",
                    showarrow=False, font=dict(size=12, color='#444444'))

st.plotly_chart(fig3, width='stretch')

st.divider()
st.caption("Built with Streamlit + Plotly")
