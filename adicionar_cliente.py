import asyncio
import sys

# CORREÇÃO CRÍTICA PARA O PYTHON 3.14 (TEM QUE FICAR ANTES DO PYROGRAM)
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client
import json
import os

ARQUIVO_DB = "clientes_config.json"

def ler_todos_clientes():
    if os.path.exists(ARQUIVO_DB):
        with open(ARQUIVO_DB, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def salvar_cliente_completo(nome_cliente, api_id, api_hash, id_grupo, horario_inicio, horario_fim, mensagem):
    dados = ler_todos_clientes()
    dados[nome_cliente] = {
        "api_id": int(api_id),
        "api_hash": api_hash,
        "id_grupo": int(id_grupo),
        "horario_inicio": horario_inicio,
        "horario_fim": horario_fim,
        "mensagem": mensagem
    }
    with open(ARQUIVO_DB, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    print(f"✅ Configurações de [{nome_cliente.upper()}] atualizadas com sucesso no JSON!")

async def buscar_e_escolher_grupo(app):
    print("\n🔍 Buscando os grupos da conta no Telegram...")
    print("="*60)
    print("📋 GRUPOS ENCONTRADOS NESTA CONTA:")
    print("="*60)
    
    lista_grupos = []
    contador = 1
    
    async for dialog in app.get_dialogs():
        chat = dialog.chat
        if chat.type.value in ["group", "supergroup"]:
            print(f"[{contador}] Nome: {chat.title}  (ID: {chat.id})")
            lista_grupos.append((chat.title, chat.id))
            contador += 1
            if contador > 30:
                break
                
    print("="*60)
    
    if not lista_grupos:
        print("❌ Nenhum grupo encontrado nesta conta.")
        return None

    try:
        opcao = int(input("\nDigite o NÚMERO do grupo escolhido para monitorar: "))
        return lista_grupos[opcao - 1]
    except Exception:
        print("❌ Opção inválida!")
        return None

async def iniciar_gerenciador():
    print("="*60)
    print("🚀 TURBOBOT - GERENCIADOR DE CLIENTES")
    print("="*60)
    print("[1] Cadastrar um NOVO cliente (Primeiro login)")
    print("[2] Editar um cliente JÁ CADASTRADO (Usa a API e Sessão existentes)")
    print("="*60)
    
    escolha = input("Escolha uma opção (1 ou 2): ").strip()
    clientes_salvos = ler_todos_clientes()
    
    if escolha == "1":
        # === FLUXO DE NOVO CADASTRO ===
        nome = input("\nNome do NOVO cliente (ex: maria, pedro): ").strip().lower()
        if nome in clientes_salvos:
            print(f"⚠️ O cliente [{nome}] já existe! Use a opção [2] para editá-lo.")
            return
            
        api_id = input("Digite o API_ID para este cliente: ").strip()
        api_hash = input("Digite o API_HASH para este cliente: ").strip()
        
    elif escolha == "2":
        # === FLUXO DE EDIÇÃO ===
        if not clientes_salvos:
            print("❌ Nenhum cliente cadastrado no banco ainda. Use a opção [1].")
            return
            
        print("\n📋 CLIENTES DISPONÍVEIS PARA EDIÇÃO:")
        for idx, c_nome in enumerate(clientes_salvos.keys(), 1):
            print(f"[{idx}] {c_nome.upper()}")
            
        try:
            op_cliente = int(input("\nDigite o número do cliente que deseja editar: "))
            nome = list(clientes_salvos.keys())[op_cliente - 1]
        except Exception:
            print("❌ Seleção inválida.")
            return
            
        # Puxa os dados antigos para não ter que digitar a API de novo
        api_id = clientes_salvos[nome]["api_id"]
        api_hash = clientes_salvos[nome]["api_hash"]
        print(f"\n🔄 Carregando credenciais salvas de [{nome.upper()}]...")
        
    else:
        print("❌ Opção inválida.")
        return

    # === INICIALIZAÇÃO DA SESSÃO DO TELEGRAM ===
    print(f"📲 Conectando à conta de [{nome.upper()}]...")
    try:
        app = Client(name=f"sessao_{nome}", api_id=int(api_id), api_hash=api_hash)
        await app.start()
        print(f"✅ Conta de [{nome.upper()}] conectada!")
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return

    # Busca os grupos usando a função reaproveitável
    grupo_selecionado = await buscar_e_escolher_grupo(app)
    if not grupo_selecionado:
        await app.stop()
        return
        
    nome_grupo, id_grupo = grupo_selecionado
    print(f"➔ Selecionado: {nome_grupo} ({id_grupo})")

    print("\n📝 CONFIGURAÇÃO DA JANELA DE TEMPO")
    horario_ini = input("Hora de INÍCIO (Ex: 14:00): ").strip()
    horario_fim = input("Hora de TÉRMINO (Ex: 14:15): ").strip()
    msg = input("Mensagem que este cliente vai enviar:\n> ")
    
    # Salva ou Sobrescreve no JSON
    salvar_cliente_completo(nome, api_id, api_hash, id_grupo, horario_ini, horario_fim, msg)
    
    await app.stop()
    print(f"\n🎉 Processo concluído para o cliente [{nome.upper()}]!")

if __name__ == "__main__":
    try:
        asyncio.run(iniciar_gerenciador())
    except (KeyboardInterrupt, SystemExit):
        print("\nOperação cancelada.")