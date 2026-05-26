import sqlite3
import json
import os
from pathlib import Path

# Constantes
PASTA_JSONS = "./pdfs/resultados_json"
PASTA_JSON_CAB = "./pdfs/resultados_json_cabecalhos"
NOME_BANCO = "./hst_database.sqlite.txt"


def criar_banco_e_tabela():
    """Conecta ao banco SQLite e cria as tabelas necessárias."""

    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()

    # Criando a tabela para situação proposta
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
            foto TEXT,
            script BOOLEAN
        )
    """)

    # Criando a tabela para situação atual
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
            foto TEXT,
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

    conn.commit()
    conn.close()


def processar_pasta_para_banco(caminho_pasta):
    """Lê todos os arquivos JSON da pasta e insere os dados no banco, evitando duplicados."""

    pasta_origem = Path(caminho_pasta)
    arquivos_json = list(pasta_origem.glob("*.json"))

    if not arquivos_json:
        print(f"Erro: Nenhum arquivo JSON encontrado na pasta '{pasta_origem}'.")
        return

    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()

    contador_proposta = 0
    contador_atual = 0
    contador_duplicados = 0  # <-- Novo contador para sabermos quantos foram ignorados

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

            # 1. Extraindo os valores para variáveis
            v_tipo = linha.get("Tipo_Grupo") or linha.get("tipo_grupo", "")
            v_perigo = linha.get("Perigo") or linha.get("perigo", "")
            v_risco = linha.get("Risco_Consequencia") or linha.get("risco_consequencia", "")
            v_p = linha.get("P") or linha.get("p", "")
            v_f = linha.get("F") or linha.get("f", "")
            v_gpl = linha.get("GPL") or linha.get("gpl", "")
            v_np = linha.get("NP") or linha.get("np", "")
            v_av_valor = linha.get("Avaliacao_Valor") or linha.get("avaliacao_valor", "")
            v_av_status = linha.get("Avaliacao_Status") or linha.get("avaliacao_status", "")
            v_medida = linha.get("Medida_Controle") or linha.get("medida_controle", "")
            v_foto = linha.get("Foto") or linha.get("foto", "")

            # =========================
            # SITUAÇÃO PROPOSTA
            # =========================
            if chave_proposta and linha.get(chave_proposta):

                v_medida_prop = linha.get(chave_proposta, "")

                # Verifica se já existe um risco idêntico no banco
                cursor.execute("""
                    SELECT 1
                    FROM hrn_sit_proposta
                    WHERE perigo = ?
                      AND risco_consequencia = ?
                      AND medida_Controle_Proposta = ?
                """, (v_perigo, v_risco, v_medida_prop))

                # Se não existir, insere
                if cursor.fetchone() is None:

                    cursor.execute("""
                        INSERT INTO hrn_sit_proposta (
                            tipo_grupo,
                            perigo,
                            risco_consequencia,
                            medida_Controle_Proposta,
                            p,
                            f,
                            gpl,
                            np,
                            avaliacao_valor,
                            avaliacao_status,
                            medida_controle,
                            foto,
                            script
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                    """, (
                        v_tipo,
                        v_perigo,
                        v_risco,
                        v_medida_prop,
                        v_p,
                        v_f,
                        v_gpl,
                        v_np,
                        v_av_valor,
                        v_av_status,
                        v_medida,
                        v_foto
                    ))

                    contador_proposta += 1

                else:
                    contador_duplicados += 1

            # =========================
            # SITUAÇÃO ATUAL
            # =========================
            else:

                # Verifica duplicidade na tabela atual
                cursor.execute("""
                    SELECT 1
                    FROM hrn_sit_atual
                    WHERE perigo = ?
                      AND risco_consequencia = ?
                """, (v_perigo, v_risco))

                if cursor.fetchone() is None:

                    cursor.execute("""
                        INSERT INTO hrn_sit_atual (
                            tipo_grupo,
                            perigo,
                            risco_consequencia,
                            p,
                            f,
                            gpl,
                            np,
                            avaliacao_valor,
                            avaliacao_status,
                            medida_controle,
                            foto,
                            script
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                    """, (
                        v_tipo,
                        v_perigo,
                        v_risco,
                        v_p,
                        v_f,
                        v_gpl,
                        v_np,
                        v_av_valor,
                        v_av_status,
                        v_medida,
                        v_foto
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
                    revisao,
                    tecnico_responsavel,
                    operacao,
                    manutencao,
                    seguranca,
                    demais_participantes,
                    area,
                    ilha,
                    registro,
                    denominacao,
                    tipo,
                    capacidade,
                    desenho_referencia,
                    fabricante,
                    modelo,
                    numero_serie,
                    ano_fabricacao,
                    observacoes_gerais,
                    script
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
            """, (
                v_revisao,
                v_tecnico_responsavel,
                v_operacao,
                v_manutencao,
                v_seguranca,
                v_demais_participantes,
                v_area,
                v_ilha,
                v_registro,
                v_denominacao,
                v_tipo,
                v_capacidade,
                v_desenho,
                v_fabricante,
                v_modelo,
                v_numero_serie,
                v_ano,
                v_obs
            ))

            contador += 1

        print(f"✅ Arquivo processado: {arquivo.name}")

    conn.commit()
    conn.close()

    print(f"\n🎉 {contador} cabeçalhos importados!")


            
if __name__ == "__main__":

    criar_banco_e_tabela()

    # Processa os JSONs
    processar_pasta_para_banco(PASTA_JSONS)
    processar_header_para_banco(PASTA_JSON_CAB)