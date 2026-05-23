#!/usr/bin/env python3
"""
Sincroniza leads capturados (Gmail / localStorage / WhatsApp) com Buttondown.

PRE-REQUISITO: criar conta em https://buttondown.email e gerar API key em
https://buttondown.email/settings/programming → exportar BUTTONDOWN_TOKEN

Uso:
  # importar 1 lead pontual
  python3 buttondown_sync.py add email@dominio.com [--tag origem]

  # listar subscribers atuais
  python3 buttondown_sync.py list

  # importar lote (arquivo txt com 1 email por linha)
  python3 buttondown_sync.py import leads.txt

  # criar/atualizar campanha de welcome (envia automaticamente pra novos subs)
  python3 buttondown_sync.py welcome
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.request, urllib.error
from pathlib import Path

API = "https://api.buttondown.email/v1"
TOKEN = os.environ.get("BUTTONDOWN_TOKEN", "")

if not TOKEN:
    print("ERRO: exporta BUTTONDOWN_TOKEN antes de usar (settings → programming).", file=sys.stderr)
    print("       echo 'export BUTTONDOWN_TOKEN=xxx' >> ~/.zshrc && source ~/.zshrc")
    sys.exit(2)

HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json",
}


def req(method: str, path: str, payload: dict | None = None):
    url = f"{API}{path}"
    data = json.dumps(payload).encode() if payload else None
    r = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        print(f"HTTP {e.code}: {body[:200]}", file=sys.stderr)
        return None


def add_sub(email: str, tag: str = "ebook"):
    payload = {"email_address": email, "tags": [tag], "type": "regular"}
    res = req("POST", "/subscribers", payload)
    if res:
        print(f"✓ {email} adicionado (tag={tag})")
    return res


def list_subs(limit: int = 50):
    res = req("GET", f"/subscribers?type=regular&page_size={limit}")
    if not res:
        return
    print(f"Total: {res.get('count', 0)}")
    for s in res.get("results", []):
        tags = ",".join(s.get("tags", []))
        print(f"  {s.get('email_address'):40} tags=[{tags}]  criado={s.get('creation_date','')[:10]}")


def import_lote(path: str):
    p = Path(path)
    if not p.exists():
        print(f"arquivo {path} nao existe", file=sys.stderr)
        return
    emails = [l.strip() for l in p.read_text().splitlines() if l.strip() and "@" in l]
    print(f"Importando {len(emails)} emails...")
    for e in emails:
        add_sub(e, "import-lote")


WELCOME_SUBJECT = "Bem-vindo ao BIT ADICT · próximo passo"
WELCOME_BODY = """Salve!

Você acaba de baixar o eBook **10 erros que fazem você perder acesso ao seu Bitcoin**.

Algumas coisas que você pode esperar daqui pra frente:

**Toda quarta** — 3 linhas sobre o que rolou na minha frota de bots BIT ADICT (PnL real, win rate, sem print editado).

**Eventualmente** — algum produto novo que eu mesmo uso. Nunca shitcoin, nunca "compre minha mentoria de 50% ao mês".

Se você quiser ir mais a fundo agora:

→ [Recovery Kit Digital €20](https://radiobitcoin.org/recovery.html) — ferramenta offline pra validar seed, recuperar acesso, multi-chain. O mesmo que eu uso.

→ [Pacote Completo €200](https://radiobitcoin.org/recovery.html) — código completo dos 4 bots que rodam na minha frota + Recovery Kit + brindes físicos.

→ [VIP €20/mês](https://radiobitcoin.org/vip.html) — sinais em tempo real dos 3 bots + comunidade WhatsApp.

Sem chamada de venda. Sem call. Sem agenda. Tudo automatizado.

Bom estudo,
Rafael · BIT ADICT
radiobitcoin.org

---

Se não quer mais receber, é só responder este email com "sair" (eu mesmo removo).
"""


def setup_welcome():
    """Cria/atualiza o welcome email automatico."""
    # Buttondown chama isso de "automation" — pra ja deixar pronto sem dashboard, criar uma "email"
    # do tipo "scheduled_or_draft" que vira welcome via configuracao manual depois.
    payload = {
        "subject": WELCOME_SUBJECT,
        "body": WELCOME_BODY,
        "email_type": "public",
        "status": "draft",
    }
    res = req("POST", "/emails", payload)
    if res:
        print(f"✓ welcome email criado (draft) id={res.get('id')}")
        print("  Vai em buttondown.email/emails pra revisar e ativar como welcome automation.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("add"); a.add_argument("email"); a.add_argument("--tag", default="ebook")
    sub.add_parser("list")
    i = sub.add_parser("import"); i.add_argument("file")
    sub.add_parser("welcome")
    args = ap.parse_args()

    if args.cmd == "add":     add_sub(args.email, args.tag)
    elif args.cmd == "list":  list_subs()
    elif args.cmd == "import":import_lote(args.file)
    elif args.cmd == "welcome": setup_welcome()
    else: ap.print_help()


if __name__ == "__main__":
    main()
