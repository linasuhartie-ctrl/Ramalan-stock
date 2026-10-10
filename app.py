import os
import re
import math
import time
import logging
from io import StringIO

import requests
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("gpr-scanner")

ARJUM_BASE_URL = os.getenv(
    "ARJUM_BASE_URL", "https://stock.arjum.com"
).rstrip("/")
ARJUM_API_KEY = os.getenv("ARJUM_API_KEY", "").strip()
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "15"))
CACHE_SECONDS = int(os.getenv("CACHE_SECONDS", "300"))
STOCK_UNIVERSE_URL = os.getenv("STOCK_UNIVERSE_URL", "").strip()


# Daftar cadangan kode saham.
# Daftar ini bukan jaminan seluruh saham BEI aktif dan terkini.
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

    if CODE_RE.fullmatch(code):
        return code

    return None


def arjum_get(path, params=None):
    if not ARJUM_API_KEY:
        raise RuntimeError(
            "API Key belum diatur di Environment Variables SnapDeploy."
        )

    response = requests.get(
        f"{ARJUM_BASE_URL}{path}",
        headers={
            "X-API-Key": ARJUM_API_KEY,
            "Accept": "application/json",
        },
        params=params or {},
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code in (401, 403):
        raise RuntimeError(
            "Arjum menolak API Key (401/403). Periksa key dan hak akses."
        )

    response.raise_for_status()
    return response.json()


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
        possible_keys = (
            "data", "results", "history", "candles",
            "items", "stocks", "screener", "result"
        )

        for key in possible_keys:
            value = payload.get(key)

            if isinstance(value, list):
                return value

        for value in payload.values():
            if (
                isinstance(value, list)
                and value
                and isinstance(value[0], dict)
            ):
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

            for key in (
                "stock_code", "code", "symbol", "ticker",
                "stockCode", "kode", "Kode"
            ):
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
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "GPR-Stock-Scanner/1.0"},
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()

    if "json" in content_type or url.lower().split("?")[0].endswith(".json"):
        payload = response.json()
        codes = codes_from_payload(payload)

        if codes:
            return codes

        rows = (
            payload.get("data", payload.get("items", []))
            if isinstance(payload, dict)
            else payload
        )

        dataframe = pd.DataFrame(rows if isinstance(rows, list) else [])

    else:
        dataframe = pd.read_csv(StringIO(response.text))

    columns = (
        "code", "Code", "ticker", "Ticker", "symbol",
        "Symbol", "Kode", "kode", "stock_code"
    )

    for column in columns:
        if column in dataframe.columns:
            codes = [
                normalize_code(value)
                for value in dataframe[column].tolist()
            ]

            return list(dict.fromkeys(
                code for code in codes if code
            ))

    return []


def get_universe(force_refresh=False):
    global UNIVERSE_CACHE

    now = time.time()

    if (
        not force_refresh
        and UNIVERSE_CACHE
        and now - UNIVERSE_CACHE[0] < 3600
    ):
        return UNIVERSE_CACHE[1], UNIVERSE_CACHE[2]

    if STOCK_UNIVERSE_URL:
        try:
            codes = external_universe(STOCK_UNIVERSE_URL)

            if codes:
                UNIVERSE_CACHE = (
                    now, codes, "STOCK_UNIVERSE_URL"
                )
                return codes, "STOCK_UNIVERSE_URL"

        except Exception as error:
            LOG.warning(
                "STOCK_UNIVERSE_URL gagal: %s", error
            )

    if ARJUM_API_KEY:
        try:
            codes = codes_from_payload(
                cached_get("universe", "/api/screener/latest")
            )

            # Jangan mengganti daftar cadangan yang luas dengan
            # daftar ranking kecil yang hanya berisi beberapa saham.
            if len(codes) >= 100:
                UNIVERSE_CACHE = (
                    now, codes, "Arjum screener"
                )
                return codes, "Arjum screener"

            if codes:
                LOG.warning(
                    "Screener Arjum hanya mengembalikan %s kode; "
                    "menggunakan daftar cadangan yang lebih luas.",
                    len(codes),
                )

        except Exception as error:
            LOG.warning("Arjum universe gagal: %s", error)

    codes = list(dict.fromkeys(
        normalize_code(code)
        for code in DEFAULT_CODES
        if normalize_code(code)
    ))

    UNIVERSE_CACHE = (
        now,
        codes,
        "fallback seed list (bukan seluruh BEI)",
    )

    return codes, "fallback seed list (bukan seluruh BEI)"


def normalize_history(payload):
    rows = extract_rows(payload)

    if not rows:
        return pd.DataFrame()

    dataframe = pd.DataFrame(rows)

    aliases = {
        "time": ["time", "date", "datetime", "timestamp", "t"],
        "open": ["open", "o", "Open"],
        "high": ["high", "h", "High"],
        "low": ["low", "l", "Low"],
        "close": ["close", "c", "Close", "price"],
        "volume": ["volume", "vol", "v", "Volume"],
    }

    rename = {}

    for target, choices in aliases.items():
        for column in choices:
            if column in dataframe.columns:
                rename[column] = target
                break

    dataframe = dataframe.rename(columns=rename)

    if "close" not in dataframe.columns:
        return pd.DataFrame()

    for column in ("open", "high", "low"):
        if column not in dataframe.columns:
            dataframe[column] = dataframe["close"]

    if "volume" not in dataframe.columns:
        dataframe["volume"] = 0.0

    if "time" in dataframe.columns:
        if pd.api.types.is_numeric_dtype(dataframe["time"]):
            values = pd.to_numeric(
                dataframe["time"], errors="coerce"
            ).dropna()

            unit = (
                "ms"
                if not values.empty and values.iloc[0] > 10**11
                else "s"
            )

            dataframe["time"] = pd.to_datetime(
                dataframe["time"],
                errors="coerce",
                utc=True,
                unit=unit,
            )
        else:
            dataframe["time"] = pd.to_datetime(
                dataframe["time"],
                errors="coerce",
                utc=True,
            )

        dataframe = dataframe.sort_values("time")

    for column in ("open", "high", "low", "close", "volume"):
        dataframe[column] = pd.to_numeric(
            dataframe[column], errors="coerce"
        )

    return dataframe.dropna(
        subset=["close"]
    ).reset_index(drop=True)


def ema(series, length):
    return series.ewm(
        span=length,
        adjust=False,
        min_periods=1,
    ).mean()


def matern32_kernel(x, z, amplitude, scale):
    difference = x - z

    distance_squared = (
        difference[0] ** 2
        + 0.8 * difference[1] ** 2
        + 0.6 * difference[2] ** 2
        + 0.8 * difference[3] ** 2
        + 0.6 * difference[4] ** 2
    )

    u = (
        math.sqrt(3.0 * max(float(distance_squared), 0.0))
        / scale
    )

    return amplitude * (1.0 + u) * math.exp(-u)


def gpr_project(
    dataframe,
    horizon=10,
    training=30,
    momentum_len=5,
    vol_len=14,
    ema_fast=8,
    ema_slow=21,
    kernel_scale=1.5,
    noise_ratio=0.30,
    volume_fade=0.65,
    band_mode="ATR",
    atr_width=0.70,
    gpr_sigma_width=1.96,
):
    min_needed = max(
        training + vol_len + ema_slow + 10,
        60,
    )

    if len(dataframe) < min_needed:
        raise ValueError(
            f"Data historis belum cukup: {len(dataframe)} candle; "
            f"perlu sekitar {min_needed}."
        )

    close = dataframe["close"].astype(float).to_numpy()
    volume = dataframe["volume"].fillna(0).astype(float).to_numpy()

    logret = np.full(len(close), np.nan)
    logret[1:] = np.log(
        np.maximum(close[1:], 1e-12)
        / np.maximum(close[:-1], 1e-12)
    )

    returns = pd.Series(logret)

    momentum = returns.ewm(
        span=momentum_len,
        adjust=False,
        min_periods=1,
    ).mean().to_numpy()

    volatility = returns.rolling(
        vol_len,
        min_periods=vol_len,
    ).std(ddof=1).to_numpy()

    vol_base = pd.Series(volatility).rolling(
        training,
        min_periods=training,
    ).mean().to_numpy()

    avg_volume = pd.Series(volume).rolling(
        vol_len,
        min_periods=1,
    ).mean().to_numpy()

    rel_volume = np.zeros(len(close))
    valid = (volume > 0) & (avg_volume > 0)

    rel_volume[valid] = np.log(
        volume[valid] / avg_volume[valid]
    )

    fast = ema(pd.Series(close), ema_fast).to_numpy()
    slow = ema(pd.Series(close), ema_slow).to_numpy()

    direction = (
        (fast - slow) / np.maximum(close, 1e-12)
    )

    high = dataframe["high"].astype(float).to_numpy()
    low = dataframe["low"].astype(float).to_numpy()

    previous_close = np.r_[np.nan, close[:-1]]

    true_range = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - previous_close),
            np.abs(low - previous_close),
        ),
    )

    true_range[0] = high[0] - low[0]

    atr = pd.Series(true_range).ewm(
        alpha=1 / vol_len,
        adjust=False,
        min_periods=vol_len,
    ).mean().to_numpy()

    index = len(dataframe) - 1

    vol_ref = max(
        float(vol_base[index])
        if np.isfinite(vol_base[index])
        else 0.0,
        0.0001,
    )

    if (
        not np.isfinite(volatility[index])
        or not np.isfinite(atr[index])
        or not np.isfinite(logret[index])
    ):
        raise ValueError(
            "Indikator belum siap pada candle terakhir."
        )

    X = []
    y = []

    for row_index in range(training):
        target_index = index - training + 1 + row_index
        feature_index = target_index - 1

        if (
            feature_index < 1
            or not np.isfinite(logret[target_index])
        ):
            continue

        X.append([
            logret[feature_index] / vol_ref,
            momentum[feature_index] / vol_ref,
            rel_volume[feature_index],
            (
                volatility[feature_index] / vol_ref - 1.0
                if np.isfinite(volatility[feature_index])
                else 0.0
            ),
            direction[feature_index] / vol_ref,
        ])

        y.append(logret[target_index])

    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)

    sample_count = len(y)

    if sample_count < max(20, training - 3):
        raise ValueError(
            "Observasi training valid terlalu sedikit."
        )

    signal_var = max(float(np.mean(y * y)), 1e-8)
    noise_var = signal_var * noise_ratio + 1e-10

    kernel_matrix = np.empty(
        (sample_count, sample_count),
        dtype=float,
    )

    for i in range(sample_count):
        for j in range(i + 1):
            value = matern32_kernel(
                X[i], X[j], signal_var, kernel_scale
            )

            if i == j:
                value += noise_var

            kernel_matrix[i, j] = value
            kernel_matrix[j, i] = value

    try:
        L = np.linalg.cholesky(kernel_matrix)

        alpha = np.linalg.solve(
            L.T,
            np.linalg.solve(L, y),
        )

    except np.linalg.LinAlgError:
        raise ValueError(
            "Matriks GPR tidak stabil untuk data ini."
        )

    price_start = float(close[index])
    price_previous = price_start
    return_previous = float(logret[index])
    momentum_previous = float(momentum[index])
    fast_previous = float(fast[index])
    slow_previous = float(slow[index])
    volume_previous = float(rel_volume[index])

    volatility_previous = (
        float(volatility[index])
        if np.isfinite(volatility[index])
        else vol_ref
    )

    cumulative_return = 0.0
    cumulative_variance = 0.0

    predictions = []
    future_features = []
    solved_future = []

    for step in range(horizon):
        fade = volume_fade ** step

        assumed_volatility = (
            vol_ref
            + (volatility_previous - vol_ref) * fade
        )

        future_feature = np.array([
            return_previous / vol_ref,
            momentum_previous / vol_ref,
            volume_previous * fade,
            assumed_volatility / vol_ref - 1.0,
            (
                (fast_previous - slow_previous)
                / max(price_previous, 1e-12)
            ) / vol_ref,
        ])

        future_features.append(future_feature)

        kernel_star = np.array([
            matern32_kernel(
                X[i],
                future_feature,
                signal_var,
                kernel_scale,
            )
            for i in range(sample_count)
        ])

        predicted_return = float(kernel_star @ alpha)

        if band_mode == "GPR":
            solved = np.linalg.solve(L, kernel_star)

            own_variance = max(
                signal_var
                + noise_var
                - float(solved @ solved),
                0.0,
            )

            cross_sum = 0.0

            for j in range(step):
                cross = matern32_kernel(
                    future_feature,
                    future_features[j],
                    signal_var,
                    kernel_scale,
                ) - float(solved @ solved_future[j])

                cross_sum += cross

            cumulative_variance = max(
                cumulative_variance
                + own_variance
                + 2.0 * cross_sum,
                0.0,
            )

            solved_future.append(solved)

        cumulative_return += predicted_return

        predicted_price = (
            price_start * math.exp(cumulative_return)
        )

        distance = (
            atr_width
            * float(atr[index])
            * math.sqrt(step + 1.0)
        )

        if band_mode == "GPR":
            upper = price_start * math.exp(
                cumulative_return
                + gpr_sigma_width * math.sqrt(cumulative_variance)
            )

            lower = price_start * math.exp(
                cumulative_return
                - gpr_sigma_width * math.sqrt(cumulative_variance)
            )
        else:
            upper = predicted_price + distance
            lower = max(0.0001, predicted_price - distance)

        predictions.append({
            "step": step + 1,
            "price": round(predicted_price, 4),
            "return_pct": round(
                (predicted_price / price_start - 1.0) * 100.0,
                3,
            ),
            "upper": round(upper, 4),
            "lower": round(lower, 4),
        })

        price_previous = predicted_price
        return_previous = predicted_return

        momentum_alpha = 2.0 / (momentum_len + 1.0)
        fast_alpha = 2.0 / (ema_fast + 1.0)
        slow_alpha = 2.0 / (ema_slow + 1.0)

        momentum_previous = (
            momentum_alpha * predicted_return
            + (1.0 - momentum_alpha) * momentum_previous
        )

        fast_previous = (
            fast_alpha * predicted_price
            + (1.0 - fast_alpha) * fast_previous
        )

        slow_previous = (
            slow_alpha * predicted_price
            + (1.0 - slow_alpha) * slow_previous
        )

    momentum_now = (
        float(momentum[index])
        if np.isfinite(momentum[index])
        else 0.0
    )

    volume_average = (
        float(avg_volume[index])
        if np.isfinite(avg_volume[index])
        else 0.0
    )

    final_prediction = predictions[-1]

    return {
        "price": round(float(close[index]), 4),
        "trend": "BULLISH" if fast[index] > slow[index] else "BEARISH",
        "momentum": "POSITIVE" if momentum_now > 0 else "NEGATIVE",
        "relative_volume": round(
            float(volume[index]) / volume_average, 2
        ) if volume_average > 0 else 0,
        "gpr_return_pct": final_prediction["return_pct"],
        "projected_price": final_prediction["price"],
        "upper": final_prediction["upper"],
        "lower": final_prediction["lower"],
        "horizon": horizon,
        "predictions": predictions,
        "as_of": str(dataframe.iloc[index].get("time", "")),
        "bars": len(dataframe),
    }


def get_history(code, timeframe="1d"):
    interval = {
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "1d": "1d",
    }.get(timeframe, "1d")

    return normalize_history(
        cached_get(
            f"history:{code}:{timeframe}",
            f"/api/history/{code}",
            {"interval": interval},
        )
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    codes, source = get_universe()

    return jsonify({
        "api_key_configured": bool(ARJUM_API_KEY),
        "provider": "Arjum",
        "universe_count": len(codes),
        "universe_source": source,
        "intraday_note": (
            "Dukungan timeframe intraday harus dikonfirmasi "
            "dari respons API Arjum."
        ),
        "status": "ready" if ARJUM_API_KEY else "needs_api_key",
    })


@app.route("/api/universe")
def universe():
    codes, source = get_universe(
        request.args.get("refresh") == "1"
    )

    return jsonify({
        "count": len(codes),
        "source": source,
        "codes": codes,
        "note": (
            "Daftar cadangan bukan daftar BEI lengkap. "
            "Jumlah kode bukan jaminan seluruh saham aktif."
        ),
    })


@app.route("/api/scan")
def scan():
    """
    Memproses maksimal 50 kode per permintaan.
    Frontend perlu mengirim offset 0, 50, 100, dan seterusnya.
    """
    timeframe = request.args.get("timeframe", "1d")
    horizon = max(
        1,
        min(int(request.args.get("horizon", 10)), 30),
    )

    limit = max(
        1,
        min(int(request.args.get("limit", 50)), 50),
    )

    offset = max(
        0,
        int(request.args.get("offset", 0)),
    )

    if not ARJUM_API_KEY:
        return jsonify({
            "error": "API Key belum diatur di backend.",
            "items": [],
        }), 400

    codes, source = get_universe()
    selected_codes = codes[offset:offset + limit]

    results = []
    errors = []
    started = time.time()

    for code in selected_codes:
        try:
            history = get_history(code, timeframe)

            if history.empty:
                errors.append({
                    "code": code,
                    "error": "Riwayat candle kosong/tidak dikenali",
                })
                continue

            result = gpr_project(
                history,
                horizon=horizon,
            )

            result["code"] = code

            bullish_score = (
                35 if result["trend"] == "BULLISH" else 0
            )

            momentum_score = (
                20 if result["momentum"] == "POSITIVE" else 0
            )

            volume_score = (
                20 * min(result["relative_volume"] / 2.0, 1.0)
            )

            return_score = (
                25 * max(
                    0,
                    min(result["gpr_return_pct"] / 5.0, 1.0),
                )
            )

            result["score"] = round(
                max(
                    0,
                    min(
                        100,
                        bullish_score
                        + momentum_score
                        + volume_score
                        + return_score,
                    ),
                ),
                1,
            )

            if (
                result["trend"] == "BULLISH"
                and result["momentum"] == "POSITIVE"
                and result["gpr_return_pct"] > 0
            ):
                result["signal"] = "KANDIDAT"

            elif result["gpr_return_pct"] > 0:
                result["signal"] = "PANTAU"

            else:
                result["signal"] = "HINDARI"

            results.append(result)

        except Exception as error:
            LOG.warning(
                "Gagal memproses %s: %s",
                code,
                str(error)[:180],
            )

            errors.append({
                "code": code,
                "error": str(error)[:180],
            })

    results.sort(
        key=lambda item: (
            item["score"],
            item["gpr_return_pct"],
        ),
        reverse=True,
    )

    return jsonify({
        "timeframe": timeframe,
        "horizon": horizon,
        "universe_source": source,
        "universe_count": len(codes),
        "offset": offset,
        "requested": len(selected_codes),
        "scanned": len(results),
        "errors_count": len(errors),
        "errors": errors[:25],
        "elapsed_seconds": round(time.time() - started, 2),
        "items": results,
    })


@app.route("/api/analyze/<code>")
def analyze(code):
    timeframe = request.args.get("timeframe", "1d")
    horizon = max(
        1,
        min(int(request.args.get("horizon", 10)), 30),
    )

    code = normalize_code(code)

    if not code:
        return jsonify({
            "error": "Kode saham tidak valid.",
        }), 400

    try:
        history = get_history(code, timeframe)

        if history.empty:
            return jsonify({
                "error": "Riwayat candle kosong/tidak dikenali.",
            }), 422

        result = gpr_project(
            history,
            horizon=horizon,
        )

        result["code"] = code

        result["history"] = [
            {
                "time": str(row.get("time", "")),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for _, row in history.tail(100).iterrows()
        ]

        return jsonify(result)

    except Exception as error:
        LOG.exception("Analisis %s gagal", code)

        return jsonify({
            "error": str(error),
        }), 400


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )
