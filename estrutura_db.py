import sqlite3
import json
from pathlib import Path
import os

PASTA_JSONS = "./output/json"
PASTA_JSON_CAB = "./output/json_cabecalho"
NOME_BANCO = "Y:/27 - HIGIENE OCUPACIONAL/BANCOS_BASE/convert_hst_database/hst_database.sqlite-teste.db"

os.makedirs(os.path.dirname(NOME_BANCO), exist_ok=True)

def get_field(linha, *chaves):
    """Busca segura por múltiplas chaves, sem mascarar valores falsy com `or`."""
    for chave in chaves:
        if chave in linha:
            return linha[chave]
    return None

#--------------------------------------------------------------------------------

def create_table():
    """Cria as tabelas e faz a conexão com o banco de dados."""
    with sqlite3.connect(NOME_BANCO) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Cria a tabela de cabeçalho
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cab_hrn (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_arquivo TEXT UNIQUE, 
                revisao TEXT,
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

        # Cria a tabela de Situacao proposta
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hrn_sit_proposta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cab INTEGER NOT NULL,
                tipo_grupo TEXT,
                perigo TEXT,
                risco_consequencia TEXT,
                medida_controle_proposta TEXT,
                p TEXT,
                f TEXT,
                gpl TEXT,
                np TEXT,
                avaliacao_valor TEXT,
                avaliacao_status TEXT,
                medida_controle TEXT,
                foto TEXT,
                script BOOLEAN,
                FOREIGN KEY (id_cab) REFERENCES cab_hrn (id)
            )
        """)

        # Cria a tabela de situacao atual
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hrn_sit_atual (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cab INTEGER NOT NULL,
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
                script BOOLEAN,
                FOREIGN KEY (id_cab) REFERENCES cab_hrn (id)
            )
        """)
        conn.commit()

#--------------------------------------------------------------------------------

def header_to_db(caminho_pasta):
    """Insere os cabeçalhos e remove o arquivo após o sucesso."""
    pasta_origem = Path(caminho_pasta)
    arquivos_json = list(pasta_origem.glob("*.json"))

    if not arquivos_json:
        print(f"Erro: Nenhum arquivo JSON encontrado em '{pasta_origem}'.")
        return

    print(f"Importando {len(arquivos_json)} cabeçalho(s)...\n")

    # Usando o context manager 'with' para fechar a conexão automaticamente em caso de erro
    with sqlite3.connect(NOME_BANCO) as conn:
        conn.execute("PRAGMA foreign_keys = ON") #p aceitar chave estrangeira
        cursor = conn.cursor()
        contador = 0

        for arquivo in arquivos_json:
            nome_base = arquivo.stem.replace("_cabecalho", "")
            sucesso_arquivo = True

            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    relatorios = json.load(f)

                for linha in relatorios:
                    if not isinstance(linha, dict):
                        continue
                    
                    data = (
                        nome_base,
                        get_field(linha, "Revisão", "revisao", "Revisao"),
                        get_field(linha, "Técnico Responsável", "tecnico_responsavel", "Tecnico_Responsavel"),
                        get_field(linha, "Operação (área)", "operacao", "Operacao"),
                        get_field(linha, "Manutenção (área)", "manutencao", "Manutencao"),
                        get_field(linha, "Segurança (área)", "seguranca", "Seguranca"),
                        get_field(linha, "Demais Participantes", "demais_participantes"),
                        get_field(linha, "Área", "area", "Area"),
                        get_field(linha, "Ilha", "ilha"),
                        get_field(linha, "Registro (Tag)", "registro", "Registro"),
                        get_field(linha, "Denominação", "denominacao", "Denominacao"),
                        get_field(linha, "Tipo", "tipo"),
                        get_field(linha, "Capacidade", "capacidade"),
                        get_field(linha, "Desenho de Referência", "desenho_referencia", "desenho_de_referencia"),
                        get_field(linha, "Fabricante", "fabricante"),
                        get_field(linha, "Modelo", "modelo"),
                        get_field(linha, "Número de Série", "Numero de Série", "numero_serie", "numero_de_serie"),
                        get_field(linha, "Ano de Fabricação", "ano_fabricacao", "ano_de_fabricacao"),
                        get_field(linha, "Observações Gerais", "observacoes_gerais"),
                    )

                    cursor.execute("SELECT 1 FROM cab_hrn WHERE nome_arquivo = ?", (nome_base,))
                    
                    if cursor.fetchone():
                        print(f"Duplicado ignorado: {nome_base}")
                    else:
                        cursor.execute("""
                            INSERT INTO cab_hrn (
                                nome_arquivo, revisao, tecnico_responsavel, operacao, manutencao,
                                seguranca, demais_participantes, area, ilha, registro,
                                denominacao, tipo, capacidade, desenho_referencia,
                                fabricante, modelo, numero_serie, ano_fabricacao,
                                observacoes_gerais, script
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                        """, data)
                        contador += 1

                print(f"Processado com sucesso: {arquivo.name}")
                
            except Exception as e:
                print(f"Erro ao processar o arquivo {arquivo.name}: {e}")
                sucesso_arquivo = False  # Marca como falso se houver erro no JSON ou SQL
            
            # Deleta o arquivo IMEDIATAMENTE se deu tudo certo com ele
            if sucesso_arquivo:
                try:
                    arquivo.unlink()
                    print(f"Removido: {arquivo.name}")
                except Exception as e:
                    print(f"Arquivo não pôde ser removido {arquivo.name}: {e}")

        conn.commit()
    print(f"\n{contador} cabeçalho(s) importado(s)!\n")

#--------------------------------------------------------------------------------

def processar_pasta_para_banco(caminho_pasta):
    """Lê os JSONs de detalhe e limpa após processar."""
    pasta_origem = Path(caminho_pasta)
    arquivos_json = list(pasta_origem.glob("*.json"))

    if not arquivos_json:
        print(f"Erro: Nenhum arquivo JSON encontrado em '{pasta_origem}'.")
        return

    print(f"Importando {len(arquivos_json)} arquivo(s) de detalhe...\n")

    with sqlite3.connect(NOME_BANCO) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        contador_proposta = 0
        contador_atual = 0
        contador_duplicados = 0
        contador_sem_cab = 0

        for arquivo in arquivos_json:
            nome_base = arquivo.stem
            cursor.execute("SELECT id FROM cab_hrn WHERE nome_arquivo = ?", (nome_base,))
            row = cursor.fetchone()

            if row is None:
                print(f"Cabeçalho não encontrado para '{arquivo.name}' — pulando.")
                contador_sem_cab += 1
                continue

            id_cab = row[0]
            sucesso_arquivo = True

            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    relatorios = json.load(f)

                for linha in relatorios:
                    if not isinstance(linha, dict):
                        continue

                    chave_proposta = next(
                        (k for k in linha if k.lower() == "medida_controle_proposta"),
                        None
                    )

                    v_tipo = get_field(linha, "Tipo_Grupo", "tipo_grupo")
                    v_perigo = get_field(linha, "Perigo", "perigo")
                    v_risco = get_field(linha, "Risco_Consequencia", "risco_consequencia")
                    v_p = get_field(linha, "P", "p")
                    v_f = get_field(linha, "F", "f")
                    v_gpl = get_field(linha, "GPL", "gpl")
                    v_np = get_field(linha, "NP", "np")
                    v_av_val = get_field(linha, "Avaliacao_Valor", "avaliacao_valor")
                    v_av_st = get_field(linha, "Avaliacao_Status", "avaliacao_status")
                    v_medida = get_field(linha, "Medida_Controle_Existente", "Medida_Controle", "medida_controle")
                    v_foto = get_field(linha, "Foto", "foto")

                    # ---------- SITUAÇÃO PROPOSTA ----------
                    if chave_proposta and linha.get(chave_proposta):
                        v_medida_prop = linha[chave_proposta]

                        cursor.execute("""
                            SELECT 1 FROM hrn_sit_proposta
                            WHERE id_cab = ? AND perigo = ?
                              AND risco_consequencia = ? AND medida_controle_proposta = ?
                        """, (id_cab, v_perigo, v_risco, v_medida_prop))

                        if cursor.fetchone() is None:
                            cursor.execute("""
                                INSERT INTO hrn_sit_proposta (
                                    id_cab, tipo_grupo, perigo, risco_consequencia,
                                    medida_controle_proposta, p, f, gpl, np,
                                    avaliacao_valor, avaliacao_status, medida_controle, foto, script
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                            """, (
                                id_cab, v_tipo, v_perigo, v_risco, v_medida_prop,
                                v_p, v_f, v_gpl, v_np, v_av_val, v_av_st, v_medida, v_foto
                            ))
                            contador_proposta += 1
                        else:
                            contador_duplicados += 1

                    # ---------- SITUAÇÃO ATUAL ----------
                    else:
                        cursor.execute("""
                            SELECT 1 FROM hrn_sit_atual
                            WHERE id_cab = ? AND perigo = ? AND risco_consequencia = ?
                        """, (id_cab, v_perigo, v_risco))

                        if cursor.fetchone() is None:
                            cursor.execute("""
                                INSERT INTO hrn_sit_atual (
                                    id_cab, tipo_grupo, perigo, risco_consequencia,
                                    p, f, gpl, np, avaliacao_valor, avaliacao_status,
                                    medida_controle, foto, script
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                            """, (
                                id_cab, v_tipo, v_perigo, v_risco,
                                v_p, v_f, v_gpl, v_np, v_av_val, v_av_st, v_medida, v_foto
                            ))
                            contador_atual += 1
                        else:
                            contador_duplicados += 1

                print(f"Detalhes Processados: {arquivo.name} (id_cab={id_cab})")

            except Exception as e:
                print(f"Erro ao processar o arquivo de detalhe {arquivo.name}: {e}")
                sucesso_arquivo = False

            # Deleta se o processamento terminou sem exceções
            if sucesso_arquivo:
                try:
                    arquivo.unlink()
                    print(f"Removido: {arquivo.name}")
                except Exception as e:
                    print(f"Arquivo não pôde ser removido {arquivo.name}: {e}")

        conn.commit()

    print("\nImportação finalizada!")
    print(f" ↳ {contador_proposta} linha(s) em 'hrn_sit_proposta'")
    print(f" ↳ {contador_atual} linha(s) em 'hrn_sit_atual'")
    print(f" ↳ {contador_duplicados} ignorada(s) (duplicadas)")
    if contador_sem_cab:
        print(f" ↳ {contador_sem_cab} arquivo(s) sem cabeçalho correspondente")

#--------------------------------------------------------------------------------

if __name__ == "__main__":
    create_table()
    header_to_db(PASTA_JSON_CAB)
    processar_pasta_para_banco(PASTA_JSONS)