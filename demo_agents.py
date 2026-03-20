#!/usr/bin/env python3
"""
DEMO: Simulador de Agentes para RADIO BITADICT V5.0

Simula agentes enviando Zaps ao Cockpit sem precisar de Nostr real.
Útil para testes e demonstração.
"""

import asyncio
import websockets
import json
import time

DEMO_MESSAGES = [
    {
        "agent": "Satoshi_Bot",
        "message": "🔗 Escaneando transações... Detectada mineração em Marataízes!",
        "zaps": 50
    },
    {
        "agent": "Oracle_AI",
        "message": "📊 Análise tecnica: BTC quebrou resistência em $96.5K. Padrão de rompimento detectado.",
        "zaps": 100
    },
    {
        "agent": "LN_Watch",
        "message": "⚡ Monitoramento Lightning: +234.5 mBTC em pagamentos P2P detectados nos últimos 5 minutos.",
        "zaps": 25
    },
    {
        "agent": "Whale_Alert",
        "message": "🐋 GRANDE MOVIMENTO: Transferência de 50 BTC detectada. Origem: Exchange desconhecida.",
        "zaps": 250
    },
    {
        "agent": "BitFeed_News",
        "message": "📰 NOTÍCIA: Salvador anuncia nova iniciativa de mineração com energia renovável.",
        "zaps": 150
    },
]

async def send_demo_message(ws, agent_data):
    """Envia uma mensagem de agente via WebSocket"""
    msg = {
        "type": "agent_message",
        "agent": agent_data["agent"],
        "message": agent_data["message"],
        "zaps": agent_data["zaps"],
        "timestamp": int(time.time())
    }
    
    print(f"\n📡 Enviando: @{agent_data['agent']} | ⚡{agent_data['zaps']} sats")
    print(f"   Mensagem: {agent_data['message'][:60]}...")
    
    await ws.send(json.dumps(msg))
    await asyncio.sleep(1)


async def demo_client():
    """Cliente demo que envia mensagens ao servidor"""
    
    print("""
    ═══════════════════════════════════════════════════════════
    🎙️  RADIO BITADICT V5.0 - DEMO DE AGENTES
    ═══════════════════════════════════════════════════════════
    
    Este script simula 5 agentes enviando mensagens com Zaps.
    
    Requisitos:
    1. Abre index.html no navegador
    2. Executa 'python radio_nostr_agent.py' em outro terminal
    3. Descomenta 'initAgentListener()' no index.html (descomentar)
    4. Recarrega o navegador
    5. Executa ESTE script
    
    ═══════════════════════════════════════════════════════════
    """)
    
    input("Pressiona ENTER para iniciar a demo...")
    
    try:
        print("\n🔌 Conectando ao servidor local...")
        async with websockets.connect('ws://localhost:8765') as ws:
            print("✓ Conexão estabelecida!\n")
            
            for i, agent_data in enumerate(DEMO_MESSAGES, 1):
                print(f"\n[{i}/5]" + "─" * 50)
                await send_demo_message(ws, agent_data)
                
                if i < len(DEMO_MESSAGES):
                    print("⏳ Aguardando 3 segundos até próxima mensagem...")
                    await asyncio.sleep(3)
            
            print("\n" + "═" * 55)
            print("✓ DEMO CONCLUÍDA!")
            print("═" * 55)
            print("\nVerifica o Cockpit para ver todas as mensagens com efeitos Zap 🎆")
            
    except ConnectionRefusedError:
        print("\n❌ ERRO: Não consegui ligar-me ao servidor!")
        print("\nVerifica que:")
        print("  1. Executaste: python radio_nostr_agent.py")
        print("  2. index.html tem 'initAgentListener()' ativo")
        print("  3. A página está aberta no navegador")
    except Exception as e:
        print(f"\n❌ Erro: {e}")


# ══════════════════════════════════════════════════════════════
# OPÇÃO 2: Servidor Mock para Testar Localmente
# ══════════════════════════════════════════════════════════════

async def mock_server():
    """
    Servidor mock que simula o servidor real.
    Útil para testes quando não tens radio_nostr_agent.py em execução.
    """
    
    async def handle_client(websocket, path):
        print(f"[MOCK] Cliente conectado")
        try:
            async for message in websocket:
                print(f"[MOCK] Mensagem recebida: {message[:50]}...")
        except Exception as e:
            print(f"[MOCK] Erro: {e}")
    
    print("[MOCK] Iniciando servidor mock em ws://localhost:8765...")
    server = await websockets.serve(handle_client, "localhost", 8765)
    
    # Envia mensagens de demo periodicamente
    await asyncio.sleep(2)
    print("[MOCK] Enviando mensagens de demo...")
    
    await demo_client()


# ══════════════════════════════════════════════════════════════
# MENU PRINCIPAL
# ══════════════════════════════════════════════════════════════

async def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     SELECIONA MODE DE TESTE (DEMO)                        ║
    ╠═══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║  [1] Cliente Demo (envia para servidor real)             ║
    ║      → Precisa de: python radio_nostr_agent.py           ║
    ║                                                           ║
    ║  [2] Servidor Mock (incluso, servidor + demo)           ║
    ║      → Não precisa de nada más                           ║
    ║                                                           ║
    ║  [0] Sair                                                 ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    choice = input("Escolhe (0-2): ").strip()
    
    if choice == "1":
        await demo_client()
    elif choice == "2":
        await mock_server()
    else:
        print("Adeus!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrompida.")
    except Exception as e:
        print(f"Erro: {e}")
