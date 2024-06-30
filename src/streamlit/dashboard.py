"""Dashboard related functions."""

import os
import sys

import plotly.express as px
from environs import Env
from pydtm import utils
from pygeoboundaries.pygeoboundaries import get_adm

import streamlit as st

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
        )
    )
)

from utils import get_country_level_data_for_map, run_pipeline

from pipeline.call_llm import get_mistral_client  # noqa: E402

env = Env()
env.read_env(path="./src/.env")


################
# DASHBOARD
################

st.set_page_config(layout="wide")
st.title("Pipeline Data Dashboard")

if "json" not in st.session_state:
    st.session_state.json = {}
col1, col2 = st.columns([1, 3])

with col1:
    # Select countries
    countries = st.multiselect(
        "Select countries",
        utils.load_ISO3166_data()['    "Country"'],
        default=[
            '    "Somalia"',
            '    "Ethiopia"',
            '    "Kenya"',
            '    "Uganda"',
            '    "South Sudan"',
        ],
    )
    countries_iso3 = [utils.countryToISO3166_A3(country[5:-1]) for country in countries]

    # SITUATION REPORT
    st.header("Situation Report")
    st.write(st.session_state.json)

with col2:
    client = get_mistral_client()
    st.header("Situation Overview")
    st.session_state.json = run_pipeline(client, countries)

    # MAP PLOT
    geojson = get_adm(territories=countries_iso3, adm="ADM0")
    df = get_country_level_data_for_map(countries, st.session_state.json)

    fig = px.choropleth_mapbox(
        df,
        geojson=geojson,
        locations="Country",
        featureidkey="properties.shapeISO",
        mapbox_style="carto-positron",
        color="Metric",
        color_discrete_map={
            "crisis situation": "red",
            "concerning situation": "orange",
            "mild situation": "yellow",
            "normal situation": "green",
            "no relevant data": "grey",
        },
        category_orders={
            "Metric": [
                "crisis situation",
                "concerning situation",
                "mild situation",
                "normal situation",
                "no relevant data",
            ]
        },
        labels={"Metric": "General Situation"},
        title="General Situation per country",
        opacity=0.5,
        zoom=1,
    )

    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
