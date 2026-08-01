from flask import Flask, jsonify, render_template_string, request
import random
import time

app = Flask(__name__)

# ==================== DATA & TECHNICAL ANALYSIS CALCULATOR ====================

def fetch_ohlcv(symbol):
    """
    মার্কেট ক্যান্ডেলস্টিক ও ভলিউম ডেটা জেনারেটর
    """
    random.seed(int(time.time() / 10) + ord(symbol[0]))
    base_price = 1.0850 if "EUR" in symbol else (100.50 if "BRL" in symbol else 150.20)
    
    closes, highs, lows, opens, volumes = [], [], [], [], []
    curr = base_price
    for _ in range(120):
        change = random.uniform(-0.002, 0.002)
        op = curr
        cl = curr + change
        hi = max(op, cl) + random.uniform(0, 0.0008)
        lo = min(op, cl) - random.uniform(0, 0.0008)
        vol = random.randint(300, 1500)
        
        opens.append(op)
        closes.append(cl)
        highs.append(hi)
        lows.append(lo)
        volumes.append(vol)
        curr = cl
        
    return opens, highs, lows, closes, volumes

def calc_ema(closes, period):
    multiplier = 2 / (period + 1)
    ema = closes[0]
    for price in closes[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    return ema

def calc_rsi(closes, period=14):
    gains = [max(0, closes[i] - closes[i-1]) for i in range(1, len(closes))]
    losses = [max(0, closes[i-1] - closes[i]) for i in range(1, len(closes))]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calc_macd(closes):
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    macd_line = ema12 - ema26
    signal_line = macd_line * 0.85  # Simulated Signal Line
    return macd_line, signal_line

def calc_bollinger(closes, period=20, std_dev=2):
    slice_closes = closes[-period:]
    sma = sum(slice_closes) / period
    variance = sum((x - sma) ** 2 for x in slice_closes) / period
    sd = variance ** 0.5
    return sma + (std_dev * sd), sma, sma - (std_dev * sd)

def detect_candle_pattern(opens, closes, highs, lows):
    op, cl = opens[-1], closes[-1]
    prev_op, prev_cl = opens[-2], closes[-2]
    
    if cl > op and (prev_cl < prev_op) and (cl > prev_op) and (op < prev_cl):
        return "Bullish Engulfing"
    elif cl < op and (prev_cl > prev_op) and (cl < prev_op) and (op > prev_cl):
        return "Bearish Engulfing"
    elif (cl - op) > 0 and (op - lows[-1]) > 2 * (cl - op):
        return "Hammer"
    elif (op - cl) > 0 and (highs[-1] - op) > 2 * (op - cl):
        return "Shooting Star"
    elif cl > op:
        return "Pin Bar Bullish"
    else:
        return "Pin Bar Bearish"

# ==================== YOUR CUSTOM WEIGHTED AI SIGNAL ENGINE ====================

def ai_signal(symbol):
    opens, highs, lows, closes, volumes = fetch_ohlcv(symbol)
    if not closes or len(closes) < 100:
        return {"signal": "WAIT", "confidence": 0, "trend": "NEUTRAL", "reasons": ["Insufficient Data"]}

    close = closes[-1]
    ema_fast = calc_ema(closes, 9)
    ema_slow = calc_ema(closes, 21)
    rsi = calc_rsi(closes)
    macd, macd_signal = calc_macd(closes)
    bb_upper, bb_middle, bb_lower = calc_bollinger(closes)
    candle_pattern = detect_candle_pattern(opens, closes, highs, lows)
    support = min(lows[-30:])
    resistance = max(highs[-30:])
    volume = volumes[-1]
    avg_volume = sum(volumes[-10:]) / 10

    score = 0
    reasons = []

    # 1. EMA Trend (20 Points)
    if ema_fast > ema_slow:
        trend = "CALL"
        score += 20
        reasons.append("EMA Bullish Alignment")
    elif ema_fast < ema_slow:
        trend = "PUT"
        score += 20
        reasons.append("EMA Bearish Alignment")
    else:
        trend = "WAIT"

    if trend == "WAIT":
        return {"signal": "WAIT", "confidence": 0, "trend": "NEUTRAL", "reasons": ["EMA Flat"]}

    # 2. RSI (15 Points)
    if trend == "CALL":
        if 35 <= rsi <= 65:
            score += 15
            reasons.append(f"RSI Healthy Buy ({rsi})")
        elif rsi < 30:
            score += 15
            reasons.append(f"RSI Deep Oversold Rebound ({rsi})")

    elif trend == "PUT":
        if 35 <= rsi <= 65:
            score += 15
            reasons.append(f"RSI Healthy Sell ({rsi})")
        elif rsi > 70:
            score += 15
            reasons.append(f"RSI Deep Overbought Drop ({rsi})")

    # 3. MACD (15 Points)
    if trend == "CALL" and macd > macd_signal:
        score += 15
        reasons.append("MACD Bullish Crossover")

    if trend == "PUT" and macd < macd_signal:
        score += 15
        reasons.append("MACD Bearish Crossover")

    # 4. Bollinger Bands (15 Points)
    if trend == "CALL" and (close > bb_middle or close <= bb_lower * 1.002):
        score += 15
        reasons.append("Bollinger Support / Bounce")

    if trend == "PUT" and (close < bb_middle or close >= bb_upper * 0.998):
        score += 15
        reasons.append("Bollinger Resistance / Rejection")

    # 5. Candlestick Patterns (15 Points)
    bullish_patterns = ["Bullish Engulfing", "Hammer", "Morning Star", "Pin Bar Bullish"]
    bearish_patterns = ["Bearish Engulfing", "Shooting Star", "Evening Star", "Pin Bar Bearish"]

    if trend == "CALL" and candle_pattern in bullish_patterns:
        score += 15
        reasons.append(f"Pattern: {candle_pattern}")

    if trend == "PUT" and candle_pattern in bearish_patterns:
        score += 15
        reasons.append(f"Pattern: {candle_pattern}")

    # 6. Support / Resistance (10 Points)
    if trend == "CALL" and abs(close - support) < (close * 0.0025):
        score += 10
        reasons.append("Near Strong Support")

    if trend == "PUT" and abs(close - resistance) < (close * 0.0025):
        score += 10
        reasons.append("Near Strong Resistance")

    # 7. Volume (10 Points)
    if volume > avg_volume:
        score += 10
        reasons.append("High Volume Confirmation")

    # Final Decision Output
    if score >= 80:
        signal = "STRONG " + trend
    elif score >= 65:
        signal = trend
    else:
        signal = "WAIT"

    return {
        "signal": signal,
        "confidence": score,
        "trend": trend,
        "reasons": reasons
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
#signal{ font-size:26px; font-weight:900; }
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
<div class="title">🤖 QX ENGINE v11.3 (100 PTS ENGINE)</div>
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
        <div id="icon">🧠</div>
        <div id="signal" style="color:#fff; font-size: 20px;">RESULT LOGGED! READY</div>`;
}

function startScan(){
    calculateAmounts();
    displayArea.className = "signalBox";
    mainContent.innerHTML = `<div class="loader"></div><div style="color:#00ffcc;font-weight:bold;">COMPUTING 100-PT WEIGHTED ALGO...</div>`;
    fetch(`/api/get_quotex_signal?pair=${selectedPair}&tf=${selectedTF}`)
    .then(res => res.json())
    .then(data => {
        let tfText = selectedTF;
        if(data.signal.includes("CALL") || data.signal.includes("PUT")){
            let isUp = data.signal.includes("CALL");
            displayArea.className = isUp ? "signalBox signal-active-up" : "signalBox signal-active-down";
            mainContent.innerHTML = `
                <div style="font-size:12px;color:#00ffcc;font-weight:bold;">${selectedPair} (OTC) [${tfText}]</div>
                <div id="icon">${isUp ? '🟢':'🔴'}</div>
                <div id="signal" style="color: ${isUp ? '#00ff88':'#ff4466'};">${data.signal}</div>
                <div class="stats-grid">
                    <div class="stat-item">AI CONFIDENCE<span>${data.confidence} / 100 PTS</span></div>
                    <div class="stat-item">KEY REASON<span>${data.reasons[0] || 'Technical Match'}</span></div>
                    <div class="stat-item">REC. INVEST<span>$${baseInvest}</span></div>
                    <div class="stat-item">M1 INVEST<span>$${m1Invest}</span></div>
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
                <div id="signal" style="color:#94a3b8; font-size:22px;">MARKET WAIT (${data.confidence} PTS)</div>
                <div style="font-size:11px; color:#64748b; margin-top:8px;">SCORE IS BELOW 65 PTS THRESHOLD</div>`;
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

# ==================== API ROUTE ====================

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/get_quotex_signal')
def get_quotex_signal_api():
    pair = request.args.get('pair', 'USD/BRL')
    res = ai_signal(pair)
    
    return jsonify({
        "status": "success",
        "pair": pair,
        "signal": res["signal"],
        "confidence": res["confidence"],
        "trend": res["trend"],
        "reasons": res["reasons"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
