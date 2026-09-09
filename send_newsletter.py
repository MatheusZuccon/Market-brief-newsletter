"""Send a newsletter to every subscriber saved in the local SQLite database.

By default the command only previews recipients. Add --send to actually deliver.
Credentials must be supplied through environment variables, never hard-coded.
"""

from __future__ import annotations

import argparse
import os
import smtplib
import sqlite3
import sys
import time
from email.message import EmailMessage
from pathlib import Path
from html import unescape
import re


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def get_subscribers() -> list[sqlite3.Row]:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            "O banco database.db não foi encontrado. Execute primeiro: python app.py"
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(
            "SELECT first_name, last_name, email FROM subscribers ORDER BY id"
        ).fetchall()
    finally:
        connection.close()


def html_to_text(html: str) -> str:
    """Creates a readable fallback for e-mail clients without HTML support."""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</p>|</h[1-6]>|</li>|</tr>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", unescape(text)).strip()


def build_message(
    sender: str, recipient: sqlite3.Row, subject: str, body: str, html: str | None
) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"Market Brief <{sender}>"
    message["To"] = recipient["email"]
    plain_content = f"Olá, {recipient['first_name']}!\n\n{body}\n\nAté a próxima,\nEquipe Market Brief"
    message.set_content(plain_content)
    if html:
        personalized_html = html.replace("{{first_name}}", recipient["first_name"])
        message.add_alternative(personalized_html, subtype="html")
    return message


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dispara uma newsletter via Gmail SMTP.")
    parser.add_argument("--subject", required=True, help="Assunto do e-mail.")
    parser.add_argument(
        "--body-file",
        type=Path,
        help="Arquivo .txt para o conteúdo alternativo em texto puro.",
    )
    parser.add_argument(
        "--html-file",
        type=Path,
        help="Arquivo .html da newsletter formatada.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Envia os e-mails. Sem esta opção, somente mostra uma prévia segura.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Pausa entre mensagens em segundos (padrão: 0.5).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.delay < 0:
        print("O valor de --delay não pode ser negativo.", file=sys.stderr)
        return 2
    if not args.body_file and not args.html_file:
        print("Informe --html-file ou --body-file.", file=sys.stderr)
        return 2
    if args.body_file and not args.body_file.is_file():
        print(f"Arquivo não encontrado: {args.body_file}", file=sys.stderr)
        return 2
    if args.html_file and not args.html_file.is_file():
        print(f"Arquivo não encontrado: {args.html_file}", file=sys.stderr)
        return 2

    subscribers = get_subscribers()
    html = args.html_file.read_text(encoding="utf-8").strip() if args.html_file else None
    body = args.body_file.read_text(encoding="utf-8").strip() if args.body_file else html_to_text(html)
    if not body:
        print("O arquivo da newsletter está vazio.", file=sys.stderr)
        return 2
    if not subscribers:
        print("Não há assinantes cadastrados para receber a newsletter.")
        return 0

    print(f"Assunto: {args.subject}")
    print(f"Assinantes encontrados: {len(subscribers)}")
    for subscriber in subscribers:
        print(f"  - {subscriber['first_name']} {subscriber['last_name']} <{subscriber['email']}>")

    if not args.send:
        print("\nModo de prévia: nenhum e-mail foi enviado. Use --send para confirmar o disparo.")
        return 0

    sender = os.environ.get("NEWSLETTER_SENDER_EMAIL")
    # Google displays app passwords in groups of four. Remove regular and
    # non-breaking formatting spaces that can be introduced while copying.
    app_password = "".join(os.environ.get("NEWSLETTER_GMAIL_APP_PASSWORD", "").split())
    if not sender or not app_password:
        print(
            "Defina NEWSLETTER_SENDER_EMAIL e NEWSLETTER_GMAIL_APP_PASSWORD antes de enviar.",
            file=sys.stderr,
        )
        return 2

    sent, failed = 0, []
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(sender, app_password)
        for subscriber in subscribers:
            try:
                server.send_message(build_message(sender, subscriber, args.subject, body, html))
                sent += 1
                print(f"Enviado: {subscriber['email']}")
            except smtplib.SMTPException as error:
                failed.append(subscriber["email"])
                print(f"Falhou: {subscriber['email']} ({error})", file=sys.stderr)
            time.sleep(args.delay)

    print(f"\nConcluído: {sent} enviado(s), {len(failed)} falha(s).")
    if failed:
        print("Falharam: " + ", ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, sqlite3.Error, OSError, smtplib.SMTPException) as error:
        print(f"Erro: {error}", file=sys.stderr)
        raise SystemExit(1)
