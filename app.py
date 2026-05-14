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

@app.route("/limpar", methods=["GET"])
def limpar():
    init_db()
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM leituras")
    conn.commit()
    conn.close()
    return jsonify({"status": "banco limpo!"}), 200

@app.route("/", methods=["GET"])
def home():
    return """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Leituras IoT</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 32px; color: #222; }
    h1 { font-size: 20px; font-weight: normal; margin-bottom: 16px; }
    button { padding: 6px 14px; margin-right: 8px; cursor: pointer;
             border: 1px solid #999; background: #fff; border-radius: 4px; }
    button.red { border-color: #c00; color: #c00; }
    table { border-collapse: collapse; width: 100%; margin-top: 16px; font-size: 14px; }
    th { text-align: left; border-bottom: 2px solid #222; padding: 8px 12px; }
    td { padding: 8px 12px; border-bottom: 1px solid #ddd; }
    .status { font-size: 12px; color: #888; margin-top: 8px; }
  </style>
</head>
<body>
  <h1>Leituras IoT</h1>
  <button onclick="carregar()">Atualizar</button>
  <button class="red" onclick="limpar()">Limpar banco</button>
  <div class="status" id="status"></div>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Timestamp</th><th>Temp (C)</th>
        <th>Umidade (%)</th><th>Luminosidade</th>
        <th>Presenca</th><th>Prob. Vida (%)</th>
      </tr>
    </thead>
    <tbody id="tabela"></tbody>
  </table>
  <script>
    async function carregar() {
      const res = await fetch('/leituras');
      const dados = await res.json();
      const tbody = document.getElementById('tabela');
      if (dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="color:#888">Nenhuma leitura ainda.</td></tr>';
      } else {
        tbody.innerHTML = dados.map(d => `
          <tr>
            <td>${d.id}</td>
            <td>${d.timestamp}</td>
            <td>${d.temperatura_c ?? '-'}</td>
            <td>${d.umidade_pct ?? '-'}</td>
            <td>${d.luminosidade ?? '-'}</td>
            <td>${d.presenca == 1 ? 'Sim' : 'Nao'}</td>
            <td>${d.probabilidade_vida ?? '-'}</td>
          </tr>`).join('');
      }
      document.getElementById('status').textContent =
        'Atualizado em ' + new Date().toLocaleTimeString() + ' — ' + dados.length + ' registro(s)';
    }
    async function limpar() {
      if (!confirm('Limpar todos os dados?')) return;
      await fetch('/limpar');
      carregar();
    }
    carregar();
    setInterval(carregar, 3000);
  </script>
</body>
</html>""", 200

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
