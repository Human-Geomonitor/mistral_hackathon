"""Functions to get data from APIs."""

import json
import os
from datetime import datetime
from typing import Dict, Optional

import pandas as pd
import requests
from newsapi import NewsApiClient
from newspaper import Article, Config
from newspaper.utils import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0"
)

config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 30

BBC_URL_BASE = "https://www.bbc.co.uk"


def _get_article_text(url):
    article = Article(url, config=config)
    article.download()
    article.parse()
    return article.text


def _get_articles_news_api(country, start_date: datetime, end_date: datetime):
    print(f"USING API for {country}")
    news_api_key = os.environ.get("NEWS_API_KEY")
    newsapi = NewsApiClient(api_key=news_api_key)

    all_articles = newsapi.get_everything(
        q=f'+"{country}"',
        sources="bbc-news",
        domains="bbc.co.uk",
        from_param=start_date,
        to=end_date,
        language="en",
    )
    url_list = [doc["url"] for doc in all_articles["articles"]]
    texts = "\n\n\n\n\n\n\n".join([_get_article_text(url) for url in url_list])
    return texts


def _get_bbc_articles(country: str, nb_pages_res: int = 10) -> pd.DataFrame:
    """Get BBC News articles related to a country.

    Args:
        country (str): name of a country, or region of the world.
        nb_pages_res (int): number of result pages to look into. Default = 10.

    Returns:
        pd.DataFrame: dataframe with articles
    """
    search_url = f"{BBC_URL_BASE}/search?q={country}&seqId=a2619180-339d-11ef-b51b-05b0b4d9a140&d=NEWS_PS"

    articles = []
    dates = []

    # Iterate over search result pages
    for page in range(1, nb_pages_res):
        response = requests.get(search_url + f"&page={page}")
        if response.status_code != 200:
            break
        soup = BeautifulSoup(response.text, "html.parser")
        # Adjust the selector based on the actual structure
        for article in soup.find_all("a", class_="ssrcss-its5xf-PromoLink exn3ah91"):
            base_url = article["href"]
            if "news" not in base_url:
                continue
            try:
                article = Article(base_url, config=config)
                article.download()
                article.parse()
                soup_article = BeautifulSoup(article.html, "html.parser")
                bbc_dictionary = json.loads(
                    "".join(
                        soup_article.find(
                            "script", {"type": "application/ld+json"}
                        ).contents
                    )
                )
                date_published = [
                    value
                    for (key, value) in bbc_dictionary.items()
                    if key == "datePublished"
                ]
                if len(date_published) > 0:
                    articles.append("Title: " + article.title + "\n" + article.text)
                    dates.append(
                        datetime.strptime(
                            date_published[0], "%Y-%m-%dT%H:%M:%S.%fZ"
                        ).strftime("%Y-%m-%d")
                    )
            except Exception as e:
                print(f"Could not read the article at {base_url}: {e}")
    articles_df = pd.DataFrame(data={"articles": articles, "dates": dates})
    print(f"{len(articles_df)} articles found for {country}")

    return articles_df


def _prepare_input(text: str) -> str:
    """Prepare the input for the LLM with context."""
    prompt = """You are an expert at building JSON. 
    Based on the following articles, for the country, here is a JSON where the keys are 
    - "political_situation": political situation of the country, 
    - "economy": economic situation of the country, 
    - "climate": climatic situation of the country, 
    - "sanitarian_situation": sanitarian situation of the country from a humanitarian point of view, 
    - "immigration_situation": the immigration situation in the country, from a humanitarian point of view
    - "general_situation": the general HUMANITARIAN situation of the country. It can have the values "normal situation", "mild situation", "concerning situation" and "crisis situation" and indicates the general HUMANITARIAN situation of the country 
    The values of each field is 2 sentences maximum relating to the keys and based on the articles. If nothing is relevant for a field, it is empty ("").
    """

    suffix = """

    JSON:
    """

    llm_input = prompt + text + suffix
    return llm_input


def _preprocess_data(
    articles_df: pd.DataFrame, start_date: datetime, end_date: datetime
) -> str:
    """Preprocess the data to be usable by the LLM.

    Args:
        articles_df (pd.DataFrame): dataframe containing articles and dates.
        start_date (datetime): starting date of the timeframe for selecting the articles.
        end_date (datetime) : ending date of the timeframe for selecting the articles.

    Return:
        str: text for the LLM.
    """
    subset_articles_df = articles_df.loc[
        (articles_df["dates"] > start_date) & (articles_df["dates"] <= end_date)
    ]
    if subset_articles_df.empty:
        print(
            f"No article found between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}. Change "
            f"timeframe "
        )
        raise Exception("Change timeframe.")
    texts = subset_articles_df["articles"].to_list()
    preprocessed_text = "\n\n\n\n\n\n\n".join(texts)
    return preprocessed_text


def get_data(
    country: str, start_date: datetime, end_date: datetime, nb_pages_res: int = 10
) -> str:
    """Get the data to feed the LLM, for a specific country or region and timeframe.

    Args:
        country (str): name of a country, or region of the world.
        start_date (datetime): starting date of the timeframe for selecting the articles.
        end_date (datetime) : ending date of the timeframe for selecting the articles.
        nb_pages_res (int): number of pages to look for results in news website.

    Return:
        str: text for the LLM.
    """
    articles_df = _get_bbc_articles(country=country, nb_pages_res=nb_pages_res)
    text = _preprocess_data(
        articles_df=articles_df, start_date=start_date, end_date=end_date
    )
    # text = _get_articles_news_api(country, start_date, end_date)
    text_for_llm = _prepare_input(text)
    return text_for_llm
