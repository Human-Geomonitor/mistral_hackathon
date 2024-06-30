""" Main Python script for web scrapping and and chunking PDFs

Simply run:
python3 report2chunks.py

"""

import os

from webscraper import scrap_DTM_reports
from data_extraction import Extractor


def main(PATH='.', reports_dir="dtm_reports", chunks_dir="dtm_chunks",
         verbose = True):
    
    reports_dir = os.path.join(PATH, reports_dir)
    chunks_dir = os.path.join(PATH, chunks_dir)
    
    print("--- Web scrapping ---")
    scrap_DTM_reports(reports_dir=reports_dir, verbose=verbose)

    print("--- Converting PDF into chunks")
    extractor = Extractor()
    extractor.pdf_to_chunks(reports_dir, chunks_dir, verbose=verbose)
    

if __name__ == "__main__":
    main()
    # main(*sys.argv[1:])
