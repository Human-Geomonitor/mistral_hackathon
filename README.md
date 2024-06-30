# Pipeline
LLM enabled humanitarian data aggregation and visualisation pipeline.


## Environment and requirements for main pipeline

* Create virtual environment for the porject: `conda env create -f env/environment.yaml`
* Activate virtual environment: `conda activate llm-pipeline`
* Import / update packages: `pip install -r env/requirements.txt`. NB: on Mac, you might need to run `brew install gdal` before using 
`homebrew` package manager, which will take quite some time so go grab a coffee. It is because of the geographical nature of the dashboard,
which requires GDAL (a translator library for raster and vector geospatial data formats).

### Environment variables

Environment variables are located in `src/.env`
* MISTRAL_API_KEY : your mistral API key to access the model
* NEW_API_KEY : please visit https://newsapi.org/, you can create an account and get an API key for free.
Alternatively, if you don't want to do so, you could uncomment lines 176 to 179 in 'src/pipeline/get_api_data.py' and comment
line 180.

## Streamlit dashboard
* Make sure to be on the right conda virtual environment.
* Run `streamlit run src/streamlit/dashboard.py`.
