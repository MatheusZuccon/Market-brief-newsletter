from __future__ import annotations

import os
import re

from flask import Flask, jsonify, render_template, request
import psycopg
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = Flask(__name__)
db_initialized = False


def get_db_connection() -> psycopg.Connection:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("A variável de ambiente DATABASE_URL não foi configurada.")
    return psycopg.connect(database_url, row_factory=dict_row)


def init_db() -> None:
    """Creates the subscribers table when the application starts."""
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscribers (
                id BIGSERIAL PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@app.before_request
def ensure_db_initialized() -> None:
    global db_initialized
    if not db_initialized:
        init_db()
        db_initialized = True


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/subscribe")
def subscribe():
    data = request.get_json(silent=True) or request.form
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    email = data.get("email", "").strip().lower()

    if not all((first_name, last_name, email)):
        return jsonify(success=False, message="Preencha todos os campos para continuar."), 400

    if not EMAIL_PATTERN.fullmatch(email):
        return jsonify(success=False, message="Informe um e-mail válido."), 400

    try:
        with get_db_connection() as connection:
            connection.execute(
                "INSERT INTO subscribers (first_name, last_name, email) VALUES (%s, %s, %s)",
                (first_name, last_name, email),
            )
    except UniqueViolation:
        return jsonify(success=False, message="Este e-mail já está inscrito na newsletter."), 409

    return jsonify(
        success=True,
        message=f"Pronto, {first_name}! Sua inscrição foi confirmada.",
    ), 201


if __name__ == "__main__":
    app.run(debug=True)
