"""
Módulo responsável por extrair as imagens embutidas nos PDFs e
prepará-las para serem salvas no banco de dados em formato binário (BLOB).
"""

import fitz  # PyMuPDF
from pathlib import Path


def extrair_imagens_pdf(caminho_pdf, pasta_imagens=None):
    """
    Percorre todas as páginas de um PDF e extrai as imagens embutidas.

    Parâmetros:
        caminho_pdf: caminho para o arquivo PDF de origem.
        pasta_imagens: se informado, cada imagem também é salva em disco
                       nessa pasta (além de ser retornada em binário).

    Retorna uma lista de dicionários, um por imagem encontrada, com:
        - pagina: número da página de origem (começando em 1)
        - indice: posição da imagem dentro da página (começando em 1)
        - nome_arquivo: nome sugerido para o arquivo (ex: "laudo01_pagina2_img1.png")
        - extensao: formato original da imagem ("png", "jpeg", etc.)
        - conteudo_binario: bytes da imagem, prontos para inserir num campo BLOB
    """
    caminho_pdf = Path(caminho_pdf)
    imagens_extraidas = []

    if pasta_imagens is not None:
        pasta_imagens = Path(pasta_imagens)
        pasta_imagens.mkdir(parents=True, exist_ok=True)

    documento = fitz.open(caminho_pdf)

    for numero_pagina in range(len(documento)):
        pagina = documento[numero_pagina]
        # full=True traz também imagens usadas mais de uma vez no documento
        lista_imagens = pagina.get_images(full=True)

        for indice, info_imagem in enumerate(lista_imagens, start=1):
            xref = info_imagem[0]

            try:
                imagem_extraida = documento.extract_image(xref)
            except Exception as erro:
                print(
                    f"Não foi possível extrair a imagem {indice} "
                    f"da página {numero_pagina + 1} de {caminho_pdf.name}: {erro}"
                )
                continue

            conteudo_binario = imagem_extraida["image"]
            extensao = imagem_extraida["ext"]  #extensao da img, tipo jpg, png

            nome_arquivo = (
                f"{caminho_pdf.stem}_pagina{numero_pagina + 1}"
                f"_img{indice}.{extensao}"
            )

            if pasta_imagens is not None:
                caminho_saida = pasta_imagens / nome_arquivo
                with open(caminho_saida, "wb") as f:
                    f.write(conteudo_binario)

            imagens_extraidas.append({
                "pagina": numero_pagina + 1,
                "indice": indice,
                "nome_arquivo": nome_arquivo,
                "extensao": extensao,
                "conteudo_binario": conteudo_binario,
            })

    documento.close()
    return imagens_extraidas
#---------------------------------------------------------------------------------

def processar_pasta_de_imagens(caminho_pasta_pdfs):
    """
    
    Processa todos os PDFs de uma pasta e extrai as imagens de cada um.
    Salva os arquivos de imagem em 'caminho_pasta_pdfs/imagens'
    
    """
    pasta_origem = Path(caminho_pasta_pdfs)
    pasta_imagens = pasta_origem / "imagens"

    arquivos_pdf = list(pasta_origem.glob("*.pdf"))
    if not arquivos_pdf:
        print(f" Nenhum arquivo PDF encontrado em '{pasta_origem}'.")
        return {}

    print(f"Extraindo imagens de {len(arquivos_pdf)} PDF(s)...")

    resultado = {}
    for caminho_pdf in arquivos_pdf:
        imagens = extrair_imagens_pdf(caminho_pdf, pasta_imagens)
        resultado[caminho_pdf.stem] = imagens
        print(f" {caminho_pdf.name}: {len(imagens)} imagem(ns) encontrada(s).")

    print(f"\n Imagens salvas em: {pasta_imagens}")
    return resultado
#---------------------------------------------------------------------------------

if __name__ == "__main__":
    processar_pasta_de_imagens("./pdfs")
