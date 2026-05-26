import pdfplumber
import json
import re
from pathlib import Path # <-- Nova importação para lidar com pastas e arquivos

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
    
    status_av, medida, foto = "", "", ""
    if len(textos_depois) >= 3:
        status_av = textos_depois[0]
        medida = textos_depois[1]
        foto = " ".join(textos_depois[2:])
    elif len(textos_depois) == 2:
        if len(textos_depois[0]) < 15:
            status_av = textos_depois[0]
            medida = textos_depois[1]
        else:
            medida = textos_depois[0]
            foto = textos_depois[1]
    elif len(textos_depois) == 1:
        if len(textos_depois[0]) < 15:
            status_av = textos_depois[0]
        else:
            medida = textos_depois[0]

    # Dicionário Bruto
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
        "Foto": foto
    }
    
    linha_json = {chave: valor for chave, valor in linha_bruta.items() if str(valor).strip() != ""}
    return linha_json, grupo_anterior


def extrair_somente_riscos_plano(caminho_pdf):
    lista_plana_final = [] 
    grupo_risco_atual = None

    with pdfplumber.open(caminho_pdf) as pdf:
        for num_pagina, pagina in enumerate(pdf.pages):
            tabelas = pagina.extract_tables()
            if not tabelas:
                continue
                
            for tabela in tabelas:
                if not tabela or len(tabela) == 0:
                    continue
                
                texto_topo = " ".join([str(c) for row in tabela[:2] for c in row if c is not None]).lower()
                if "aspectos gerais" in texto_topo:
                    continue
                
                for row in tabela:
                    dados_linha, grupo_novo = identificar_e_mapear_linha(row, grupo_risco_atual)
                    
                    if dados_linha is not None:
                        grupo_risco_atual = grupo_novo
                        lista_plana_final.append(dados_linha)
                        
    # Retorna os dados em vez de salvar diretamente
    return lista_plana_final


def processar_pasta_de_pdfs(caminho_pasta):
    # Transforma a string em um objeto de caminho do Pathlib
    pasta_origem = Path(caminho_pasta)
    
    # Cria uma subpasta para não misturar os JSONs com os PDFs
    pasta_destino = pasta_origem / "resultados_json"
    pasta_destino.mkdir(exist_ok=True)

    # Busca todos os arquivos com extensão .pdf na pasta
    arquivos_pdf = list(pasta_origem.glob("*.pdf"))

    if not arquivos_pdf:
        print(f"Nenhum arquivo PDF encontrado na pasta: '{pasta_origem}'.")
        return

    print(f"🚀 Iniciando o processamento em lote. Encontrados {len(arquivos_pdf)} PDFs.")

    for caminho_pdf in arquivos_pdf:
        print(f"\nExtraindo dados de: {caminho_pdf.name}...")
        
        # Extrai os dados do PDF atual
        dados_extraidos = extrair_somente_riscos_plano(caminho_pdf)
        
        # Pega o nome do PDF sem a extensão e cria o nome do novo JSON
        nome_arquivo_json = f"{caminho_pdf.stem}.json"
        caminho_saida = pasta_destino / nome_arquivo_json
        
        # Salva o arquivo JSON exclusivo para este PDF
        with open(caminho_saida, "w", encoding="utf-8") as f:
            json.dump(dados_extraidos, f, ensure_ascii=False, indent=4)
            
        print(f"✅ Salvo: {len(dados_extraidos)} riscos extraídos para '{caminho_saida.name}'.")
        
    print(f"\n🎉 FIM! Todos os arquivos foram salvos na pasta: {pasta_destino}")


def extrair_cabecalho_blindado(caminho_pdf):

    dados_cabecalho = {}

    with pdfplumber.open(caminho_pdf) as pdf:

        if not pdf.pages:
            return {}

        # Primeira página
        primeira_pagina = pdf.pages[0]

        tabelas = primeira_pagina.extract_tables()

        for tabela in tabelas:

            if not tabela:
                continue
            texto_tabela = " ".join(
                [
                    str(c)
                    for row in tabela
                    for c in row
                    if c
                ]
            ).lower()

            if "técnico responsável" not in texto_tabela:
                continue

            chaves_no_bolso = []
            capturando_observacao = False

            # =========================
            # Percorre linhas da tabela
            # =========================
            for row in tabela:

                # Limpeza da linha
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
                
                if (
                    "revisão:" in texto_linha
                    and len(linha) == 1
                ):

                    partes = linha[0].split(":")

                    if len(partes) == 2:

                        dados_cabecalho["Revisão"] = (
                            partes[1].strip()
                        )

                    continue

                if "observações gerais" in texto_linha:

                    capturando_observacao = True

                    dados_cabecalho["Observações Gerais"] = ""

                    continue

                if capturando_observacao:

                    dados_cabecalho["Observações Gerais"] += (
                        " ".join(linha) + " "
                    )

                    continue


                linha_tem_titulos = any(
                    item.endswith(":")
                    for item in linha
                )

                if linha_tem_titulos:

                    # Guarda as chaves
                    chaves_no_bolso = linha

                elif len(chaves_no_bolso) > 0:

                    # Linha atual contém os valores
                    for i in range(
                        min(len(chaves_no_bolso), len(linha))
                    ):

                        chave_limpa = (
                            chaves_no_bolso[i]
                            .replace(":", "")
                            .strip()
                        )

                        valor = linha[i]

                        if chave_limpa:
                            dados_cabecalho[chave_limpa] = valor

                    # Limpa o bolso
                    chaves_no_bolso = []

            # Se encontrou dados válidos
            if dados_cabecalho:
                break

    # =========================
    # Limpeza final
    # =========================
    if "Observações Gerais" in dados_cabecalho:

        dados_cabecalho["Observações Gerais"] = (
            dados_cabecalho["Observações Gerais"].strip()
        )

    return dados_cabecalho


# ==================================================
# PROCESSAMENTO EM LOTE
# ==================================================
def processar_pasta_de_pdfs_cab(caminho_pasta):

    # Converte em objeto Path
    pasta_origem = Path(caminho_pasta)

    # Pasta destino
    pasta_destino = (
        pasta_origem / "resultados_json_cabecalhos"
    )

    pasta_destino.mkdir(exist_ok=True)

    # Busca PDFs
    arquivos_pdf = list(
        pasta_origem.glob("*.pdf")
    )

    if not arquivos_pdf:

        print(
            f"⚠️ Nenhum arquivo PDF encontrado na pasta: '{pasta_origem}'."
        )

        return

    print(
        f"🚀 Iniciando processamento em lote. "
        f"Encontrados {len(arquivos_pdf)} PDFs."
    )

    # =========================
    # Loop dos PDFs
    # =========================
    for caminho_pdf in arquivos_pdf:

        print(
            f"\nExtraindo cabeçalho de: "
            f"{caminho_pdf.name}..."
        )

        # Extrai cabeçalho
        cabecalho_extraido = (
            extrair_cabecalho_blindado(caminho_pdf)
        )

        if cabecalho_extraido:

            # Nome do JSON
            nome_arquivo_json = (
                f"{caminho_pdf.stem}_cabecalho.json"
            )

            caminho_saida = (
                pasta_destino / nome_arquivo_json
            )

            # Lista para banco
            dados_para_salvar = [
                cabecalho_extraido
            ]

            # Salva JSON
            with open(
                caminho_saida,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    dados_para_salvar,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

            print(
                f"✅ Salvo: "
                f"'{caminho_saida.name}'."
            )

        else:

            print(
                f"❌ Falha: "
                f"Não foi possível extrair "
                f"o cabeçalho de "
                f"{caminho_pdf.name}."
            )

    print(
        f"\n🎉 FIM! "
        f"Todos os cabeçalhos foram salvos em:\n"
        f"{pasta_destino}"
    )


# ==================================================
# EXECUÇÃO PRINCIPAL
# ==================================================

if __name__ == "__main__":
    # Insira o caminho para a pasta onde estão os seus PDFs
    # Se o script estiver na mesma pasta dos PDFs, você pode usar "."
    pasta_dos_arquivos = "./pdfs"
    processar_pasta_de_pdfs(pasta_dos_arquivos)
    processar_pasta_de_pdfs_cab(pasta_dos_arquivos)
