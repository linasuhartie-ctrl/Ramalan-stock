import os
import math
import time
import logging
from typing import Any

import requests
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("gpr-scanner")

ARJUM_BASE_URL = os.getenv(
    "ARJUM_BASE_URL",
    "https://stock.arjum.com"
).rstrip("/")

ARJUM_API_KEY = os.getenv("ARJUM_API_KEY", "").strip()

REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "15"))
CACHE_SECONDS = int(os.getenv("CACHE_SECONDS", "90"))
MAX_BATCH_SIZE = 50

DEFAULT_CODES = [
    "AADI", "AALI", "ABBA", "ABDA", "ABMM", "ACES", "ACRO",
    "ACST", "ADCP", "ADES", "ADHI", "ADMF", "ADMG", "ADMR",
    "ADRO", "AEGS", "AGAR", "AGII", "AGRO", "AHAP", "AIMS",
    "AISA", "AKKU", "AKPI", "AKRA", "AKSI", "ALDO", "ALKA",
    "ALMI", "ALTO", "AMAG", "AMAN", "AMAR", "AMFG", "AMIN",
    "AMMN", "AMMS", "AMOR", "AMRT", "ANDI", "ANJT", "ANTM",
    "APEX", "APIC", "APII", "APLI", "APLN", "ARCI", "AREA",
    "ARGO", "ARII", "ARKA", "ARKO", "ARMY", "ARNA", "ARTA",
    "ARTI", "ARTO", "ASBI", "ASDM", "ASGR", "ASHA", "ASII",
    "ASJT", "ASLC", "ASLI", "ASMI", "ASPI", "ASPR", "ASRI",
    "ASSA", "ATAP", "ATIC", "ATLA", "AUTO", "AVIA", "AWAN",
    "AXIO", "AYAM", "AYLS", "BABP", "BACA", "BAJA", "BALI",
    "BANK", "BAPA", "BAPI", "BATA", "BATR", "BAUT", "BAYU",
    "BBCA", "BBHI", "BBKP", "BBLD", "BBMD", "BBNI", "BBRI",
    "BBRM", "BBSI", "BBTN", "BBYB", "BCAP", "BCIC", "BCIP",
    "BDMN", "BEBS", "BEEF", "BEER", "BEKS", "BELI", "BELL",
    "BESS", "BEST", "BFIN", "BGTG", "BHAT", "BHIT", "BIKA",
    "BIMA", "BINA", "BINO", "BIPP", "BIRD", "BISI", "BJBR",
    "BJTM", "BKDP", "BKSL", "BKSW", "BLTA", "BLTZ", "BLUE",
    "BMAS", "BMBL", "BMHS", "BMRI", "BMSR", "BMTR", "BNBA",
    "BNBR", "BNGA", "BNII", "BNLI", "BOAT", "BOBA", "BOGA",
    "BOLA", "BOLT", "BOSS", "BPFI", "BPII", "BPTR", "BRAM",
    "BRIS", "BRMS", "BRNA", "BRPT", "BRRC", "BSBK", "BSDE",
    "BSIM", "BSML", "BSSR", "BSWD", "BTEK", "BTEL", "BTON",
    "BTPN", "BTPS", "BUAH", "BUDI", "BUKA", "BUKK", "BULL",
    "BUMI", "BUVA", "BVIC", "BWPT", "BYAN", "CAKK", "CAMP",
    "CANI", "CARE", "CARS", "CASA", "CASH", "CASS", "CBDK",
    "CBMF", "CBPE", "CBRE", "CCSI", "CEKA", "CENT", "CFIN",
    "CHEM", "CHIP", "CINT", "CITA", "CITY", "CLAY", "CLEO",
    "CLPI", "CMNP", "CMNT", "CMPP", "CMRY", "CNKO", "CNTX",
    "COAL", "COCO", "COIN", "COWL", "CPIN", "CPRO", "CRAB",
    "CSAP", "CSIS", "CSMI", "CSRA", "CTBN", "CTRA", "CTTH",
    "CUAN", "CYBR", "DADA", "DART", "DATA", "DAYA", "DCII",
    "DEAL", "DEFI", "DEPO", "DEWA", "DEWI", "DFAM", "DGIK",
    "DGNS", "DGWG", "DIGI", "DILD", "DIVA", "DKFT", "DLTA",
    "DMAS", "DMMX", "DMND", "DNAR", "DNET", "DOID", "DOOH",
    "DRMA", "DSFI", "DSNG", "DSSA", "DUTI", "DVLA", "DWGL",
    "DYAN", "EAST", "ECII", "EDGE", "EKAD", "ELIT", "ELPI",
    "ELSA", "ELTY", "EMDE", "EMTK", "ENAK", "ENRG", "ENVY",
    "EPAC", "EPMT", "ERAA", "ERAL", "ERTX", "ESIP", "ESSA",
    "ESTA", "ESTI", "ETWA", "EURO", "EXCL", "FAPA", "FASW",
    "FILM", "FIMP", "FIRE", "FISH", "FIT", "FITT", "FLMC",
    "FMII", "FOLK", "FOOD", "FORU", "FORZ", "FPNI", "FREN",
    "FUJI", "FUTR", "FWCT", "GAMA", "GDST", "GDYR", "GEMA",
    "GEMS", "GGRM", "GGRP", "GHON", "GIAA", "GJTL", "GLVA",
    "GMFI", "GMTD", "GOLF", "GOOD", "GOTO", "GPRA", "GPSO",
    "GTRA", "GTSI", "GULA", "GUNA", "GWSA", "GZCO", "HADE",
    "HAIS", "HAJJ", "HATM", "HBAT", "HDFA", "HDIT", "HEAL",
    "HELI", "HERO", "HGII", "HILL", "HITS", "HKMU", "HMSP",
    "HOKI", "HOME", "HOPE", "HOTL", "HRME", "HRTA", "HRUM",
    "HUMI", "HYGN", "IATA", "IBFN", "IBOS", "IBST", "ICBP",
    "ICON", "IDEA", "IDPR", "IFII", "IFSH", "IGAR", "IIKP",
    "IKAI", "IKAN", "IKBI", "IKPM", "IMAS", "IMJS", "IMPC",
    "INAI", "INCF", "INCI", "INCO", "INDO", "INDR", "INDS",
    "INDX", "INDY", "INET", "INKP", "INOV", "INPC", "INPP",
    "INPS", "INRU", "INTA", "INTD", "INTP", "IOTF", "IPAC",
    "IPCC", "IPCM", "IPOL", "IPPE", "IPTV", "IRRA", "IRSX",
    "ISAT", "ISSP", "ITIC", "ITMA", "ITMG", "JARR", "JAST",
    "JATI", "JAYA", "JECC", "JGLE", "JIHD", "JKON", "JMAS",
    "JPFA", "JRPT", "JSKY", "JSMR", "JSPT", "JTPE", "KAEF",
    "KARW", "KAYU", "KBAG", "KBLI", "KBLM", "KBLV", "KBRI",
    "KDSI", "KDTN", "KEEN", "KEJU", "KIJA", "KING", "KINO",
    "KIOS", "KKGI", "KLBF", "KMDS", "KMTR", "KOBX", "KOIN",
    "KONI", "KOPI", "KPIG", "KREN", "KRYA", "LABA", "LAJU",
    "LAND", "LAPD", "LCAS", "LCKM", "LEAD", "LINK", "LMAS",
    "LMPI", "LOPI", "LPCK", "LPKR", "LPPF", "LRNA", "LSIP",
    "LTLS", "LUCY", "MAGP", "MAIN", "MAPA", "MAPB", "MAPI",
    "MARK", "MASA", "MASB", "MAYA", "MBAP", "MBSS", "MBTO",
    "MCAS", "MCOI", "MDIA", "MDKA", "MDKI", "MDLN", "MDRN",
    "MEDC", "MEGA", "MERK", "META", "MFMI", "MGNA", "MGRO",
    "MICE", "MIDI", "MIKA", "MINA", "MIRA", "MITI", "MKNT",
    "MKPI", "MLBI", "MLIA", "MLPL", "MLPT", "MMLP", "MMSI",
    "MNCN", "MPPA", "MPRO", "MREI", "MSIN", "MTDL", "MTEL",
    "MTLA", "MTMH", "MTPS", "MTRA", "MTSM", "MTWI", "MULT",
    "MYOH", "MYOR", "MYTX", "NASI", "NATO", "NELY", "NEST",
    "NETV", "NFCX", "NICL", "NIKL", "NIPS", "NITRO", "NISP",
    "NICE", "NOBU", "NRCA", "NSSS", "NUSA", "OASA", "OBMD",
    "OCAP", "OKAS", "OMRE", "OPMS", "PADI", "PALM", "PAMG",
    "PANI", "PANR", "PANS", "PBID", "PBRX", "PBSA", "PCAR",
    "PDES", "PEGE", "PEHA", "PGAS", "PGEO", "PGLI", "PGUN",
    "PICO", "PJAA", "PKPK", "PLAN", "PLIN", "PMJS", "PMMP",
    "PMUI", "PNBN", "PNGO", "PNIN", "PNSE", "POLA", "POLI",
    "POLL", "POLU", "PORT", "POWR", "PPGL", "PPRE", "PPRO",
    "PRDA", "PRIM", "PSAB", "PSAT", "PSDN", "PSKT", "PTPP",
    "PUDP", "PURA", "PURE", "PWON", "PYFA", "RALS", "RANC",
    "RBMS", "RDTX", "REAL", "RELI", "RICY", "RIGS", "RISE",
    "RMBA", "RMKE", "ROCK", "RODA", "ROTI", "RUCI", "RUNS",
    "SAFE", "SAME", "SAMF", "SAPX", "SATU", "SBAT", "SBCS",
    "SBMA", "SCCO", "SCMA", "SCNP", "SDMU", "SDPC", "SDRA",
    "SGER", "SGRO", "SHID", "SHIP", "SICO", "SIDO", "SILO",
    "SIMA", "SIMP", "SIPD", "SKBM", "SKLT", "SKRN", "SLIS",
    "SMAR", "SMBR", "SMCB", "SMDM", "SMDR", "SMGA", "SMGR",
    "SMIL", "SMKL", "SMKM", "SMMT", "SMRA", "SMSM", "SNLK",
    "SOCI", "SOFA", "SOHO", "SOSS", "SOTS", "SPMA", "SPTO",
    "SQMI", "SRAJ", "SRTG", "SSIA", "SSMS", "SSTM", "STAR",
    "STTP", "SUNI", "SUPR", "SURE", "SWAT", "SWID", "TALE",
    "TAMU", "TBIG", "TBLA", "TBMS", "TCID", "TCPI", "TDPM",
    "TELE", "TFAS", "TGKA", "TGRA", "TIFA", "TINS", "TIRA",
    "TKIM", "TLKM", "TMAS", "TMPO", "TNCA", "TOBA", "TOPS",
    "TOTL", "TOTO", "TOWR", "TPIA", "TPMA", "TRGU", "TRIL",
    "TRIM", "TRIN", "TRIO", "TRIS", "TRJA", "TRON", "TRUE",
    "TSPC", "TUGU", "TYRE", "UANG", "UCID", "ULTJ", "UNIC",
    "UNIT", "UNTR", "UNVR", "VICI", "VINS", "VKTR", "VRNA",
    "WAPO", "WEGE", "WEHA", "WIFI", "WIIM", "WIKA", "WINE",
    "WINS", "WIRG", "WMUU", "WTON", "YPAS", "ZATA", "ZBRA",
    "ZINC", "ZONE"
]

_cache: dict[str, tuple[float, Any]] = {}


def arjum_get(path: str, params: dict | None = None):
    if not ARJUM_API_KEY:
        raise RuntimeError("API Key belum diatur di SnapDeploy.")

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


def cached_get(key: str, path: str, params: dict | None = None):
    now = time.time()
    cached = _cache.get(key)

    if cached and now - cached[0] < CACHE_SECONDS:
        return cached[1]

    result = arjum_get(path, params)
    _cache[key] = (now, result)
    return result


def extract_rows(payload):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in (
            "data", "results", "history", "candles",
            "items", "stocks", "screener"
        ):
            value = payload.get(key)
            if isinstance(value, list):
                return value

        for value in payload.values():
            if isinstance(value, list) and value:
                if isinstance(value[0], dict):
                    return value

    return []


def normalize_history(payload) -> pd.DataFrame:
    rows = extract_rows(payload)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    aliases = {
        "time": ["time", "date", "datetime", "timestamp", "t"],
        "open": ["open", "o", "Open"],
        "high": ["high", "h", "High"],
        "low": ["low", "l", "Low"],
        "close": ["close", "c", "Close", "price"],
        "volume": ["volume", "vol", "v", "Volume"],
    }

    rename = {}

    for standard, candidates in aliases.items():
        for candidate in candidates:
            if candidate in df.columns:
                rename[candidate] = standard
                break

    df = df.rename(columns=rename)

    if "close" not in df.columns:
        return pd.DataFrame()

    for column in ("open", "high", "low"):
        if column not in df.columns:
            df[column] = df["close"]

    if "volume" not in df.columns:
        df["volume"] = 0.0

    if "time" in df.columns:
        df["time"] = pd.to_datetime(
            df["time"], errors="coerce", utc=True
        )
        df = df.sort_values("time")

    for column in ("open", "high", "low", "close", "volume"):
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["close"]).reset_index(drop=True)
    return df


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(
        span=length, adjust=False, min_periods=1
    ).mean()


def matern32_kernel(
    x: np.ndarray,
    z: np.ndarray,
    amplitude: float,
    scale: float
) -> float:
    d = x - z

    distance2 = (
        d[0] ** 2
        + 0.8 * d[1] ** 2
        + 0.6 * d[2] ** 2
        + 0.8 * d[3] ** 2
        + 0.6 * d[4] ** 2
    )

    u = math.sqrt(3.0 * max(float(distance2), 0.0)) / scale
    return amplitude * (1.0 + u) * math.exp(-u)


def gpr_project(
    df: pd.DataFrame,
    horizon: int = 10,
    training: int = 30,
    momentum_len: int = 5,
    vol_len: int = 14,
    ema_fast: int = 8,
    ema_slow: int = 21,
    kernel_scale: float = 1.5,
    noise_ratio: float = 0.30,
    volume_fade: float = 0.65,
    band_mode: str = "ATR",
    atr_width: float = 0.70,
    gpr_sigma_width: float = 1.96,
):
    min_needed = max(training + vol_len + ema_slow + 10, 60)

    if len(df) < min_needed:
        raise ValueError(
            f"Data historis belum cukup: {len(df)} candle; "
            f"perlu sekitar {min_needed}."
        )

    close = df["close"].astype(float).to_numpy()
    volume = df["volume"].fillna(0).astype(float).to_numpy()

    logret = np.full(len(close), np.nan)
    logret[1:] = np.log(
        np.maximum(close[1:], 1e-12)
        / np.maximum(close[:-1], 1e-12)
    )

    ret_series = pd.Series(logret)

    momentum = ret_series.ewm(
        span=momentum_len, adjust=False, min_periods=1
    ).mean().to_numpy()

    volatility = ret_series.rolling(
        vol_len, min_periods=vol_len
    ).std(ddof=1).to_numpy()

    vol_base = pd.Series(volatility).rolling(
        training, min_periods=training
    ).mean().to_numpy()

    avg_volume = pd.Series(volume).rolling(
        vol_len, min_periods=1
    ).mean().to_numpy()

    rel_volume = np.zeros(len(close))
    valid = (volume > 0) & (avg_volume > 0)
    rel_volume[valid] = np.log(
        volume[valid] / avg_volume[valid]
    )

    fast = ema(pd.Series(close), ema_fast).to_numpy()
    slow = ema(pd.Series(close), ema_slow).to_numpy()
    direction = (fast - slow) / np.maximum(close, 1e-12)

    high = df["high"].astype(float).to_numpy()
    low = df["low"].astype(float).to_numpy()
    prev_close = np.r_[np.nan, close[:-1]]

    tr = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - prev_close),
            np.abs(low - prev_close)
        )
    )
    tr[0] = high[0] - low[0]

    atr = pd.Series(tr).ewm(
        alpha=1 / vol_len,
        adjust=False,
        min_periods=vol_len
    ).mean().to_numpy()

    idx = len(df) - 1

    vol_ref = max(
        float(vol_base[idx])
        if np.isfinite(vol_base[idx]) else 0.0,
        0.0001
    )

    if (
        not np.isfinite(volatility[idx])
        or not np.isfinite(atr[idx])
        or not np.isfinite(logret[idx])
    ):
        raise ValueError("Indikator belum siap pada candle terakhir.")

    X, y = [], []

    for r in range(training):
        target_idx = idx - training + 1 + r
        feature_idx = target_idx - 1

        if feature_idx < 1 or not np.isfinite(logret[target_idx]):
            continue

        X.append([
            logret[feature_idx] / vol_ref,
            momentum[feature_idx] / vol_ref,
            rel_volume[feature_idx],
            (
                volatility[feature_idx] / vol_ref - 1.0
            ) if np.isfinite(volatility[feature_idx]) else 0.0,
            direction[feature_idx] / vol_ref,
        ])

        y.append(logret[target_idx])

    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(y)

    if n < max(20, training - 3):
        raise ValueError("Observasi training valid terlalu sedikit.")

    signal_var = max(float(np.mean(y * y)), 1e-8)
    noise_var = signal_var * noise_ratio + 1e-10

    K = np.empty((n, n), dtype=float)

    for i in range(n):
        for j in range(i + 1):
            value = matern32_kernel(
                X[i], X[j], signal_var, kernel_scale
            )

            if i == j:
                value += noise_var

            K[i, j] = K[j, i] = value

    try:
        L = np.linalg.cholesky(K)
        alpha = np.linalg.solve(
            L.T, np.linalg.solve(L, y)
        )
    except np.linalg.LinAlgError:
        raise ValueError("Matriks GPR tidak stabil untuk data ini.")

    price_start = float(close[idx])
    price_prev = price_start
    ret_prev = float(logret[idx])
    mom_prev = float(momentum[idx])
    fast_prev = float(fast[idx])
    slow_prev = float(slow[idx])
    volume_prev = float(rel_volume[idx])
    vol_prev = (
        float(volatility[idx])
        if np.isfinite(volatility[idx]) else vol_ref
    )

    cumulative_return = 0.0
    cumulative_variance = 0.0
    predictions = []
    feature_future = []
    solved_future = []

    for h in range(horizon):
        fade = volume_fade ** h
        assumed_vol = vol_ref + (vol_prev - vol_ref) * fade

        feature_future.append(np.array([
            ret_prev / vol_ref,
            mom_prev / vol_ref,
            volume_prev * fade,
            assumed_vol / vol_ref - 1.0,
            (
                (fast_prev - slow_prev)
                / max(price_prev, 1e-12)
            ) / vol_ref,
        ]))

        x_star = feature_future[-1]

        kstar = np.array([
            matern32_kernel(
                X[i], x_star, signal_var, kernel_scale
            )
            for i in range(n)
        ])

        pred_ret = float(kstar @ alpha)

        if band_mode == "GPR":
            solved = np.linalg.solve(L, kstar)

            own_var = max(
                signal_var + noise_var - float(solved @ solved),
                0.0
            )

            cross_sum = 0.0

            for j in range(h):
                cross = matern32_kernel(
                    x_star,
                    feature_future[j],
                    signal_var,
                    kernel_scale
                )
                cross -= float(solved @ solved_future[j])
                cross_sum += cross

            cumulative_variance = max(
                cumulative_variance + own_var + 2.0 * cross_sum,
                0.0
            )

            solved_future.append(solved)

        cumulative_return += pred_ret
        price_pred = price_start * math.exp(cumulative_return)

        distance = atr_width * float(atr[idx]) * math.sqrt(h + 1.0)

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
            upper = price_pred + distance
            lower = max(0.0001, price_pred - distance)

        predictions.append({
            "step": h + 1,
            "price": round(price_pred, 4),
            "return_pct": round(
                (price_pred / price_start - 1.0) * 100.0, 3
            ),
            "upper": round(upper, 4),
            "lower": round(lower, 4),
        })

        price_prev = price_pred
        ret_prev = pred_ret

        a_m = 2.0 / (momentum_len + 1.0)
        mom_prev = a_m * pred_ret + (1.0 - a_m) * mom_prev

        a_f = 2.0 / (ema_fast + 1.0)
        a_s = 2.0 / (ema_slow + 1.0)

        fast_prev = a_f * price_pred + (1.0 - a_f) * fast_prev
        slow_prev = a_s * price_pred + (1.0 - a_s) * slow_prev

    latest_price = float(close[idx])
    trend = "BULLISH" if fast[idx] > slow[idx] else "BEARISH"

    mom_now = float(momentum[idx]) if np.isfinite(momentum[idx]) else 0.0
    vol_now = float(volume[idx])
    vol_avg = float(avg_volume[idx]) if np.isfinite(avg_volume[idx]) else 0.0
    rel_vol = vol_now / vol_avg if vol_avg > 0 else 0.0

    final = predictions[-1]

    return {
        "price": round(latest_price, 4),
        "trend": trend,
        "momentum": "POSITIVE" if mom_now > 0 else "NEGATIVE",
        "relative_volume": round(rel_vol, 2),
        "gpr_return_pct": final["return_pct"],
        "projected_price": final["price"],
        "upper": final["upper"],
        "lower": final["lower"],
        "horizon": horizon,
        "predictions": predictions,
        "as_of": str(df.iloc[idx].get("time", "")),
        "bars": len(df),
    }


def get_history(code: str, timeframe: str = "1d"):
    allowed = {"5m", "15m", "1h", "1d", "1wk", "1mo"}

    if timeframe not in allowed:
        timeframe = "1d"

    key = f"history:{code}:{timeframe}"

    return normalize_history(
        cached_get(
            key,
            f"/api/history/{code}",
            {"interval": timeframe}
        )
    )


def get_universe():
    """
    Tries the documented Arjum screener endpoint first.
    If the response schema cannot be recognized, uses the built-in seed list.
    The fallback list is not guaranteed to be the complete current IDX universe.
    """
    try:
        payload = cached_get(
            "universe",
            "/api/screener/latest"
        )

        rows = extract_rows(payload)
        codes = []

        for row in rows:
            if not isinstance(row, dict):
                continue

            code = (
                row.get("stock_code")
                or row.get("code")
                or row.get("symbol")
                or row.get("ticker")
            )

            if code:
                code = str(code).upper().replace(".JK", "").strip()

                if code.isalnum() and 4 <= len(code) <= 5:
                    codes.append(code)

        codes = list(dict.fromkeys(codes))

        if codes:
            return codes, "Arjum screener"

    except Exception as exc:
        LOG.warning("Arjum screener endpoint gagal: %s", exc)

    return DEFAULT_CODES, "fallback seed list (bukan seluruh BEI)"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify({
        "api_key_configured": bool(ARJUM_API_KEY),
        "provider": "Arjum",
        "status": "ready" if ARJUM_API_KEY else "needs_api_key",
        "max_batch_size": MAX_BATCH_SIZE,
    })


@app.route("/api/universe")
def universe_api():
    try:
        codes, source = get_universe()

        return jsonify({
            "count": len(codes),
            "source": source,
            "codes": codes,
            "is_complete": source == "Arjum screener",
            "message": (
                "Daftar berasal dari endpoint screener Arjum."
                if source == "Arjum screener"
                else "Daftar fallback bukan jaminan seluruh saham BEI."
            ),
        })

    except Exception as exc:
        LOG.exception("Universe endpoint gagal")

        return jsonify({
            "error": str(exc),
            "count": 0,
            "codes": [],
        }), 502


@app.route("/api/scan")
def scan():
    timeframe = request.args.get("timeframe", "1d")
    horizon = max(1, min(int(request.args.get("horizon", 10)), 30))

    try:
        requested_limit = max(
            1, min(int(request.args.get("limit", 50)), 1000)
        )
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        return jsonify({
            "error": "Parameter limit, offset, atau horizon tidak valid."
        }), 400

    if not ARJUM_API_KEY:
        return jsonify({
            "error": "API Key belum diatur di backend.",
            "items": [],
        }), 400

    universe, universe_source = get_universe()

    selected_codes = universe[offset:offset + min(requested_limit, MAX_BATCH_SIZE)]

    results = []
    errors = []

    for code in selected_codes:
        try:
            hist = get_history(code, timeframe)

            if hist.empty:
                errors.append({
                    "code": code,
                    "error": "Riwayat candle kosong/tidak dikenali",
                })
                continue

            result = gpr_project(hist, horizon=horizon)
            result["code"] = code

            result["score"] = round(
                max(0, min(100,
                    35 * (1 if result["trend"] == "BULLISH" else 0)
                    + 20 * (1 if result["momentum"] == "POSITIVE" else 0)
                    + 20 * min(result["relative_volume"] / 2.0, 1.0)
                    + 25 * max(
                        0, min(result["gpr_return_pct"] / 5.0, 1.0)
                    )
                )),
                1
            )

            result["signal"] = (
                "KANDIDAT"
                if result["trend"] == "BULLISH"
                and result["momentum"] == "POSITIVE"
                and result["gpr_return_pct"] > 0
                else "PANTAU"
                if result["gpr_return_pct"] > 0
                else "HINDARI"
            )

            results.append(result)

        except Exception as exc:
            errors.append({
                "code": code,
                "error": str(exc)[:180],
            })

    results.sort(
        key=lambda item: (
            item["score"],
            item["gpr_return_pct"]
        ),
        reverse=True
    )

    next_offset = offset + len(selected_codes)
    has_more = next_offset < len(universe)

    return jsonify({
        "timeframe": timeframe,
        "horizon": horizon,
        "universe_source": universe_source,
        "universe_count": len(universe),
        "requested": len(selected_codes),
        "offset": offset,
        "next_offset": next_offset,
        "has_more": has_more,
        "scanned": len(results),
        "errors_count": len(errors),
        "errors": errors[:12],
        "items": results,
    })


@app.route("/api/analyze/<code>")
def analyze(code):
    timeframe = request.args.get("timeframe", "1d")

    try:
        horizon = max(1, min(int(request.args.get("horizon", 10)), 30))
    except ValueError:
        return jsonify({"error": "Horizon tidak valid."}), 400

    try:
        hist = get_history(code.upper(), timeframe)

        if hist.empty:
            return jsonify({
                "error": "Riwayat candle kosong/tidak dikenali."
            }), 422

        result = gpr_project(hist, horizon=horizon)
        result["code"] = code.upper()

        history = []

        for _, row in hist.tail(100).iterrows():
            history.append({
                "time": str(row.get("time", "")),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })

        result["history"] = history

        return jsonify(result)

    except Exception as exc:
        LOG.exception("Analisis gagal untuk %s", code)

        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
