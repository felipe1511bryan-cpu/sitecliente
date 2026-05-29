import asyncio
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os

# ==============================================================================
# 🔥 CORREÇÃO CRÍTICA PARA O PYTHON 3.14 (OBRIGATÓRIO ANTES DO PYROGRAM)
# ==============================================================================
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# ==============================================================================

from pyrogram import Client, handlers
from pyrogram.types import ChatMemberUpdated

ARQUIVO_DB = "clientes_config.json"
STATUS_ENVIO = {}
FUSO = ZoneInfo("America/Sao_Paulo")

def ler_clientes():
    if os.path.exists(ARQUIVO_DB):
        with open(ARQUIVO_DB, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def salvar_cliente(nome, api_id, api_hash, id_grupo, horario_inicio, horario_fim, mensagem):
    dados = ler_clientes()
    dados[nome] = {
        "api_id": int(api_id),
        "api_hash": api_hash,
        "id_grupo": int(id_grupo),
        "horario_inicio": horario_inicio,
        "horario_fim": horario_fim,
        "mensagem": mensagem
    }
    with open(ARQUIVO_DB, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ==============================================================================
# 🏎️ GATILHO ULTRA-RÁPIDO: INTERCEPTAÇÃO DE EVENTOS NATIVOS
# ==============================================================================
async def interceptar_abertura(client, chat_member_updated: ChatMemberUpdated, nome_cliente, id_grupo, mensagem, horario_fim):
    global STATUS_ENVIO
    
    if STATUS_ENVIO.get(nome_cliente, False) or chat_member_updated.chat.id != id_grupo:
        return

    # Garante que não vai disparar fora do horário limite
    if datetime.now(FUSO).strftime("%H:%M") > horario_fim:
        return

    velhas = chat_member_updated.old_chat_member.permissions
    novas = chat_member_updated.new_chat_member.permissions

    # Se liberou o envio de mensagens, chuta pro gol
    if (not velhas or not velhas.can_send_messages) and (novas and novas.can_send_messages):
        STATUS_ENVIO[nome_cliente] = True
        try:
            await client.send_message(id_grupo, mensagem)
            print(f"\n⚡⚡ [BOOM! EVENTO] {nome_cliente.upper()} INJETADO POR MUDANÇA DE PERMISSÃO EM MILISSEGUNDOS! ⚡⚡")
        except Exception as e:
            print(f"❌ Falha no disparo por evento: {e}")

async def gerenciar_rotina_cliente(nome_cliente, config):
    global STATUS_ENVIO
    STATUS_ENVIO[nome_cliente] = False
    
    id_grupo = config["id_grupo"]
    horario_inicio = config["horario_inicio"]
    horario_fim = config["horario_fim"]
    mensagem = config["mensagem"]
    
    print(f"⏳ [{nome_cliente.upper()}] Monitor aguardando janela: {horario_inicio} até {horario_fim}.")
    
    # Loop de espera inteligente
    while True:
        agora = datetime.now(FUSO).strftime("%H:%M")
        # Se já chegou o horário de início e ainda não passou do horário de fim
        if agora >= horario_inicio and agora <= horario_fim:
            break
        await asyncio.sleep(0.5)
        
    print(f"🚀 [{nome_cliente.upper()}] Janela Ativa! Conectando conta ao servidor do Telegram...")
    
    app = Client(name=f"sessao_{nome_cliente}", api_id=config["api_id"], api_hash=config["api_hash"])
    
    # Configura o sensor de milissegundos para escutar alterações
    sensor = handlers.ChatMemberUpdatedHandler(
        lambda client, cmu: interceptar_abertura(client, cmu, nome_cliente, id_grupo, message=mensagem, horario_fim=horario_fim)
    )
    app.add_handler(sensor)
    
    await app.start()
    
    # --- CHECAGEM INSTANTÂNEA DE ENTRADA ---
    # Se o grupo já estiver aberto no momento exato do login, envia na hora!
    try:
        chat = await app.get_chat(id_grupo)
        if chat.permissions and chat.permissions.can_send_messages and not STATUS_ENVIO[nome_cliente]:
            STATUS_ENVIO[nome_cliente] = True
            await app.send_message(id_grupo, mensagem)
            print(f"\n⚡⚡ [BOOM! PRIMEIRA CHECAGEM] {nome_cliente.upper()} ENVIADO IMEDIATAMENTE (GRUPO JÁ ESTAVA ABERTO)! ⚡⚡")
    except Exception:
        pass
    # ----------------------------------------
    
    # Mantém o script vivo escutando os eventos até que a mensagem seja enviada ou o tempo acabe
    while datetime.now(FUSO).strftime("%H:%M") <= horario_fim and not STATUS_ENVIO[nome_cliente]:
        await asyncio.sleep(0.2)
        
    await app.stop()
    print(f"💤 [{nome_cliente.upper()}] Monitoramento finalizado. Conta em repouso.")

# ==============================================================================
# 🎛️ PAINEL CENTRAL DE COMANDO INTERNO
# ==============================================================================
async def menu_configurar():
    clientes_salvos = ler_clientes()
    print("\n" + "="*40)
    print("⚙️ MÓDULO DE CONFIGURAÇÃO DE CLIENTES")
    print("="*40)
    print("[1] Novo Cadastro (Primeiro Login)")
    print("[2] Editar Cliente Existente")
    op = input("Escolha: ").strip()
    
    if op == "1":
        nome = input("Nome do cliente: ").strip().lower()
        api_id = input("API_ID: ").strip()
        api_hash = input("API_HASH: ").strip()
    elif op == "2" and clientes_salvos:
        for idx, c in enumerate(clientes_salvos.keys(), 1):
            print(f"[{idx}] {c.upper()}")
        idx_escolha = int(input("Número do cliente: ")) - 1
        nome = list(clientes_salvos.keys())[idx_escolha]
        api_id = clientes_salvos[nome]["api_id"]
        api_hash = clientes_salvos[nome]["api_hash"]
    else:
        print("Opção inválida ou banco vazio.")
        return

    print("📲 Conectando para ler os grupos...")
    app = Client(name=f"sessao_{nome}", api_id=int(api_id), api_hash=api_hash)
    await app.start()
    
    lista_grupos = []
    print("\n📋 SELECIONE O GRUPO:")
    contador = 1
    async for dialog in app.get_dialogs():
        if dialog.chat.type.value in ["group", "supergroup"]:
            print(f"[{contador}] {dialog.chat.title}")
            lista_grupos.append(dialog.chat.id)
            contador += 1
            if contador > 20: break
            
    id_grupo = lista_grupos[int(input("Número do Grupo: ")) - 1]
    horario_ini = input("Hora de INÍCIO (Ex: 20:00): ").strip()
    horario_fim = input("Hora de TÉRMINO (Ex: 20:15): ").strip()
    msg = input("Mensagem de envio:\n> ")
    
    salvar_cliente(nome, api_id, api_hash, id_grupo, horario_ini, horario_fim, msg)
    await app.stop()
    print("🎉 Salvo com sucesso!")

async def main():
    print("="*60)
    print("🚀 TURBOBOT PLATINUM - CENTRAL DE ALTA PERFORMANCE")
    print("="*60)
    print("[1] 🏁 LIGAR O MOTOR (Monitorar Todos os Clientes Ativos)")
    print("[2] 📝 CONFIGURAR CLIENTES (Cadastrar / Editar Horários)")
    print("="*60)
    
    opcao_inicial = input("Selecione a ação (1 ou 2): ").strip()
    
    if opcao_inicial == "2":
        await menu_configurar()
    elif opcao_inicial == "1":
        clientes = ler_clientes()
        if not clientes:
            print("❌ Nenhum cliente configurado. Vá na opção [2] primeiro.")
            return
        print(f"\n⚡ Ligando os sensores em paralelo para {len(clientes)} cliente(s)...")
        await asyncio.gather(*[gerenciar_rotina_cliente(nome, dados) for nome, dados in clientes.items()])

if __name__ == "__main__":
    try: asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): print("\nSistema desligado.")