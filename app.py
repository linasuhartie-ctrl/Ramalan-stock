import os, re, math, time, logging
from io import StringIO
from typing import Any

import requests
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("gpr-scanner")

ARJUM_BASE_URL = os.getenv("ARJUM_BASE_URL", "https://stock.arjum.com").rstrip("/")
ARJUM_API_KEY = os.getenv("ARJUM_API_KEY", "").strip()
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "15"))
CACHE_SECONDS = int(os.getenv("CACHE_SECONDS", "300"))
# Optional URL to a maintained CSV/JSON file of IDX tickers.
STOCK_UNIVERSE_URL = os.getenv("STOCK_UNIVERSE_URL", "").strip()

# Broad fallback only. For full/current IDX coverage, configure STOCK_UNIVERSE_URL
# with a maintained CSV/JSON file, or use an Arjum endpoint returning all tickers.
DEFAULT_CODES = """
AADI AALI ABBA ABDA ABMM ACES ACRO ACST ADCP ADES ADHI ADMF ADMG ADMR ADRO
AGAR AGII AGRO AGRS AHAP AIMS AISA AKKU AKPI AKRA AKSI ALDO ALKA ALMI ALTO
AMAG AMAN AMAR AMFG AMIN AMMN AMMS AMOR ANJT ANTM APII APIC APLI ARCI AREA
ARGO ARII ARKO ARNA ARTA ARTO ASBI ASDM ASGR ASHA ASII ASJT ASLC ASRI ATAP
ATIC AUTO AVIA AWAN AXIO AYLS BABP BACA BAJA BALI BANK BBCA BBHI BBKP BBMD
BBNI BBRI BBSI BBTN BBYB BCAP BCIC BCIP BDMN BEBS BEEF BEER BELI BELL BESS
BEST BFIN BHAT BHIT BIKA BIMA BINA BINO BIPI BIRD BISI BJBR BJTM BKDP BKSL
BKSW BLES BLTA BLTZ BMAS BMHS BMRI BNBA BNBR BNGA BNII BNLI BOBA BOOM BORR
BOSS BPFI BPTR BRAM BRIS BRMS BRNA BRPT BSBK BSDE BSIM BSSR BTEK BTON BTPN
BTPS BUDI BUKA BUVA BVIC BWPT BYAN CAMP CANI CARE CARS CASA CASH CBMF CCSI
CEKA CENT CFIN CGAS CHEM CHIT CINT CITA CITY CLAY CLEO CLPI CMNP CMPP CMRY
CNKO CNMA COAL CPIN CPRO CRAB CSAP CSIS CSRA CTBN CTTH CUAN CYBR DADA DATA
DCII DEFI DEWA DGIK DGNS DGWG DIGI DILD DKFT DLTA DMAS DMND DNAR DOID DOSS
DSFI DSNG DSSA DUTI DVLA EAST ECII EDGE EKAD ELIT ELPI ELTY EMTK ENAK ENRG
EPMT ERAA ERTX ESSA ESTA ESTI ETWA EURO EXCL FAPA FAST FASW FILM FIRE FITT
FLMC FMII FOLK FOOD FPNI FUJI FUTR GAMA GDST GDYR GEMA GEMS GGRM GGRP GHON
GIAA GJTL GLVA GMFI GMTD GOLD GOOD GOTO GPRA GPSO GSMF GTBO GTRA GTSI GULA
GUNA GWSA HAIS HAJJ HALO HDFA HEAL HELI HERO HEXA HGII HILL HITS HKMU HOKI
HOME HOPE HRTA HRUM IATA IBST ICBP ICON IDEA IDPR IFII IFSH IGAR IKAI IKAN
IKBI IKPM IMAS IMJS IMPC INAF INAI INCF INCI INCO INDF INDR INDS INDX INET
INKP INOV INPC INPP INPS INRU INTA INTD INTP IOTF IPAC IPCC IPOL IPTV IRRA
ISAT ISSP ITIC ITMG JAST JATI JAWA JECC JGLE JIHD JKON JPFA JRPT JSMR JSPT
JTPE KAEF KBAG KBLI KBLM KBRI KDSI KDTN KEEN KEJU KIAS KIJA KING KINO KIOS
KKGI KLBF KMDS KMTR KOBX KOIN KONI KOPI KPIG KREN KRYA LABA LAJU LAND LAPD
LCAS LCKM LEAD LINK LMAS LMPI LOPI LPCK LPKR LPPF LRNA LSIP LTLS LUCY MAGP
MAIN MAPA MAPB MAPI MARK MASA MASB MAYA MBAP MBSS MBTO MCAS MCOL MDIA MDKA
MDKI MDLN MDRN MEDC MEGA MERK META MFMI MGNA MGRO MICE MIDI MIKA MINA MIRA
MITI MKNT MKPI MLBI MLIA MLPL MLPT MMLP MMSI MNCN MPPA MPRO MREI MSIN MTDL
MTEL MTLA MTMH MTPS MTRA MTSM MTWI MULT MYOH MYOR MYTX NASI NATO NELY NEST
NETV NFCX NICL NIKL NIPS NIRO NISP NICE NOBU NRCA NSSS NUSA OASA OBMD OCAP
OKAS OMRE OPMS PADI PALM PAMG PANI PANR PANS PBID PBRX PBSA PCAR PDES PEGE
PEHA PGAS PGEO PGLI PGUN PICO PJAA PKPK PLAN PLIN PMJS PMMP PMUI PNBN PNGO
PNIN PNSE POLA POLI POLL POLU PORT POWR PPGL PPRE PPRO PRDA PRIM PSAB PSAT
PSDN PSKT PTPP PUDP PURA PURE PWON PYFA RALS RANC RBMS RDTX REAL RELI RICY
RIGS RISE RMBA RMKE ROCK RODA ROTI RUCI RUNS SAFE SAME SAMF SAPX SATU SBAT
SBCS SBMA SCCO SCMA SCNP SDMU SDPC SDRA SGER SGRO SHID SHIP SICO SIDO SILO
SIMA SIMP SIPD SKBM SKLT SKRN SLIS SMAR SMBR SMCB SMDM SMDR SMGA SMGR SMIL
SMKL SMKM SMMT SMRA SMSM SNLK SOCI SOFA SOHO SOSS SOTS SPMA SPTO SQMI SRAJ
SRTG SSIA SSMS SSTM STAR STTP SUNI SUPR SURE SWAT SWID TALF TAMU TBIG TBLA
TBMS TCID TCPI TDPM TELE TFAS TGKA TGRA TIFA TINS TIRA TKIM TLDN TLKM TMAS
TMPO TNCA TOBA TOPS TOTL TOTO TOWR TPIA TPMA TRGU TRIL TRIM TRIN TRIO TRIS
TRJA TRON TRUE TSPC TUGU TYRE UANG UCID ULTJ UNIC UNIT UNTR UNVR VICI VINS
VKTR VRNA WAPO WEGE WEHA WIFI WIIM WIKA WINE WINS WIRG WMPP WMUU WTON YPAS
ZATA ZBRA ZINC ZONE
""".split()

CACHE = {}
UNIVERSE_CACHE = None
CODE_RE = re.compile(r"^[A-Z0-9]{3,5}$")


def normalize_code(value):
    if value is None:
        return None
    code = str(value).strip().upper().replace(".JK", "")
    return code if CODE_RE.fullmatch(code) else None


def arjum_get(path, params=None):
    if not ARJUM_API_KEY:
        raise RuntimeError("API Key belum diatur di Environment Variables SnapDeploy.")
    r = requests.get(
        f"{ARJUM_BASE_URL}{path}",
        headers={"X-API-Key": ARJUM_API_KEY, "Accept": "application/json"},
        params=params or {}, timeout=REQUEST_TIMEOUT
    )
    if r.status_code in (401, 403):
        raise RuntimeError("Arjum menolak API Key (401/403). Periksa key dan hak akses.")
    r.raise_for_status()
    return r.json()


def cached_get(key, path, params=None):
    now = time.time()
    if key in CACHE and now - CACHE[key][0] < CACHE_SECONDS:
        return CACHE[key][1]
    result = arjum_get(path, params)
    CACHE[key] = (now, result)
    return result


def extract_rows(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "results", "history", "candles", "items", "stocks", "screener", "result"):
            if isinstance(payload.get(key), list):
                return payload[key]
        for value in payload.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
    return []


def codes_from_payload(payload):
    rows = extract_rows(payload)
    codes = []
    for row in rows:
        if isinstance(row, str):
            code = normalize_code(row)
        elif isinstance(row, dict):
            code = None
            for key in ("stock_code", "code", "symbol", "ticker", "stockCode", "kode", "Kode"):
                if row.get(key):
                    code = normalize_code(row[key])
                    if code:
                        break
        else:
            code = None
        if code:
            codes.append(code)
    return list(dict.fromkeys(codes))


def external_universe(url):
    r = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "GPR-Stock-Scanner/1.0"})
    r.raise_for_status()
    if "json" in r.headers.get("content-type", "").lower() or url.lower().split("?")[0].endswith(".json"):
        payload = r.json()
        codes = codes_from_payload(payload)
        if codes:
            return codes
        rows = payload.get("data", payload.get("items", [])) if isinstance(payload, dict) else payload
        df = pd.DataFrame(rows if isinstance(rows, list) else [])
    else:
        df = pd.read_csv(StringIO(r.text))
    for col in ("code", "Code", "ticker", "Ticker", "symbol", "Symbol", "Kode", "kode", "stock_code"):
        if col in df.columns:
            codes = [normalize_code(x) for x in df[col].tolist()]
            return list(dict.fromkeys(x for x in codes if x))
    return []


def get_universe(force_refresh=False):
    global UNIVERSE_CACHE
    now = time.time()
    if not force_refresh and UNIVERSE_CACHE and now - UNIVERSE_CACHE[0] < 3600:
        return UNIVERSE_CACHE[1], UNIVERSE_CACHE[2]
    if STOCK_UNIVERSE_URL:
        try:
            codes = external_universe(STOCK_UNIVERSE_URL)
            if codes:
                UNIVERSE_CACHE = (now, codes, "STOCK_UNIVERSE_URL")
                return codes, "STOCK_UNIVERSE_URL"
        except Exception as e:
            LOG.warning("STOCK_UNIVERSE_URL gagal: %s", e)
    if ARJUM_API_KEY:
        try:
            codes = codes_from_payload(cached_get("universe", "/api/screener/latest"))
            # Do not let a tiny daily screener result (e.g. only 3 ranked stocks)
            # replace the broader ticker seed list. Prefer Arjum only when it
            # actually returns a reasonably broad universe.
            if len(codes) >= 100:
                UNIVERSE_CACHE = (now, codes, "Arjum screener")
                return codes, "Arjum screener"
            if codes:
                LOG.warning("Arjum screener returned only %d codes; using broader fallback list instead.", len(codes))
        except Exception as e:
            LOG.warning("Arjum universe gagal: %s", e)
    codes = list(dict.fromkeys(normalize_code(x) for x in DEFAULT_CODES if normalize_code(x)))
    UNIVERSE_CACHE = (now, codes, "fallback seed list (bukan seluruh BEI)")
    return codes, "fallback seed list (bukan seluruh BEI)"


def normalize_history(payload):
    rows = extract_rows(payload)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    aliases = {
        "time": ["time", "date", "datetime", "timestamp", "t"],
        "open": ["open", "o", "Open"], "high": ["high", "h", "High"],
        "low": ["low", "l", "Low"], "close": ["close", "c", "Close", "price"],
        "volume": ["volume", "vol", "v", "Volume"]
    }
    rename = {}
    for target, choices in aliases.items():
        for col in choices:
            if col in df.columns:
                rename[col] = target
                break
    df = df.rename(columns=rename)
    if "close" not in df.columns:
        return pd.DataFrame()
    for col in ("open", "high", "low"):
        if col not in df.columns:
            df[col] = df["close"]
    if "volume" not in df.columns:
        df["volume"] = 0.0
    if "time" in df.columns:
        if pd.api.types.is_numeric_dtype(df["time"]):
            vals = pd.to_numeric(df["time"], errors="coerce").dropna()
            unit = "ms" if not vals.empty and vals.iloc[0] > 10**11 else "s"
            df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True, unit=unit)
        else:
            df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)
        df = df.sort_values("time")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["close"]).reset_index(drop=True)


def ema(series, length):
    return series.ewm(span=length, adjust=False, min_periods=1).mean()


def matern32_kernel(x, z, amplitude, scale):
    d = x - z
    dist2 = d[0]**2 + .8*d[1]**2 + .6*d[2]**2 + .8*d[3]**2 + .6*d[4]**2
    u = math.sqrt(3.0 * max(float(dist2), 0.0)) / scale
    return amplitude * (1.0 + u) * math.exp(-u)


def gpr_project(df, horizon=10, training=30, momentum_len=5, vol_len=14,
                ema_fast=8, ema_slow=21, kernel_scale=1.5, noise_ratio=.30,
                volume_fade=.65, band_mode="ATR", atr_width=.70, gpr_sigma_width=1.96):
    min_needed = max(training + vol_len + ema_slow + 10, 60)
    if len(df) < min_needed:
        raise ValueError(f"Data historis belum cukup: {len(df)} candle; perlu sekitar {min_needed}.")
    close = df.close.astype(float).to_numpy()
    volume = df.volume.fillna(0).astype(float).to_numpy()
    logret = np.full(len(close), np.nan)
    logret[1:] = np.log(np.maximum(close[1:], 1e-12) / np.maximum(close[:-1], 1e-12))
    ret = pd.Series(logret)
    momentum = ret.ewm(span=momentum_len, adjust=False, min_periods=1).mean().to_numpy()
    volatility = ret.rolling(vol_len, min_periods=vol_len).std(ddof=1).to_numpy()
    vol_base = pd.Series(volatility).rolling(training, min_periods=training).mean().to_numpy()
    avg_volume = pd.Series(volume).rolling(vol_len, min_periods=1).mean().to_numpy()
    rel_volume = np.zeros(len(close))
    valid = (volume > 0) & (avg_volume > 0)
    rel_volume[valid] = np.log(volume[valid] / avg_volume[valid])
    fast, slow = ema(pd.Series(close), ema_fast).to_numpy(), ema(pd.Series(close), ema_slow).to_numpy()
    direction = (fast - slow) / np.maximum(close, 1e-12)
    high, low = df.high.astype(float).to_numpy(), df.low.astype(float).to_numpy()
    prev_close = np.r_[np.nan, close[:-1]]
    tr = np.maximum(high-low, np.maximum(np.abs(high-prev_close), np.abs(low-prev_close)))
    tr[0] = high[0] - low[0]
    atr = pd.Series(tr).ewm(alpha=1/vol_len, adjust=False, min_periods=vol_len).mean().to_numpy()
    idx = len(df)-1
    vol_ref = max(float(vol_base[idx]) if np.isfinite(vol_base[idx]) else 0, .0001)
    if not np.isfinite(volatility[idx]) or not np.isfinite(atr[idx]) or not np.isfinite(logret[idx]):
        raise ValueError("Indikator belum siap pada candle terakhir.")
    X, y = [], []
    for r in range(training):
        target_idx = idx-training+1+r
        feature_idx = target_idx-1
        if feature_idx < 1 or not np.isfinite(logret[target_idx]):
            continue
        X.append([logret[feature_idx]/vol_ref, momentum[feature_idx]/vol_ref,
                  rel_volume[feature_idx],
                  volatility[feature_idx]/vol_ref-1 if np.isfinite(volatility[feature_idx]) else 0,
                  direction[feature_idx]/vol_ref])
        y.append(logret[target_idx])
    X, y = np.asarray(X, float), np.asarray(y, float)
    n = len(y)
    if n < max(20, training-3):
        raise ValueError("Observasi training valid terlalu sedikit.")
    signal_var = max(float(np.mean(y*y)), 1e-8)
    noise_var = signal_var*noise_ratio+1e-10
    K = np.empty((n,n), float)
    for i in range(n):
        for j in range(i+1):
            v = matern32_kernel(X[i], X[j], signal_var, kernel_scale)
            if i == j: v += noise_var
            K[i,j] = K[j,i] = v
    try:
        L = np.linalg.cholesky(K)
        alpha = np.linalg.solve(L.T, np.linalg.solve(L,y))
    except np.linalg.LinAlgError:
        raise ValueError("Matriks GPR tidak stabil untuk data ini.")
    price_start = float(close[idx]); price_prev = price_start
    ret_prev = float(logret[idx]); mom_prev = float(momentum[idx])
    fast_prev = float(fast[idx]); slow_prev = float(slow[idx])
    volume_prev = float(rel_volume[idx]); vol_prev = float(volatility[idx]) if np.isfinite(volatility[idx]) else vol_ref
    cumulative_return = cumulative_variance = 0.0
    predictions, future_features, solved_future = [], [], []
    for h in range(horizon):
        fade = volume_fade**h
        assumed_vol = vol_ref + (vol_prev-vol_ref)*fade
        xstar = np.array([ret_prev/vol_ref, mom_prev/vol_ref, volume_prev*fade,
                          assumed_vol/vol_ref-1,
                          ((fast_prev-slow_prev)/max(price_prev,1e-12))/vol_ref])
        future_features.append(xstar)
        kstar = np.array([matern32_kernel(X[i],xstar,signal_var,kernel_scale) for i in range(n)])
        pred_ret = float(kstar @ alpha)
        if band_mode == "GPR":
            solved = np.linalg.solve(L,kstar)
            own_var = max(signal_var+noise_var-float(solved@solved),0)
            cross_sum = 0.0
            for j in range(h):
                cross = matern32_kernel(xstar,future_features[j],signal_var,kernel_scale)-float(solved@solved_future[j])
                cross_sum += cross
            cumulative_variance = max(cumulative_variance+own_var+2*cross_sum,0)
            solved_future.append(solved)
        cumulative_return += pred_ret
        price_pred = price_start*math.exp(cumulative_return)
        distance = atr_width*float(atr[idx])*math.sqrt(h+1)
        if band_mode == "GPR":
            upper = price_start*math.exp(cumulative_return+gpr_sigma_width*math.sqrt(cumulative_variance))
            lower = price_start*math.exp(cumulative_return-gpr_sigma_width*math.sqrt(cumulative_variance))
        else:
            upper, lower = price_pred+distance, max(.0001,price_pred-distance)
        predictions.append({"step":h+1,"price":round(price_pred,4),
            "return_pct":round((price_pred/price_start-1)*100,3),
            "upper":round(upper,4),"lower":round(lower,4)})
        price_prev, ret_prev = price_pred, pred_ret
        am, af, ass = 2/(momentum_len+1), 2/(ema_fast+1), 2/(ema_slow+1)
        mom_prev = am*pred_ret+(1-am)*mom_prev
        fast_prev = af*price_pred+(1-af)*fast_prev
        slow_prev = ass*price_pred+(1-ass)*slow_prev
    mom_now = float(momentum[idx]) if np.isfinite(momentum[idx]) else 0
    vol_avg = float(avg_volume[idx]) if np.isfinite(avg_volume[idx]) else 0
    final = predictions[-1]
    return {"price":round(float(close[idx]),4),
        "trend":"BULLISH" if fast[idx]>slow[idx] else "BEARISH",
        "momentum":"POSITIVE" if mom_now>0 else "NEGATIVE",
        "relative_volume":round(float(volume[idx])/vol_avg,2) if vol_avg>0 else 0,
        "gpr_return_pct":final["return_pct"],"projected_price":final["price"],
        "upper":final["upper"],"lower":final["lower"],"horizon":horizon,
        "predictions":predictions,"as_of":str(df.iloc[idx].get("time","")),"bars":len(df)}


def get_history(code, timeframe="1d"):
    params = {"interval": {"5m":"5m","15m":"15m","1h":"1h","1d":"1d"}.get(timeframe,"1d")}
    payload = cached_get(f"history:{code}:{timeframe}", f"/api/history/{code}", params)
    return normalize_history(payload)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    codes, source = get_universe()
    return jsonify({"api_key_configured":bool(ARJUM_API_KEY),"provider":"Arjum",
                    "universe_count":len(codes),"universe_source":source,
                    "intraday_note":"Dukungan timeframe intraday harus dikonfirmasi dari respons API Arjum.",
                    "status":"ready" if ARJUM_API_KEY else "needs_api_key"})


@app.route("/api/universe")
def universe():
    codes, source = get_universe(request.args.get("refresh")=="1")
    return jsonify({"count":len(codes),"source":source,"codes":codes,
                    "note":"Fallback seed list bukan daftar BEI lengkap. Untuk universe terkini, konfigurasi STOCK_UNIVERSE_URL ke CSV/JSON kode saham."})


@app.route("/api/scan")
def scan():
    timeframe = request.args.get("timeframe","1d")
    horizon = max(1,min(int(request.args.get("horizon",10)),30))
    raw_limit = request.args.get("limit","300")
    limit = 10000 if raw_limit.lower() in ("all","semua","universe","1000") else max(1,min(int(raw_limit),10000))
    if not ARJUM_API_KEY:
        return jsonify({"error":"API Key belum diatur di backend.","items":[]}),400
    codes, source = get_universe()
    selected = codes[:limit]
    results, errors = [], []
    started = time.time()
    for i, code in enumerate(selected,1):
        try:
            hist = get_history(code,timeframe)
            if hist.empty:
                errors.append({"code":code,"error":"Riwayat candle kosong/tidak dikenali"})
                continue
            result = gpr_project(hist,horizon=horizon)
            result["code"] = code
            result["score"] = round(
                max(0, min(100,
                    35 * (1 if result["trend"] == "BULLISH" else 0)
                    + 20 * (1 if result["momentum"] == "POSITIVE" else 0)
                    + 20 * min(result["relative_volume"] / 2, 1.0)
                    + 25 * max(0, min(result["gpr_return_pct"] / 5, 1.0))
                )),
                1
            )
            result["signal"] = ("KANDIDAT" if result["trend"]=="BULLISH" and
                result["momentum"]=="POSITIVE" and result["gpr_return_pct"]>0
                else "PANTAU" if result["gpr_return_pct"]>0 else "HINDARI")
        except Exception as e:
            errors.append({"code":code,"error":str(e)[:180]})
            continue
        results.append(result)
        if i % 50 == 0:
            LOG.info("Scan %d/%d; success=%d failed=%d",i,len(selected),len(results),len(errors))
    results.sort(key=lambda x:(x["score"],x["gpr_return_pct"]),reverse=True)
    return jsonify({"timeframe":timeframe,"horizon":horizon,"universe_source":source,
        "universe_count":len(codes),"requested":len(selected),"scanned":len(results),
        "errors_count":len(errors),"errors":errors[:25],
        "elapsed_seconds":round(time.time()-started,2),"items":results})


@app.route("/api/analyze/<code>")
def analyze(code):
    timeframe = request.args.get("timeframe","1d")
    horizon = max(1,min(int(request.args.get("horizon",10)),30))
    code = normalize_code(code)
    if not code:
        return jsonify({"error":"Kode saham tidak valid."}),400
    try:
        hist = get_history(code,timeframe)
        if hist.empty:
            return jsonify({"error":"Riwayat candle kosong/tidak dikenali."}),422
        result = gpr_project(hist,horizon=horizon)
        result["code"] = code
        result["history"] = [{"time":str(row.get("time","")),"open":float(row["open"]),
            "high":float(row["high"]),"low":float(row["low"]),"close":float(row["close"]),
            "volume":float(row["volume"])} for _,row in hist.tail(100).iterrows()]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error":str(e)}),400


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")),debug=False)
