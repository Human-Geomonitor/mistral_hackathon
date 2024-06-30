""" Webscraper
"""

import os

import requests
from bs4 import BeautifulSoup

from PyPDF2 import PdfReader, PdfMerger


def scrap_DTM_reports(reports_dir, countries=None, 
                      verbose=True):
    
    # TODO: scrap country codes automatically
    code_countries = {
        'Ethiopia':63,
        'Somalia':80
    }
    
    if countries is None:
        countries = code_countries.keys()
    
    if not os.path.isdir(reports_dir):
        os.mkdir(reports_dir)
    
    year = 2024
    page = 0
    
    for country in countries:
        if country  in code_countries.keys():
            URL = f"https://dtm.iom.int/reports?f%5B0%5D=published_date%3A{year}&f%5B1%5D=report_country%3A{code_countries[country]}&page={page}"

            response = requests.get(URL)
            soup = BeautifulSoup ( response.content , "html.parser" )

            all_reports = soup.find_all('span',
                                  attrs={
                                      'class' :"file file--mime-application-pdf file--application-pdf"
                                     }
                                  )

            all_links = [report.a.attrs['href'] for report in all_reports]

            for i, link in enumerate(all_links):
                response = requests.get("https://dtm.iom.int/" + link)
                file_path = os.path.join(reports_dir, f"report_{country}_{i}.pdf")
                open(file_path, "wb").write(response.content)
                
                # TODO: check metadata, see what we can add
                metadata = {
                    '/Title': f'Report_{country}_{i}',
                    '/Country': country,
                    '/Year': str(year)
                }
                
                add_metadata_to_pdf(file_path, metadata)
                
                if verbose:
                    print(f"Report #{i} saved for {country}")
              
        elif verbose:
            print(f"Unknown reference to country {country} code in URL")

    return reports_dir

def add_metadata_to_pdf(filename, metadata):
    #print("Adding metadata to:", filename)
    
    file_in = open(filename, 'ab+')
    pdf_reader = PdfReader(file_in)
    old_metadata = pdf_reader.metadata
    
    pdf_merger = PdfMerger()
    pdf_merger.append(file_in)
    pdf_merger.add_metadata(dict(old_metadata,**metadata))
    pdf_merger.write(file_in)

    file_in.close()


# TODO: itérer les pages et s'arrêter quand il n'y a plus de rapport
# TODO: regarder les autres années
# TODO: ajouter les autres pays
# -> On s'en passe parce qu'il y a moins de 20 rapports par page, et qu'il y a qu'une seule année de rapports disponible


