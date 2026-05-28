import fitz # Importa a biblioteca PyMuPDF

def extrair_imagens_do_pdf(caminho_pdf):
    # 1. Abre o arquivo PDF
    documento = fitz.open(caminho_pdf)
    
    contador_imagens = 0
    
    # 2. Percorre todas as páginas do documento
    for numero_pagina in range(len(documento)):
        pagina = documento[numero_pagina]
        
        # Obtém uma lista de todas as imagens presentes na página
        lista_imagens = pagina.get_images(full=True)
        
        # 3. Percorre cada imagem encontrada na página atual
        for indice_imagem, img in enumerate(lista_imagens, start=1):
            xref = img[0] # 'xref' é o número de referência única da imagem dentro do PDF
            
            # Extrai os dados base da imagem usando a referência
            imagem_base = documento.extract_image(xref)
            bytes_imagem = imagem_base["image"]
            extensao = imagem_base["ext"]
            
            # Define o nome do arquivo (ex: imagem_pag1_1.jpeg)
            nome_arquivo = f"imagem_pag{numero_pagina + 1}_{indice_imagem}.{extensao}"
            
            # 4. Salva os bytes da imagem em um arquivo físico no disco
            with open(nome_arquivo, "wb") as arquivo_imagem:
                arquivo_imagem.write(bytes_imagem)
                
            contador_imagens += 1
            print(f"Imagem salva: {nome_arquivo}")
            
    print(f"\nExtração concluída! {contador_imagens} imagem(ns) extraída(s) com sucesso.")

# --- Como usar ---
# Substitua 'meu_arquivo.pdf' pelo caminho real do seu PDF
caminho_do_seu_pdf = "teste1.pdf" 
extrair_imagens_do_pdf(caminho_do_seu_pdf)

