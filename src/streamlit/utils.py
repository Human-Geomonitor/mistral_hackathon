import os
from datetime import date, timedelta

import pandas as pd
from mistralai.client import MistralClient
from pydtm import utils

import streamlit as st
from pipeline.call_llm import call_mistral_model  # noqa: E402
from pipeline.get_api_data import get_data  # noqa: E402


################
# DATA CALLING FUNCTIONS
################
def _get_anterior_date(today_date):
    """Get the date from one month before.

    Args:
        today_date: today's date.

    Returns:
        date one month ago.
    """
    # Handle the end of month case
    one_day = timedelta(days=1)
    first_of_this_month = today_date.replace(day=1)
    last_of_last_month = first_of_this_month - one_day
    return (
        today_date.replace(day=1) - one_day
        if today_date.day > last_of_last_month.day
        else (
            today_date.replace(month=today_date.month - 1)
            if today_date.month > 1
            else today_date.replace(year=today_date.year - 1, month=12)
        )
    )


# TODO: Implement the run_pipeline function by calling other functions from the pipeline
def run_pipeline(client: MistralClient, countries: list[str]):
    """Run the LLM pipeline to generate a situation report for the given countries and time period.

    Args:
        client (MistralClient): Mistral AI client
        countries (lis(str)): list of countries to get information for.
        json (dict): previous dict of situation reports

    Returns:
    - json: A json object containing the situation report.
    """
    # global _cache_country_predictions # doesn't work
    clean_countries = {country: country.strip(" ") for country in countries}
    for country, clean_country in clean_countries.items():
        clean_countries[country] = run_pipeline_single_country(client, clean_country)

    return clean_countries


def is_json_empty(json_country_res):
    return (
        json_country_res["political_situation"] == ""
        and json_country_res["economy"] == ""
        and json_country_res["climate"] == ""
        and json_country_res["sanitarian_situation"] == ""
        and json_country_res["immigration_situation"] == ""
    )


@st.cache_data  # doing all the caching of the country param
def run_pipeline_single_country(_client: MistralClient, country: str):
    # global _cache_country_predictions # doesn't work
    end_date = date.today()
    start_date = _get_anterior_date(end_date)
    llm_input = get_data(
        country=country,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        nb_pages_res=3,
    )
    model_name = os.environ.get("MODEL")
    json_country_res = call_mistral_model(
        client=_client,
        model_name=model_name,
        input_text=llm_input,
    )
    if is_json_empty(json_country_res):
        json_country_res["general_situation"] = "no relevant data"
    return json_country_res


def get_country_level_data_for_map(list_of_countries, json):
    """Load data for the selected countries to be displayed on the map.

    Args:
        list_of_countries: A list of countries selected by the user.
        json: The json returned by the pipeline

    Returns:
        df: A pandas dataframe containing the general situation to be displayed on the map.
    """
    df = pd.DataFrame(columns=["Country", "Metric"])
    for country in list_of_countries:
        admin0Pcode = utils.countryToISO3166_A3(country[5:-1])

        json_country = json[country]
        try:
            metric = json_country[
                "general_situation"
            ]  # can be modified for topic specific data
            if metric not in [
                "crisis situation",
                "concerning situation",
                "mild situation",
                "normal situation",
            ]:
                metric = "no relevant data"
        except KeyError:
            metric = "no relevant data"
            pass

        df = pd.concat(
            [df, pd.DataFrame({"Country": [admin0Pcode], "Metric": [metric]})],
            ignore_index=True,
        )

    return df
