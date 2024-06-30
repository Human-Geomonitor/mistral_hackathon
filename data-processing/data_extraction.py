"""  Class Extractor:
The role of the Extractor is to convert a pdf into chunks for RAG.
    An extractor object can:
    - extract text from pdf
    - clean text before chunking
    - chunk text
"""

import os

from PyPDF2 import PdfReader
        
import pymupdf
#import pymupdf4llm
from langchain.text_splitter import MarkdownTextSplitter

import json

class Extractor():
    """
    The role of the Extractor is to convert a pdf into chunks for RAG.
    An extractor object can:
    - extract text from pdf
    - clean text before chunking
    - chunk text

    The method `pdf_to_chunks` does everything all at once.

    """
    
    def __init__(self):
        pass

    def convert_pdf_to_text(self, filename, text_folder):
        """
        Converts a PDF file into a text file

        Parameters:
            filename (str): path of the PDF file
        
        Returns:
            file_path (str): path of the new txt file
            metadata (dict): updated metadata of the PDF file
        """

        assert filename.split('.')[-1] == "pdf", f"File {filename} format is not PDF"
        
        # extract metadata
        reader = PdfReader(filename)
        metadata = dict(reader.metadata)
        
        # extract text content
        doc = pymupdf.open(filename)
        
        text_filename = filename.split('/')[-1].replace('.pdf', '.txt')
        file_path = os.path.join(text_folder, text_filename)
        
        # Iterate the document pages and save them in a txt file
        text_file = open(file_path, "wb")
        for page_number, page in enumerate(doc):
            print(f"Page {page_number+1}/{len(doc)}", end="\r")
            text = page.get_text().encode("utf8")
            text_file.write(text)
        text_file.close()
        
        return file_path, metadata

    def clean_text(self, filename):
        """
        Cleans the text files before chunking.
        Yet to be implemented, for instance using a small LLM.
        """

        cleaned_text_filename = filename
        return cleaned_text_filename
    
    def convert_text_to_chunks(self, filename, chunks_dir,
                               metadata,
                               chunk_size=512, chunk_overlap=0,
                               keep_alpha_chunks=True,
                               verbose=False):
        """
        Converts a text file into multiple chunks.

        Parameters:
            filename (str): name of the text file
            chunks_dir (str): directory to save the chunks into
            metadata (dict): metadata to add to every chunk
            chunk_size (int): approximate number of tokens per chunk
            chunk_overlap (int): number of tokens in two chunks when they overlap 
            keep_alpha_chunks (bool): indicates whether to keep chunks containing enough text
        
        """
        
        # Load splitter
        splitter = MarkdownTextSplitter(chunk_size=chunk_size,
                                        chunk_overlap=chunk_overlap)

        with open(filename, "r", encoding='utf-8') as text_file:
            
            text_content = text_file.read()
            docs = splitter.create_documents([text_content])
            
            # Select the best chunks
            # TODO: put it in a separate function
            text_docs = []
            for doc in docs:
                if keep_alpha_chunks:
                    # We only keep chunks that are mostly made out of text
                    alpha_ratio = sum([x.isalpha() for x in doc.page_content])/len(doc.page_content)
                    if alpha_ratio >= 0.7:
                        text_docs.append(doc)
                    
                    if verbose:
                        print(f"We kept {len(text_docs)} chunks out of {len(docs)}")
            
                else:
                    text_docs.append(doc)
            
        # Save chunks in chunks_dir
        print(f"Saving {filename.split('/')[-1]} in {len(text_docs)} chunks")
        chunk_prefix = filename.split('/')[-1].replace('.txt', '_chunk')
        for i_chunk, doc in enumerate(text_docs):
            chunk_fn = f"{chunk_prefix}_{i_chunk}.json"
            file_path = os.path.join(chunks_dir, chunk_fn)
            metadata['/Chunk'] = str(i_chunk)
        
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(dict({'page_content': doc.page_content},
                                **metadata), 
                          file, ensure_ascii=False, indent=4)
        

    def pdf_to_chunks(self, reports_dir, chunks_dir, verbose=False):
        """
        Goes through 'reports_dir' to convert PDF reports into chunks.

        Parameters:
            reports_dir (str): directory where the reports are saved
            chunks_dir (str): directory to save the chunks into
        
        """
        if not os.path.isdir(chunks_dir):
            os.mkdir(chunks_dir)

        text_folder = 'text_files'
        
        if not os.path.isdir(text_folder):
            os.mkdir(text_folder)
        
        reports_paths = os.listdir(reports_dir)
        reports_paths = [path for path in reports_paths if path.split('.')[-1]=='pdf']
        nb_reports = len(reports_paths)
        
        for i_report, report_fn in enumerate(sorted(reports_paths)):
            if verbose:
                print(f"Extracting text from ({i_report+1}/{nb_reports}) {report_fn}")
            
            pdf_filename = os.path.join(reports_dir, report_fn)
            
            file_path, metadata = self.convert_pdf_to_text(pdf_filename, text_folder)
         
        #texts_paths = os.listdir(text_folder)
        #texts_paths = [path for path in texts_paths if path.split('.')[-1]=='txt']

        #for text_filename in texts_paths:
            #file_path = os.path.join(text_folder, text_filename)
            
            cleaned_text_filename = self.clean_text(file_path)
            
            # TODO: what is this metadata lmao
            self.convert_text_to_chunks(cleaned_text_filename, chunks_dir, metadata)  
        

