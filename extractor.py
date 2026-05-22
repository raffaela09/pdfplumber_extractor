import pdfplumber
import json
import re

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

    # --- 1. MAPEAMENTO (ESQUERDA) - Agora com Medida Proposta Dinâmica! ---
    textos_antes = [cells[i] for i in range(start_num_idx) if cells[i] != ""]
    tipo, perigo, risco, medida_proposta = "", "", "", ""
    
    # Se vieram 4 colunas antes dos números (Tem a medida proposta!)
    if len(textos_antes) >= 4:
        tipo = textos_antes[0]
        perigo = textos_antes[1]
        risco = textos_antes[2]
        medida_proposta = " ".join(textos_antes[3:])
    # Padrão normal (Só 3 colunas)
    elif len(textos_antes) == 3:
        tipo = textos_antes[0]
        perigo = textos_antes[1]
        risco = textos_antes[2]
    # Células mescladas
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
        "Medida_Controle_Proposta": medida_proposta, # Se existir, entra. Se não, some!
        "P": val_p,
        "F": val_f,
        "GPL": val_gpl,
        "NP": val_np,
        "Avaliacao_Valor": val_avaliacao,
        "Avaliacao_Status": status_av,
        "Medida_Controle_Existente": medida, # Renomeei para diferenciar da proposta
        "Foto": foto
    }
    
    # Limpeza condicional
    linha_json = {chave: valor for chave, valor in linha_bruta.items() if str(valor).strip() != ""}
    return linha_json, grupo_anterior


def extrair_somente_riscos_plano(caminho_pdf):
    print("🚀 Extraindo matriz de riscos final...")
    
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

    arquivo_saida = "extracao_finalizada2.json"
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(lista_plana_final, f, ensure_ascii=False, indent=4)
        
    print(f"\nFIM! {len(lista_plana_final)} riscos puros e dinâmicos extraídos e salvos em '{arquivo_saida}'.")

if __name__ == "__main__":
    extrair_somente_riscos_plano("teste2.pdf") 