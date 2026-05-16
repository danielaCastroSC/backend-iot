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
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    body { font-family: Arial, sans-serif; padding: 32px; color: #222; background: #fff; }
    h1 { font-size: 20px; font-weight: normal; margin-bottom: 16px; }
    button { padding: 6px 14px; margin-right: 8px; cursor: pointer;
             border: 1px solid #999; background: #fff; border-radius: 4px; }
    button.red { border-color: #c00; color: #c00; }
    .status { font-size: 12px; color: #888; margin: 8px 0 24px; }
    .graficos { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px; }
    .grafico-box { border: 1px solid #ddd; border-radius: 8px; padding: 16px; }
    .grafico-box h2 { font-size: 14px; font-weight: normal; margin: 0 0 12px; color: #555; }
    table { border-collapse: collapse; width: 100%; font-size: 13px; }
    th { text-align: left; border-bottom: 2px solid #222; padding: 8px 12px; }
    td { padding: 8px 12px; border-bottom: 1px solid #ddd; }
    @media (max-width: 600px) { .graficos { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <h1>Leituras IoT</h1>
  <button onclick="carregar()">Atualizar</button>
  <button class="red" onclick="limpar()">Limpar banco</button>
  <div class="status" id="status"></div>

  <div class="graficos">
    <div class="grafico-box">
      <h2>Temperatura (°C)</h2>
      <canvas id="graficoTemp"></canvas>
    </div>
    <div class="grafico-box">
      <h2>Umidade (%)</h2>
      <canvas id="graficoUmid"></canvas>
    </div>
    <div class="grafico-box">
      <h2>Luminosidade</h2>
      <canvas id="graficoLumi"></canvas>
    </div>
    <div class="grafico-box">
      <h2>Probabilidade de Vida (%)</h2>
      <canvas id="graficoProb"></canvas>
    </div>
  </div>

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
    let charts = {};

    function criarGrafico(id, label, cor) {
      const ctx = document.getElementById(id).getContext('2d');
      return new Chart(ctx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: label,
            data: [],
            borderColor: cor,
            backgroundColor: cor + '22',
            borderWidth: 2,
            pointRadius: 3,
            tension: 0,
            fill: true
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { maxTicksLimit: 6, font: { size: 11 } } },
            y: { ticks: { font: { size: 11 } } }
          }
        }
      });
    }

    function atualizarGrafico(chart, labels, valores) {
      chart.data.labels = labels;
      chart.data.datasets[0].data = valores;
      chart.update();
    }

    window.onload = function() {
      charts.temp = criarGrafico('graficoTemp', 'Temperatura', '#e05c2a');
      charts.umid = criarGrafico('graficoUmid', 'Umidade', '#2a7ae0');
      charts.lumi = criarGrafico('graficoLumi', 'Luminosidade', '#e0b02a');
      charts.prob = criarGrafico('graficoProb', 'Prob. Vida', '#2ae07a');
      carregar();
    };

    async function carregar() {
      const res = await fetch('/leituras');
      const dados = await res.json();

      const invertidos = [...dados].reverse();
      const labels = invertidos.map((d, i) => '#' + d.id);

      atualizarGrafico(charts.temp, labels, invertidos.map(d => d.temperatura_c));
      atualizarGrafico(charts.umid, labels, invertidos.map(d => d.umidade_pct));
      atualizarGrafico(charts.lumi, labels, invertidos.map(d => d.luminosidade));
      atualizarGrafico(charts.prob, labels, invertidos.map(d => d.probabilidade_vida));

      const tbody = document.getElementById('tabela');
      if (dados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="color:#888">Nenhuma leitura ainda.</td></tr>';
      } else {
        tbody.innerHTML = dados.map(d => '<tr>' +
          '<td>' + d.id + '</td>' +
          '<td>' + d.timestamp + '</td>' +
          '<td>' + (d.temperatura_c ?? '-') + '</td>' +
          '<td>' + (d.umidade_pct ?? '-') + '</td>' +
          '<td>' + (d.luminosidade ?? '-') + '</td>' +
          '<td>' + (d.presenca == 1 ? 'Sim' : 'Nao') + '</td>' +
          '<td>' + (d.probabilidade_vida ?? '-') + '</td>' +
          '</tr>').join('');
      }

      document.getElementById('status').textContent =
        'Atualizado em ' + new Date().toLocaleTimeString() + ' — ' + dados.length + ' registro(s)';
    }

    async function limpar() {
      if (!confirm('Limpar todos os dados?')) return;
      await fetch('/limpar');
      carregar();
    }

    setInterval(carregar, 3000);
  </script>
</body>
</html>""", 200

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
