import fitz
from pathlib import Path

caminho_pdf = "./pdfs/teste.pdf"
pasta_destino = Path("paginas_cortadas")
pasta_destino.mkdir(exist_ok=True)

# Defina a "zona de perigo" do cabeçalho (ex: os 120 pixels do topo da página)
LIMITE_ZONA_CABECALHO = 120

doc = fitz.open(caminho_pdf)

for num_pagina, pagina in enumerate(doc):
    largura = pagina.rect.width
    altura = pagina.rect.height

    # Pega todos os blocos de texto da página com suas respectivas coordenadas
    # Cada bloco retorna: (x0, y0, x1, y1, "texto do bloco", numero_do_bloco, tipo)
    blocos_de_texto = pagina.get_text("blocks")

    y_inicial = 0
    maior_y_do_cabecalho = 0
    tem_cabecalho = False

    for b in blocos_de_texto:
        y0_do_bloco = b[1]  # Onde o bloco de texto começa (topo)
        y1_do_bloco = b[3]  # Onde o bloco de texto termina (fundo)
        texto = b[4].strip()

        # Se o texto começa dentro da zona do topo e não está em branco
        if y0_do_bloco < LIMITE_ZONA_CABECALHO and texto:
            tem_cabecalho = True

            # Guardamos o ponto mais baixo que o texto do cabeçalho alcançou
            if y1_do_bloco > maior_y_do_cabecalho:
                maior_y_do_cabecalho = y1_do_bloco

    # Definição dinâmica do corte
    if tem_cabecalho:
        # Começa a imagem 15 pixels abaixo do final do texto do cabeçalho
        y_inicial = maior_y_do_cabecalho + 15
        print(
            f"➔ [Pág. {num_pagina + 1}] Cabeçalho dinâmico detectado! "
            f"Cortando em Y = {y_inicial:.2f}"
        )
    else:
        y_inicial = 0
        print(
            f"➔ [Pág. {num_pagina + 1}] Topo limpo. "
            "Renderizando página cheia."
        )

    # Criar a área de corte e salvar a imagem
    area_de_corte = fitz.Rect(0, y_inicial, largura, altura)
    pix = pagina.get_pixmap(clip=area_de_corte)

    caminho_final = pasta_destino / f"pagina_{num_pagina + 1}.png"
    pix.save(caminho_final)

print("\nProntinho! Todas as páginas foram processadas e salvas.")