import pdfplumber
import fitz # pymupdf
import os

def extrair_imagens_por_linha(caminho_pdf, pasta_saida):
    os.makedirs(pasta_saida, exist_ok=True)
    
    doc_fitz = fitz.open(caminho_pdf)
    resultado = []

    with pdfplumber.open(caminho_pdf) as pdf:
        for num_pagina, pagina in enumerate(pdf.pages):
            tabelas = pagina.extract_tables()
            if not tabelas:
                continue

            pagina_fitz = doc_fitz[num_pagina]
            imagens_da_pagina = pagina_fitz.get_images(full=True)

            for tabela in tabelas:
                # pega as bounding boxes de cada linha via pdfplumber
                tabela_obj = pagina.find_tables()
                if not tabela_obj:
                    continue

                for idx_linha, linha in enumerate(tabela):
                    # pega o Y da linha na página
                    try:
                        bbox_linha = tabela_obj[0].rows[idx_linha].bbox
                        y_topo = bbox_linha[1]
                        y_base = bbox_linha[3]
                    except (IndexError, AttributeError):
                        continue

                    # verifica cada imagem da página
                    for img in imagens_da_pagina:
                        xref = img[0]
                        # pega onde a imagem está na página
                        rects = pagina_fitz.get_image_rects(xref)
                        if not rects:
                            continue

                        img_y_topo = rects[0].y0
                        img_y_base = rects[0].y1

                        # se o centro da imagem estiver dentro da faixa Y da linha
                        centro_img_y = (img_y_topo + img_y_base) / 2
                        if y_topo <= centro_img_y <= y_base:
                            # extrai e salva a imagem
                            base_img = doc_fitz.extract_image(xref)
                            ext = base_img["ext"]
                            nome_img = f"pag{num_pagina+1}_linha{idx_linha}.{ext}"
                            caminho_img = os.path.join(pasta_saida, nome_img)

                            with open(caminho_img, "wb") as f:
                                f.write(base_img["image"])

                            resultado.append({
                                "pagina": num_pagina + 1,
                                "linha_idx": idx_linha,
                                "imagem": nome_img,
                                "dados_linha": linha
                            })

    doc_fitz.close()
    return resultado
