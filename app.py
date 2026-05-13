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
  <title>Dashboard IoT</title>
  <style>
    body { font-family: monospace; background: #111; color: #0f0; padding: 20px; }
    h1 { color: #0f0; }
    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
    th { background: #0f0; color: #111; padding: 8px 12px; }
    td { padding: 8px 12px; border-bottom: 1px solid #333; }
    tr:hover { background: #1a1a1a; }
    .btn { background: #0f0; color: #111; border: none; padding: 8px 16px;
           cursor: pointer; font-family: monospace; font-size: 14px;
           margin-right: 8px; border-radius: 4px; }
    .btn.red { background: #f00; color: #fff; }
    .status { margin: 10px 0; color: #888; font-size: 13px; }
  </style>
</head>
<body>
  <h1>📡 Dashboard IoT — Leituras em tempo real</h1>
  <button class="btn" onclick="carregar()">🔄 Atualizar agora</button>
  <button class="btn red" onclick="limpar()">🗑️ Limpar banco</button>
  <div class="status" id="status">Aguardando...</div>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Timestamp</th><th>Temp (°C)</th>
        <th>Umidade (%)</th><th>Luminosidade</th>
        <th>Presença</th><th>Prob. Vida (%)</th>
      </tr>
    </thead>
    <tbody id="tabela"></tbody>
  </table>
  <script>
    async function carregar() {
      document.getElementById('status').textContent = 'Atualizando...';
      const res = await fetch('/leituras');
      const dados = await res.json();
      const tbody = document.getElementById('tabela');
      if (dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#888">Nenhuma leitura ainda</td></tr>';
      } else {
        tbody.innerHTML = dados.map(d => `
          <tr>
            <td>${d.id}</td>
            <td>${d.timestamp}</td>
            <td>${d.temperatura_c ?? '-'}</td>
            <td>${d.umidade_pct ?? '-'}</td>
            <td>${d.luminosidade ?? '-'}</td>
            <td>${d.presenca == 1 ? '✅ Sim' : '❌ Não'}</td>
            <td>${d.probabilidade_vida ?? '-'}</td>
          </tr>`).join('');
      }
      document.getElementById('status').textContent =
        `Última atualização: ${new Date().toLocaleTimeString()} — ${dados.length} registro(s)`;
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
