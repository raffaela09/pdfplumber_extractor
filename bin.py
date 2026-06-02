import fitz
import base64
import json

doc = fitz.open("./pdfs/teste.pdf")
pagina = doc[0]

# Lista para guardar os dados que vão pro JSON
dados_para_salvar = []

# 1. EXTRAIR DO PDF (Direto da memória)
imagens = pagina.get_images(full=True)

for index, img in enumerate(imagens):
    xref = img[0]
    imagem_base = doc.extract_image(xref)

    # Aqui estão os bytes da imagem direto na memória RAM
    bytes_imagem = imagem_base["image"]
    extensao = imagem_base["ext"]  # ex: 'png' ou 'jpeg'

    # 2. TRANSFORMAR PARA BASE64 (Texto que o JSON aceita)
    # b64encode transforma em bytes-base64, e .decode('utf-8') transforma em texto puro
    imagem_em_base64 = base64.b64encode(bytes_imagem).decode("utf-8")

    # Criando a estrutura para o JSON
    dados_foto = {
        "id_imagem": index,
        "extensao": extensao,
        "dados_da_imagem": imagem_em_base64
    }

    dados_para_salvar.append(dados_foto)

# 3. SALVAR NO JSON
# Agora o JSON aceita perfeitamente porque a imagem virou TEXTO
string_json = json.dumps(dados_para_salvar, indent=4)

# (Opcional) Se quiser salvar o arquivo .json físico para ver:
with open("dados_imagens.json", "w", encoding="utf-8") as f:
    f.write(string_json)

print("Imagens convertidas e prontas para o Banco de Dados!")