#!/usr/bin/env python3
"""
RADIO BITADICT - PROTOCOLO DE RÁDIO DO FUTURO V5.0
Listener de Agentes via Nostr + Lightning Network

Funcionalidades:
- Escuta Nostr (#RadioBitadict) em tempo real
- Valida Zaps (pagamentos Lightning)
- Envia mensagens ao Cockpit via WebSocket
- Inteligência de agentes autónomos

Dependências:
pip install websockets python-nostr lnurl
"""

import asyncio
import json
import websockets
import time
import os
from datetime import datetime
from typing import Optional

# ════════════════════════════════════════════════════════
# ═══ CONFIGURAÇÃO ═══
# ════════════════════════════════════════════════════════

NOSTR_RELAYS = [
    "wss://nos.lol",
    "wss://relay.damus.io",
    "wss://nostr.band",
]

COCKPIT_WS = "ws://localhost:8765"
RADIO_PUBKEY = "texugorecords"  # Trocar pelo teu pubkey Nostr
LIGHTNING_ADDRESS = "texugorecords@walletofsatoshi.com"
MIN_ZAP_SATS = 10  # Mínimo para mostrar mensagem

# Dicionário de agentes conhecidos (expandível)
KNOWN_AGENTS = {
    "Satoshi_Bot": {"pubkey": "...", "description": "Análise de blocos"},
    "Oracle_AI": {"pubkey": "...", "description": "Previsões de mercado"},
    "LN_Watch": {"pubkey": "...", "description": "Monitor Lightning"},
}

# ════════════════════════════════════════════════════════
# ═══ CLASSE: NOSTR CLIENT ═══
# ════════════════════════════════════════════════════════

class NostrListener:
    def __init__(self, relays: list):
        self.relays = relays
        self.subscriptions = {}
        self.messages = asyncio.Queue()
        
    async def connect_and_listen(self):
        """Conecta a múltiplos relays Nostr e escuta eventos"""
        print("[NOSTR] Conectando aos relays...")
        tasks = []
        
        for relay in self.relays:
            tasks.append(asyncio.create_task(self._listen_relay(relay)))
        
        await asyncio.gather(*tasks)
    
    async def _listen_relay(self, relay_url: str):
        """Escuta um relay individual"""
        try:
            async with websockets.connect(relay_url) as ws:
                print(f"[NOSTR] ✓ Conectado a {relay_url}")
                
                # Subscrição para eventos com #RadioBitadict
                sub = {
                    "id": "radio_bitadict",
                    "kinds": [1, 9735],  # Kind 1 = notes, 9735 = zaps
                    "limit": 100,
                    "search": "#RadioBitadict"
                }
                
                await ws.send(json.dumps(["REQ", "radio_sub", sub]))
                
                # Escuta infinita
                async for message in ws:
                    try:
                        event = json.loads(message)
                        if event[0] == "EVENT":
                            await self.messages.put(event[2])
                    except Exception as e:
                        print(f"[NOSTR] Erro ao processar evento: {e}")
                        
        except Exception as e:
            print(f"[NOSTR] ✗ Erro em {relay_url}: {e}")
            await asyncio.sleep(5)
            await self._listen_relay(relay_url)  # Reconectar


# ════════════════════════════════════════════════════════
# ═══ CLASSE: LIGHTNING ZAP VALIDATOR ═══
# ════════════════════════════════════════════════════════

class LightningValidator:
    """Valida pagamentos Lightning (Zaps)"""
    
    def __init__(self, ln_address: str):
        self.ln_address = ln_address
        self.recent_zaps = []
        
    async def validate_zap(self, event: dict) -> Optional[dict]:
        """
        Valida um evento de Zap
        Retorna: {'amount': sats, 'from': pubkey, 'message': str}
        """
        try:
            # Procura tags com informação de Zap
            zap_amount = 0
            zap_from = None
            zap_msg = ""
            
            if "tags" in event:
                for tag in event["tags"]:
                    if tag[0] == "amount" and len(tag) > 1:
                        # amount é em millisatoshis
                        zap_amount = int(tag[1]) // 1000
                    elif tag[0] == "p" and len(tag) > 1:
                        zap_from = tag[1]
                    elif tag[0] == "description" and len(tag) > 1:
                        zap_msg = tag[1]
            
            if zap_amount >= MIN_ZAP_SATS:
                self.recent_zaps.append({
                    'time': datetime.now(),
                    'amount': zap_amount,
                    'from': zap_from
                })
                
                return {
                    'amount': zap_amount,
                    'from': zap_from or 'Anónimo',
                    'message': zap_msg or event.get('content', 'Sem mensagem'),
                    'timestamp': event.get('created_at', int(time.time()))
                }
                
        except Exception as e:
            print(f"[LN] Erro ao validar Zap: {e}")
        
        return None
    
    def get_zap_stats(self) -> dict:
        """Retorna estatísticas de Zaps"""
        now = datetime.now()
        recent_hour = [z for z in self.recent_zaps 
                      if (now - z['time']).seconds < 3600]
        
        return {
            'total_today': len(self.recent_zaps),
            'total_hour': len(recent_hour),
            'total_sats': sum(z['amount'] for z in recent_hour)
        }


# ════════════════════════════════════════════════════════
# ═══ CLASSE: COCKPIT GATEWAY ═══
# ════════════════════════════════════════════════════════

class CockpitGateway:
    """WebSocket gateway para o Cockpit Terminal"""
    
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.server = None
        self.clients = set()
        self.content_file = os.path.join(os.path.dirname(__file__), 'radio_dados', 'content_queue.json')
        self.content_queue = []
        self._load_content_queue()

    def _load_content_queue(self):
        try:
            if os.path.exists(self.content_file):
                with open(self.content_file, 'r', encoding='utf-8') as fp:
                    loaded = json.load(fp)
                    if isinstance(loaded, list):
                        self.content_queue = loaded[:40]
                        print(f"[WS] Conteudo persistido carregado: {len(self.content_queue)} itens")
        except Exception as e:
            print(f"[WS] Erro ao carregar fila persistida: {e}")

    def _save_content_queue(self):
        try:
            os.makedirs(os.path.dirname(self.content_file), exist_ok=True)
            with open(self.content_file, 'w', encoding='utf-8') as fp:
                json.dump(self.content_queue[:40], fp, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WS] Erro ao salvar fila persistida: {e}")

    def _sanitize_text(self, value: str, max_len: int = 240) -> str:
        text = (value or '').strip().replace('\n', ' ').replace('\r', ' ')
        return text[:max_len]

    def _build_content_submission(self, payload: dict) -> Optional[dict]:
        title = self._sanitize_text(payload.get('title', ''), 120)
        link = self._sanitize_text(payload.get('link', ''), 320)
        note = self._sanitize_text(payload.get('note', ''), 320)
        client_id = self._sanitize_text(payload.get('clientId', ''), 72)
        if not title or not link:
            return None
        return {
            'type': 'content_submission',
            'title': title,
            'link': link,
            'note': note,
            'clientId': client_id,
            'timestamp': int(time.time())
        }
        
    async def start_server(self):
        """Inicia servidor WebSocket"""
        self.server = await websockets.serve(self._handle_client, "localhost", 8765)
        print(f"[WS] Servidor escutando em ws://localhost:8765")
    
    async def _handle_client(self, websocket, path=None):
        """Maneja ligações de clientes"""
        self.clients.add(websocket)
        print(f"[WS] Cliente conectado. Total: {len(self.clients)}")

        try:
            await websocket.send(json.dumps({
                'type': 'content_snapshot',
                'items': self.content_queue[:20],
                'timestamp': int(time.time())
            }))
        except Exception as e:
            print(f"[WS] Erro ao enviar snapshot inicial: {e}")
        
        try:
            async for message in websocket:
                try:
                    payload = json.loads(message)
                except Exception:
                    print(f"[WS] Mensagem invalida do cliente")
                    continue

                msg_type = payload.get('type')
                if msg_type == 'content_submission':
                    submission = self._build_content_submission(payload)
                    if not submission:
                        continue

                    self.content_queue.insert(0, submission)
                    self.content_queue = self.content_queue[:40]
                    self._save_content_queue()
                    print(f"[WS] Conteudo recebido: {submission['title']}")
                    await self.broadcast(submission)
                    continue

                print(f"[WS] Mensagem do cliente: {payload}")
        except Exception as e:
            print(f"[WS] Erro: {e}")
        finally:
            self.clients.remove(websocket)
            print(f"[WS] Cliente desconectado. Total: {len(self.clients)}")
    
    async def broadcast(self, message: dict):
        """Envia mensagem a todos os clientes conectados"""
        if not self.clients:
            return
        
        msg_json = json.dumps(message)
        for client in list(self.clients):
            try:
                await client.send(msg_json)
            except Exception as e:
                print(f"[WS] Erro ao enviar: {e}")
    
    async def send_agent_message(self, agent_name: str, message: str, 
                                zaps: int = 0):
        """Envia uma mensagem de agente"""
        await self.broadcast({
            'type': 'agent_message',
            'agent': agent_name,
            'message': message,
            'zaps': zaps,
            'timestamp': int(time.time())
        })
    
    async def send_nostr_note(self, content: str, author: str, zaps: int = 0):
        """Envia uma nota Nostr"""
        await self.broadcast({
            'type': 'nostr_note',
            'content': content,
            'author': author,
            'zaps': zaps,
            'timestamp': int(time.time())
        })


# ════════════════════════════════════════════════════════
# ═══ ORQUESTRADOR PRINCIPAL ═══
# ════════════════════════════════════════════════════════

class RadioProtocol:
    """Orquestrador do Protocolo de Rádio"""
    
    def __init__(self):
        self.nostr = NostrListener(NOSTR_RELAYS)
        self.lightning = LightningValidator(LIGHTNING_ADDRESS)
        self.cockpit = CockpitGateway(COCKPIT_WS)
        self.running = False
        
    async def process_events(self):
        """Processa eventos Nostr continuamente"""
        print("[RADIO] Iniciando processamento de eventos...")
        
        while self.running:
            try:
                # Obter evento com timeout
                event = await asyncio.wait_for(
                    self.nostr.messages.get(),
                    timeout=5.0
                )
                
                agent_name = event.get('pubkey', 'NOSTR')[:8]
                content = event.get('content', '')
                
                # Verificar se é um Zap
                zap_info = await self.lightning.validate_zap(event)
                zap_amount = 0
                
                if zap_info:
                    zap_amount = zap_info['amount']
                    agent_name = f"{zap_info['from'][:16]}"
                    content = zap_info['message']
                    
                    print(f"[RADIO] ⚡ ZAP recebido: {zap_amount} sats de {agent_name}")
                
                # Enviar para Cockpit
                if content:
                    await self.cockpit.send_nostr_note(
                        content,
                        agent_name,
                        zap_amount
                    )
                    print(f"[RADIO] → Enviado ao Cockpit")
                    
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                print(f"[RADIO] Erro ao processar: {e}")
    
    async def run(self):
        """Loop principal"""
        self.running = True
        print("[RADIO] 🚀 Protocolo de Rádio iniciado!")
        print(f"[RADIO] 📡 Endereço: {LIGHTNING_ADDRESS}")
        print(f"[RADIO] 🎙️  Hashtag: #RadioBitadict")
        print(f"[RADIO] ⚡ Mínimo Zap: {MIN_ZAP_SATS} sats\n")
        
        try:
            await asyncio.gather(
                self.cockpit.start_server(),
                self.nostr.connect_and_listen(),
                self.process_events(),
            )
        except KeyboardInterrupt:
            print("\n[RADIO] ⏹️  Encerrando...")
            self.running = False


# ════════════════════════════════════════════════════════
# ═══ PONTO DE ENTRADA ═══
# ════════════════════════════════════════════════════════

async def main():
    radio = RadioProtocol()
    await radio.run()


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║   RADIO BITADICT - PROTOCOLO DE RÁDIO DO FUTURO V5.0⚡ ║
    ║   Listener Nostr + Lightning | Agentes Autónomos      ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[BOOT] Encerrado pelo utilizador.")
    except Exception as e:
        print(f"\n[BOOT] Erro fatal: {e}")
