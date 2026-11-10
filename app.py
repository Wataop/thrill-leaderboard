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
    <title>Kxrvinho Thrill Referral Leaderboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #1B1D29;
            --secondary: #5CFFC1;
            --accent: #FFFFFF;
            --card: #232533;
            --card-hover: #2a2d3e;
            --border: #2f3347;
            --muted: #9ca3af;
            --gold: #FFD700;
            --silver: #C0C0C0;
            --bronze: #CD7F32;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', system-ui, sans-serif;
            background: var(--primary);
            color: var(--accent);
            min-height: 100vh;
            padding: 40px 20px 80px;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
        }

        header {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 18px;
            margin-bottom: 50px;
            flex-wrap: wrap;
        }

        .avatar {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid var(--secondary);
            box-shadow: 0 0 20px rgba(92, 255, 193, 0.25);
        }

        .header-text {
            text-align: left;
        }

        header h1 {
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.8px;
            margin-bottom: 6px;
            color: var(--accent);
            line-height: 1.2;
        }

        header h1 a {
            text-decoration: none;
            transition: 0.2s;
        }

        header h1 a.kxrvinho {
            color: var(--accent);
        }

        header h1 a.kxrvinho:hover {
            color: var(--secondary);
        }

        header h1 a.thrill {
            color: var(--secondary);
        }

        header h1 a.thrill:hover {
            color: #8bffe0;
            text-shadow: 0 0 12px rgba(92, 255, 193, 0.4);
        }

        .subtitle {
            color: var(--muted);
            font-size: 15px;
            font-weight: 500;
        }

        /* Top 3 */
        .top3 {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 45px;
        }

        .top-card {
            background: var(--card);
            border: 2px solid var(--border);
            border-radius: 18px;
            padding: 28px 20px;
            text-align: center;
            transition: all 0.25s ease;
            position: relative;
        }

        .top-card:hover {
            transform: translateY(-6px);
        }

        .top-card.first {
            border-color: var(--gold);
            box-shadow: 0 0 25px rgba(255, 215, 0, 0.15);
        }

        .top-card.second {
            border-color: var(--silver);
            box-shadow: 0 0 20px rgba(192, 192, 192, 0.12);
        }

        .top-card.third {
            border-color: var(--bronze);
            box-shadow: 0 0 20px rgba(205, 127, 50, 0.12);
        }

        .place {
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 14px;
        }

        .top-card.first .place { color: var(--gold); }
        .top-card.second .place { color: var(--silver); }
        .top-card.third .place { color: var(--bronze); }

        .username {
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 18px;
            word-break: break-all;
        }

        .stat {
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 6px;
        }

        .stat strong {
            display: block;
            color: var(--accent);
            font-size: 18px;
            font-weight: 700;
            margin-top: 2px;
        }

        /* Table */
        .table-wrapper {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 18px;
            overflow: hidden;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            padding: 18px 22px;
            font-size: 13px;
            font-weight: 600;
            color: var(--muted);
            background: #1e2030;
            border-bottom: 1px solid var(--border);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        td {
            padding: 16px 22px;
            border-bottom: 1px solid var(--border);
            font-size: 15px;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr:hover td {
            background: var(--card-hover);
        }

        .rank {
            width: 70px;
            font-weight: 700;
            color: var(--muted);
        }

        .rank.gold { color: var(--gold); }
        .rank.silver { color: var(--silver); }
        .rank.bronze { color: var(--bronze); }

        .number {
            font-variant-numeric: tabular-nums;
            font-weight: 600;
        }

        .loading, .error {
            text-align: center;
            padding: 60px 20px;
            color: var(--muted);
        }

        @media (max-width: 800px) {
            header {
                flex-direction: column;
                text-align: center;
            }
            .header-text {
                text-align: center;
            }
            .top3 {
                grid-template-columns: 1fr;
            }
            header h1 {
                font-size: 26px;
            }
            th, td {
                padding: 13px 14px;
                font-size: 13px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <img src="https://static-cdn.jtvnw.net/jtv_user_pictures/d0d7bc81-f630-4503-9f50-a50ed431a044-profile_image-300x300.png" 
                 alt="Kxrvinho" 
                 class="avatar">
            <div class="header-text">
                <h1>
                    <a href="https://www.twitch.tv/kxrvinho" target="_blank" class="kxrvinho">Kxrvinho</a> 
                    <a href="https://thrill.com/?r=GG33" target="_blank" class="thrill">Thrill</a> 
                    Referral Leaderboard
                </h1>
                <div class="subtitle" id="info">Загрузка данных...</div>
            </div>
        </header>

        <div class="top3" id="top3" style="display: none;"></div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th class="rank">#</th>
                        <th>Игрок</th>
                        <th>Оборот ($)</th>
                        <th>XP</th>
                        <th>Дата</th>
                    </tr>
                </thead>
                <tbody id="tbody">
                    <tr>
                        <td colspan="5" class="loading">Загрузка...</td>
                    </tr>
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
                    const labels = ['1 место', '2 место', '3 место'];
                    const classes = ['first', 'second', 'third'];

                    top3.innerHTML = json.items.slice(0, 3).map((item, i) => `
                        <div class="top-card ${classes[i]}">
                            <div class="place">${labels[i]}</div>
                            <div class="username">${item.username}</div>
                            <div class="stat">Оборот<strong>${item.wager.toLocaleString('ru-RU', {maximumFractionDigits: 0})} $</strong></div>
                            <div class="stat" style="margin-top:12px">XP<strong>${Math.round(item.xp).toLocaleString('ru-RU')}</strong></div>
                        </div>
                    `).join('');
                }

                // Table
                const tbody = document.getElementById('tbody');
                tbody.innerHTML = json.items.map((item, i) => {
                    let rankClass = '';
                    if (i === 0) rankClass = 'gold';
                    else if (i === 1) rankClass = 'silver';
                    else if (i === 2) rankClass = 'bronze';

                    return `
                        <tr>
                            <td class="rank ${rankClass}">${i + 1}</td>
                            <td><strong>${item.username}</strong></td>
                            <td class="number">${item.wager.toLocaleString('ru-RU', {maximumFractionDigits: 2})}</td>
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
            xp = float(item["xp"]["value"]) / (10 ** item["xp"].get("decimals", 0))

            items.append({
                "username": item["username"],
                "wager": wager,
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
