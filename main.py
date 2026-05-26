import os
from extractor import processar_pasta_de_pdfs
from estrutura_db import criar_banco_e_tabela, processar_pasta_para_banco

PASTA_JSONS = "./pdfs/resultados_json"
NOME_BANCO = "./database/avaliacoes.db"

def main():
    pasta_dos_arquivos = "./pdfs"
    processar_pasta_de_pdfs(pasta_dos_arquivos)
    criar_banco_e_tabela()
    processar_pasta_para_banco(PASTA_JSONS)


if __name__ == '__main__':  
    main()