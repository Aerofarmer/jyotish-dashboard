"""
Core Vedic astrology engine using Swiss Ephemeris (pyswisseph).
Lahiri ayanamsa, sidereal zodiac, Whole Sign houses.
"""
import math
import swisseph as swe
import ephem
from datetime import datetime, date, timedelta
import pytz
from typing import Optional

# Lahiri ayanamsa (most common in Indian astrology)
swe.set_sid_mode(swe.SIDM_LAHIRI)

PLANETS = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mars":    swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus":   swe.VENUS,
    "Saturn":  swe.SATURN,
    "Rahu":    swe.MEAN_NODE,   # North Node
}

PLANET_SYMBOLS = {
    "Sun": "☉", "Moon": "☽", "Mars": "♂", "Mercury": "☿",
    "Jupiter": "♃", "Venus": "♀", "Saturn": "♄",
    "Rahu": "☊", "Ketu": "☋",
}

RASHI_NAMES = [
    "Mesha", "Vrishabha", "Mithuna", "Karka",
    "Simha", "Kanya", "Tula", "Vrishchika",
    "Dhanu", "Makara", "Kumbha", "Meena",
]

RASHI_ENGLISH = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

RASHI_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon",
    4: "Sun", 5: "Mercury", 6: "Venus", 7: "Mars",
    8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
    "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
    "Sun", "Moon", "Mars", "Rahu", "Jupiter",
    "Saturn", "Mercury",
]

NAKSHATRA_DEVATAS = [
    "Ashwini Kumara", "Yama", "Agni", "Brahma", "Soma",
    "Rudra", "Aditi", "Brihaspati", "Sarpa", "Pitru",
    "Bhaga", "Aryama", "Savita", "Vishwakarma", "Vayu",
    "Indragni", "Mitra", "Indra", "Niriti", "Apas",
    "Vishwadeva", "Vishnu", "Ashta Vasu", "Varuna", "Aja Ekapada",
    "Ahir Budhnya", "Pusha",
]

WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
WEEKDAY_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

PLANET_COLORS = {
    "Sun": "#FF6B35", "Moon": "#C0C0C0", "Mars": "#FF4444",
    "Mercury": "#00CC88", "Jupiter": "#FFD700", "Venus": "#FF69B4",
    "Saturn": "#6B7280", "Rahu": "#8B5CF6", "Ketu": "#EC4899",
}

PLANET_NATURE = {
    "Sun": "Cruel/Separative", "Moon": "Benefic (waxing)/Malefic (waning)",
    "Mars": "Cruel/Separative", "Mercury": "Benefic/Neutral",
    "Jupiter": "Benefic", "Venus": "Benefic",
    "Saturn": "Cruel/Separative", "Rahu": "Cruel/Shadow",
    "Ketu": "Cruel/Shadow",
}

EXALTATION = {
    "Sun": (0, 10), "Moon": (1, 3), "Mars": (9, 28),
    "Mercury": (5, 15), "Jupiter": (3, 5), "Venus": (11, 27),
    "Saturn": (6, 20), "Rahu": (1, 20), "Ketu": (7, 20),
}

DEBILITATION = {
    "Sun": (6, 10), "Moon": (7, 3), "Mars": (3, 28),
    "Mercury": (11, 15), "Jupiter": (9, 5), "Venus": (5, 27),
    "Saturn": (0, 20), "Rahu": (7, 20), "Ketu": (1, 20),
}

OWN_SIGN = {
    "Sun": [4], "Moon": [3], "Mars": [0, 7], "Mercury": [2, 5],
    "Jupiter": [8, 11], "Venus": [1, 6], "Saturn": [9, 10],
}


def datetime_to_jd(dt: datetime, tz_str: str = "UTC") -> float:
    """Convert datetime to Julian Day (UT)."""
    if dt.tzinfo is None:
        tz = pytz.timezone(tz_str)
        dt = tz.localize(dt)
    dt_utc = dt.astimezone(pytz.utc)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    )


def get_planet_position(jd: float, planet_id: int) -> dict:
    """Get sidereal longitude, speed, and house for a planet."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    result, ret_flag = swe.calc_ut(jd, planet_id, flags)
    lon = result[0] % 360
    speed = result[3]
    rashi_idx = int(lon // 30)
    degree_in_rashi = lon % 30
    return {
        "longitude": round(lon, 4),
        "speed": round(speed, 4),
        "retrograde": speed < 0,
        "rashi": rashi_idx,
        "rashi_name": RASHI_NAMES[rashi_idx],
        "rashi_english": RASHI_ENGLISH[rashi_idx],
        "degree_in_rashi": round(degree_in_rashi, 4),
        "dms": _decimal_to_dms(degree_in_rashi),
    }


def get_lagna(jd: float, lat: float, lon: float) -> dict:
    """Calculate sidereal Lagna (Ascendant)."""
    flags = swe.FLG_SIDEREAL
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', flags)  # Whole Sign
    asc = ascmc[0] % 360
    rashi_idx = int(asc // 30)
    degree_in_rashi = asc % 30
    return {
        "longitude": round(asc, 4),
        "rashi": rashi_idx,
        "rashi_name": RASHI_NAMES[rashi_idx],
        "rashi_english": RASHI_ENGLISH[rashi_idx],
        "degree_in_rashi": round(degree_in_rashi, 4),
        "dms": _decimal_to_dms(degree_in_rashi),
    }


def get_all_houses(jd: float, lat: float, lon: float) -> list:
    """Get all 12 Whole-Sign house cusp longitudes."""
    flags = swe.FLG_SIDEREAL
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', flags)
    asc = ascmc[0] % 360
    lagna_rashi = int(asc // 30)
    houses = []
    for i in range(12):
        rashi_idx = (lagna_rashi + i) % 12
        houses.append({
            "house": i + 1,
            "rashi": rashi_idx,
            "rashi_name": RASHI_NAMES[rashi_idx],
            "rashi_english": RASHI_ENGLISH[rashi_idx],
            "longitude": rashi_idx * 30.0,
        })
    return houses


def get_nakshatra_info(longitude: float) -> dict:
    """Nakshatra, pada, lord and remaining degrees."""
    nak_idx = int(longitude / (360 / 27))
    nak_degree = longitude % (360 / 27)
    pada = int(nak_degree / (360 / 108)) + 1
    remaining = (360 / 27) - nak_degree
    return {
        "index": nak_idx,
        "name": NAKSHATRA_NAMES[nak_idx],
        "pada": pada,
        "lord": NAKSHATRA_LORDS[nak_idx],
        "devata": NAKSHATRA_DEVATAS[nak_idx],
        "degree_in_nak": round(nak_degree, 4),
        "remaining_degrees": round(remaining, 4),
    }


def get_planet_dignity(planet: str, rashi: int) -> str:
    """Return dignity: Exalted, Debilitated, Own Sign, Moolatrikona, Neutral."""
    if planet in EXALTATION and EXALTATION[planet][0] == rashi:
        return "Exalted"
    if planet in DEBILITATION and DEBILITATION[planet][0] == rashi:
        return "Debilitated"
    if planet in OWN_SIGN and rashi in OWN_SIGN[planet]:
        return "Own Sign"
    return "Neutral"


def calculate_full_chart(
    birth_dt: datetime,
    lat: float,
    lon: float,
    tz_str: str,
    name: str = "",
    place: str = "",
) -> dict:
    """Master function: returns complete birth chart data."""
    jd = datetime_to_jd(birth_dt, tz_str)

    lagna = get_lagna(jd, lat, lon)
    lagna_rashi = lagna["rashi"]
    houses = get_all_houses(jd, lat, lon)

    # Build house-to-rashi map (Whole Sign: house 1 = lagna rashi)
    house_rashi_map = {h["house"]: h["rashi"] for h in houses}
    rashi_house_map = {v: k for k, v in house_rashi_map.items()}

    planets = {}
    for pname, pid in PLANETS.items():
        pos = get_planet_position(jd, pid)
        pos["house"] = rashi_house_map.get(pos["rashi"], 1)
        pos["nakshatra"] = get_nakshatra_info(pos["longitude"])
        pos["dignity"] = get_planet_dignity(pname, pos["rashi"])
        pos["color"] = PLANET_COLORS.get(pname, "#FFFFFF")
        pos["symbol"] = PLANET_SYMBOLS.get(pname, "?")
        pos["nature"] = PLANET_NATURE.get(pname, "Neutral")
        planets[pname] = pos

    # Ketu = Rahu + 180
    rahu_lon = planets["Rahu"]["longitude"]
    ketu_lon = (rahu_lon + 180) % 360
    ketu_rashi = int(ketu_lon // 30)
    ketu_pos = {
        "longitude": round(ketu_lon, 4),
        "speed": -planets["Rahu"]["speed"],
        "retrograde": True,
        "rashi": ketu_rashi,
        "rashi_name": RASHI_NAMES[ketu_rashi],
        "rashi_english": RASHI_ENGLISH[ketu_rashi],
        "degree_in_rashi": round(ketu_lon % 30, 4),
        "dms": _decimal_to_dms(ketu_lon % 30),
        "house": rashi_house_map.get(ketu_rashi, 7),
        "nakshatra": get_nakshatra_info(ketu_lon),
        "dignity": get_planet_dignity("Ketu", ketu_rashi),
        "color": PLANET_COLORS["Ketu"],
        "symbol": PLANET_SYMBOLS["Ketu"],
        "nature": PLANET_NATURE["Ketu"],
    }
    planets["Ketu"] = ketu_pos

    # Lagna nakshatra
    lagna["nakshatra"] = get_nakshatra_info(lagna["longitude"])

    # Navamsa (D9) chart
    navamsa = _calculate_navamsa(planets, lagna)

    # House occupants map
    house_occupants = {i: [] for i in range(1, 13)}
    for pname, pdata in planets.items():
        house_occupants[pdata["house"]].append(pname)

    return {
        "name": name,
        "place": place,
        "birth_datetime": birth_dt.isoformat(),
        "timezone": tz_str,
        "latitude": lat,
        "longitude_coord": lon,
        "julian_day": round(jd, 6),
        "lagna": lagna,
        "planets": planets,
        "houses": houses,
        "house_occupants": house_occupants,
        "navamsa": navamsa,
        "ayanamsa": round(swe.get_ayanamsa_ut(jd), 4),
    }


def calculate_transit_chart(lat: float, lon: float, tz_str: str,
                            dt: datetime = None) -> dict:
    """Planetary positions for a given datetime (defaults to now)."""
    tz = pytz.timezone(tz_str)
    if dt is None:
        dt = datetime.now(tz)
    elif dt.tzinfo is None:
        dt = tz.localize(dt)
    chart = calculate_full_chart(dt, lat, lon, tz_str, name="Transit")
    chart["transit_time"] = dt.strftime("%d %b %Y, %I:%M %p %Z")
    return chart


def get_sunrise_sunset_moonrise(
    target_date: date,
    lat: float,
    lon: float,
    tz_str: str,
) -> dict:
    """
    Accurate sunrise, sunset, moonrise, moonset, solar noon
    using the ephem library (works for any location on Earth).
    """
    tz = pytz.timezone(tz_str)

    obs = ephem.Observer()
    obs.lat = str(lat)
    obs.lon = str(lon)
    obs.elevation = 0
    obs.pressure = 1013.25   # standard atmosphere
    obs.horizon = "-0:34"    # standard refraction correction

    # Set date to midnight UTC of that calendar day in the given timezone
    local_midnight = tz.localize(datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0))
    utc_midnight = local_midnight.astimezone(pytz.utc)
    obs.date = utc_midnight.strftime("%Y/%m/%d %H:%M:%S")

    sun = ephem.Sun()
    moon = ephem.Moon()

    def _to_local(ephem_date) -> Optional[str]:
        if ephem_date is None:
            return None
        utc_dt = ephem.Date(ephem_date).datetime().replace(tzinfo=pytz.utc)
        local_dt = utc_dt.astimezone(tz)
        return local_dt.strftime("%I:%M %p")

    def _to_local_full(ephem_date) -> Optional[datetime]:
        if ephem_date is None:
            return None
        utc_dt = ephem.Date(ephem_date).datetime().replace(tzinfo=pytz.utc)
        return utc_dt.astimezone(tz)

    # Sunrise / Sunset
    try:
        sunrise_ephem = obs.next_rising(sun)
        sunrise_local = _to_local(sunrise_ephem)
        sunrise_dt = _to_local_full(sunrise_ephem)
    except ephem.AlwaysUpError:
        sunrise_local = "Always up"
        sunrise_dt = None
    except ephem.NeverUpError:
        sunrise_local = "Never rises"
        sunrise_dt = None

    try:
        sunset_ephem = obs.next_setting(sun)
        sunset_local = _to_local(sunset_ephem)
        sunset_dt = _to_local_full(sunset_ephem)
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        sunset_local = "N/A"
        sunset_dt = None

    # Solar noon (transit)
    try:
        noon_ephem = obs.next_transit(sun)
        solar_noon = _to_local(noon_ephem)
    except Exception:
        solar_noon = "N/A"

    # Moonrise / Moonset
    obs.horizon = "0"  # exact horizon for moon
    try:
        moonrise_ephem = obs.next_rising(moon)
        moonrise_local = _to_local(moonrise_ephem)
        moonrise_dt = _to_local_full(moonrise_ephem)
    except ephem.AlwaysUpError:
        moonrise_local = "Always up"
        moonrise_dt = None
    except ephem.NeverUpError:
        moonrise_local = "Never rises"
        moonrise_dt = None

    try:
        moonset_ephem = obs.next_setting(moon)
        moonset_local = _to_local(moonset_ephem)
    except (ephem.AlwaysUpError, ephem.NeverUpError):
        moonset_local = "N/A"

    # Moon phase
    moon.compute(obs.date)
    moon_phase_pct = round(moon.moon_phase * 100, 1)
    moon_phase_name = _moon_phase_name(moon.moon_phase)

    # Day length
    day_length = "N/A"
    if sunrise_dt and sunset_dt:
        delta = sunset_dt - sunrise_dt
        hours, rem = divmod(int(delta.total_seconds()), 3600)
        mins = rem // 60
        day_length = f"{hours}h {mins}m"

    # Rahu Kaal, Gulika Kaal, Yamaghanta (based on weekday + sunrise)
    weekday = target_date.weekday()  # Monday=0, Sunday=6
    rahu_kaal = "N/A"
    gulika_kaal = "N/A"
    yamaghanta = "N/A"
    if sunrise_dt and sunset_dt:
        rahu_kaal   = _rahu_kaal(weekday, sunrise_dt, sunset_dt)
        gulika_kaal = _gulika_kaal(weekday, sunrise_dt, sunset_dt)
        yamaghanta  = _yamaghanta(weekday, sunrise_dt, sunset_dt)

    return {
        "sunrise": sunrise_local,
        "sunset": sunset_local,
        "solar_noon": solar_noon,
        "moonrise": moonrise_local,
        "moonset": moonset_local,
        "moon_phase_pct": moon_phase_pct,
        "moon_phase_name": moon_phase_name,
        "day_length": day_length,
        "rahu_kaal": rahu_kaal,
        "gulika_kaal": gulika_kaal,
        "yamaghanta": yamaghanta,
    }


def _rahu_kaal(weekday: int, sunrise: datetime, sunset: datetime) -> str:
    """Rahu Kaal period — inauspicious 90-minute window each day."""
    # Rahu Kaal order by weekday (Mon=0 … Sun=6 in Python, but Sun=0 in Indian week)
    # Sunday=7th part, Monday=2nd, Tuesday=7th, Wednesday=5th,
    # Thursday=6th, Friday=4th, Saturday=3rd
    order = {0: 2, 1: 7, 2: 4, 3: 5, 4: 6, 5: 3, 6: 8}  # Python Mon=0
    part = order.get(weekday, 1)
    return _kaal_window(part, sunrise, sunset)


def _gulika_kaal(weekday: int, sunrise: datetime, sunset: datetime) -> str:
    # Sunday=6, Mon=5, Tue=4, Wed=3, Thu=2, Fri=1, Sat=0 (day parts from sunrise)
    order = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}
    part = order.get(weekday, 1)
    return _kaal_window(part, sunrise, sunset)


def _yamaghanta(weekday: int, sunrise: datetime, sunset: datetime) -> str:
    order = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 7, 6: 6}
    part = order.get(weekday, 1)
    return _kaal_window(part, sunrise, sunset)


def _kaal_window(part: int, sunrise: datetime, sunset: datetime) -> str:
    total_secs = (sunset - sunrise).total_seconds()
    segment = total_secs / 8.0
    start = sunrise + timedelta(seconds=(part - 1) * segment)
    end   = sunrise + timedelta(seconds=part * segment)
    return f"{start.strftime('%I:%M %p')} – {end.strftime('%I:%M %p')}"


def _moon_phase_name(phase: float) -> str:
    if phase < 0.02:    return "New Moon"
    if phase < 0.25:    return "Waxing Crescent"
    if phase < 0.27:    return "First Quarter"
    if phase < 0.50:    return "Waxing Gibbous"
    if phase < 0.52:    return "Full Moon"
    if phase < 0.75:    return "Waning Gibbous"
    if phase < 0.77:    return "Last Quarter"
    if phase < 0.98:    return "Waning Crescent"
    return "New Moon"


def _decimal_to_dms(deg: float) -> str:
    d = int(deg)
    m = int((deg - d) * 60)
    s = int(((deg - d) * 60 - m) * 60)
    return f"{d}°{m}'{s}\""


def _calculate_navamsa(planets: dict, lagna: dict) -> dict:
    """D9 Navamsa chart — each sign is divided into 9 parts of 3°20'."""
    navamsa = {}
    all_positions = {**planets, "Lagna": {"longitude": lagna["longitude"]}}
    for name, data in all_positions.items():
        lon = data["longitude"]
        rashi = int(lon // 30)
        degree_in_rashi = lon % 30
        navamsa_num = int(degree_in_rashi / (10 / 3))
        # Starting navamsa rashi depends on element
        fire_signs  = [0, 4, 8]   # Mesha, Simha, Dhanu
        earth_signs = [1, 5, 9]
        air_signs   = [2, 6, 10]
        water_signs = [3, 7, 11]
        if rashi in fire_signs:
            start = 0
        elif rashi in earth_signs:
            start = 9
        elif rashi in air_signs:
            start = 6
        else:
            start = 3
        nav_rashi = (start + navamsa_num) % 12
        navamsa[name] = {
            "rashi": nav_rashi,
            "rashi_name": RASHI_NAMES[nav_rashi],
        }
    return navamsa
