import os
from src.extractor import processar_pasta_de_pdfs, processar_pasta_de_pdfs_cab
from src.estrutura_db import criar_banco_e_tabela, processar_pasta_para_banco
from img_bin import extrair_imagens_por_linha

PASTA_JSONS = "./output/json"
NOME_BANCO = "./database/avaliacoes.db"

def main():
    pasta_dos_arquivos = "./pdfs"
    processar_pasta_de_pdfs(pasta_dos_arquivos)
    pasta_dos_arquivos_cab = "./pdfs"
    processar_pasta_de_pdfs(pasta_dos_arquivos_cab)
    processar_pasta_de_pdfs_cab(pasta_dos_arquivos_cab)
    criar_banco_e_tabela()
    processar_pasta_para_banco(PASTA_JSONS)
    pasta_saida = './output/picture'
    extrair_imagens_por_linha('./pdfs/teste.pdf', pasta_saida)


if __name__ == '__main__':  
    main()
    
    
#transformar a img em binario - feito - transformado em bytes - com pymupdf
#arrumar p n pegar as imgs do cabecalho - 
#apagar as imagens depois que transformar em bin - nao precisa mais, ja que nao baixa as img
#