import pdfplumber
import json


def extrair_cabecalho_blindado(caminho_pdf):

    print("Extraindo Cabeçalho com Escudo Anti-Legenda...")

    dados_cabecalho = {}

    with pdfplumber.open(caminho_pdf) as pdf:

        if not pdf.pages:
            return {}

        # Primeira página apenas
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

            # Variáveis auxiliares
            chaves_no_bolso = []
            capturando_observacao = False


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

                #para n pegar a legenda
                if (
                    "legenda" in texto_linha
                    or "probabilidade de ocorrência" in texto_linha
                    or "tipo ou grupo" in texto_linha
                ):

                    print("🛑 Escudo ativado: Matriz/Legenda ignoradas com sucesso!")

                    # Interrompe leitura da tabela
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

                        dados_cabecalho["Revisão"] = partes[1].strip()

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


                # Detecta linha de títulos
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

            # Se conseguiu dados válidos
            if dados_cabecalho:
                break

    if "Observações Gerais" in dados_cabecalho:

        dados_cabecalho["Observações Gerais"] = (
            dados_cabecalho["Observações Gerais"].strip()
        )

    return dados_cabecalho


if __name__ == "__main__":

    meu_pdf = "./pdfs/teste.pdf"

    cabecalho_extraido = extrair_cabecalho_blindado(meu_pdf)

    dados_para_salvar = (
        [cabecalho_extraido]
        if cabecalho_extraido
        else []
    )

    arquivo_saida = "cabecalho_perfeito.json"

    with open(arquivo_saida, "w", encoding="utf-8") as f:

        json.dump(
            dados_para_salvar,
            f,
            ensure_ascii=False,
            indent=4
        )

    print(f"\nFIM! Arquivo salvo em '{arquivo_saida}'.")

    print(
        json.dumps(
            cabecalho_extraido,
            indent=4,
            ensure_ascii=False
        )
    )