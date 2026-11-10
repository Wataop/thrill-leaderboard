from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv
import requests
import os
from datetime import datetime, timedelta
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

cache = {"data": None, "last_update": None}

HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thrill Referral Leaderboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0b0f;
            --card: #15151c;
            --card-hover: #1c1c26;
            --border: #2a2a35;
            --text: #f0f0f5;
            --muted: #8b8b9b;
            --accent: #8b5cf6;
            --gold: #fbbf24;
            --silver: #94a3b8;
            --bronze: #d97706;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 30px 20px 60px;
            line-height: 1.5;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
        }

        header h1 {
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #fff, #c4b5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            color: var(--muted);
            font-size: 15px;
        }

        /* Top 3 */
        .top3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }

        .top-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px 20px;
            text-align: center;
            position: relative;
            transition: 0.2s;
        }

        .top-card:hover {
            transform: translateY(-4px);
            border-color: #3f3f4a;
        }

        .top-card.first {
            border-color: var(--gold);
            background: linear-gradient(145deg, #1a1608, #15151c);
        }

        .place {
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }

        .place.gold { color: var(--gold); }
        .place.silver { color: var(--silver); }
        .place.bronze { color: var(--bronze); }

        .username {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
            word-break: break-all;
        }

        .stat {
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 4px;
        }

        .stat strong {
            color: var(--text);
            font-size: 16px;
            font-weight: 600;
        }

        /* Table */
        .table-wrapper {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            padding: 16px 20px;
            font-size: 13px;
            font-weight: 500;
            color: var(--muted);
            background: #121218;
            border-bottom: 1px solid var(--border);
        }

        td {
            padding: 14px 20px;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background: var(--card-hover);
        }

        .rank {
            width: 60px;
            font-weight: 600;
            color: var(--muted);
        }

        .rank.gold { color: var(--gold); }
        .rank.silver { color: var(--silver); }
        .rank.bronze { color: var(--bronze); }

        .number {
            font-variant-numeric: tabular-nums;
            font-weight: 500;
        }

        .loading {
            text-align: center;
            padding: 60px 20px;
            color: var(--muted);
        }

        .error {
            text-align: center;
            padding: 40px;
            color: #f87171;
        }

        @media (max-width: 768px) {
            .top3 {
                grid-template-columns: 1fr;
            }
            header h1 { font-size: 26px; }
            th, td { padding: 12px 14px; font-size: 13px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Thrill Referral Leaderboard</h1>
            <div class="subtitle" id="info">Загрузка данных...</div>
        </header>

        <div class="top3" id="top3" style="display: none;"></div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th class="rank">#</th>
                        <th>Игрок</th>
                        <th>Оборот ($)</th>
                        <th>Заработок ($)</th>
                        <th>XP</th>
                        <th>Дата</th>
                    </tr>
                </thead>
                <tbody id="tbody">
                    <tr><td colspan="6" class="loading">Загрузка...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        async function loadData() {
            try {
                const res = await fetch('/api/data');
                const json = await res.json();

                if (json.error) {
                    document.getElementById('info').innerHTML = '<span style="color:#f87171">Ошибка: ' + json.error + '</span>';
                    return;
                }

                document.getElementById('info').textContent = 
                    `Обновлено: ${new Date(json.updated).toLocaleString('ru-RU')}  •  Всего игроков: ${json.total}`;

                // Top 3
                const top3 = document.getElementById('top3');
                if (json.items.length >= 3) {
                    top3.style.display = 'grid';
                    const places = ['gold', 'silver', 'bronze'];
                    const labels = ['1 место', '2 место', '3 место'];

                    top3.innerHTML = json.items.slice(0, 3).map((item, i) => `
                        <div class="top-card ${i === 0 ? 'first' : ''}">
                            <div class="place ${places[i]}">${labels[i]}</div>
                            <div class="username">${item.username}</div>
                            <div class="stat">Оборот<br><strong>${item.wager.toLocaleString('ru-RU', {maximumFractionDigits: 0})} $</strong></div>
                            <div class="stat" style="margin-top:10px">Заработок<br><strong>${item.earning.toLocaleString('ru-RU', {maximumFractionDigits: 2})} $</strong></div>
                        </div>
                    `).join('');
                }

                // Table
                const tbody = document.getElementById('tbody');
                tbody.innerHTML = json.items.map((item, i) => {
                    const rankClass = i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';
                    return `
                        <tr>
                            <td class="rank ${rankClass}">${i + 1}</td>
                            <td><strong>${item.username}</strong></td>
                            <td class="number">${item.wager.toLocaleString('ru-RU', {maximumFractionDigits: 2})}</td>
                            <td class="number">${item.earning.toLocaleString('ru-RU', {maximumFractionDigits: 2})}</td>
                            <td class="number">${Math.round(item.xp).toLocaleString('ru-RU')}</td>
                            <td>${new Date(item.createdAt).toLocaleDateString('ru-RU')}</td>
                        </tr>
                    `;
                }).join('');

            } catch (e) {
                document.getElementById('info').innerHTML = '<span style="color:#f87171">Ошибка загрузки</span>';
            }
        }

        loadData();
        setInterval(loadData, 180000);
    </script>
</body>
</html>
"""

def get_leaderboard():
    now = datetime.now()
    
    if cache["data"] and cache["last_update"] and (now - cache["last_update"]).total_seconds() < 120:
        return cache["data"]

    token = os.getenv("THRILL_TOKEN")
    if not token:
        return {"error": "Токен не найден"}

    from_date = "2025-09-01"
    to_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://api.thrill.com/referral/v1/referral-links/streamers?fromDate={from_date}&toDate={to_date}"

    headers = {
        "Cookie": f"token={token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://thrill.com/",
        "Origin": "https://thrill.com"
    }

    try:
        r = requests.get(url, headers=headers, timeout=25)
        r.raise_for_status()
        data = r.json()

        items = []
        for item in data.get("items", []):
            wager = float(item["wager"]["value"]) / (10 ** item["wager"]["decimals"])
            earning = float(item["earning"]["value"]) / (10 ** item["earning"]["decimals"])
            xp = float(item["xp"]["value"]) / (10 ** item["xp"].get("decimals", 0))

            items.append({
                "username": item["username"],
                "wager": wager,
                "earning": earning,
                "xp": xp,
                "createdAt": item["createdAt"]
            })

        items.sort(key=lambda x: x["wager"], reverse=True)

        result = {
            "items": items,
            "total": data.get("totalCount", len(items)),
            "updated": now.isoformat()
        }

        cache["data"] = result
        cache["last_update"] = now
        return result

    except Exception as e:
        return {"error": str(e)}

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/data")
def api_data():
    return jsonify(get_leaderboard())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
