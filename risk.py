# risk.py
from __future__ import annotations
from typing import Dict, Any, List, Optional

# ---------- Helpers de datos ----------
def _get_prior(supabase, disease: str, month: int) -> Optional[float]:
    resp = supabase.table("disease_prior") \
        .select("prior") \
        .eq("disease", disease) \
        .eq("month", month) \
        .limit(1).execute()
    rows = resp.data or []
    return float(rows[0]["prior"]) if rows else None

def _get_weather(supabase, region_id: str, year: int, month: int) -> Dict[str, Any]:
    resp = supabase.table("weather_monthly") \
        .select("t_mean_c,rh_mean,rain_days,leaf_wet_hours,cloudy_days") \
        .eq("region_id", region_id).eq("year", year).eq("month", month) \
        .limit(1).execute()
    return (resp.data or [{}])[0]

def _get_factors(supabase, region_id: str, year: int, month: int) -> Dict[str, Any]:
    resp = supabase.table("farm_factors") \
        .select("shade_level,leftover_fruit,defoliation_prev") \
        .eq("region_id", region_id).eq("year", year).eq("month", month) \
        .limit(1).execute()
    return (resp.data or [{}])[0]

def _cat(v: float) -> str:
    if v >= 0.66: return "Alto"
    if v >= 0.33: return "Medio"
    return "Bajo"

def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))

# ---------- Multiplicadores por enfermedad ----------
def _mult_roya(w: Dict[str, Any], f: Dict[str, Any]) -> (float, List[str]):
    drivers = []
    m = 1.0
    t = w.get("t_mean_c"); rh = w.get("rh_mean"); wet = w.get("leaf_wet_hours"); rain = w.get("rain_days")
    shade = (f.get("shade_level") or "").lower()

    if t is not None:
        if 20 <= t <= 25: m *= 1.15; drivers.append(f"T óptima {t:.0f}°C")
        elif t >= 30: m *= 0.85
        elif t < 17: m *= 0.90
    if rh is not None:
        if rh >= 80: m *= 1.10; drivers.append(f"HR {rh:.0f}%")
        elif rh < 60: m *= 0.90
    if wet is not None:
        if wet >= 6: m *= 1.10; drivers.append(f"Mojado foliar {wet}h")
    if rain is not None and rain >= 10:
        m *= 1.05; drivers.append(f"{rain} días lluvia")
    if shade == "alta":
        m *= 1.08; drivers.append("Sombra alta")

    return m, drivers

def _mult_broca(w: Dict[str, Any], f: Dict[str, Any]) -> (float, List[str]):
    drivers = []
    m = 1.0
    t = w.get("t_mean_c"); rh = w.get("rh_mean"); rain = w.get("rain_days")
    shade = (f.get("shade_level") or "").lower()
    leftover = bool(f.get("leftover_fruit") or False)

    if t is not None:
        if 20 <= t <= 27: m *= 1.12; drivers.append(f"T favorable {t:.0f}°C")
        elif t < 18: m *= 0.88
    if rh is not None and rh >= 80:
        m *= 1.06; drivers.append(f"HR {rh:.0f}%")
    if rain is not None and rain >= 8:
        m *= 1.08; drivers.append(f"{rain} días lluvia (vuelos)")
    if shade == "alta": m *= 1.04
    if leftover: 
        m *= 1.10; drivers.append("Fruto remanente")

    return m, drivers

def _mult_ojogallo(w: Dict[str, Any], f: Dict[str, Any]) -> (float, List[str]):
    drivers = []
    m = 1.0
    t = w.get("t_mean_c"); rh = w.get("rh_mean"); wet = w.get("leaf_wet_hours"); rain = w.get("rain_days")
    shade = (f.get("shade_level") or "").lower()

    if t is not None:
        if 17 <= t <= 23: m *= 1.12; drivers.append(f"T fresca {t:.0f}°C")
        elif t >= 28: m *= 0.85
    if rh is not None and rh >= 85:
        m *= 1.10; drivers.append(f"HR {rh:.0f}%")
    if wet is not None and wet >= 6:
        m *= 1.08; drivers.append(f"Mojado {wet}h")
    if rain is not None and rain >= 12:
        m *= 1.05
    if shade == "alta":
        m *= 1.10; drivers.append("Sombra alta")

    return m, drivers

def _mult_antracnosis(w: Dict[str, Any], f: Dict[str, Any]) -> (float, List[str]):
    drivers = []
    m = 1.0
    t = w.get("t_mean_c"); rh = w.get("rh_mean"); rain = w.get("rain_days")
    defol = bool(f.get("defoliation_prev") or False)

    if t is not None and 20 <= t <= 25:
        m *= 1.10; drivers.append(f"T {t:.0f}°C")
    if rh is not None and rh >= 85:
        m *= 1.08; drivers.append(f"HR {rh:.0f}%")
    if rain is not None and rain >= 10:
        m *= 1.06; drivers.append(f"{rain} días lluvia")
    if defol:
        m *= 1.10; drivers.append("Defoliación previa")

    return m, drivers

# ---------- Cálculo por mes ----------
def _compute_one(supabase, region_id: str, year: int, month: int, disease: str) -> Dict[str, Any]:
    prior = _get_prior(supabase, disease, month)
    w = _get_weather(supabase, region_id, year, month)
    f = _get_factors(supabase, region_id, year, month)

    if prior is None:
        # sin prior → no hay base estacional
        return {"disease": disease, "risk": 0.0, "category": "Bajo", "uncertainty": 1.0, "drivers": ["Sin prior"]}

    # elige multiplicadores
    if disease == "roya":      mult, drivers = _mult_roya(w, f)
    elif disease == "broca":   mult, drivers = _mult_broca(w, f)
    elif disease == "ojogallo":mult, drivers = _mult_ojogallo(w, f)
    else:                      mult, drivers = _mult_antracnosis(w, f)

    risk = _clip01(prior * mult)

    # incertidumbre simple: si faltan variables clave, sube
    missing = 0; total = 5
    for k in ("t_mean_c","rh_mean","rain_days","leaf_wet_hours"):
        if w.get(k) is None: missing += 1
    if f.get("shade_level") is None: missing += 1
    uncertainty = _clip01(0.2 + 0.15*missing)  # base 0.2 + 0.15 por falta

    return {
        "disease": disease,
        "risk": risk,
        "category": _cat(risk),
        "uncertainty": uncertainty,
        "drivers": drivers or []
    }

def risk_json(supabase, region_id: str, year: int, month: int) -> Dict[str, Any]:
    diseases = ["roya","broca","ojogallo","antracnosis"]
    results = [_compute_one(supabase, region_id, year, month, d) for d in diseases]
    return {
        "region_id": region_id,
        "year": year,
        "month": month,
        "results": results
    }

def risk_series_json(supabase, region_id: str, year: int) -> List[Dict[str, Any]]:
    out = []
    for m in range(1, 13):
        out.append(risk_json(supabase, region_id, year, m))
    return out
