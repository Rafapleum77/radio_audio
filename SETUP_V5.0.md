# RADIO BITADICT V5.0 - PROTOCOLO DE RÁDIO DO FUTURO
## Guia de Setup: Nostr + Lightning + Agentes

---

## 📋 VISÃO GERAL DO SISTEMA

```
┌─────────────────────────────────────────────────────────────┐
│                  Protocolos Nostr Públicos                  │
│         (Escuta: #RadioBitadict, Zaps em Lightning)         │
└────────────────────────┬────────────────────────────────────┘
                         │ Relays: nos.lol, damus.io, nostr.band
                         ↓
        ┌────────────────────────────────┐
        │  radio_nostr_agent.py          │
        │  ✓ Listener Nostr              │
        │  ✓ Validador de Zaps           │
        │  ✓ WebSocket Server            │
        └────────┬───────────────────────┘
                 │ (ws://localhost:8765)
                 ↓
    ┌──────────────────────────────────┐
    │   COCKPIT TERMINAL (V5.0)        │
    │   index.html                     │
    │   ✓ Módulo de Agentes            │
    │   ✓ Visual Effects (Zaps)        │
    │   ✓ Chat em Tempo Real           │
    └──────────────────────────────────┘
```

---

## 🔧 INSTALAÇÃO

### 1. **Python 3.8+**
Verifica se tens Python instalado:
```powershell
python --version
```

### 2. **Instalar Dependências**
```powershell
cd c:\Users\alegr\Downloads\radio_audio

pip install websockets
pip install python-nostr
pip install lnurl
pip install aiohttp
```

### 3. **Configurar credenciais**

Edita `radio_nostr_agent.py` e substitui:

```python
RADIO_PUBKEY = "seu_pubkey_nostr_aqui"          # ex: hexadecimal de 64 caracteres
LIGHTNING_ADDRESS = "seu_endereco@walletofsatoshi.com"  # ou getalby.com
```

**Como obter teu pubkey Nostr:**
1. Vai a https://nostr.band (ou outro cliente)
2. Procura o teu nome de utilizador
3. Vê o "Public Key" (começará com npub1... ou será hex)
4. Copia o formato hexadecimal (64 caracteres)

---

## 🚀 EXECUÇÃO

### **Passo 1: Abre o Cockpit**
```powershell
# Abre a janela do navegador
start index.html
```

### **Passo 2: Inicia o Listener de Agentes**
```powershell
# Numa nova aba do terminal PowerShell
python radio_nostr_agent.py
```

Output esperado:
```
╔════════════════════════════════════════════════════════╗
║   RADIO BITADICT - PROTOCOLO V5.0⚡                    ║
║   Listener Nostr + Lightning | Agentes Autónomos      ║
╚════════════════════════════════════════════════════════╝

[BOOT] Conectando aos relays Nostr...
[NOSTR] ✓ Conectado a wss://nos.lol
[NOSTR] ✓ Conectado a wss://relay.damus.io
[WS] Servidor escutando em ws://localhost:8765
[RADIO] 🚀 Protocolo iniciado!
```

### **Passo 3: Descomenta o inicializador no index.html**
Edita `index.html` e procura:
```javascript
// IniciarListener (desativado até Python estar pronto - descomentar quando necessário)
// initAgentListener();
```

Muda para:
```javascript
// InicialListener (desativado até Python estar pronto - descomentar quando necessário)
initAgentListener();
```

**Recarrega o navegador (Ctrl+Shift+R)**

---

## 🧪 TESTES

### **Teste 1: Simulação Local (Sem Nostr)**
O script já tem uma simulação que entra passados 8 segundos:
- Verás: `@Satoshi_Bot` com ⚡50 sats
- Deve funcionar sem estar ligado ao receptor Python

### **Teste 2: Com Python em Execução**
Se Python está ligado:
1. Abre https://nostr.band
2. Procura `#RadioBitadict` (com menciona do teu pubkey)
3. Envia um Zap de 50+ sats com uma mensagem
4. Vê aparecer no Cockpit em tempo real

### **Teste 3: Verificar WebSocket**
No navegador, abre a consola (F12) e vê:
```
✓ Conexão com Protocolo de Agentes estabelecida
```

Se vires `⚠ Protocolo de Agentes indisponível`, é porque Python não está executando em background.

---

## 💡 COMANDOS ÚTEIS

### **Reiniciar tudo:**
```powershell
# Mata o Python
taskkill /IM python.exe

# Recarrega o HTML no navegador
Ctrl+Shift+R
```

### **Ver logs em tempo real:**
```powershell
# Executa com output verboso
python radio_nostr_agent.py -v
```

---

## ⚡ COMO ENVIAR ZAPS PARA A RÁDIO

### **Via Alby Wallet:**
1. Instala extensão: https://getalby.com
2. Vai a qualquer cliente Nostr (Snort, Primal, etc.)
3. Escreve uma nota com `#RadioBitadict`
4. Clica "Zap" e envia 100+ sats
5. Inclui mensagem tipo: "Minas de Bitcoin em Marataízes!"
6. Vê aparecer no Cockpit automaticamente

### **Via Lightning Address diretamente:**
Qualquer carteira Lightning pode enviar para: `texugorecords@walletofsatoshi.com`

---

## 🤖 ESTRUTURA DE AGENTES

Agentes podem interagir assim:

```javascript
{
  "type": "agent_message",
  "agent": "@Satoshi_Bot",
  "message": "Mensagem que vai aparecer no cockpit",
  "zaps": 100,  // Satoshis pagos
  "timestamp": 1708295847
}
```

Exemplo de automatização (um agente externo):

```python
# pseudo-código
for block in blockchain.new_blocks():
    if "bitcoin" in block.tx_data:
        send_zap(
            amount=50,
            message=f"🔗 Bloco {block.height} minerado!",
            hashtag="#RadioBitadict"
        )
```

---

## 🔒 SEGURANÇA

⚠️ **Importante:**
- WebSocket está em `localhost:8765` (seguro localmente)
- Para usar remotamente, precisa SSL/TLS
- Nunca abra a porta 8765 para a internet sem autenticação
- Lightning Addresses são públicas (normal)
- Pubkeys Nostr são públicas (normal)

---

## 🐛 TROUBLESHOOTING

| Problema | Solução |
|----------|---------|
| WebSocket conexão recusada | Verifica se Python está executando |
| Não vê agentes no Cockpit | Descomenta `initAgentListener()` |
| Python não inicia | `pip install -r requirements.txt` (ver abaixo) |
| Zaps não aparecem | Mínimo é 10 sats (MIN_ZAP_SATS) |
| Relay Nostr timeout | Tenta trocar relay em NOSTR_RELAYS |

---

## 📦 REQUIREMENTS.TXT

Criar arquivo `requirements.txt`:
```
websockets>=10.0
python-nostr>=0.0.2
lnurl>=0.3.6
aiohttp>=3.8.0
```

Depois instalar com:
```powershell
pip install -r requirements.txt
```

---

## 🎯 PRÓXIMOS PASSOS

1. **Adicionar persistência de histórico:**
   - Guardar mensagens em SQLite
   - Mostrar feed histórico no startup

2. **Integrar com Lightning Node Local (LND):**
   - Receber Zaps diretamente em teu nó
   - Validação automática

3. **Dashboard de Agentes:**
   - Mostrar agentes top pelo total enviado
   - Ranking em tempo real

4. **Comandos interativos:**
   - `/about` - Info sobre agente
   - `/list` - Listar agentes online
   - `/stats` - Estatísticas

---

## 📡 SUPORTE

Se precisar de ajuda:
- Documentação Nostr: https://nostr.how
- Lightning Network: https://lnurl.fyi
- WebSockets Python: https://websockets.readthedocs.io

---

**Versão:** 5.0 | **Data:** Março 2026 | **Protocolo:** Radio Bitadict | **Status:** 🟢 ATIVO
