import os
from src.extractor import process_pdf_folder, process_pdf_folder_cab
from src.estrutura_db import create_table, processar_pasta_para_banco, header_to_db

PASTA_JSONS = "./output/json"
#caminho pro banco na nuvem 
NOME_BANCO = "Y:/27 - HIGIENE OCUPACIONAL/BANCOS_BASE/convert_hst_database/hst_database.sqlite-teste.db"
PASTA_JSON_CAB = "./output/json_cabecalho"

#verifica se o caminho existe
os.makedirs(os.path.dirname(NOME_BANCO), exist_ok=True)
def main():
    pasta_dos_arquivos = "./pdfs"
    process_pdf_folder(pasta_dos_arquivos)
    pasta_dos_arquivos_cab = "./pdfs"
    process_pdf_folder(pasta_dos_arquivos_cab)
    create_table()
    header_to_db(PASTA_JSON_CAB)
    processar_pasta_para_banco(PASTA_JSONS)
    process_pdf_folder_cab(pasta_dos_arquivos_cab)

if __name__ == '__main__':  
    main()
    

    
    
#Y:\27 - HIGIENE OCUPACIONAL\BANCOS_BASE\
#Y:\27 - HIGIENE OCUPACIONAL\BANCOS_BASE\convert_hst_database\hst_database.sqlite-teste.db
