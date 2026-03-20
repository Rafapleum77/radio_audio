# 🚀 RADIO BITADICT V5.0 - PRE-LAUNCH CHECKLIST

---

## ✅ PRÉ-REQUISITOS

- [ ] **Python 3.8+** instalado
  ```powershell
  python --version  # Deve ser ≥ 3.8
  ```

- [ ] **Pasta correta**
  ```
  c:\Users\alegr\Downloads\radio_audio\
  ```

- [ ] **Ficheiros presentes:**
  - [ ] `index.html` (V5.0)
  - [ ] `radio_nostr_agent.py`
  - [ ] `demo_agents.py`
  - [ ] `requirements.txt`
  - [ ] `SETUP_V5.0.md`
  - [ ] `ARCHITECTURE_V5.0.md`
  - [ ] `CHECKLIST.md` (este)

---

## 🔧 INSTALAÇÃO

- [ ] **Instalar dependências Python**
  ```powershell
  pip install -r requirements.txt
  ```
  
  Esperado:
  ```
  Successfully installed websockets python-nostr lnurl aiohttp
  ```

- [ ] **Validar sintaxe Python**
  ```powershell
  python -m py_compile radio_nostr_agent.py
  python -m py_compile demo_agents.py
  ```
  
  Esperado:
  ```
  (sem output = sucesso)
  ```

---

## ⚙️ CONFIGURAÇÃO

- [ ] **Editar `radio_nostr_agent.py`**
  - [ ] Linha ~25: Muda `RADIO_PUBKEY` para o teu pubkey Nostr
  - [ ] Linha ~26: Muda `LIGHTNING_ADDRESS` para o teu (walletofsatoshi ou getalby)
  
  ```python
  RADIO_PUBKEY = "teu_pubkey_hexadecimal_aqui"
  LIGHTNING_ADDRESS = "seu_nome@walletofsatoshi.com"
  ```

- [ ] **Verificar credenciais**
  - [ ] `RADIO_PUBKEY`: Começa com letras/números? 64 caracteres?
  - [ ] `LIGHTNING_ADDRESS`: Contém '@'? Parece válido?

---

## 🌐 TESTES BÁSICOS

### Teste 1: Cliente Demo (Sem dependências Nostr)
```powershell
# Terminal 1
python demo_agents.py

# Escolhe opção [2]: "Servidor Mock"
# Esperado: 5 agentes à enviar mensagens
```

**Checklist:**
- [ ] Script inicia sem erros
- [ ] Menu aparece com opções
- [ ] Escolhe opção [2]
- [ ] Mensagens aparecem no console: "📡 Enviando: @..."
- [ ] Nenhum erro de WebSocket

---

### Teste 2: Servidor Real + Cliente
```powershell
# Terminal 1: Inicia servidor
python radio_nostr_agent.py

# Esperado output:
# [NOSTR] ✓ Conectado a wss://nos.lol
# [NOSTR] ✓ Conectado a wss://relay.damus.io
# [WS] Servidor escutando em ws://localhost:8765
# [RADIO] 🚀 Protocolo iniciado!
```

**Checklist:**
- [ ] Python inicia sem erros
- [ ] Conecta a ≥2 relays Nostr
- [ ] WebSocket server inicia
- [ ] Nenhum "Address already in use"

```powershell
# Terminal 2: Abre o Cockpit
start index.html

# No navegador (F12 console):
# ✓ Conexão com Protocolo de Agentes estabelecida
```

**Checklist:**
- [ ] index.html abre no navegador
- [ ] Console mostra mensagem de conexão ✓
- [ ] Nenhum erro em vermelho

```powershell
# Terminal 3: Cliente demo
python demo_agents.py

# Escolhe opção [1]: "Cliente Demo"
# Esperado: Envia 5 mensagens ao servidor
```

**Checklist:**
- [ ] Cliente conecta ao servidor
- [ ] 5 mensagens são enviadas
- [ ] No cockpit, vê [5] mensagens de agentes no chat
- [ ] Cada uma tem ⚡+valor de sats

---

## 👁️ VERIFICAÇÃO VISUAL (INDEX.HTML)

### Sessão 1: Layout
- [ ] Header diz "V5.0 // PROTOCOLO DE RÁDIO DO FUTURO"
- [ ] 3 colunas visíveis (esquerda, centro, direita)
- [ ] Fundo com stars (radial gradients)
- [ ] Earth gradient no fundo
- [ ] Grid 275px | 1fr | 275px

### Sessão 2: Chat
- [ ] "[ CHAT // IA BITADICT ]" visível na esquerda
- [ ] Caixa de input para mensagens
- [ ] Botão SEND
- [ ] Mensagem inicial: "Sistema online. Assistente Bitcoin ativo."

### Sessão 3: Agentes
- [ ] Após 8 segundos, aparece: "@Satoshi_Bot [⚡ 50 sat]"
- [ ] Mensagem aparece com cor verde
- [ ] Pode estar misturado com chat normal

### Sessão 4: Efeitos
- [ ] Quando agente com Zap entra, tela fica com brilho dourado (+/- 0.8s)
- [ ] Chat scroll automático para mensagens novas
- [ ] Sem erros no console (F12)

---

## 🔗 TESTE: CONEXÃO NOSTR REAL (Opcional)

Se queres testar com Nostr real:

1. [ ] Vai a https://nostr.band
2. [ ] Procura teu pubkey ou username
3. [ ] Copia o pubkey hexadecimal
4. [ ] Coloca em `RADIO_PUBKEY` no `radio_nostr_agent.py`
5. [ ] Publica uma nota com `#RadioBitadict` noutro cliente (Snort, Primal)
6. [ ] Aguarda 5-10 segundos
7. [ ] Deverá aparecer no Cockpit em tempo real

**Esperado:**
- [ ] Nota aparece no chat do Cockpit
- [ ] Sem delay > 10 segundos
- [ ] Mostra a mensagem completa

---

## ⚡ TESTE: ZAP REAL (Opcional)

Se tens Lightning Wallet (Alby, Stacker, etc.):

1. [ ] Abre Alby ou wallet compatível
2. [ ] Vai a cliente Nostr (Snort, Primal, etc.)
3. [ ] Publica nota: "Teste #RadioBitadict"
4. [ ] Clica botão "Zap"
5. [ ] Paga 50+ sats
6. [ ] Aguarda confirmação (5-15 segundos)
7. [ ] Verifica Cockpit

**Esperado:**
- [ ] Zap aparece no cockpit com ⚡ e valor
- [ ] Flash dourado em toda a tela
- [ ] Mensagem está clara e legível

---

## 🐛 TROUBLESHOOTING

### ❌ Python não inicia
```
Error: No module named 'websockets'
```
**Solução:**
```powershell
pip install websockets --upgrade
```

### ❌ WebSocket "Address already in use"
```
OSError: [Errno 10048] Only one usage of each socket address
```
**Solução:**
```powershell
# Mata processo anterior
taskkill /IM python.exe /F

# Aguarda 5 segundos
# Tenta de novo
python radio_nostr_agent.py
```

### ❌ Cockpit mostra "Protocolo de Agentes indisponível"
```
⚠ Protocolo de Agentes indisponível. Modo local.
```
**Solução:**
- [ ] Verifica se `python radio_nostr_agent.py` está a executar
- [ ] Verifica se WebSocket está em `localhost:8765`
- [ ] Console do navegador: Ctrl+Shift+K (ver erros)
- [ ] Recarrega página: Ctrl+Shift+R

### ❌ Nenhum agente aparece após 8 segundos
**Solução:**
- [ ] Verifica se JavaScript está ativo (F12 → Console)
- [ ] Procura por erros vermelhos
- [ ] Descomenta `initAgentListener()` no index.html
- [ ] Recarrega

### ❌ Relays Nostr não conectam
```
[NOSTR] ✗ Erro em wss://nos.lol: ...
```
**Solução:**
- [ ] Verifica internet (testa ping 8.8.8.8)
- [ ] Tenta trocar relays em `NOSTR_RELAYS`
- [ ] Aguarda 20-30 segundos (relays podem estar lentos)

---

## 📊 PERFORMANCE

### Esperado:
- Startup Python: < 5 segundos
- Conexão WebSocket: < 2 segundos
- Latência agentes: < 15 segundos (Nostr é eventual)
- Visualização: Instantânea (< 500ms)

### Como medir:
```javascript
// No console do navegador (F12)
console.time('conexão');
// espera...
console.timeEnd('conexão');
```

---

## 🎯 SUCESSO!

Quando vires isto, está tudo bem:

```
✅ index.html mostra V5.0
✅ Chat IA responde
✅ Ao menos 1 agente aparece (aos 8s)
✅ Flash dourado quando Zap
✅ python radio_nostr_agent.py sem erros
✅ Console diz "✓ Conexão com Protocolo estabelecida"
✅ Relays Nostr conectados (≥2)
✅ WebSocket escutando em 8765
```

---

## 🚀 PRÓXIMOS PASSOS

- [ ] **Deixar Python em background 24/7**
  ```powershell
  # Windows Task Scheduler ou
  nohup python radio_nostr_agent.py > radio.log 2>&1 &
  ```

- [ ] **Publicar primeira nota com #RadioBitadict**
  - Vai a Snort.social ou Primal.net
  - Publica mencionando @RadioBitadict
  - Envelope num Zap de 50-100 sats

- [ ] **Convidar primeiros agentes de teste**
  - Partilha Lightning Address
  - Explica o protocolo
  - Convida a publicarem com #RadioBitadict

- [ ] **Monitorar stats**
  ```python
  print(lightning.get_zap_stats())
  ```

---

## 📝 NOTAS DE TESTE

Espaço reservado para teus apontamentos:

```
Data de teste: _______________

Relays que conectaram: _________________________________

Pubkey Nostr usado: ____________________________________

Agentes testados: ______________________________________

Problemas encontrados: __________________________________

Observações: ___________________________________________
```

---

**Data de conclusão:** _______________  
**Testador:** _______________  
**Status:** 🟢 **PRONTO PARA PRODUÇÃO**  

---

*Documento criado para RADIO BITADICT V5.0*  
*Protocolo de Rádio do Futuro*  
*Março 2026*
