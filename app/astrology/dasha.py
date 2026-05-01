"""
Vimshottari Dasha system — 120-year cycle based on Moon's Nakshatra at birth.
Computes Mahadasha, Antardasha (Bhukti), and Pratyantardasha (Prana).
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math

DASHA_SEQUENCE = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]

DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10,
    "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

TOTAL_YEARS = 120

PLANET_COLORS = {
    "Sun": "#FF6B35", "Moon": "#C0C0C0", "Mars": "#FF4444",
    "Mercury": "#00CC88", "Jupiter": "#FFD700", "Venus": "#FF69B4",
    "Saturn": "#6B7280", "Rahu": "#8B5CF6", "Ketu": "#EC4899",
}

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
    "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
    "Sun", "Moon", "Mars", "Rahu", "Jupiter",
    "Saturn", "Mercury",
]

NAK_SPAN = 360 / 27  # 13.333...°


def _years_to_timedelta(years_decimal: float) -> timedelta:
    """Convert fractional years to a timedelta (365.25 days/year)."""
    return timedelta(days=years_decimal * 365.25)


def _fraction_elapsed(moon_longitude: float) -> float:
    """Fraction of current nakshatra already elapsed at birth."""
    nak_idx = int(moon_longitude / NAK_SPAN)
    nak_start = nak_idx * NAK_SPAN
    elapsed_in_nak = moon_longitude - nak_start
    return elapsed_in_nak / NAK_SPAN


def calculate_vimshottari(moon_longitude: float, birth_dt: datetime) -> dict:
    """
    Full Vimshottari Dasha tree.
    Returns: birth nakshatra info, dasha balance at birth,
             list of all Mahadashas with nested Antardashas.
    """
    nak_idx = int(moon_longitude / NAK_SPAN)
    fraction_elapsed = _fraction_elapsed(moon_longitude)

    birth_lord = NAKSHATRA_LORDS[nak_idx]
    birth_lord_total = DASHA_YEARS[birth_lord]

    # Balance of birth Mahadasha
    balance_years = birth_lord_total * (1 - fraction_elapsed)
    balance_start = birth_dt
    balance_end   = birth_dt + _years_to_timedelta(balance_years)

    mahadashas = []
    current = birth_dt
    lord_idx = DASHA_SEQUENCE.index(birth_lord)

    for i in range(9):
        maha_lord = DASHA_SEQUENCE[(lord_idx + i) % 9]
        if i == 0:
            maha_years = balance_years
        else:
            maha_years = DASHA_YEARS[maha_lord]

        maha_end = current + _years_to_timedelta(maha_years)

        antardashas = _calc_antardashas(maha_lord, current, maha_years, birth_dt)

        mahadashas.append({
            "lord": maha_lord,
            "years": round(maha_years, 4),
            "start": current.strftime("%d %b %Y"),
            "end": maha_end.strftime("%d %b %Y"),
            "start_dt": current.isoformat(),
            "end_dt": maha_end.isoformat(),
            "color": PLANET_COLORS.get(maha_lord, "#FFFFFF"),
            "is_current": current <= datetime.now() < maha_end,
            "antardashas": antardashas,
        })
        current = maha_end

    # Current Dasha / Antardasha / Pratyantardasha
    current_maha = next((m for m in mahadashas if m["is_current"]), None)
    current_antar = None
    current_pratyantar = None
    if current_maha:
        now = datetime.now()
        for a in current_maha["antardashas"]:
            a_start = datetime.fromisoformat(a["start_dt"])
            a_end   = datetime.fromisoformat(a["end_dt"])
            if a_start <= now < a_end:
                current_antar = a
                current_pratyantar = _current_pratyantar(a, now)
                break

    return {
        "birth_lord": birth_lord,
        "birth_nakshatra_idx": nak_idx,
        "balance_years": round(balance_years, 4),
        "balance_months": round(balance_years * 12, 2),
        "balance_days": int(balance_years * 365.25),
        "mahadashas": mahadashas,
        "current_maha": current_maha,
        "current_antar": current_antar,
        "current_pratyantar": current_pratyantar,
    }


def _calc_antardashas(maha_lord: str, maha_start: datetime, maha_years: float, birth_dt: datetime) -> list:
    """Compute 9 Antardashas (Bhuktis) within a Mahadasha."""
    antars = []
    lord_idx = DASHA_SEQUENCE.index(maha_lord)
    current = maha_start
    total = DASHA_YEARS[maha_lord]

    for i in range(9):
        antar_lord = DASHA_SEQUENCE[(lord_idx + i) % 9]
        antar_years = maha_years * (DASHA_YEARS[antar_lord] / TOTAL_YEARS)
        antar_end = current + _years_to_timedelta(antar_years)
        now = datetime.now()
        antars.append({
            "lord": antar_lord,
            "years": round(antar_years, 4),
            "months": round(antar_years * 12, 2),
            "start": current.strftime("%d %b %Y"),
            "end": antar_end.strftime("%d %b %Y"),
            "start_dt": current.isoformat(),
            "end_dt": antar_end.isoformat(),
            "color": PLANET_COLORS.get(antar_lord, "#FFFFFF"),
            "is_current": current <= now < antar_end,
            "pratyantardashas": _calc_pratyantardashas(antar_lord, current, antar_years),
        })
        current = antar_end

    return antars


def _calc_pratyantardashas(antar_lord: str, antar_start: datetime, antar_years: float) -> list:
    """Compute 9 Pratyantardashas within an Antardasha."""
    pratys = []
    lord_idx = DASHA_SEQUENCE.index(antar_lord)
    current = antar_start
    now = datetime.now()

    for i in range(9):
        lord = DASHA_SEQUENCE[(lord_idx + i) % 9]
        years = antar_years * (DASHA_YEARS[lord] / TOTAL_YEARS)
        end = current + _years_to_timedelta(years)
        days = int(years * 365.25)
        pratys.append({
            "lord": lord,
            "days": days,
            "start": current.strftime("%d %b %Y"),
            "end": end.strftime("%d %b %Y"),
            "start_dt": current.isoformat(),
            "end_dt": end.isoformat(),
            "color": PLANET_COLORS.get(lord, "#FFFFFF"),
            "is_current": current <= now < end,
        })
        current = end

    return pratys


def _current_pratyantar(antar: dict, now: datetime) -> dict | None:
    for p in antar.get("pratyantardashas", []):
        ps = datetime.fromisoformat(p["start_dt"])
        pe = datetime.fromisoformat(p["end_dt"])
        if ps <= now < pe:
            return p
    return None


def dasha_summary(moon_longitude: float, birth_dt: datetime) -> dict:
    """Quick summary: current running Maha/Antar/Pratyantar."""
    data = calculate_vimshottari(moon_longitude, birth_dt)
    return {
        "mahadasha":      data["current_maha"]["lord"]          if data["current_maha"]      else "N/A",
        "antardasha":     data["current_antar"]["lord"]         if data["current_antar"]     else "N/A",
        "pratyantardasha": data["current_pratyantar"]["lord"]   if data["current_pratyantar"] else "N/A",
        "maha_end":       data["current_maha"]["end"]           if data["current_maha"]      else "N/A",
        "antar_end":      data["current_antar"]["end"]          if data["current_antar"]     else "N/A",
        "maha_color":     data["current_maha"]["color"]         if data["current_maha"]      else "#FFF",
        "antar_color":    data["current_antar"]["color"]        if data["current_antar"]     else "#FFF",
    }
