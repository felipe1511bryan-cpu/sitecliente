import json
import os

ARQUIVO_DB = "clientes_config.json"

def ler_clientes():
    """Lê todos os clientes cadastrados no arquivo JSON"""
    if not os.path.exists(ARQUIVO_DB):
        return {}
    try:
        with open(ARQUIVO_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def salvar_cliente(nome_cliente, id_grupo, horario_inicio, horario_fim, mensagem):
    """Salva ou atualiza a configuração de um cliente"""
    dados = ler_clientes()
    
    dados[nome_cliente] = {
        "id_grupo": int(id_grupo),
        "horario_inicio": horario_inicio,
        "horario_fim": horario_fim,
        "mensagem": mensagem
    }
    
    with open(ARQUIVO_DB, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    print(f"✅ Configurações de [{nome_cliente}] salvas com sucesso!")