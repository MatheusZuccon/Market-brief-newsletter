from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database.db"
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = Flask(__name__)


def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Creates the subscribers table when the application starts."""
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


init_db()


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
                "INSERT INTO subscribers (first_name, last_name, email) VALUES (?, ?, ?)",
                (first_name, last_name, email),
            )
    except sqlite3.IntegrityError:
        return jsonify(success=False, message="Este e-mail já está inscrito na newsletter."), 409

    return jsonify(
        success=True,
        message=f"Pronto, {first_name}! Sua inscrição foi confirmada.",
    ), 201


if __name__ == "__main__":
    app.run(debug=True)
