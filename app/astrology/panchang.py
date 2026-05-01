"""
Daily Panchang — the five limbs of the Hindu almanac.
Pancha = five, Anga = limb:
  1. Vara   — weekday & lord
  2. Tithi  — lunar day (1–30)
  3. Nakshatra — lunar mansion (1–27)
  4. Yoga  — Sun+Moon sum index (1–27)
  5. Karana — half-tithi (1–11, repeating)

Also computes: Rashi of Sun & Moon, Chandra Bala, Tarabala,
Sunrise, Sunset, Moonrise, Moonset, Rahu Kaal, Gulika Kaal,
Yamaghanta, day-length, and Abhijit Muhurta.
"""
import math
import swisseph as swe
from datetime import datetime, date
import pytz

from .calculator import (
    datetime_to_jd, get_planet_position, get_sunrise_sunset_moonrise,
    RASHI_NAMES, NAKSHATRA_NAMES, NAKSHATRA_LORDS,
    WEEKDAYS, WEEKDAY_LORDS,
)

swe.set_sid_mode(swe.SIDM_LAHIRI)

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
    "Purnima",           # 15 — Full Moon
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
    "Amavasya",          # 30 — New Moon
]

TITHI_PAKSHA = (["Shukla"] * 15) + (["Krishna"] * 15)

YOGA_NAMES = [
    "Vishkamba", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]

YOGA_NATURE = {
    "Vishkamba": "Inauspicious", "Priti": "Auspicious", "Ayushman": "Auspicious",
    "Saubhagya": "Auspicious", "Shobhana": "Auspicious", "Atiganda": "Inauspicious",
    "Sukarma": "Auspicious", "Dhriti": "Auspicious", "Shula": "Inauspicious",
    "Ganda": "Inauspicious", "Vriddhi": "Auspicious", "Dhruva": "Auspicious",
    "Vyaghata": "Inauspicious", "Harshana": "Auspicious", "Vajra": "Inauspicious",
    "Siddhi": "Auspicious", "Vyatipata": "Inauspicious", "Variyan": "Auspicious",
    "Parigha": "Inauspicious", "Shiva": "Auspicious", "Siddha": "Auspicious",
    "Sadhya": "Auspicious", "Shubha": "Auspicious", "Shukla": "Auspicious",
    "Brahma": "Auspicious", "Indra": "Auspicious", "Vaidhriti": "Inauspicious",
}

KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitula", "Garija",
    "Vanija", "Vishti",          # 7 movable karanas (repeat 8×)
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",  # 4 fixed karanas
]

KARANA_NATURE = {
    "Bava": "Auspicious", "Balava": "Auspicious", "Kaulava": "Auspicious",
    "Taitula": "Auspicious", "Garija": "Auspicious", "Vanija": "Auspicious",
    "Vishti": "Inauspicious (Bhadra)", "Shakuni": "Inauspicious",
    "Chatushpada": "Neutral", "Naga": "Inauspicious", "Kimstughna": "Auspicious",
}

# Tarabala — 27-star count from birth nakshatra
TARABALA_NAMES = [
    "Janma", "Sampat", "Vipat", "Kshema", "Pratyak",
    "Sadhana", "Naidhana", "Mitra", "Parama Mitra",
]
TARABALA_NATURE = {
    "Janma": "Neutral", "Sampat": "Auspicious", "Vipat": "Inauspicious",
    "Kshema": "Auspicious", "Pratyak": "Inauspicious", "Sadhana": "Auspicious",
    "Naidhana": "Inauspicious", "Mitra": "Auspicious", "Parama Mitra": "Highly Auspicious",
}

NAK_SPAN = 360 / 27


def calculate_panchang(target_date: date, lat: float, lon: float, tz_str: str,
                        birth_nak_idx: int = None) -> dict:
    """
    Full Panchang for a given date and location.
    Optional birth_nak_idx enables Tarabala and Chandra Bala calculations.
    """
    tz = pytz.timezone(tz_str)
    # Use local noon as the reference moment for Panchang calculations
    noon_dt = tz.localize(datetime(target_date.year, target_date.month, target_date.day, 12, 0, 0))
    jd = datetime_to_jd(noon_dt, tz_str)

    sun_pos  = get_planet_position(jd, swe.SUN)
    moon_pos = get_planet_position(jd, swe.MOON)

    sun_lon  = sun_pos["longitude"]
    moon_lon = moon_pos["longitude"]

    # 1. Vara (weekday)
    weekday_idx = target_date.weekday()  # 0=Monday
    # Convert to Indian week: Sunday=0 ... Saturday=6
    indian_day_idx = (weekday_idx + 1) % 7
    vara = {
        "name": WEEKDAYS[indian_day_idx],
        "lord": WEEKDAY_LORDS[indian_day_idx],
        "index": indian_day_idx,
    }

    # 2. Tithi
    tithi_data = _calc_tithi(moon_lon, sun_lon, jd)

    # 3. Nakshatra
    nak_data = _calc_nakshatra(moon_lon, jd)

    # 4. Yoga
    yoga_data = _calc_yoga(moon_lon, sun_lon)

    # 5. Karana
    karana_data = _calc_karana(moon_lon, sun_lon)

    # Sun / Moon Rashi
    sun_rashi  = {"name": RASHI_NAMES[sun_pos["rashi"]],  "degree": round(sun_pos["degree_in_rashi"], 2)}
    moon_rashi = {"name": RASHI_NAMES[moon_pos["rashi"]], "degree": round(moon_pos["degree_in_rashi"], 2)}

    # Sunrise, Sunset, Moonrise, Moonset
    sky_data = get_sunrise_sunset_moonrise(target_date, lat, lon, tz_str)

    # Abhijit Muhurta (solar noon ± 24 min)
    abhijit = _abhijit_muhurta(sky_data)

    # Tarabala & Chandra Bala (only if birth nakshatra known)
    tarabala = _calc_tarabala(nak_data["index"], birth_nak_idx) if birth_nak_idx is not None else None
    chandra_bala = _calc_chandra_bala(moon_pos["rashi"], birth_nak_idx) if birth_nak_idx is not None else None

    # Auspicious / inauspicious summary
    is_auspicious = (
        tithi_data["nature"] == "Auspicious"
        and yoga_data["nature"] == "Auspicious"
        and karana_data["nature"] != "Inauspicious (Bhadra)"
    )

    return {
        "date": target_date.strftime("%A, %d %B %Y"),
        "date_iso": target_date.isoformat(),
        "vara": vara,
        "tithi": tithi_data,
        "nakshatra": nak_data,
        "yoga": yoga_data,
        "karana": karana_data,
        "sun_rashi": sun_rashi,
        "moon_rashi": moon_rashi,
        "sky": sky_data,
        "abhijit_muhurta": abhijit,
        "tarabala": tarabala,
        "chandra_bala": chandra_bala,
        "is_auspicious": is_auspicious,
        "ayanamsa": round(swe.get_ayanamsa_ut(jd), 4),
    }


def _calc_tithi(moon_lon: float, sun_lon: float, jd: float) -> dict:
    diff = (moon_lon - sun_lon) % 360
    tithi_num = int(diff / 12)          # 0–29
    tithi_fraction = (diff % 12) / 12
    remaining = (1 - tithi_fraction) * 12  # degrees remaining

    # Approximate time remaining (Moon moves ~13.17°/day)
    hours_remaining = remaining / 0.549  # 0.549 °/hour approx

    tithi_idx = tithi_num % 30

    # Special tithis
    is_ekadashi = tithi_idx in (10, 25)    # 11th (Shukla/Krishna)
    is_purnima  = tithi_idx == 14
    is_amavasya = tithi_idx == 29
    is_pradosh  = tithi_idx in (12, 27)

    nature = "Auspicious"
    if tithi_idx in (3, 7, 8, 13, 14, 28, 29):
        nature = "Mixed"
    elif tithi_idx in (5, 9, 14, 29):
        nature = "Inauspicious"

    return {
        "number": tithi_idx + 1,
        "name": TITHI_NAMES[tithi_idx],
        "paksha": TITHI_PAKSHA[tithi_idx],
        "fraction_elapsed": round(tithi_fraction * 100, 1),
        "hours_remaining": round(hours_remaining, 1),
        "nature": nature,
        "is_ekadashi": is_ekadashi,
        "is_purnima": is_purnima,
        "is_amavasya": is_amavasya,
        "is_pradosh": is_pradosh,
    }


def _calc_nakshatra(moon_lon: float, jd: float) -> dict:
    nak_idx = int(moon_lon / NAK_SPAN)
    nak_degree = moon_lon % NAK_SPAN
    pada = int(nak_degree / (NAK_SPAN / 4)) + 1
    fraction_elapsed = nak_degree / NAK_SPAN
    remaining_degrees = NAK_SPAN * (1 - fraction_elapsed)

    # Moon speed ~13.17 °/day → time to leave nakshatra
    moon_speed_per_hour = 13.17 / 24
    hours_remaining = remaining_degrees / moon_speed_per_hour

    return {
        "index": nak_idx,
        "number": nak_idx + 1,
        "name": NAKSHATRA_NAMES[nak_idx],
        "lord": NAKSHATRA_LORDS[nak_idx],
        "pada": pada,
        "fraction_elapsed": round(fraction_elapsed * 100, 1),
        "hours_remaining": round(hours_remaining, 1),
        "degree": round(moon_lon, 4),
        "degree_in_nak": round(nak_degree, 4),
    }


def _calc_yoga(moon_lon: float, sun_lon: float) -> dict:
    total = (moon_lon + sun_lon) % 360
    yoga_idx = int(total / (360 / 27))
    fraction = (total % (360 / 27)) / (360 / 27)
    name = YOGA_NAMES[yoga_idx]
    return {
        "index": yoga_idx,
        "number": yoga_idx + 1,
        "name": name,
        "nature": YOGA_NATURE.get(name, "Neutral"),
        "fraction_elapsed": round(fraction * 100, 1),
    }


def _calc_karana(moon_lon: float, sun_lon: float) -> dict:
    diff = (moon_lon - sun_lon) % 360
    karana_num = int(diff / 6)   # 0–59 (each tithi has 2 karanas)

    # First 4 karanas are fixed, remaining 56 rotate through 7 movable
    if karana_num == 0:
        name = "Kimstughna"
    elif 1 <= karana_num <= 56:
        name = KARANA_NAMES[(karana_num - 1) % 7]
    elif karana_num == 57:
        name = "Shakuni"
    elif karana_num == 58:
        name = "Chatushpada"
    else:
        name = "Naga"

    fraction = (diff % 6) / 6
    return {
        "number": (karana_num % 60) + 1,
        "name": name,
        "nature": KARANA_NATURE.get(name, "Neutral"),
        "fraction_elapsed": round(fraction * 100, 1),
        "is_vishti": name == "Vishti",
    }


def _calc_tarabala(transit_nak: int, birth_nak: int) -> dict:
    if birth_nak is None:
        return None
    count = ((transit_nak - birth_nak) % 27) + 1
    tarabala_idx = ((count - 1) % 9)
    name = TARABALA_NAMES[tarabala_idx]
    return {
        "count": count,
        "name": name,
        "nature": TARABALA_NATURE.get(name, "Neutral"),
    }


def _calc_chandra_bala(transit_moon_rashi: int, birth_moon_rashi_or_nak: int) -> dict:
    """
    Chandra Bala: auspicious positions of transit Moon from natal Moon.
    Favourable houses: 1, 3, 6, 7, 10, 11.
    """
    if birth_moon_rashi_or_nak is None:
        return None
    birth_rashi = birth_moon_rashi_or_nak
    count = ((transit_moon_rashi - birth_rashi) % 12) + 1
    favourable = count in (1, 3, 6, 7, 10, 11)
    return {
        "count_from_natal": count,
        "is_favourable": favourable,
        "nature": "Auspicious" if favourable else "Inauspicious",
    }


def _abhijit_muhurta(sky: dict) -> str:
    """Solar noon ± 24 minutes — most auspicious window of the day."""
    solar_noon = sky.get("solar_noon")
    if not solar_noon or solar_noon == "N/A":
        return "N/A"
    try:
        from datetime import datetime, timedelta
        noon_dt = datetime.strptime(solar_noon, "%I:%M %p")
        start = (noon_dt - timedelta(minutes=24)).strftime("%I:%M %p")
        end   = (noon_dt + timedelta(minutes=24)).strftime("%I:%M %p")
        return f"{start} – {end}"
    except Exception:
        return "N/A"
