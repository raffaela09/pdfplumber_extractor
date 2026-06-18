import os
from src.extractor import process_pdf_folder, process_pdf_folder_cab
from src.estrutura_db import create_table, processar_pasta_para_banco, header_to_db

PASTA_JSONS = "./output/json"
NOME_BANCO = "./database/avaliacoes.db"
PASTA_JSON_CAB = "./output/json_cabecalho"

def main():
    pasta_dos_arquivos = "./pdfs"
    process_pdf_folder(pasta_dos_arquivos)
    pasta_dos_arquivos_cab = "./pdfs"
    process_pdf_folder(pasta_dos_arquivos_cab)
    create_table()
    header_to_db(PASTA_JSON_CAB)
    processar_pasta_para_banco(PASTA_JSONS)
    process_pdf_folder_cab(pasta_dos_arquivos_cab)
    # pasta_saida = './output/picture'
    
    # extrair_imagens_por_linha('./pdfs/teste.pdf', pasta_saida)


if __name__ == '__main__':  
    main()
    
    
#verificar pra depois da execucao do codigo, limpar a pasta de jsons
#alguma forma de ver se teve alteracao na pasta, pra entao executar o codigo
#questao das imagens
    
