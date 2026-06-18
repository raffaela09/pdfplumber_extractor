from src.extractor import process_pdf_folder, process_pdf_folder_cab
from src.estrutura_db import (
    criar_banco_e_tabela,
    processar_pasta_para_banco,
    processar_header_para_banco,
    processar_pasta_de_imagens_para_banco,
)

PASTA_PDFS = "./pdfs"
PASTA_JSONS = "./pdfs/resultados_json"
PASTA_JSON_CAB = "./pdfs/resultados_json_cabecalhos"


def main():
    # 1. Extrai as tabelas de risco e os cabeçalhos de cada PDF para JSON
    process_pdf_folder(PASTA_PDFS)
    process_pdf_folder_cab(PASTA_PDFS)

    # 2. Garante que as tabelas do banco existem (incluindo a tabela 'imagens')
    criar_banco_e_tabela()

    # 3. Importa os JSONs (riscos e cabeçalhos) para o banco de dados
    processar_pasta_para_banco(PASTA_JSONS)
    processar_header_para_banco(PASTA_JSON_CAB)

    # 4. Extrai as imagens dos PDFs e salva o binário delas no banco
    processar_pasta_de_imagens_para_banco(PASTA_PDFS)


if __name__ == '__main__':
    main()
