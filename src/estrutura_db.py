import sqlite3
import json
import os
from pathlib import Path

from src.image_extractor import processar_pasta_de_imagens

# Constantes
PASTA_JSONS = "./pdfs/resultados_json"
PASTA_JSON_CAB = "./pdfs/resultados_json_cabecalhos"
NOME_BANCO = "./hst_database.sqlite.txt"


def criar_banco_e_tabela():
    """Conecta ao banco SQLite e cria as tabelas necessárias."""
    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()

    # -----------------------------------------------------------------------
    # MUDANÇA: coluna "foto" agora é BLOB (binário da imagem).
    # Se o banco já existe com "foto TEXT", rode o script de migração
    # abaixo (ou apague o banco e recrie do zero).
    # -----------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hrn_sit_proposta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_grupo TEXT,
            perigo TEXT,
            risco_consequencia TEXT,
            medida_Controle_Proposta TEXT,
            p TEXT,
            f TEXT,
            gpl TEXT,
            np TEXT,
            avaliacao_valor TEXT,
            avaliacao_status TEXT,
            medida_controle TEXT,
            foto BLOB,
            script BOOLEAN
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hrn_sit_atual (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_grupo TEXT,
            perigo TEXT,
            risco_consequencia TEXT,
            p TEXT,
            f TEXT,
            gpl TEXT,
            np TEXT,
            avaliacao_valor TEXT,
            avaliacao_status TEXT,
            medida_controle TEXT,
            foto BLOB,
            script BOOLEAN
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cab_hrn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            revisao NUMBER,
            tecnico_responsavel TEXT,
            operacao TEXT,
            manutencao TEXT,
            seguranca TEXT,
            demais_participantes TEXT,
            area TEXT,
            ilha TEXT,
            registro TEXT,
            denominacao TEXT,
            tipo TEXT,
            capacidade TEXT,
            desenho_referencia TEXT,
            fabricante TEXT,
            modelo TEXT,
            numero_serie TEXT,
            ano_fabricacao TEXT,
            observacoes_gerais TEXT,
            script BOOLEAN
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS imagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_origem TEXT,
            pagina INTEGER,
            indice_imagem INTEGER,
            nome_arquivo TEXT,
            extensao TEXT,
            conteudo_binario BLOB,
            script BOOLEAN
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# NOVA FUNÇÃO: importa dados diretamente da memória (com binário da foto)
# Chame esta função passando o retorno de processar_pasta_de_pdfs().
# ---------------------------------------------------------------------------

def processar_dados_em_memoria(todos_os_dados):
    """
    Recebe o dicionário devolvido por extractor.processar_pasta_de_pdfs()
    — que inclui a chave '_foto_binario' com os bytes de cada imagem —
    e insere os dados nas tabelas hrn_sit_proposta / hrn_sit_atual.

    Esta função substitui processar_pasta_para_banco() quando você quer
    ter a foto como BLOB no banco em vez de string vazia.

    Parâmetro:
        todos_os_dados : dict { nome_pdf: [lista de dicts de linha] }
    """
    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()

    contador_proposta = 0
    contador_atual = 0
    contador_duplicados = 0

    for nome_pdf, linhas in todos_os_dados.items():
        for linha in linhas:
            if not isinstance(linha, dict):
                continue

            # Identifica se é situação proposta
            chave_proposta = None
            for k in linha.keys():
                if k.lower() == 'medida_controle_proposta':
                    chave_proposta = k
                    break

            v_tipo = linha.get("Tipo_Grupo") or linha.get("tipo_grupo", "")
            v_perigo = linha.get("Perigo") or linha.get("perigo", "")
            v_risco = linha.get("Risco_Consequencia") or linha.get("risco_consequencia", "")
            v_p = linha.get("P") or linha.get("p", "")
            v_f = linha.get("F") or linha.get("f", "")
            v_gpl = linha.get("GPL") or linha.get("gpl", "")
            v_np = linha.get("NP") or linha.get("np", "")
            v_av_valor = linha.get("Avaliacao_Valor") or linha.get("avaliacao_valor", "")
            v_av_status= linha.get("Avaliacao_Status") or linha.get("avaliacao_status", "")
            v_medida = linha.get("Medida_Controle_Existente") or linha.get("medida_controle", "")

            # Pega o binário da foto (pode ser None se não houver imagem)
            v_foto_blob = linha.get("_foto_binario") # bytes ou None

            if chave_proposta and linha.get(chave_proposta):
                v_medida_prop = linha.get(chave_proposta, "")

                cursor.execute("""
                    SELECT 1 FROM hrn_sit_proposta
                    WHERE perigo = ? AND risco_consequencia = ? AND medida_Controle_Proposta = ?
                """, (v_perigo, v_risco, v_medida_prop))

                if cursor.fetchone() is None:
                    cursor.execute("""
                        INSERT INTO hrn_sit_proposta (
                            tipo_grupo, perigo, risco_consequencia,
                            medida_Controle_Proposta, p, f, gpl, np,
                            avaliacao_valor, avaliacao_status,
                            medida_controle, foto, script
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                    """, (
                        v_tipo, v_perigo, v_risco, v_medida_prop,
                        v_p, v_f, v_gpl, v_np,
                        v_av_valor, v_av_status, v_medida,
                        v_foto_blob, # <-- BLOB
                    ))
                    contador_proposta += 1
                else:
                    contador_duplicados += 1

            else:
                cursor.execute("""
                    SELECT 1 FROM hrn_sit_atual
                    WHERE perigo = ? AND risco_consequencia = ?
                """, (v_perigo, v_risco))

                if cursor.fetchone() is None:
                    cursor.execute("""
                        INSERT INTO hrn_sit_atual (
                            tipo_grupo, perigo, risco_consequencia,
                            p, f, gpl, np,
                            avaliacao_valor, avaliacao_status,
                            medida_controle, foto, script
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                    """, (
                        v_tipo, v_perigo, v_risco,
                        v_p, v_f, v_gpl, v_np,
                        v_av_valor, v_av_status, v_medida,
                        v_foto_blob, # <-- BLOB
                    ))
                    contador_atual += 1
                else:
                    contador_duplicados += 1

    conn.commit()
    conn.close()

    print("\n🎉 Importação finalizada!")
    print(f" ↳ {contador_proposta} novas linhas salvas em 'hrn_sit_proposta'")
    print(f" ↳ {contador_atual} novas linhas salvas em 'hrn_sit_atual'")
    print(f" ↳ ⚠️ {contador_duplicados} linhas ignoradas (já existiam no banco)")


# ---------------------------------------------------------------------------
# FUNÇÕES ORIGINAIS — mantidas sem alteração para compatibilidade
# ---------------------------------------------------------------------------

def processar_pasta_para_banco(caminho_pasta):
    """
    Versão original: lê JSONs do disco e insere no banco.
    Nesta versão a coluna 'foto' fica NULL (os JSONs não têm o binário).
    Prefira usar processar_dados_em_memoria() para ter o binário da foto.
    """
    pasta_origem = Path(caminho_pasta)
    arquivos_json = list(pasta_origem.glob("*.json"))

    if not arquivos_json:
        print(f"Erro: Nenhum arquivo JSON encontrado na pasta '{pasta_origem}'.")
        return

    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()

    contador_proposta = 0
    contador_atual = 0
    contador_duplicados = 0

    print(f"Iniciando a importação de {len(arquivos_json)} arquivos para o banco de dados...\n")

    for arquivo in arquivos_json:
        with open(arquivo, 'r', encoding='utf-8') as f:
            relatorios = json.load(f)

        for linha in relatorios:
            if not isinstance(linha, dict):
                continue

            chave_proposta = None
            for k in linha.keys():
                if k.lower() == 'medida_controle_proposta':
                    chave_proposta = k
                    break

            v_tipo = linha.get("Tipo_Grupo") or linha.get("tipo_grupo", "")
            v_perigo = linha.get("Perigo") or linha.get("perigo", "")
            v_risco = linha.get("Risco_Consequencia") or linha.get("risco_consequencia", "")
            v_p = linha.get("P") or linha.get("p", "")
            v_f = linha.get("F") or linha.get("f", "")
            v_gpl = linha.get("GPL") or linha.get("gpl", "")
            v_np = linha.get("NP") or linha.get("np", "")
            v_av_valor = linha.get("Avaliacao_Valor") or linha.get("avaliacao_valor", "")
            v_av_status= linha.get("Avaliacao_Status") or linha.get("avaliacao_status", "")
            v_medida = linha.get("Medida_Controle") or linha.get("medida_controle", "")
            # JSON não carrega binário; foto fica NULL
            v_foto_blob = None

            if chave_proposta and linha.get(chave_proposta):
                v_medida_prop = linha.get(chave_proposta, "")

                cursor.execute("""
                    SELECT 1 FROM hrn_sit_proposta
                    WHERE perigo = ? AND risco_consequencia = ? AND medida_Controle_Proposta = ?
                """, (v_perigo, v_risco, v_medida_prop))

                if cursor.fetchone() is None:
                    cursor.execute("""
                        INSERT INTO hrn_sit_proposta (
                            tipo_grupo, perigo, risco_consequencia,
                            medida_Controle_Proposta, p, f, gpl, np,
                            avaliacao_valor, avaliacao_status,
                            medida_controle, foto, script
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                    """, (
                        v_tipo, v_perigo, v_risco, v_medida_prop,
                        v_p, v_f, v_gpl, v_np,
                        v_av_valor, v_av_status, v_medida, v_foto_blob,
                    ))
                    contador_proposta += 1
                else:
                    contador_duplicados += 1
            else:
                cursor.execute("""
                    SELECT 1 FROM hrn_sit_atual
                    WHERE perigo = ? AND risco_consequencia = ?
                """, (v_perigo, v_risco))

                if cursor.fetchone() is None:
                    cursor.execute("""
                        INSERT INTO hrn_sit_atual (
                            tipo_grupo, perigo, risco_consequencia,
                            p, f, gpl, np,
                            avaliacao_valor, avaliacao_status,
                            medida_controle, foto, script
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                    """, (
                        v_tipo, v_perigo, v_risco,
                        v_p, v_f, v_gpl, v_np,
                        v_av_valor, v_av_status, v_medida, v_foto_blob,
                    ))
                    contador_atual += 1
                else:
                    contador_duplicados += 1

        print(f"✅ Arquivo processado: {arquivo.name}")

    conn.commit()
    conn.close()

    print("\n🎉 Importação finalizada!")
    print(f" ↳ {contador_proposta} novas linhas salvas em 'hrn_sit_proposta'")
    print(f" ↳ {contador_atual} novas linhas salvas em 'hrn_sit_atual'")
    print(f" ↳ ⚠️ {contador_duplicados} linhas ignoradas (já existiam no banco)")


def processar_header_para_banco(caminho_pasta):
    pasta_origem = Path(caminho_pasta)
    arquivos_json = list(pasta_origem.glob("*.json"))

    if not arquivos_json:
        print(f"Erro: Nenhum arquivo JSON encontrado na pasta '{pasta_origem}'.")
        return

    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()

    contador = 0
    print(f"Iniciando a importação de {len(arquivos_json)} arquivos...\n")

    for arquivo in arquivos_json:
        with open(arquivo, 'r', encoding='utf-8') as f:
            relatorios = json.load(f)

        for linha in relatorios:
            if not isinstance(linha, dict):
                continue

            v_revisao = linha.get("Revisão") or linha.get("revisao", "")
            v_tecnico_responsavel = linha.get("Técnico Responsável") or linha.get("tecnico_responsavel", "")
            v_operacao = linha.get("Operação (área)") or linha.get("operacao", "")
            v_manutencao = linha.get("Manutenção (área)") or linha.get("manutencao", "")
            v_seguranca = linha.get("Segurança (área)") or linha.get("seguranca", "")
            v_demais_participantes = linha.get("Demais Participantes") or linha.get("demais_participantes", "")
            v_area = linha.get("Área") or linha.get("area", "")
            v_ilha = linha.get("Ilha") or linha.get("ilha", "")
            v_registro = linha.get("Registro (Tag)") or linha.get("registro", "")
            v_denominacao = linha.get("Denominação") or linha.get("denominacao", "")
            v_tipo = linha.get("Tipo") or linha.get("tipo", "")
            v_capacidade = linha.get("Capacidade") or linha.get("capacidade", "")
            v_desenho = linha.get("Desenho de Referência") or linha.get("desenho_de_referencia", "")
            v_fabricante = linha.get("Fabricante") or linha.get("fabricante", "")
            v_modelo = linha.get("Modelo") or linha.get("modelo", "")
            v_numero_serie = linha.get("Numero de Série") or linha.get("numero_de_serie", "")
            v_ano = linha.get("Ano de Fabricação") or linha.get("ano_de_fabricacao", "")
            v_obs = linha.get("Observações Gerais") or linha.get("observacoes_gerais", "")

            cursor.execute("""
                INSERT INTO cab_hrn (
                    revisao, tecnico_responsavel, operacao, manutencao,
                    seguranca, demais_participantes, area, ilha, registro,
                    denominacao, tipo, capacidade, desenho_referencia,
                    fabricante, modelo, numero_serie, ano_fabricacao,
                    observacoes_gerais, script
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
            """, (
                v_revisao, v_tecnico_responsavel, v_operacao, v_manutencao,
                v_seguranca, v_demais_participantes, v_area, v_ilha, v_registro,
                v_denominacao, v_tipo, v_capacidade, v_desenho,
                v_fabricante, v_modelo, v_numero_serie, v_ano, v_obs
            ))
            contador += 1

        print(f"✅ Arquivo processado: {arquivo.name}")

    conn.commit()
    conn.close()
    print(f"\n🎉 {contador} cabeçalhos importados!")


def processar_pasta_de_imagens_para_banco(caminho_pasta_pdfs):
    """
    Extrai as imagens de todos os PDFs de uma pasta e salva na tabela 'imagens'.
    (Tabela de inventário geral de imagens — separada da coluna foto das tabelas de risco.)
    """
    imagens_por_pdf = processar_pasta_de_imagens(caminho_pasta_pdfs)

    if not imagens_por_pdf:
        return

    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()

    contador_inseridas = 0
    contador_duplicadas = 0

    for nome_pdf, imagens in imagens_por_pdf.items():
        for imagem in imagens:
            cursor.execute("""
                SELECT 1 FROM imagens
                WHERE pdf_origem = ? AND pagina = ? AND indice_imagem = ?
            """, (nome_pdf, imagem["pagina"], imagem["indice"]))

            if cursor.fetchone() is not None:
                contador_duplicadas += 1
                continue

            cursor.execute("""
                INSERT INTO imagens (
                    pdf_origem, pagina, indice_imagem,
                    nome_arquivo, extensao, conteudo_binario, script
                ) VALUES (?, ?, ?, ?, ?, ?, TRUE)
            """, (
                nome_pdf,
                imagem["pagina"],
                imagem["indice"],
                imagem["nome_arquivo"],
                imagem["extensao"],
                imagem["conteudo_binario"],
            ))
            contador_inseridas += 1

    conn.commit()
    conn.close()

    print("\n Imagens importadas para o banco!")
    print(f" ↳ {contador_inseridas} novas imagens salvas em 'imagens'")
    print(f" ↳  {contador_duplicadas} imagens já existiam no banco")


if __name__ == "__main__":
    criar_banco_e_tabela()
    processar_pasta_para_banco(PASTA_JSONS)
    processar_header_para_banco(PASTA_JSON_CAB)
    processar_pasta_de_imagens_para_banco("./pdfs")
