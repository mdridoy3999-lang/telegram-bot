from flask import Flask, jsonify, render_template_string, request
import random
import time

app = Flask(__name__)

# ==================== OHLCV DATA GENERATOR ====================

def fetch_ohlcv(symbol):
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

# ==================== TECHNICAL INDICATORS & DOW THEORY ====================

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

def find_swing_points(highs, lows, left=2, right=2, window=40):
    n = len(highs)
    if n < (left + right + 1):
        return [], []
    start = max(left, n - window)
    swing_highs, swing_lows = [], []
    for i in range(start, n - right):
        window_highs = highs[i - left : i + right + 1]
        window_lows = lows[i - left : i + right + 1]
        if highs[i] == max(window_highs) and window_highs.count(highs[i]) == 1:
            swing_highs.append((i, highs[i]))
        if lows[i] == min(window_lows) and window_lows.count(lows[i]) == 1:
            swing_lows.append((i, lows[i]))
    return swing_highs, swing_lows

def calc_dow_trend(highs, lows):
    swing_highs, swing_lows = find_swing_points(highs, lows)
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "UNCLEAR", ["Dow Theory: Low Swing Data"]
    h1, h2 = swing_highs[-2][1], swing_highs[-1][1]
    l1, l2 = swing_lows[-2][1], swing_lows[-1][1]
    if h2 > h1 and l2 > l1:
        return "UPTREND", ["Dow Theory: HH + HL Structure"]
    elif h2 < h1 and l2 < l1:
        return "DOWNTREND", ["Dow Theory: LH + LL Structure"]
    else:
        return "UNCLEAR", ["Dow Theory: Consolidation Range"]

def ai_signal(symbol):
    opens, highs, lows, closes, volumes = fetch_ohlcv(symbol)
    if not closes or len(closes) < 100:
        return {"signal": "WAIT", "confidence": 0, "trend": "NEUTRAL", "reasons": ["Insufficient Data"]}

    close = closes[-1]
    ema_fast = calc_ema(closes, 9)
    ema_slow = calc_ema(closes, 21)
    rsi = calc_rsi(closes)
    dow_trend, dow_reasons = calc_dow_trend(highs, lows)

    score = 0
    reasons = []

    # 1. EMA Base
    if ema_fast > ema_slow:
        trend = "CALL"
        score += 35
        reasons.append("EMA Fast > Slow (Bullish)")
    elif ema_fast < ema_slow:
        trend = "PUT"
        score += 35
        reasons.append("EMA Fast < Slow (Bearish)")
    else:
        return {"signal": "WAIT", "confidence": 0, "trend": "NEUTRAL", "reasons": ["EMA Flat"]}

    # 2. Dow Theory & Penalty Engine
    if trend == "CALL" and dow_trend == "UPTREND":
        score += 25
        reasons.extend(dow_reasons)
    elif trend == "PUT" and dow_trend == "DOWNTREND":
        score += 25
        reasons.extend(dow_reasons)
    elif trend == "CALL" and dow_trend == "DOWNTREND":
        score -= 20
        reasons.append("Dow Structure Conflicts Trend")
    elif trend == "PUT" and dow_trend == "UPTREND":
        score -= 20
        reasons.append("Dow Structure Conflicts Trend")

    score = max(0, score)

    # 3. RSI Health Check
    if trend == "CALL" and (35 <= rsi <= 65 or rsi < 30):
        score += 25
        reasons.append(f"RSI Confirmed ({rsi})")
    elif trend == "PUT" and (35 <= rsi <= 65 or rsi > 70):
        score += 25
        reasons.append(f"RSI Confirmed ({rsi})")

    # Final Decision
    if score >= 75:
        signal = "STRONG " + trend
    elif score >= 60:
        signal = trend
    else:
        signal = "WAIT"

    return {"signal": signal, "confidence": score, "trend": trend, "reasons": reasons}

# ==================== ADVANCED UI TEMPLATE ====================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Pro AI Chart Scanner v13.0</title>
<style>
*{ margin:0; padding:0; box-sizing:border-box; font-family:'Inter', system-ui, sans-serif; }
body{ background:#030712; color:#f9fafb; max-width:480px; margin:auto; padding: 10px; }
.header{ background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(10px); padding:16px; border-radius:18px; border:1px solid #1f2937; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.title{ font-size:13px; font-weight:800; color:#38bdf8; letter-spacing:1px; display:flex; align-items:center; gap:6px; }
.status{ font-size:10px; color:#4ade80; background: rgba(74, 222, 128, 0.1); padding: 4px 8px; border-radius: 20px; border: 1px solid rgba(74, 222, 128, 0.2); font-weight: 700; }

/* Pair Grid */
.section-title{ font-size:11px; color:#9ca3af; margin:10px 0 6px 4px; font-weight:700; letter-spacing: 1px; }
.pairs{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.pair { padding: 9px 4px; background: #111827; border: 1px solid #1f2937; border-radius: 10px; cursor: pointer; text-align: center; font-size: 11px; font-weight: 700; color:#9ca3af; transition: 0.2s; }
.pair.active{ border-color: #38bdf8; color:#38bdf8; background: rgba(56, 189, 248, 0.1); }

/* Timeframe Selector */
.tf-grid{ display:flex; gap:6px; margin-top:6px; }
.tf-btn{ flex:1; padding:9px; border:1px solid #1f2937; background:#111827; color:#9ca3af; border-radius:10px; font-weight:700; font-size:11px; cursor:pointer; }
.tf-btn.active{ background:#38bdf8; color:#030712; border:none; }

/* Signal Card UI */
.signalBox{ margin-top:14px; padding:20px; border-radius:20px; background: #111827; border:1px solid #1f2937; text-align:center; min-height:230px; display:flex; flex-direction:column; justify-content:center; align-items:center; position:relative; overflow:hidden; }
.signal-up { border: 2px solid #22c55e; background: radial-gradient(circle at top, rgba(34, 197, 94, 0.15), #111827); }
.signal-down { border: 2px solid #ef4444; background: radial-gradient(circle at top, rgba(239, 68, 68, 0.15), #111827); }

/* Timer Indicator */
.timer-badge { position:absolute; top:12px; right:12px; background:#1f2937; color:#38bdf8; font-size:11px; font-weight:800; padding:4px 10px; border-radius:12px; border:1px solid #374151; }

.scanBtn{ width:100%; margin-top:12px; padding:14px; border:none; border-radius:14px; background: linear-gradient(135deg, #38bdf8, #3b82f6); font-size:14px; font-weight:800; color:#030712; cursor: pointer; transition: 0.2s; }

/* History Section */
.history-box{ background:#111827; border:1px solid #1f2937; border-radius:16px; padding:12px; margin-top:14px; }
.history-list{ max-height:120px; overflow-y:auto; margin-top:8px; display:flex; flex-direction:column; gap:6px; }
.history-item{ display:flex; justify-space-between; align-items:center; font-size:11px; padding:6px 10px; background:#1f2937; border-radius:8px; }
.badge-win{ color:#4ade80; font-weight:bold; }
.badge-loss{ color:#f87171; font-weight:bold; }

/* Dashboard Footer */
.dash-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; text-align: center; margin-top: 12px; background:#111827; padding:12px; border-radius:14px; border:1px solid #1f2937; }
.dash-item { font-size: 10px; color: #9ca3af; font-weight: 700; }
.dash-item span { display: block; font-size: 15px; color: #fff; font-weight: 900; margin-top: 2px; }
.loader { border: 3px solid #1f2937; border-top: 3px solid #38bdf8; border-radius: 50%; width: 28px; height: 28px; animation: spin 0.8s linear infinite; margin-bottom: 10px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
</head>
<body>

<div class="header">
    <div class="title">⚡ AI SCANNER PRO v13</div>
    <div class="status">● LIVE SYSTEM</div>
</div>

<div class="section-title">SELECT ASSET</div>
<div class="pairs">
    <div class="pair active" onclick="setPair('USD/BRL', this)">USD/BRL</div>
    <div class="pair" onclick="setPair('EUR/USD', this)">EUR/USD</div>
    <div class="pair" onclick="setPair('USD/BDT', this)">USD/BDT</div>
    <div class="pair" onclick="setPair('NZD/CAD', this)">NZD/CAD</div>
    <div class="pair" onclick="setPair('USD/PKR', this)">USD/PKR</div>
    <div class="pair" onclick="setPair('USD/EGP', this)">USD/EGP</div>
</div>

<div class="section-title">TIMEFRAME</div>
<div class="tf-grid">
    <button class="tf-btn" onclick="setTF('15s', this)">15 SEC</button>
    <button class="tf-btn active" onclick="setTF('1m', this)">1 MIN</button>
    <button class="tf-btn" onclick="setTF('5m', this)">5 MIN</button>
</div>

<!-- Main Signal Card -->
<div class="signalBox" id="signalBox">
    <div class="timer-badge" id="timer">⏱️ --s</div>
    <div id="signalContent">
        <div style="font-size:36px; margin-bottom:6px;">📡</div>
        <div style="font-size:16px; font-weight:800; color:#9ca3af;">PRESS SCAN TO ANALYZE</div>
    </div>
</div>

<button class="scanBtn" onclick="runScan()">🔥 EXECUTE AI SCAN</button>

<!-- Live History Tracker -->
<div class="history-box">
    <div class="section-title" style="margin:0;">📜 SIGNAL HISTORY</div>
    <div class="history-list" id="historyList">
        <div style="font-size:10px; color:#6b7280; text-align:center; padding:10px;">No scan history yet</div>
    </div>
</div>

<!-- Session Stats -->
<div class="dash-grid">
    <div class="dash-item">WINS<span id="wins" style="color:#4ade80;">0</span></div>
    <div class="dash-item">LOSSES<span id="losses" style="color:#f87171;">0</span></div>
    <div class="dash-item">ACCURACY<span id="acc" style="color:#38bdf8;">0%</span></div>
</div>

<script>
let currentPair = 'USD/BRL';
let currentTF = '1m';
let timerInterval = null;
let wins = 0, losses = 0;

function setPair(pair, el){
    document.querySelectorAll('.pair').forEach(e => e.classList.remove('active'));
    el.classList.add('active');
    currentPair = pair;
}

function setTF(tf, el){
    document.querySelectorAll('.tf-btn').forEach(e => e.classList.remove('active'));
    el.classList.add('active');
    currentTF = tf;
}

function startCountdown(duration) {
    clearInterval(timerInterval);
    let timer = duration;
    const timerEl = document.getElementById('timer');
    timerInterval = setInterval(() => {
        timerEl.innerText = `⏱️ ${timer}s`;
        if (--timer < 0) {
            clearInterval(timerInterval);
            timerEl.innerText = "⏱️ EXPIRED";
        }
    }, 1000);
}

function addHistory(pair, signal, conf) {
    const list = document.getElementById('historyList');
    if (wins === 0 && losses === 0 && list.children[0].innerText.includes("No scan")) {
        list.innerHTML = '';
    }
    const isCall = signal.includes("CALL");
    const item = document.createElement('div');
    item.className = 'history-item';
    item.innerHTML = `
        <span><b>${pair}</b> (${currentTF})</span>
        <span style="color:${isCall ? '#4ade80':'#f87171'}; font-weight:800;">${signal}</span>
        <span>${conf}%</span>
        <button onclick="markResult(this, true)" class="badge-win" style="background:none;border:none;cursor:pointer;">✅</button>
        <button onclick="markResult(this, false)" class="badge-loss" style="background:none;border:none;cursor:pointer;">❌</button>
    `;
    list.prepend(item);
}

function markResult(btn, isWin) {
    if(isWin) wins++; else losses++;
    const parent = btn.parentElement;
    parent.style.opacity = '0.5';
    parent.querySelectorAll('button').forEach(b => b.remove());
    updateStats();
}

function updateStats(){
    document.getElementById('wins').innerText = wins;
    document.getElementById('losses').innerText = losses;
    let total = wins + losses;
    document.getElementById('acc').innerText = total > 0 ? Math.round((wins/total)*100) + '%' : '0%';
}

function runScan(){
    const box = document.getElementById('signalBox');
    const content = document.getElementById('signalContent');
    
    box.className = "signalBox";
    content.innerHTML = `<div class="loader"></div><div style="font-size:12px; font-weight:bold; color:#38bdf8;">SCANNING ${currentPair}...</div>`;
    
    fetch(`/api/get_quotex_signal?pair=${currentPair}`)
    .then(r => r.json())
    .then(data => {
        if(data.signal.includes("CALL") || data.signal.includes("PUT")){
            const isUp = data.signal.includes("CALL");
            box.className = isUp ? "signalBox signal-up" : "signalBox signal-down";
            content.innerHTML = `
                <div style="font-size:11px; font-weight:800; color:#38bdf8;">${data.pair} • ${currentTF}</div>
                <div style="font-size:36px; font-weight:900; color:${isUp?'#4ade80':'#f87171'}; margin:4px 0;">
                    ${isUp ? '⬆ UP (CALL)' : '⬇ DOWN (PUT)'}
                </div>
                <div style="font-size:12px; font-weight:800;">CONFIDENCE: ${data.confidence}%</div>
                <div style="font-size:10px; color:#9ca3af; margin-top:4px;">${data.reasons[0] || 'Technical Match'}</div>
            `;
            startCountdown(currentTF === '15s' ? 15 : (currentTF === '1m' ? 60 : 300));
            addHistory(data.pair, data.signal, data.confidence);
        } else {
            box.className = "signalBox";
            content.innerHTML = `
                <div style="font-size:32px;">⚖️</div>
                <div style="font-size:16px; font-weight:800; color:#9ca3af;">MARKET WAIT</div>
                <div style="font-size:10px; color:#6b7280; margin-top:4px;">Low Score: ${data.confidence} Points</div>
            `;
        }
    });
}
</script>
</body>
</html>
"""

# ==================== CONTROLLER ====================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/get_quotex_signal')
def api_signal():
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
