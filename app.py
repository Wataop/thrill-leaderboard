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
    <title>Thrill Leaderboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #0f0f13;
            color: #eee;
            padding: 20px;
            min-height: 100vh;
        }
        .container { max-width: 1100px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 8px; font-size: 28px; }
        .info { text-align: center; color: #888; margin-bottom: 25px; font-size: 14px; }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #1a1a21;
            border-radius: 12px;
            overflow: hidden;
            font-size: 15px;
        }
        th, td { padding: 13px 16px; text-align: left; }
        th { background: #252530; font-weight: 600; }
        tr:nth-child(even) { background: #1f1f27; }
        .rank { width: 55px; text-align: center; font-weight: 700; }
        .gold { color: #ffd700; }
        .silver { color: #c0c0c0; }
        .bronze { color: #cd7f32; }
        .number { font-variant-numeric: tabular-nums; }
        @media (max-width: 700px) {
            table { font-size: 13px; }
            th, td { padding: 10px 8px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Thrill Referral Leaderboard</h1>
        <div class="info" id="info">Загрузка...</div>
        <table>
            <thead>
                <tr>
                    <th class="rank">#</th>
                    <th>Username</th>
                    <th>Wager ($)</th>
                    <th>Earnings ($)</th>
                    <th>XP</th>
                    <th>Дата</th>
                </tr>
            </thead>
            <tbody id="tbody"></tbody>
        </table>
    </div>

    <script>
        async function loadData() {
            try {
                const res = await fetch('/api/data');
                const json = await res.json();
                if (json.error) {
                    document.getElementById('info').innerText = 'Ошибка: ' + json.error;
                    return;
                }
                document.getElementById('info').innerText = 
                    `Обновлено: ${new Date(json.updated).toLocaleString('ru-RU')} • Игроков: ${json.total}`;

                let html = '';
                json.items.forEach((item, i) => {
                    const cls = i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';
                    html += `
                        <tr>
                            <td class="rank ${cls}">${i+1}</td>
                            <td>${item.username}</td>
                            <td class="number">${item.wager.toLocaleString('ru-RU', {maximumFractionDigits: 2})}</td>
                            <td class="number">${item.earning.toLocaleString('ru-RU', {maximumFractionDigits: 2})}</td>
                            <td class="number">${Math.round(item.xp).toLocaleString('ru-RU')}</td>
                            <td>${new Date(item.createdAt).toLocaleDateString('ru-RU')}</td>
                        </tr>`;
                });
                document.getElementById('tbody').innerHTML = html;
            } catch (e) {
                document.getElementById('info').innerText = 'Ошибка загрузки';
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
    
    # Кэш на 2 минуты
    if cache["data"] and cache["last_update"] and (now - cache["last_update"]).total_seconds() < 120:
        return cache["data"]

    token = os.getenv("THRILL_TOKEN")
    if not token:
        return {"error": "Токен не найден в файле .env"}

    from_date = "2025-09-01"
    to_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://api.thrill.com/referral/v1/referral-links/streamers?fromDate={from_date}&toDate={to_date}"

    headers = {
        "Cookie": f"token={token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
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

        # Сортировка по обороту
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