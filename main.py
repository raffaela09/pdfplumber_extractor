import sqlite3
import json
import os

# constantes 
ARQUIVO_JSON = "extracao_finalizada2.json"
NOME_BANCO = "database.db"

def criar_banco_e_tabela():
    """Conecta ao banco SQLite e cria as tabelas necessárias."""
    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()
    
    # Criando a tabela para situação proposta
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hrn_sit_proposta(
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
    
    # Criando a tabela para situação atual - retira o campo de proposta
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
        script BOOlEAN
    )
    """)
    
    conn.commit()
    conn.close()

def importar_json_para_banco():
    """Lê o arquivo JSON e insere os dados separadamente."""
    if not os.path.exists(ARQUIVO_JSON):
        print(f"Erro: O arquivo {ARQUIVO_JSON} não foi encontrado.")
        return

    with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
        relatorios = json.load(f)

    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()
    
    # contadores das linhas que foram inseridas
    contador_proposta = 0
    contador_atual = 0
    
    for linha in relatorios:
        if not isinstance(linha, dict):
            continue

        #tratando variação de maiúscula/minúscula na chave do JSON
        chave_proposta = None
        for k in linha.keys():
            if k.lower() == 'medida_controle_proposta':
                chave_proposta = k
                break

        # caso a chave exista e nao esta em branco 
        if chave_proposta and linha.get(chave_proposta):
            #faz o insert na tabela de hrn - situacao proposta
            cursor.execute("""
                INSERT INTO hrn_sit_proposta (
                    tipo_grupo, perigo, risco_consequencia, medida_Controle_Proposta, p, f, gpl, np, 
                    avaliacao_valor, avaliacao_status, medida_controle, foto, script
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
            """, (
                linha.get("Tipo_Grupo") or linha.get("tipo_grupo", ""),
                linha.get("Perigo") or linha.get("perigo", ""),
                linha.get("Risco_Consequencia") or linha.get("risco_consequencia", ""),
                linha.get(chave_proposta, ""),
                linha.get("P") or linha.get("p", ""),
                linha.get("F") or linha.get("f", ""),
                linha.get("GPL") or linha.get("gpl", ""),
                linha.get("NP") or linha.get("np", ""),
                linha.get("Avaliacao_Valor") or linha.get("avaliacao_valor", ""),
                linha.get("Avaliacao_Status") or linha.get("avaliacao_status", ""),
                linha.get("Medida_Controle") or linha.get("medida_controle", ""),
                linha.get("Foto") or linha.get("foto", "")
            ))
            contador_proposta += 1
        else:
            #faz o insert na tabela hrn - situacao atual - caso n tenha a chave de 'medida proposta'
            cursor.execute("""
                INSERT INTO hrn_sit_atual (
                    tipo_grupo, perigo, risco_consequencia, p, f, gpl, np, 
                    avaliacao_valor, avaliacao_status, medida_controle, foto, script
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
            """, (
                linha.get("Tipo_Grupo") or linha.get("tipo_grupo", ""),
                linha.get("Perigo") or linha.get("perigo", ""),
                linha.get("Risco_Consequencia") or linha.get("risco_consequencia", ""),
                linha.get("P") or linha.get("p", ""),
                linha.get("F") or linha.get("f", ""),
                linha.get("GPL") or linha.get("gpl", ""),
                linha.get("NP") or linha.get("np", ""),
                linha.get("Avaliacao_Valor") or linha.get("avaliacao_valor", ""),
                linha.get("Avaliacao_Status") or linha.get("avaliacao_status", ""),
                linha.get("Medida_Controle") or linha.get("medida_controle", ""),
                linha.get("Foto") or linha.get("foto", "")
            ))
            contador_atual += 1
        
    conn.commit()
    conn.close()
    print(f"Sucesso!")
    print(f"   ↳ {contador_proposta} linhas salvas em 'hrn_sit_proposta'")
    print(f"   ↳ {contador_atual} linhas salvas em 'hrn_sit_atual'")

if __name__ == "__main__":
    # Dica: Exclua o arquivo 'database.db' antigo da pasta antes de rodar para recriar as tabelas limpas
    criar_banco_e_tabela()
    importar_json_para_banco()