from flask import Flask, request, jsonify
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
DB = "/tmp/banco.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp         TEXT,
            temperatura_c     REAL,
            umidade_pct       REAL,
            luminosidade      INTEGER,
            presenca          INTEGER,
            probabilidade_vida REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/leituras", methods=["POST"])
def receber():
    dados = request.get_json(force=True)
    if not dados:
        return jsonify({"erro": "JSON inválido"}), 400
    ts = dados.get("timestamp", datetime.utcnow().isoformat() + "Z")
    conn = sqlite3.connect(DB)
    conn.execute("""
        INSERT INTO leituras
          (timestamp, temperatura_c, umidade_pct,
           luminosidade, presenca, probabilidade_vida)
        VALUES (?,?,?,?,?,?)
    """, (ts, dados.get("temperatura_c"), dados.get("umidade_pct"),
          dados.get("luminosidade"), dados.get("presenca"),
          dados.get("probabilidade_vida")))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201

@app.route("/leituras", methods=["GET"])
def listar():
    init_db()
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT * FROM leituras
        ORDER BY id DESC LIMIT 100
    """).fetchall()
    conn.close()
    cols = ["id","timestamp","temperatura_c","umidade_pct",
            "luminosidade","presenca","probabilidade_vida"]
    return jsonify([dict(zip(cols, r)) for r in rows]), 200

@app.route("/", methods=["GET"])
def home():
    return "API funcionando!", 200
