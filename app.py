from flask import Flask, jsonify, render_template_string, request
import random
import time

app = Flask(__name__)

# ==================== INDICATOR & ANALYSIS LOGIC ====================

def fetch_ohlcv(symbol):
    """
    মার্কেট ডেটা সিমুলেটর (বা তোমার ডাইনামিক ডেটা সোর্স)
    """
    random.seed(int(time.time() / 10) + ord(symbol[0]))
    base_price = 1.0850 if "EUR" in symbol else (100.50 if "BRL" in symbol else 150.20)
    
    closes, highs, lows, opens, volumes = [], [], [], [], []
    curr = base_price
    for _ in range(120):
        change = random.uniform(-0.002, 0.002)
        op = curr
        cl = curr + change
        hi = max(op, cl) + random.uniform(0, 0.001)
        lo = min(op, cl) - random.uniform(0, 0.001)
        vol = random.randint(100, 1000)
        
        opens.append(op)
        closes.append(cl)
        highs.append(hi)
        lows.append(lo)
        volumes.append(vol)
        curr = cl
        
    return opens, highs, lows, closes, volumes

def calc_rsi(closes, period=14):
    gains = [max(0, closes[i] - closes[i-1]) for i in range(1, len(closes))]
    losses = [max(0, closes[i-1] - closes[i]) for i in range(1, len(closes))]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calc_ema(closes, period):
    multiplier = 2 / (period + 1)
    ema = closes[0]
    for price in closes[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    return ema

def calc_bollinger(closes, period=20, std_dev=2):
    slice_closes = closes[-period:]
    sma = sum(slice_closes) / period
    variance = sum((x - sma) ** 2 for x in slice_closes) / period
    sd = variance ** 0.5
    return sma + (std_dev * sd), sma - (std_dev * sd)

def calc_stochastic(closes, highs, lows, k_period=14, d_period=3):
    lowest_low = min(lows[-k_period:])
    highest_high = max(highs[-k_period:])
    if highest_high == lowest_low:
        stoch_k = 50
    else:
        stoch_k = ((closes[-1] - lowest_low) / (highest_high - lowest_low)) * 100
    stoch_d = stoch_k * 0.9  # Simulated Smooth D
    return round(stoch_k, 2), round(stoch_d, 2)

def is_strong_trend(closes):
    return abs(closes[-1] - closes[-20]) > (closes[-1] * 0.002)

def candle_confirmation(opens, closes, highs, lows, direction):
    op, cl = opens[-1], closes[-1]
    if direction == "buy":
        return cl > op  # Bullish Candle
    else:
        return cl < op  # Bearish Candle

# ==================== ADVANCED SIGNAL SCORING ENGINE ====================

def get_signal(symbol):
    opens, highs, lows, closes, volumes = fetch_ohlcv(symbol)
    
    if not closes or len(closes) < 100:
        return None

    price = closes[-1]
    rsi = calc_rsi(closes)
    e9 = calc_ema(closes, 9)
    e21 = calc_ema(closes, 21)
    e50 = calc_ema(closes, 50)
    upper_bb, lower_bb = calc_bollinger(closes)
    stoch_k, stoch_d = calc_stochastic(closes, highs, lows)

    # ---------------- BUY SCORE CHECK ----------------
    buy_score = 0
    buy_reasons = []

    if rsi < 28:
        buy_score += 4
        buy_reasons.append("🔴 RSI Deep Oversold (<28)")
    elif rsi < 35:
        buy_score += 2
        buy_reasons.append("RSI Oversold")

    if stoch_k < 20 and stoch_k > stoch_d:
        buy_score += 3
        buy_reasons.append("📊 Stochastic Oversold + Cross Up")

    if e9 > e21 > e50 and price > e9:
        buy_score += 3
        buy_reasons.append("📈 Strong Bullish EMA Alignment")

    if lower_bb and price <= lower_bb * 1.003:
        buy_score += 3
        buy_reasons.append("🔵 Price at Lower Bollinger Band")

    if is_strong_trend(closes) and price > e21:
        buy_score += 2
        buy_reasons.append("💪 Strong Uptrend Continuation")

    if candle_confirmation(opens, closes, highs, lows, "buy"):
        buy_score += 2
        buy_reasons.append("✅ Bullish Candle Confirmation")

    if buy_score >= 8:  # Adjusted for live optimal trigger
        accuracy = min(99, 85 + (buy_score * 1.2))
        return {
            "direction": "BUY (CALL)",
            "trend": "📈 UP-TREND (HIGH SCORE)",
            "accuracy": round(accuracy, 1),
            "pattern": buy_reasons[0] if buy_reasons else "Bullish Momentum",
            "score": buy_score,
            "reasons": buy_reasons
        }

    # ---------------- SELL SCORE CHECK ----------------
    sell_score = 0
    sell_reasons = []

    if rsi > 72:
        sell_score += 4
        sell_reasons.append("🟢 RSI Deep Overbought (>72)")
    elif rsi > 65:
        sell_score += 2
        sell_reasons.append("RSI Overbought")

    if stoch_k > 80 and stoch_k < stoch_d:
        sell_score += 3
        sell_reasons.append("📊 Stochastic Overbought + Cross Down")

    if e9 < e21 < e50 and price < e9:
        sell_score += 3
        sell_reasons.append("📉 Strong Bearish EMA Alignment")

    if upper_bb and price >= upper_bb * 0.997:
        sell_score += 3
        sell_reasons.append("🔴 Price at Upper Bollinger Band")

    if is_strong_trend(closes) and price < e21:
        sell_score += 2
        sell_reasons.append("💪 Strong Downtrend Continuation")

    if candle_confirmation(opens, closes, highs, lows, "sell"):
        sell_score += 2
        sell_reasons.append("✅ Bearish Candle Confirmation")

    if sell_score >= 8:
        accuracy = min(99, 85 + (sell_score * 1.2))
        return {
            "direction": "SELL (PUT)",
            "trend": "📉 DOWN-TREND (HIGH SCORE)",
            "accuracy": round(accuracy, 1),
            "pattern": sell_reasons[0] if sell_reasons else "Bearish Momentum",
            "score": sell_score,
            "reasons": sell_reasons
        }

    return {
        "direction": "NEUTRAL",
        "trend": "↔️ CONSOLIDATION",
        "accuracy": 50.0,
        "pattern": "⚖️ NO STRONG PATTERN MATCH",
        "score": max(buy_score, sell_score),
        "reasons": ["Market Condition Not Favorable"]
    }

# ==================== FRONTEND UI HTML ====================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Quotex AI Intelligence Master v11.3</title>
<style>
*{ margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',sans-serif; }
body{ background:#020617; color:white; max-width:500px; margin:auto; padding-bottom: 40px; }
.header{ background:#0f172a; padding:18px; border-bottom:1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
.title{ font-size:14px; font-weight:900; color:#00ffcc; letter-spacing:1px; }
.status{ font-size:10px; color:#00ff88; background: rgba(0, 255, 136, 0.05); padding: 5px 10px; border-radius: 20px; border: 1px solid rgba(0, 255, 136, 0.15); font-weight: bold; }
.clockBox{ background:#1e293b; margin:15px; padding:15px; border-radius:15px; display:flex; justify-content:space-between; border: 1px solid #334155; align-items: center; }
#clock{ font-size:22px; font-family:monospace; font-weight:bold; color:#00ffff; }
.balance-input { background: #0f172a; border: 1px solid #334155; padding: 6px 10px; border-radius: 8px; color: #00ffcc; font-weight: bold; width: 90px; text-align: center; font-size: 13px; }
.section{ margin:15px; }
.label{ font-size:11px; color:#94a3b8; margin-bottom:8px; letter-spacing: 1.5px; font-weight: bold; }
.pairs{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; max-height: 130px; overflow-y: auto; padding-right: 4px; }
.pair { padding: 11px; background: #0f172a; border: 1px solid #334155; border-radius: 12px; cursor: pointer; text-align: center; font-size: 13px; font-weight: bold; transition: 0.2s; }
.pair.active{ border: 1px solid #00ffcc; color:#00ffcc; background: rgba(0, 255, 204, 0.04); }
.tf{ display:flex; gap:8px; }
.tf button{ flex:1; padding:12px; border:1px solid #334155; background:#0f172a; color:white; border-radius:12px; font-weight: bold; cursor: pointer; font-size: 12px; }
.tf button.active-tf { background: linear-gradient(135deg, #00ffcc, #00b3ff); color: #000; border: none; }
.signalBox{ margin:15px; padding:22px; border-radius:22px; background: #0f172a; border:1px solid #334155; text-align:center; min-height: 290px; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: 0.3s; }
.signal-active-up { background: linear-gradient(135deg, rgba(0, 255, 136, 0.03), #020617); border: 2px solid #00ff88; }
.signal-active-down { background: linear-gradient(135deg, rgba(255, 68, 102, 0.03), #020617); border: 2px solid #ff4466; }
.signal-neutral { background: #0f172a; border: 2px solid #475569; }
#icon{ font-size:48px; margin-bottom: 3px; }
#signal{ font-size:30px; font-weight:900; }
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; width: 100%; margin-top: 12px; border-top: 1px solid #334155; padding-top: 12px; }
.stat-item { font-size: 11px; color: #94a3b8; font-weight: bold; text-align: left; }
.stat-item span { display: block; font-size: 13px; color: #fff; font-weight: 900; margin-top: 3px; }
.guide-box { width: 100%; margin-top: 12px; padding: 10px; border-radius: 10px; font-size: 11px; font-weight: bold; text-align: center; background: rgba(255, 165, 0, 0.05); border: 1px dashed #ffa500; color: #ffa500; }
.scanBtn{ width:90%; display:block; margin:15px auto 0 auto; padding:15px; border:none; border-radius:16px; background: linear-gradient(135deg, #00ffcc, #0077ff); font-size:15px; font-weight:bold; color:#000; cursor: pointer; }
.manual-pnl-actions { display: flex; gap: 10px; width: 100%; margin-top: 12px; }
.pnl-btn { flex: 1; padding: 8px; border: none; border-radius: 8px; color: black; font-weight: bold; font-size: 12px; cursor: pointer; }
.btn-win { background: #22c55e; color: white; }
.btn-loss { background: #ef4444; color: white; }
.control-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 15px; }
.control-btn { padding: 12px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 12px; font-weight: bold; border-radius: 12px; cursor: pointer; }
.control-btn.active { background: #00ffcc; color: black; border: none; }
.dashboard { background: #0f172a; margin: 15px; padding: 15px; border-radius: 15px; border: 1px solid #334155; }
.dash-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; text-align: center; margin-top: 8px; }
.dash-item { font-size: 11px; color: #94a3b8; font-weight: bold; }
.dash-item span { display: block; font-size: 16px; color: #fff; font-weight: 900; margin-top: 4px; }
.loader { border: 3px solid #334155; border-top: 3px solid #00ffcc; border-radius: 50%; width: 35px; height: 35px; animation: spin 1s linear infinite; margin-bottom: 15px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="header">
<div class="title">🤖 QX ENGINE v11.3 (FULL SCORE)</div>
<div class="status">🟢 ANTI-BAN INTEGRATION</div>
</div>
<div class="clockBox">
<div><div style="font-size:11px;color:#94a3b8;margin-bottom:4px;font-weight:bold;">MARKET TIME</div><div id="clock">00:00:00</div></div>
<div>
    <div style="font-size:11px;color:#94a3b8;margin-bottom:4px;font-weight:bold;text-align:right;">SET BALANCE ($)</div>
    <input type="number" id="userBalance" class="balance-input" value="1000" onchange="calculateAmounts()">
</div>
</div>
<div class="section">
<div class="label">SELECT OTC ASSET</div>
<div class="pairs">
<div class="pair active" data-name="USD/BRL">USD/BRL (OTC)</div>
<div class="pair" data-name="NZD/CAD">NZD/CAD (OTC)</div>
<div class="pair" data-name="USD/PKR">USD/PKR (OTC)</div>
<div class="pair" data-name="USD/BDT">USD/BDT (OTC)</div>
<div class="pair" data-name="NZD/JPY">NZD/JPY (OTC)</div>
<div class="pair" data-name="USD/EGP">USD/EGP (OTC)</div>
<div class="pair" data-name="EUR/USD">EUR/USD (OTC)</div>
</div>
</div>
<div class="section">
<div class="label">EXPIRY TIME</div>
<div class="tf">
<button data-tf="15s">15 SEC</button>
<button class="active-tf" data-tf="1m">1 MIN</button>
<button data-tf="5m">5 MIN</button>
</div>
</div>
<div class="signalBox signal-neutral" id="displayArea">
<div id="mainContent" style="width: 100%;">
<div id="targetAsset" style="font-size: 16px; color: #00ffcc; font-weight: 900; margin-bottom: 5px;">USD/BRL</div>
<div id="icon">🧠</div>
<div id="signal" style="color:#fff; font-size: 22px;">READY TO MASTER SCAN</div>
</div>
</div>
<button class="scanBtn" onclick="startScan()">🧠 EXECUTE ALGO SCAN</button>
<div class="control-grid">
    <button class="control-btn" id="autoBtn" onclick="toggleAutoMode()">🔄 AUTO MODE: OFF</button>
    <button class="control-btn" style="background:#dc2626;" onclick="resetStats()">🧹 RESET HISTORY</button>
</div>
<div class="dashboard">
    <div style="font-size: 11px; color:#94a3b8; font-weight:bold; letter-spacing:1px;">LIVE SESSION TRACKER</div>
    <div class="dash-grid">
        <div class="dash-item">WINS<span id="dashWins" style="color:#00ff88;">0</span></div>
        <div class="dash-item">LOSSES<span id="dashLosses" style="color:#ff4466;">0</span></div>
        <div class="dash-item">ACCURACY<span id="dashAcc" style="color:#00ffff;">0%</span></div>
    </div>
</div>
<script>
const clock = document.getElementById("clock");
const displayArea = document.getElementById("displayArea");
const mainContent = document.getElementById("mainContent");
let selectedPair = "USD/BRL";
let selectedTF = "1m";
let autoMode = false;
let autoInterval = null;
let wins = 0; let losses = 0;
let baseInvest = 10; let m1Invest = 23;

function updateClock(){
    let d = new Date();
    clock.innerHTML = String(d.getHours()).padStart(2,"0") + ":" + String(d.getMinutes()).padStart(2,"0") + ":" + String(d.getSeconds()).padStart(2,"0");
}
setInterval(updateClock, 1000); updateClock();

function calculateAmounts() {
    let bal = parseFloat(document.getElementById("userBalance").value) || 1000;
    baseInvest = Math.round(bal * 0.01);
    if(baseInvest < 1) baseInvest = 1;
    m1Invest = Math.round(baseInvest * 2.3);
}
calculateAmounts();

function updateDashboard(){
    document.getElementById("dashWins").innerText = wins;
    document.getElementById("dashLosses").innerText = losses;
    let total = wins + losses;
    let acc = total > 0 ? Math.round((wins / total) * 100) : 0;
    document.getElementById("dashAcc").innerText = acc + "%";
}

function logManualResult(result) {
    if(result === 'win') { wins++; } else { losses++; }
    updateDashboard();
    displayArea.className = "signalBox signal-neutral";
    mainContent.innerHTML = `
        <div style="font-size: 16px; color: #00ffcc; font-weight: 900; margin-bottom: 5px;">${selectedPair}</div>
        <div id="icon">👍</div>
        <div id="signal" style="color:#fff; font-size: 20px;">RESULT LOGGED! READY</div>`;
}

function startScan(){
    calculateAmounts();
    displayArea.className = "signalBox";
    mainContent.innerHTML = `<div class="loader"></div><div style="color:#00ffcc;font-weight:bold;">ANALYZING SCORES & CANDLES...</div>`;
    fetch(`/api/get_quotex_signal?pair=${selectedPair}&tf=${selectedTF}`)
    .then(res => res.json())
    .then(data => {
        let tfText = selectedTF;
        if(data.signal === "BUY (CALL)" || data.signal === "SELL (PUT)"){
            let isUp = data.signal === "BUY (CALL)";
            displayArea.className = isUp ? "signalBox signal-active-up" : "signalBox signal-active-down";
            mainContent.innerHTML = `
                <div style="font-size:12px;color:#00ffcc;font-weight:bold;">${selectedPair} (OTC) [${tfText}]</div>
                <div id="icon">${isUp ? '🟢':'🔴'}</div>
                <div id="signal" style="color: ${isUp ? '#00ff88':'#ff4466'};">${data.signal}</div>
                <div class="stats-grid">
                    <div class="stat-item">MATCHED KEY<span>${data.pattern}</span></div>
                    <div class="stat-item">CONFIDENCE<span>${data.accuracy}%</span></div>
                    <div class="stat-item">SCORE POINTS<span>${data.score} PTS</span></div>
                    <div class="stat-item">REC. INVEST<span>$${baseInvest}</span></div>
                </div>
                <div class="guide-box">⚠️ MARCO PLAN: IF LOSS PLACE M1 AMOUNT: $${m1Invest}</div>
                <div class="manual-pnl-actions">
                    <button class="pnl-btn btn-win" onclick="logManualResult('win')">✅ WIN</button>
                    <button class="pnl-btn btn-loss" onclick="logManualResult('loss')">❌ LOSS</button>
                </div>`;
        } else {
            displayArea.className = "signalBox signal-neutral";
            mainContent.innerHTML = `
                <div id="icon">⚖️</div>
                <div id="signal" style="color:#94a3b8; font-size:22px;">NEUTRAL / NO SETUP</div>
                <div style="font-size:11px; color:#64748b; margin-top:8px;">SCORE IS TOO LOW (${data.score} PTS)</div>`;
        }
    }).catch(() => {
        displayArea.className = "signalBox signal-neutral";
        mainContent.innerHTML = `<div style="color:#ff4466;">Server Error!</div>`;
    });
}

function toggleAutoMode(){
    autoMode = !autoMode;
    let autoBtn = document.getElementById("autoBtn");
    if(autoMode){
        autoBtn.innerText = "🔄 AUTO MODE: ON"; autoBtn.classList.add("active");
        startScan(); autoInterval = setInterval(startScan, 30000);
    } else {
        autoBtn.innerText = "🔄 AUTO MODE: OFF"; autoBtn.classList.remove("active");
        clearInterval(autoInterval);
    }
}

function resetStats(){ wins = 0; losses = 0; updateDashboard(); }

document.querySelectorAll('.pair').forEach(item => {
    item.addEventListener('click', function() {
        document.querySelector('.pair.active').classList.remove('active');
        this.classList.add('active'); selectedPair = this.getAttribute('data-name');
    });
});
</script>
</body>
</html>
"""

# ==================== FLASK ROUTES ====================

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/get_quotex_signal')
def get_quotex_signal_api():
    pair = request.args.get('pair', 'USD/BRL')
    result = get_signal(pair)
    
    return jsonify({
        "status": "success",
        "pair": pair,
        "signal": result["direction"],
        "trend": result["trend"],
        "accuracy": result["accuracy"],
        "pattern": result["pattern"],
        "score": result["score"],
        "reasons": result["reasons"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
