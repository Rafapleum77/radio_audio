#!/usr/bin/env python3
"""
Bitadict Security Recovery Kit — utilitario offline pra recuperar acesso a wallets crypto.

MVP com 4 funcoes:
  1. Validar seed BIP39 + sugerir correcao de typo
  2. Reconstruir seed parcial (palavras faltantes via brute-force de checksum)
  3. Bruteforce senha de wallet Monero (.keys)
  4. Verificar saldo de address em multiplas chains

100% OFFLINE (excecao: aba 4, opcional, consulta blockchain publica).
Seeds/senhas que voce digita NUNCA saem da sua maquina.

Requer: bip-utils, requests (so pra aba 4). Tkinter ja vem com Python.
"""
import os, sys, json, threading, subprocess
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from pathlib import Path

# ============= AVISO DE SEGURANCA =============
AVISO = (
    "AVISO: BIT ADICT NUNCA pede sua seed phrase ou senha por mensagem, email, "
    "suporte, ligacao ou QUALQUER outro meio. Se alguem pedir, é GOLPE.\n"
    "Este utilitario roda 100% OFFLINE no seu PC. Os dados que voce digita aqui "
    "NUNCA saem da sua maquina."
)

# ============= BIP39 WORDLIST =============
def _load_wordlist():
    candidates = [
        Path(__file__).parent / "bip39_en.txt",
        Path.home() / ".seeds_finder" / "bip39_en.txt",
    ]
    for p in candidates:
        if p.exists():
            return [w.strip().lower() for w in p.read_text().splitlines() if w.strip()]
    # fallback embutido (placeholder — em produto final, embutir lista completa)
    raise FileNotFoundError("bip39_en.txt nao encontrado")

WORDS = _load_wordlist()
WORDS_SET = set(WORDS)

# ============= doacao (pos-sucesso) =============
def _load_doacao():
    p = Path(__file__).parent / "doacao.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
        if not d.get("habilitado", True):
            return None
        return d
    except Exception:
        return None

DOACAO = _load_doacao()

def show_doacao_popup(parent, contexto: str):
    """Popup pos-sucesso pedindo doacao opcional. So aparece se doacao.json existe e habilitado."""
    if not DOACAO:
        return
    win = tk.Toplevel(parent)
    win.title("Parabens — seu acesso foi recuperado")
    win.geometry("560x440")
    win.transient(parent)

    tk.Label(win, text="Acesso recuperado!", font=("Helvetica", 16, "bold"),
             fg="#1a7f37").pack(pady=(16, 4))
    tk.Label(win, text=contexto, font=("Helvetica", 10), fg="#555",
             wraplength=520).pack(pady=(0, 12))

    msg = (
        "Este kit e grátis, offline e open source.\n"
        "Se ele recuperou seu acesso, considere uma doacao — qualquer valor ajuda "
        "a manter o projeto independente e sem coleta de dados.\n\n"
        "Sugestao: 1% a 5% do valor recuperado."
    )
    tk.Label(win, text=msg, font=("Helvetica", 10), wraplength=520,
             justify="left").pack(padx=20, pady=(0, 12))

    def linha(label, endereco):
        f = tk.Frame(win); f.pack(fill="x", padx=20, pady=4)
        tk.Label(f, text=label, font=("Helvetica", 10, "bold"), width=14,
                 anchor="w").pack(side="left")
        ent = tk.Entry(f, font=("Menlo", 10))
        ent.insert(0, endereco); ent.config(state="readonly")
        ent.pack(side="left", fill="x", expand=True, padx=(0, 6))
        def copiar():
            win.clipboard_clear(); win.clipboard_append(endereco)
            btn.config(text="Copiado!")
            win.after(1500, lambda: btn.config(text="Copiar"))
        btn = ttk.Button(f, text="Copiar", command=copiar, width=10)
        btn.pack(side="left")

    if DOACAO.get("btc"):
        linha("BTC:", DOACAO["btc"])
    if DOACAO.get("usdc_polygon"):
        linha("USDC (Polygon):", DOACAO["usdc_polygon"])
    if DOACAO.get("eth"):
        linha("ETH:", DOACAO["eth"])
    if DOACAO.get("monero"):
        linha("XMR:", DOACAO["monero"])

    tk.Label(win, text="Sem cadastro, sem registro. Você decide.",
             font=("Helvetica", 9, "italic"), fg="#888").pack(pady=(14, 6))
    ttk.Button(win, text="Fechar", command=win.destroy).pack(pady=(0, 14))

def linha_doacao_inline() -> str:
    """Mensagem curta inline pra abas onde popup seria invasivo (ex: validar)."""
    if not DOACAO:
        return ""
    return ("\n\n— Esse kit e grátis e open source. Se ele te ajudou, "
            "considere uma doacao em radiobitcoin.org/doar —")

# ============= helpers =============
def levenshtein(a, b):
    if a == b: return 0
    if not a: return len(b)
    if not b: return len(a)
    prev = list(range(len(b)+1))
    for i, ca in enumerate(a):
        cur = [i+1] + [0]*len(b)
        for j, cb in enumerate(b):
            cur[j+1] = min(cur[j]+1, prev[j+1]+1, prev[j] + (ca != cb))
        prev = cur
    return prev[-1]

def suggest(word, top=3):
    if word in WORDS_SET: return [word]
    scored = sorted(((levenshtein(word, w), w) for w in WORDS), key=lambda x: x[0])
    return [w for _, w in scored[:top]]

def is_valid_bip39(mnemonic):
    try:
        from bip_utils import Bip39MnemonicValidator, Bip39Languages
        Bip39MnemonicValidator(Bip39Languages.ENGLISH).Validate(mnemonic)
        return True, None
    except ImportError:
        return None, "bip-utils nao instalado (pip install bip-utils)"
    except Exception as e:
        return False, str(e)

# ============= UI base =============
class BaseFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        # banner aviso
        banner = tk.Frame(self, bg="#fff3cd", padx=10, pady=8)
        banner.pack(fill="x", pady=(0, 12))
        tk.Label(banner, text=AVISO, bg="#fff3cd", fg="#856404",
                 wraplength=720, justify="left", font=("Helvetica", 10, "bold")).pack(anchor="w")

# ============= Aba 1: Validador =============
class TabValidar(BaseFrame):
    def __init__(self, master):
        super().__init__(master)
        ttk.Label(self, text="Cole sua seed phrase (12, 15, 18, 21 ou 24 palavras separadas por espaco):",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        self.txt = scrolledtext.ScrolledText(self, height=4, font=("Menlo", 12))
        self.txt.pack(fill="x", pady=8)
        ttk.Button(self, text="Validar", command=self.validar).pack(anchor="w")
        self.out = scrolledtext.ScrolledText(self, height=14, font=("Menlo", 11), state="disabled")
        self.out.pack(fill="both", expand=True, pady=8)

    def show(self, s):
        self.out.config(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("1.0", s)
        self.out.config(state="disabled")

    def validar(self):
        text = self.txt.get("1.0", "end").strip().lower()
        words = text.split()
        if not words:
            self.show("Cole a seed primeiro."); return
        if len(words) not in (12, 15, 18, 21, 24):
            self.show(f"Quantidade invalida: {len(words)} palavras. BIP39 usa 12, 15, 18, 21 ou 24.")
            return
        # verifica palavras
        unknown = []
        for i, w in enumerate(words, 1):
            if w not in WORDS_SET:
                sugs = suggest(w, 3)
                unknown.append(f"  Palavra {i} '{w}' NAO esta na lista BIP39. Sugestoes: {', '.join(sugs)}")
        out = []
        if unknown:
            out.append("PALAVRAS COM PROBLEMA:")
            out.extend(unknown)
            out.append("")
            out.append("Corrija e tente de novo.")
        else:
            valido, err = is_valid_bip39(" ".join(words))
            if valido:
                out.append(f"SEED VALIDA ({len(words)} palavras, checksum OK)")
                out.append("")
                out.append("Voce pode importar essa seed em qualquer carteira BIP39:")
                out.append("  - Phantom (Solana)")
                out.append("  - MetaMask (Ethereum/EVM)")
                out.append("  - Trust Wallet (multi-chain)")
                out.append("  - Electrum (Bitcoin)")
                out.append(linha_doacao_inline())
            else:
                out.append("Todas as palavras estao na lista, MAS o checksum nao bate.")
                out.append("Provavel: ordem trocada de alguma palavra ou typo nao detectado.")
                out.append("Use a aba 'Recovery parcial' pra tentar reconstruir.")
                out.append(f"")
                out.append(f"Detalhe tecnico: {err}")
        self.show("\n".join(out))

# ============= Aba 2: Recovery parcial =============
class TabRecuperar(BaseFrame):
    def __init__(self, master):
        super().__init__(master)
        ttk.Label(self, text="Cole sua seed colocando ? nas palavras faltantes (max 2 ?):",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        ttk.Label(self, text="Exemplo:  word1 word2 ? word4 ... word11 ?",
                  foreground="#666").pack(anchor="w")
        self.txt = scrolledtext.ScrolledText(self, height=4, font=("Menlo", 12))
        self.txt.pack(fill="x", pady=8)
        ttk.Button(self, text="Tentar reconstruir", command=self.recuperar).pack(anchor="w")
        self.out = scrolledtext.ScrolledText(self, height=14, font=("Menlo", 11), state="disabled")
        self.out.pack(fill="both", expand=True, pady=8)

    def show(self, s):
        self.out.config(state="normal"); self.out.delete("1.0", "end")
        self.out.insert("1.0", s); self.out.config(state="disabled")

    def recuperar(self):
        text = self.txt.get("1.0", "end").strip().lower()
        words = text.split()
        if not words:
            self.show("Cole a seed primeiro."); return
        if len(words) not in (12, 15, 18, 21, 24):
            self.show(f"Quantidade invalida: {len(words)}"); return
        missing_idx = [i for i, w in enumerate(words) if w == "?"]
        if not missing_idx:
            self.show("Nenhuma palavra faltante (?). Use a aba Validar."); return
        if len(missing_idx) > 2:
            self.show("Muitas palavras faltantes (max 2 ? suportadas — caso contrario sao bilhoes de combinacoes)"); return
        # palavras conhecidas precisam estar na wordlist
        for i, w in enumerate(words):
            if w != "?" and w not in WORDS_SET:
                self.show(f"Palavra {i+1} '{w}' nao esta na lista BIP39 — corrija primeiro na aba Validar.")
                return
        # bruteforce
        from bip_utils import Bip39MnemonicValidator, Bip39Languages
        validator = Bip39MnemonicValidator(Bip39Languages.ENGLISH)
        matches = []
        if len(missing_idx) == 1:
            i0 = missing_idx[0]
            for w in WORDS:
                test = list(words); test[i0] = w
                try:
                    validator.Validate(" ".join(test))
                    matches.append(" ".join(test))
                except Exception:
                    pass
        else:  # 2 missing — pode demorar (2048*2048 = 4M)
            self.show("Testando 4M combinacoes (pode demorar 1-2 min)..."); self.update()
            i0, i1 = missing_idx
            for w0 in WORDS:
                for w1 in WORDS:
                    test = list(words); test[i0] = w0; test[i1] = w1
                    try:
                        validator.Validate(" ".join(test))
                        matches.append(" ".join(test))
                    except Exception:
                        pass
        if not matches:
            self.show(f"Nenhuma combinacao valida encontrada. Talvez tenha mais erros alem das {len(missing_idx)} palavras marcadas.")
        else:
            out = [f"Encontrei {len(matches)} seed(s) com checksum valido:\n"]
            for m in matches[:20]:
                out.append(f"  {m}")
            if len(matches) > 20:
                out.append(f"\n  ... e mais {len(matches)-20}")
            out.append("\nValide cada uma importando numa carteira read-only pra ver qual recupera sua wallet.")
            self.show("\n".join(out))
            show_doacao_popup(self.winfo_toplevel(),
                              f"Reconstruimos {len(matches)} seed(s) candidata(s) com checksum válido.")

# ============= Aba 3: Bruteforce senha Monero =============
class TabBrute(BaseFrame):
    def __init__(self, master):
        super().__init__(master)
        ttk.Label(self, text="Bruteforce senha Monero (.keys)", font=("Helvetica", 11, "bold")).pack(anchor="w")
        f = ttk.Frame(self); f.pack(fill="x", pady=4)
        self.kv = tk.StringVar()
        ttk.Entry(f, textvariable=self.kv, width=60).pack(side="left", padx=(0, 4))
        ttk.Button(f, text="Selecionar arquivo .keys", command=self.pick_keys).pack(side="left")
        ttk.Label(self, text="Wordlist (1 senha por linha):").pack(anchor="w", pady=(8, 0))
        f2 = ttk.Frame(self); f2.pack(fill="x", pady=4)
        self.wv = tk.StringVar()
        ttk.Entry(f2, textvariable=self.wv, width=60).pack(side="left", padx=(0, 4))
        ttk.Button(f2, text="Selecionar wordlist .txt", command=self.pick_wl).pack(side="left")
        ttk.Button(self, text="Iniciar bruteforce", command=self.start_bf).pack(anchor="w", pady=8)
        self.out = scrolledtext.ScrolledText(self, height=14, font=("Menlo", 11), state="disabled")
        self.out.pack(fill="both", expand=True)

    def show(self, s, append=False):
        self.out.config(state="normal")
        if not append: self.out.delete("1.0", "end")
        self.out.insert("end", s + "\n"); self.out.see("end")
        self.out.config(state="disabled"); self.update()

    def pick_keys(self):
        p = filedialog.askopenfilename(title="Arquivo Monero .keys", filetypes=[("Monero keys", "*.keys"), ("Todos", "*")])
        if p: self.kv.set(p)

    def pick_wl(self):
        p = filedialog.askopenfilename(title="Wordlist", filetypes=[("Text", "*.txt"), ("Todos", "*")])
        if p: self.wv.set(p)

    def start_bf(self):
        keys = self.kv.get(); wl = self.wv.get()
        if not keys or not wl:
            self.show("Selecione o arquivo .keys e a wordlist."); return
        if not Path(keys).exists() or not Path(wl).exists():
            self.show("Arquivo nao encontrado."); return
        wallet_dir = str(Path(keys).parent)
        wallet_name = Path(keys).stem
        binary = "monero-wallet-cli"
        # verifica binario
        if subprocess.call(["which", binary], stdout=subprocess.DEVNULL) != 0:
            self.show(f"'{binary}' nao instalado. Mac: 'brew install monero'. Win/Linux: baixe getmonero.org.")
            return
        passwords = [l.strip() for l in Path(wl).read_text().splitlines() if l.strip()]
        self.show(f"Testando {len(passwords)} senhas em {wallet_name}...")
        threading.Thread(target=self._brute, args=(binary, wallet_dir, wallet_name, passwords), daemon=True).start()

    def _brute(self, binary, wd, wn, pws):
        wpath = str(Path(wd) / wn)
        for i, pw in enumerate(pws, 1):
            try:
                r = subprocess.run(
                    [binary, "--offline", "--wallet-file", wpath, "--password", pw, "--command", "address"],
                    capture_output=True, text=True, timeout=15,
                )
                ok = "Primary address" in r.stdout or "Address " in r.stdout
                if ok:
                    self.show(f"\n*** SENHA ENCONTRADA: {pw} ***\n", append=True)
                    self.after(0, lambda: show_doacao_popup(
                        self.winfo_toplevel(),
                        "Senha da sua wallet Monero foi descoberta. Acesso restaurado."))
                    return
            except Exception:
                pass
            if i % 10 == 0:
                self.show(f"  [{i}/{len(pws)}] testando...", append=True)
        self.show(f"\nFim. Nenhuma das {len(pws)} senhas funcionou.", append=True)

# ============= Aba 4: Saldo =============
class TabSaldo(BaseFrame):
    def __init__(self, master):
        super().__init__(master)
        ttk.Label(self, text="Verificar saldo de address (consulta blockchain publica):",
                  font=("Helvetica", 11, "bold")).pack(anchor="w")
        ttk.Label(self, text="Cole um address Bitcoin, Ethereum/EVM ou Solana:", foreground="#666").pack(anchor="w")
        self.txt = ttk.Entry(self, font=("Menlo", 12))
        self.txt.pack(fill="x", pady=4)
        ttk.Button(self, text="Consultar", command=self.consultar).pack(anchor="w", pady=4)
        self.out = scrolledtext.ScrolledText(self, height=18, font=("Menlo", 11), state="disabled")
        self.out.pack(fill="both", expand=True, pady=4)

    def show(self, s, append=False):
        self.out.config(state="normal")
        if not append: self.out.delete("1.0", "end")
        self.out.insert("end", s + "\n"); self.out.see("end")
        self.out.config(state="disabled"); self.update()

    def consultar(self):
        addr = self.txt.get().strip()
        if not addr: self.show("Cole um address."); return
        threading.Thread(target=self._check, args=(addr,), daemon=True).start()

    def _check(self, addr):
        import urllib.request
        self.show(f"Consultando saldo de {addr}...")
        def http_get(u):
            try:
                with urllib.request.urlopen(u, timeout=8) as r: return json.loads(r.read())
            except: return None
        def http_post(u, p):
            try:
                req = urllib.request.Request(u, data=json.dumps(p).encode(), headers={"Content-Type":"application/json"})
                with urllib.request.urlopen(req, timeout=8) as r: return json.loads(r.read())
            except: return None

        # detecta tipo
        if addr.startswith(("bc1", "1", "3")):
            r = http_get(f"https://blockstream.info/api/address/{addr}")
            if r:
                f = r.get("chain_stats",{}).get("funded_txo_sum",0)
                s = r.get("chain_stats",{}).get("spent_txo_sum",0)
                self.show(f"BTC saldo: {(f-s)/1e8:.8f} BTC", append=True)
            else:
                self.show("BTC: erro consulta", append=True)
        elif addr.startswith("0x") and len(addr) == 42:
            for chain, rpc in [("Ethereum","https://eth.public-rpc.com"),("BSC","https://bsc-dataseed.binance.org"),
                                ("Polygon","https://polygon-rpc.com"),("Base","https://mainnet.base.org"),
                                ("Arbitrum","https://arb1.arbitrum.io/rpc"),("Avalanche","https://api.avax.network/ext/bc/C/rpc"),
                                ("Optimism","https://mainnet.optimism.io")]:
                r = http_post(rpc, {"jsonrpc":"2.0","method":"eth_getBalance","params":[addr,"latest"],"id":1})
                if r and "result" in r:
                    bal = int(r["result"], 16) / 1e18
                    self.show(f"{chain:11} {bal:.6f}", append=True)
                else:
                    self.show(f"{chain:11} erro", append=True)
        else:
            r = http_post("https://api.mainnet-beta.solana.com",
                          {"jsonrpc":"2.0","id":1,"method":"getBalance","params":[addr]})
            if r and "result" in r:
                bal = r["result"]["value"] / 1e9
                self.show(f"SOL saldo: {bal:.6f} SOL", append=True)
            else:
                self.show("Solana: formato nao reconhecido ou erro consulta", append=True)

# ============= main =============
def main():
    root = tk.Tk()
    root.title("Bitadict Security Recovery Kit — utilitario offline de recuperacao")
    root.geometry("820x620")
    # tema
    try:
        style = ttk.Style(); style.theme_use("aqua" if sys.platform == "darwin" else "clam")
    except: pass

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=10, pady=10)
    nb.add(TabValidar(nb),   text="1. Validar seed")
    nb.add(TabRecuperar(nb), text="2. Recovery parcial")
    nb.add(TabBrute(nb),     text="3. Bruteforce senha")
    nb.add(TabSaldo(nb),     text="4. Verificar saldo")

    # rodape com aviso
    rod = tk.Label(root, text="100% offline | open source | radiobitcoin.org",
                   fg="#666", font=("Helvetica", 9))
    rod.pack(pady=(0, 6))

    root.mainloop()

if __name__ == "__main__":
    main()
