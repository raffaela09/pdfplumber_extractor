import pdfplumber
import json
import re
import fitz # PyMuPDF
from pathlib import Path

from src.image_extractor import extrair_foto_da_linha


# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES — não foram alteradas
# ---------------------------------------------------------------------------

def identificar_e_mapear_linha(row_cells, grupo_anterior):
    cells = [str(c).strip().replace('\n', ' ') if c is not None else "" for c in row_cells]

    if all(c == "" for c in cells):
        return None, grupo_anterior

    linha_completa = " ".join(cells).lower()

    # tira a legenda, e nomes repetidos
    palavras_lixo = [
        "probabilidade de ocorrência", "frequência de exposição",
        "grau da possível lesão", "pessoas sob risco",
        "classificação de risco", "possibilidade de evitar",
        "apreciação dos riscos", "tipo ou grupo",
        "perigos relacionados", "análise atual",
        "0,033", ">500", "legenda", "0 a 1", "1 a 50"
    ]
    if any(p in linha_completa for p in palavras_lixo):
        return None, grupo_anterior

    def eh_numero(s):
        return bool(re.match(r'^\d+([.,]\d+)?$', s))

    indices_num = [i for i, c in enumerate(cells) if eh_numero(c)]
    if len(indices_num) < 3:
        return None, grupo_anterior

    start_num_idx = -1
    for i in range(len(indices_num) - 2):
        if indices_num[i+2] - indices_num[i] <= 4:
            start_num_idx = indices_num[i]
            break

    if start_num_idx == -1:
        return None, grupo_anterior

    bloco_numerico = [i for i in indices_num if i >= start_num_idx]

    # --- 1. MAPEAMENTO (ESQUERDA) ---
    textos_antes = [cells[i] for i in range(start_num_idx) if cells[i] != ""]

    tipo, perigo, risco, medida_proposta = "", "", "", ""
    if len(textos_antes) >= 4:
        tipo = textos_antes[0]
        perigo = textos_antes[1]
        risco = textos_antes[2]
        medida_proposta = " ".join(textos_antes[3:])
    elif len(textos_antes) == 3:
        tipo = textos_antes[0]
        perigo = textos_antes[1]
        risco = textos_antes[2]
    elif len(textos_antes) == 2:
        if cells[0] == "":
            tipo = ""
            perigo = textos_antes[0]
            risco = textos_antes[1]
        else:
            tipo = textos_antes[0]
            perigo = textos_antes[1]
    elif len(textos_antes) == 1:
        perigo = textos_antes[0]

    if tipo == "":
        tipo = grupo_anterior
    else:
        grupo_anterior = tipo

    # --- 2. MAPEAMENTO (NÚMEROS) ---
    idx_p = bloco_numerico[0] if len(bloco_numerico) > 0 else -1
    idx_f = bloco_numerico[1] if len(bloco_numerico) > 1 else -1
    idx_gpl = bloco_numerico[2] if len(bloco_numerico) > 2 else -1
    idx_np = bloco_numerico[3] if len(bloco_numerico) > 3 else -1
    idx_av = bloco_numerico[4] if len(bloco_numerico) > 4 else -1

    val_p = cells[idx_p] if idx_p != -1 else ""
    val_f = cells[idx_f] if idx_f != -1 else ""
    val_gpl = cells[idx_gpl] if idx_gpl != -1 else ""
    val_np = cells[idx_np] if idx_np != -1 else ""
    val_avaliacao = cells[idx_av] if idx_av != -1 else ""

    # --- 3. MAPEAMENTO (DIREITA) ---
    ultimo_idx_num = idx_av if idx_av != -1 else (idx_np if idx_np != -1 else idx_gpl)
    textos_depois = [cells[i] for i in range(ultimo_idx_num + 1, len(cells)) if cells[i] != ""]

    status_av, medida, foto_texto = "", "", ""
    if len(textos_depois) >= 3:
        status_av = textos_depois[0]
        medida = textos_depois[1]
        foto_texto = " ".join(textos_depois[2:])
    elif len(textos_depois) == 2:
        if len(textos_depois[0]) < 15:
            status_av = textos_depois[0]
            medida = textos_depois[1]
        else:
            medida = textos_depois[0]
            foto_texto = textos_depois[1]
    elif len(textos_depois) == 1:
        if len(textos_depois[0]) < 15:
            status_av = textos_depois[0]
        else:
            medida = textos_depois[0]

    # Dicionário Bruto
    # Nota: "Foto" continua como texto aqui; o binário é resolvido depois,
    # no nível da página, por _extrair_linha_com_foto_binaria abaixo.
    linha_bruta = {
        "Tipo_Grupo": tipo,
        "Perigo": perigo,
        "Risco_Consequencia": risco,
        "Medida_Controle_Proposta": medida_proposta,
        "P": val_p,
        "F": val_f,
        "GPL": val_gpl,
        "NP": val_np,
        "Avaliacao_Valor": val_avaliacao,
        "Avaliacao_Status": status_av,
        "Medida_Controle_Existente": medida,
        "Foto": foto_texto, # texto (pode ser vazio)
        "_foto_binario": None, # preenchido depois com bytes
    }

    linha_json = {chave: valor for chave, valor in linha_bruta.items() if str(valor).strip() != ""}
    return linha_json, grupo_anterior


# ---------------------------------------------------------------------------
# ÍNDICE DA COLUNA "FOTO" NA TABELA
# Descubra qual índice (0-based) é a coluna Foto na sua tabela.
# Você pode inspecionar imprimindo a primeira linha do cabeçalho da tabela.
# Se não tiver cabeçalho separado, ajuste conforme necessário.
# ---------------------------------------------------------------------------

def _descobrir_idx_coluna_foto(tabela):
    """
    Tenta encontrar o índice da coluna 'Foto' no cabeçalho da tabela.
    Retorna o índice (int) ou -1 se não encontrar.
    """
    for row in tabela[:3]: # olha só as 3 primeiras linhas (cabeçalho)
        for i, cell in enumerate(row):
            if cell and "foto" in str(cell).lower():
                return i
    return -1 # não encontrou


def _bbox_celula(pagina_plumber, tabela_idx, row_idx, col_idx):
    """
    Devolve o bounding box (x0, y0, x1, y1) da célula [row_idx][col_idx]
    da tabela `tabela_idx` na página do pdfplumber.

    O pdfplumber expõe os bboxes das células via pagina.extract_tables()
    com bounding_box=True, mas a API mais segura é usar find_tables()
    que devolve objetos Table com .rows e .cells.

    Retorna None se não for possível obter as coordenadas.
    """
    try:
        tabelas = pagina_plumber.find_tables()
        if tabela_idx >= len(tabelas):
            return None
        tabela = tabelas[tabela_idx]
        rows = tabela.rows
        if row_idx >= len(rows):
            return None
        celulas = rows[row_idx].cells
        if col_idx >= len(celulas):
            return None
        # celula é uma tupla (x0, top, x1, bottom) no espaço da página
        cel = celulas[col_idx]
        if cel is None:
            return None
        x0, top, x1, bottom = cel
        return (x0, top, x1, bottom)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# EXTRAÇÃO PRINCIPAL — agora resolve o binário da foto em cada linha
# ---------------------------------------------------------------------------

def extrair_somente_riscos_plano(caminho_pdf):
    """
    Extrai as linhas de risco do PDF e, para cada linha, tenta capturar
    o binário da imagem que está na célula "Foto".

    Não toca na lógica de coordenadas / mapeamento de campos —
    apenas adiciona a chave "_foto_binario" em cada dict.
    """
    lista_plana_final = []
    grupo_risco_atual = None
    caminho_pdf = Path(caminho_pdf)

    with pdfplumber.open(caminho_pdf) as pdf:
        for num_pagina, pagina in enumerate(pdf.pages):
            tabelas = pagina.extract_tables()

            if not tabelas:
                continue

            for idx_tabela, tabela in enumerate(tabelas):
                if not tabela or len(tabela) == 0:
                    continue

                texto_topo = " ".join([str(c) for row in tabela[:2] for c in row if c is not None]).lower()
                if "aspectos gerais" in texto_topo:
                    continue

                # Descobre em qual coluna fica "Foto" nessa tabela
                idx_col_foto = _descobrir_idx_coluna_foto(tabela)

                for idx_row, row in enumerate(tabela):
                    dados_linha, grupo_novo = identificar_e_mapear_linha(row, grupo_risco_atual)

                    if dados_linha is None:
                        continue

                    grupo_risco_atual = grupo_novo

                    # -------------------------------------------------------
                    # NOVIDADE: extrai o binário da imagem na célula Foto
                    # -------------------------------------------------------
                    foto_binario = None
                    if idx_col_foto != -1:
                        bbox = _bbox_celula(pagina, idx_tabela, idx_row, idx_col_foto)
                        if bbox is not None:
                            foto_binario = extrair_foto_da_linha(
                                caminho_pdf,
                                numero_pagina=num_pagina + 1, # 1-based
                                bbox_celula_foto=bbox,
                                tolerancia=5,
                            )

                    dados_linha["_foto_binario"] = foto_binario
                    lista_plana_final.append(dados_linha)

    return lista_plana_final


# ---------------------------------------------------------------------------
# PROCESSAMENTO EM LOTE — salva JSON (sem o binário) + retorna dados completos
# ---------------------------------------------------------------------------

def processar_pasta_de_pdfs(caminho_pasta):
    """
    Lê todos os PDFs da pasta, extrai riscos e salva cada resultado em JSON.

    O campo "_foto_binario" (bytes) é omitido do JSON por não ser
    serializável, mas fica disponível nos dados retornados em memória
    para quem quiser salvar direto no banco (estrutura_db.py).
    """
    pasta_origem = Path(caminho_pasta)
    pasta_destino = pasta_origem / "resultados_json"
    pasta_destino.mkdir(exist_ok=True)

    arquivos_pdf = list(pasta_origem.glob("*.pdf"))
    if not arquivos_pdf:
        print(f"Nenhum arquivo PDF encontrado na pasta: '{pasta_origem}'.")
        return {}

    print(f"🚀 Iniciando o processamento em lote. Encontrados {len(arquivos_pdf)} PDFs.")

    todos_os_dados = {}

    for caminho_pdf in arquivos_pdf:
        print(f"\nExtraindo dados de: {caminho_pdf.name}...")

        dados_extraidos = extrair_somente_riscos_plano(caminho_pdf)

        # JSON não suporta bytes: cria versão só com texto para salvar em disco
        dados_para_json = []
        for linha in dados_extraidos:
            linha_json = {k: v for k, v in linha.items() if k != "_foto_binario"}
            dados_para_json.append(linha_json)

        nome_arquivo_json = f"{caminho_pdf.stem}.json"
        caminho_saida = pasta_destino / nome_arquivo_json

        with open(caminho_saida, "w", encoding="utf-8") as f:
            json.dump(dados_para_json, f, ensure_ascii=False, indent=4)

        print(f"✅ Salvo: {len(dados_extraidos)} riscos extraídos para '{caminho_saida.name}'.")
        todos_os_dados[caminho_pdf.stem] = dados_extraidos

    print(f"\n🎉 FIM! Todos os arquivos foram salvos na pasta: {pasta_destino}")
    return todos_os_dados # inclui _foto_binario em memória


# ---------------------------------------------------------------------------
# CABEÇALHO — sem nenhuma alteração
# ---------------------------------------------------------------------------

def extrair_cabecalho_blindado(caminho_pdf):
    dados_cabecalho = {}

    with pdfplumber.open(caminho_pdf) as pdf:
        if not pdf.pages:
            return {}

        primeira_pagina = pdf.pages[0]
        tabelas = primeira_pagina.extract_tables()

        for tabela in tabelas:
            if not tabela:
                continue

            texto_tabela = " ".join(
                [str(c) for row in tabela for c in row if c]
            ).lower()

            if "técnico responsável" not in texto_tabela:
                continue

            chaves_no_bolso = []
            capturando_observacao = False

            for row in tabela:
                linha = [
                    str(c).strip().replace('\n', ' ')
                    for c in row
                    if c and str(c).strip() != ""
                ]

                if not linha:
                    continue

                texto_linha = " ".join(linha).lower()

                if (
                    "legenda" in texto_linha
                    or "probabilidade de ocorrência" in texto_linha
                    or "tipo ou grupo" in texto_linha
                ):
                    break

                if (
                    "dados da equipe" in texto_linha
                    or "dados do equipamento" in texto_linha
                ):
                    continue

                if "revisão:" in texto_linha and len(linha) == 1:
                    partes = linha[0].split(":")
                    if len(partes) == 2:
                        dados_cabecalho["Revisão"] = partes[1].strip()
                    continue

                if "observações gerais" in texto_linha:
                    capturando_observacao = True
                    dados_cabecalho["Observações Gerais"] = ""
                    continue

                if capturando_observacao:
                    dados_cabecalho["Observações Gerais"] += " ".join(linha) + " "
                    continue

                linha_tem_titulos = any(item.endswith(":") for item in linha)

                if linha_tem_titulos:
                    chaves_no_bolso = linha
                elif len(chaves_no_bolso) > 0:
                    for i in range(min(len(chaves_no_bolso), len(linha))):
                        chave_limpa = chaves_no_bolso[i].replace(":", "").strip()
                        valor = linha[i]
                        if chave_limpa:
                            dados_cabecalho[chave_limpa] = valor
                    chaves_no_bolso = []

            if dados_cabecalho:
                break

    if "Observações Gerais" in dados_cabecalho:
        dados_cabecalho["Observações Gerais"] = dados_cabecalho["Observações Gerais"].strip()

    return dados_cabecalho


def processar_pasta_de_pdfs_cab(caminho_pasta):
    pasta_origem = Path(caminho_pasta)
    pasta_destino = pasta_origem / "resultados_json_cabecalhos"
    pasta_destino.mkdir(exist_ok=True)

    arquivos_pdf = list(pasta_origem.glob("*.pdf"))
    if not arquivos_pdf:
        print(f"⚠️ Nenhum arquivo PDF encontrado na pasta: '{pasta_origem}'.")
        return

    print(f"🚀 Iniciando processamento em lote. Encontrados {len(arquivos_pdf)} PDFs.")

    for caminho_pdf in arquivos_pdf:
        print(f"\nExtraindo cabeçalho de: {caminho_pdf.name}...")

        cabecalho_extraido = extrair_cabecalho_blindado(caminho_pdf)

        if cabecalho_extraido:
            nome_arquivo_json = f"{caminho_pdf.stem}_cabecalho.json"
            caminho_saida = pasta_destino / nome_arquivo_json

            with open(caminho_saida, "w", encoding="utf-8") as f:
                json.dump([cabecalho_extraido], f, ensure_ascii=False, indent=4)

            print(f"✅ Salvo: '{caminho_saida.name}'.")
        else:
            print(f"❌ Falha: Não foi possível extrair o cabeçalho de {caminho_pdf.name}.")

    print(f"\n🎉 FIM! Todos os cabeçalhos foram salvos em:\n{pasta_destino}")


# ---------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pasta_dos_arquivos = "./pdfs"
    processar_pasta_de_pdfs(pasta_dos_arquivos)
    processar_pasta_de_pdfs_cab(pasta_dos_arquivos)
