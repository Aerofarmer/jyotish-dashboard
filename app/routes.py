from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, date
import calendar as cal_mod
import pytz
import traceback

from .astrology.calculator import (calculate_full_chart, calculate_transit_chart,
                                    get_sunrise_sunset_moonrise, PLANET_COLORS)
from .astrology.dasha import calculate_vimshottari, dasha_summary
from .astrology.panchang import calculate_panchang
from .astrology.store import save_chart, list_charts, get_chart, delete_chart
from .astrology.predictions import generate_predictions
from .api.external import geocode_place, get_ip_location

main = Blueprint("main", __name__)


# ─────────────────────────────────────────────
#  Home — birth-data input + saved charts
# ─────────────────────────────────────────────
@main.route("/")
def index():
    ip_loc   = get_ip_location()
    saved    = list_charts()
    return render_template("index.html", ip_loc=ip_loc, saved_charts=saved)


# ─────────────────────────────────────────────
#  Kundli (birth chart)
# ─────────────────────────────────────────────
@main.route("/kundli", methods=["GET", "POST"])
def kundli():
    error = None
    chart = None
    dasha = None

    if request.method == "POST":
        try:
            name   = request.form.get("name", "").strip()
            dob    = request.form.get("dob", "")
            tob    = request.form.get("tob", "")
            place  = request.form.get("place", "").strip()
            lat    = request.form.get("lat", "")
            lon    = request.form.get("lon", "")
            tz_str = request.form.get("timezone", "Asia/Kolkata")

            if not dob or not tob:
                raise ValueError("Date and time of birth are required.")

            if not lat or not lon:
                if not place:
                    raise ValueError("Enter a place or coordinates.")
                geo = geocode_place(place)
                if "error" in geo:
                    raise ValueError(geo["error"])
                lat    = geo["lat"]
                lon    = geo["lon"]
                tz_str = geo["timezone"]
                place  = geo.get("display_name", place)
            else:
                lat = float(lat)
                lon = float(lon)

            birth_dt = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
            chart = calculate_full_chart(birth_dt, float(lat), float(lon),
                                         tz_str, name=name, place=place)

            moon_lon = chart["planets"]["Moon"]["longitude"]
            dasha    = calculate_vimshottari(moon_lon, birth_dt)

            # Persist in session for transit/dasha/predictions
            session["birth_lat"]   = float(lat)
            session["birth_lon"]   = float(lon)
            session["birth_tz"]    = tz_str
            session["birth_name"]  = name
            session["birth_place"] = place
            session["birth_dob"]   = dob
            session["birth_tob"]   = tob

        except Exception as e:
            error = str(e)
            traceback.print_exc()

    return render_template("kundli.html", chart=chart, dasha=dasha, error=error)


# ─────────────────────────────────────────────
#  Save chart
# ─────────────────────────────────────────────
@main.route("/kundli/save", methods=["POST"])
def save_kundli():
    data = request.get_json(silent=True) or {}
    chart_data = data.get("chart")
    if not chart_data:
        return jsonify({"error": "No chart data"}), 400
    cid = save_chart(chart_data)
    return jsonify({"id": cid, "message": "Chart saved successfully"})


# ─────────────────────────────────────────────
#  Load saved chart
# ─────────────────────────────────────────────
@main.route("/kundli/load/<cid>")
def load_kundli(cid):
    chart = get_chart(cid)
    if not chart:
        flash("Chart not found.", "danger")
        return redirect(url_for("main.index"))

    # Reconstitute session from saved chart
    session["birth_lat"]   = chart.get("latitude", 28.6139)
    session["birth_lon"]   = chart.get("longitude_coord", 77.2090)
    session["birth_tz"]    = chart.get("timezone", "Asia/Kolkata")
    session["birth_name"]  = chart.get("name", "")
    session["birth_place"] = chart.get("place", "")
    bd = chart.get("birth_datetime", "")[:16]
    if "T" in bd:
        session["birth_dob"] = bd[:10]
        session["birth_tob"] = bd[11:16]

    # Recompute dasha from saved moon longitude
    dasha = None
    try:
        moon_lon = chart["planets"]["Moon"]["longitude"]
        birth_dt = datetime.fromisoformat(chart["birth_datetime"])
        dasha = calculate_vimshottari(moon_lon, birth_dt)
    except Exception:
        pass

    return render_template("kundli.html", chart=chart, dasha=dasha, error=None)


# ─────────────────────────────────────────────
#  Delete saved chart
# ─────────────────────────────────────────────
@main.route("/kundli/delete/<cid>", methods=["POST"])
def delete_kundli(cid):
    delete_chart(cid)
    return jsonify({"ok": True})


# ─────────────────────────────────────────────
#  Transit chart
# ─────────────────────────────────────────────
@main.route("/transit")
def transit():
    tz_str = session.get("birth_tz", "Asia/Kolkata")
    lat    = session.get("birth_lat", 28.6139)
    lon    = session.get("birth_lon", 77.2090)
    name   = session.get("birth_name", "Transit")
    place  = session.get("birth_place", "")

    transit_data = calculate_transit_chart(float(lat), float(lon), tz_str)

    natal_chart = None
    dob = session.get("birth_dob")
    tob = session.get("birth_tob")
    if dob and tob:
        try:
            birth_dt = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
            natal_chart = calculate_full_chart(birth_dt, float(lat), float(lon),
                                               tz_str, name=name, place=place)
        except Exception:
            pass

    # Build nakshatra-in-house mapping for transit
    nak_house_map = _build_nak_house_map(transit_data, natal_chart)

    return render_template("transit.html",
                           transit=transit_data,
                           natal=natal_chart,
                           nak_house_map=nak_house_map,
                           tz_str=tz_str)


# ─────────────────────────────────────────────
#  Dasha
# ─────────────────────────────────────────────
@main.route("/dasha")
def dasha():
    dob = session.get("birth_dob")
    tob = session.get("birth_tob")
    lat = session.get("birth_lat", 28.6139)
    lon = session.get("birth_lon", 77.2090)
    tz  = session.get("birth_tz", "Asia/Kolkata")

    dasha_data = None
    chart      = None
    error      = None

    if dob and tob:
        try:
            birth_dt   = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
            chart      = calculate_full_chart(birth_dt, float(lat), float(lon), tz)
            moon_lon   = chart["planets"]["Moon"]["longitude"]
            dasha_data = calculate_vimshottari(moon_lon, birth_dt)
        except Exception as e:
            error = str(e)
    else:
        error = "Please generate a Kundli first."

    return render_template("dasha.html", dasha=dasha_data, chart=chart, error=error)


# ─────────────────────────────────────────────
#  Predictions
# ─────────────────────────────────────────────
@main.route("/predictions")
def predictions():
    dob   = session.get("birth_dob")
    tob   = session.get("birth_tob")
    lat   = session.get("birth_lat", 28.6139)
    lon   = session.get("birth_lon", 77.2090)
    tz    = session.get("birth_tz", "Asia/Kolkata")
    name  = session.get("birth_name", "Native")
    place = session.get("birth_place", "")

    # Optional date override (for calendar navigation)
    date_str      = request.args.get("date", "")
    today         = date.today()
    selected_date = today
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    preds  = None
    error  = None

    if not (dob and tob):
        error = "Please generate a Kundli first to see predictions."
        return render_template("predictions.html", preds=None, error=error,
                               selected_date=selected_date.isoformat(),
                               today=today.isoformat())

    try:
        birth_dt    = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
        natal_chart = calculate_full_chart(birth_dt, float(lat), float(lon),
                                           tz, name=name, place=place)

        if selected_date == today:
            transit_data = calculate_transit_chart(float(lat), float(lon), tz)
        else:
            tz_obj      = pytz.timezone(tz)
            transit_dt  = tz_obj.localize(datetime(selected_date.year,
                                                    selected_date.month,
                                                    selected_date.day, 12, 0))
            transit_data = calculate_transit_chart(float(lat), float(lon), tz, dt=transit_dt)

        moon_lon   = natal_chart["planets"]["Moon"]["longitude"]
        dasha_data = calculate_vimshottari(moon_lon, birth_dt)
        preds      = generate_predictions(natal_chart, transit_data,
                                          dasha_data, float(lat), float(lon), tz)
    except Exception as e:
        error = str(e)
        traceback.print_exc()

    return render_template("predictions.html", preds=preds, error=error,
                           name=name, place=place,
                           selected_date=selected_date.isoformat(),
                           today=today.isoformat())


# ─────────────────────────────────────────────
#  API: Month day-quality scores for calendar
# ─────────────────────────────────────────────
@main.route("/api/month-scores")
def month_scores():
    year   = int(request.args.get("year",  date.today().year))
    month  = int(request.args.get("month", date.today().month))
    lat    = float(request.args.get("lat",  session.get("birth_lat", 28.6139)))
    lon    = float(request.args.get("lon",  session.get("birth_lon", 77.2090)))
    tz_str = request.args.get("tz", session.get("birth_tz", "Asia/Kolkata"))

    num_days = cal_mod.monthrange(year, month)[1]
    scores   = {}

    for day in range(1, num_days + 1):
        d = date(year, month, day)
        try:
            pan        = calculate_panchang(d, lat, lon, tz_str, None)
            scores[day] = _quick_day_score(pan, d)
        except Exception:
            scores[day] = {"score": 5, "color": "#9ca3af", "label": "Neutral",
                           "tithi": "", "nakshatra": "", "vara": ""}

    return jsonify(scores)


def _quick_day_score(pan: dict, d: date) -> dict:
    score = 5
    vara_scores = {
        "Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 7,
        "Jupiter": 9, "Venus": 8, "Saturn": 3,
    }
    vara_lord = pan.get("vara", {}).get("lord", "")
    score += vara_scores.get(vara_lord, 0) - 5

    tithi_num = pan.get("tithi", {}).get("number", 5)
    good_tithis = {1, 2, 3, 5, 7, 10, 11, 13, 15}
    bad_tithis  = {4, 6, 8, 9, 12, 14, 30}
    if tithi_num in good_tithis:
        score += 1
    elif tithi_num in bad_tithis:
        score -= 1

    yoga_name = pan.get("yoga", {}).get("name", "")
    good_yogas = {"Siddhi", "Amriti", "Shubha", "Labha", "Sukla", "Brahma", "Indra"}
    bad_yogas  = {"Vyatipata", "Ganda", "Shoola", "Atiganda", "Vajra", "Vyaghata"}
    if yoga_name in good_yogas:
        score += 1
    elif yoga_name in bad_yogas:
        score -= 1

    score = max(1, min(10, score))

    if score >= 8:
        color, label = "#16a34a", "Excellent"
    elif score >= 6:
        color, label = "#65a30d", "Good"
    elif score >= 5:
        color, label = "#d97706", "Moderate"
    elif score >= 3:
        color, label = "#ea580c", "Caution"
    else:
        color, label = "#dc2626", "Difficult"

    return {
        "score":     score,
        "color":     color,
        "label":     label,
        "tithi":     pan.get("tithi", {}).get("name", ""),
        "nakshatra": pan.get("nakshatra", {}).get("name", ""),
        "vara":      vara_lord,
    }


# ─────────────────────────────────────────────
#  API: Deep day detail for calendar panel
# ─────────────────────────────────────────────
@main.route("/api/day-detail")
def day_detail():
    date_str = request.args.get("date", date.today().isoformat())
    lat      = float(request.args.get("lat",  session.get("birth_lat", 28.6139)))
    lon      = float(request.args.get("lon",  session.get("birth_lon", 77.2090)))
    tz_str   = request.args.get("tz", session.get("birth_tz", "Asia/Kolkata"))

    try:
        d    = datetime.strptime(date_str, "%Y-%m-%d").date()
        pan  = calculate_panchang(d, lat, lon, tz_str, None)
        sky  = get_sunrise_sunset_moonrise(d, lat, lon, tz_str)
        q    = _quick_day_score(pan, d)

        # Per-element quality for breakdown display
        tithi_num  = pan.get("tithi", {}).get("number", 5)
        yoga_name  = pan.get("yoga",  {}).get("name", "")
        vara_lord  = pan.get("vara",  {}).get("lord", "")
        nak_name   = pan.get("nakshatra", {}).get("name", "")

        _vara_scores  = {"Sun":7,"Moon":8,"Mars":4,"Mercury":7,"Jupiter":9,"Venus":8,"Saturn":3}
        _good_tithis  = {1,2,3,5,7,10,11,13,15}
        _bad_tithis   = {4,6,8,9,12,14,30}
        _good_yogas   = {"Siddhi","Amriti","Shubha","Labha","Sukla","Brahma","Indra","Siddha",
                         "Sadhya","Priti","Ayushman","Saubhagya","Shobhana","Sukarma",
                         "Dhriti","Vriddhi","Dhruva","Harshana","Variyan","Shiva"}
        _bad_yogas    = {"Vyatipata","Ganda","Shoola","Atiganda","Vajra","Vyaghata",
                         "Vishkamba","Parigha","Vaidhriti"}

        vara_q  = "positive" if _vara_scores.get(vara_lord, 5) >= 7 else (
                  "negative" if _vara_scores.get(vara_lord, 5) <= 4 else "neutral")
        tithi_q = "positive" if tithi_num in _good_tithis else (
                  "negative" if tithi_num in _bad_tithis   else "neutral")
        yoga_q  = "positive" if yoga_name in _good_yogas else (
                  "negative" if yoga_name in _bad_yogas    else "neutral")

        # Nakshatra nature from panchang result
        nak_nature = pan.get("nakshatra", {}).get("nature", "Mixed")
        nak_q = "positive" if nak_nature == "Auspicious" else (
                "negative" if nak_nature == "Inauspicious" else "neutral")

        breakdown = [
            {"limb":"Vara",      "name":pan.get("vara",{}).get("name",""),
             "detail":f"Lord: {vara_lord}", "quality": vara_q},
            {"limb":"Tithi",     "name":pan.get("tithi",{}).get("name",""),
             "detail":pan.get("tithi",{}).get("paksha",""), "quality": tithi_q},
            {"limb":"Nakshatra", "name":nak_name,
             "detail":f"Lord: {pan.get('nakshatra',{}).get('lord','')}", "quality": nak_q},
            {"limb":"Yoga",      "name":yoga_name,
             "detail":pan.get("yoga",{}).get("nature",""), "quality": yoga_q},
            {"limb":"Karana",    "name":pan.get("karana",{}).get("name",""),
             "detail":pan.get("karana",{}).get("nature",""), "quality":"neutral"},
        ]

        # Inauspicious windows from sky data
        inauspicious = [
            {"name":"Rahu Kaal",   "time": sky.get("rahu_kaal","—"),   "color":"#7c3aed"},
            {"name":"Gulika Kaal", "time": sky.get("gulika_kaal","—"), "color":"#6b7280"},
            {"name":"Yamaghanta",  "time": sky.get("yamaghanta","—"),  "color":"#ef4444"},
        ]

        return jsonify({
            "date":         date_str,
            "weekday":      d.strftime("%A"),
            "score":        q,
            "panchang":     pan,
            "breakdown":    breakdown,
            "sunrise":      sky.get("sunrise","—"),
            "sunset":       sky.get("sunset","—"),
            "moonrise":     sky.get("moonrise","—"),
            "moonset":      sky.get("moonset","—"),
            "solar_noon":   sky.get("solar_noon","—"),
            "day_length":   sky.get("day_length","—"),
            "moon_phase":   sky.get("moon_phase_name","—"),
            "moon_phase_pct": sky.get("moon_phase_pct", 0),
            "abhijit":      pan.get("abhijit_muhurta","—"),
            "tarabala":     pan.get("tarabala",{}),
            "chandra_bala": pan.get("chandra_bala",{}),
            "inauspicious": inauspicious,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
#  Panchang
# ─────────────────────────────────────────────
@main.route("/panchang", methods=["GET", "POST"])
def panchang():
    error         = None
    panchang_data = None
    sky_data      = None

    today  = date.today()
    lat    = session.get("birth_lat", 28.6139)
    lon    = session.get("birth_lon", 77.2090)
    tz_str = session.get("birth_tz", "Asia/Kolkata")
    place  = session.get("birth_place", "New Delhi")

    birth_nak_idx = None
    dob = session.get("birth_dob")
    tob = session.get("birth_tob")
    if dob and tob:
        try:
            birth_dt = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
            import swisseph as swe_mod
            from .astrology.calculator import datetime_to_jd, get_planet_position
            jd = datetime_to_jd(birth_dt, tz_str)
            moon_pos = get_planet_position(jd, swe_mod.MOON)
            from .astrology.panchang import NAK_SPAN
            birth_nak_idx = int(moon_pos["longitude"] / NAK_SPAN)
        except Exception:
            pass

    if request.method == "POST":
        try:
            date_str = request.form.get("date", today.isoformat())
            place_q  = request.form.get("place", "").strip()
            lat_f    = request.form.get("lat", "")
            lon_f    = request.form.get("lon", "")
            tz_str_f = request.form.get("timezone", tz_str)

            if lat_f and lon_f:
                lat    = float(lat_f)
                lon    = float(lon_f)
                tz_str = tz_str_f
            elif place_q:
                geo = geocode_place(place_q)
                if "error" not in geo:
                    lat    = geo["lat"]
                    lon    = geo["lon"]
                    tz_str = geo["timezone"]
                    place  = geo.get("display_name", place_q)

            target_date   = date.fromisoformat(date_str)
            panchang_data = calculate_panchang(target_date, float(lat), float(lon),
                                               tz_str, birth_nak_idx)
            sky_data = panchang_data["sky"]
        except Exception as e:
            error = str(e)
            traceback.print_exc()
    else:
        try:
            panchang_data = calculate_panchang(today, float(lat), float(lon),
                                               tz_str, birth_nak_idx)
            sky_data = panchang_data["sky"]
        except Exception as e:
            error = str(e)

    return render_template("panchang.html",
                           panchang=panchang_data, sky=sky_data,
                           place=place, today=today.isoformat(), error=error)


# ─────────────────────────────────────────────
#  JSON API
# ─────────────────────────────────────────────
@main.route("/api/geocode")
def api_geocode():
    q = request.args.get("q", "")
    if not q:
        return jsonify({"error": "No query"}), 400
    return jsonify(geocode_place(q))


@main.route("/api/sky")
def api_sky():
    try:
        lat    = float(request.args.get("lat", 28.6139))
        lon    = float(request.args.get("lon", 77.2090))
        tz_str = request.args.get("tz", "Asia/Kolkata")
        date_s = request.args.get("date", date.today().isoformat())
        d      = date.fromisoformat(date_s)
        data   = get_sunrise_sunset_moonrise(d, lat, lon, tz_str)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@main.route("/api/panchang")
def api_panchang():
    try:
        lat    = float(request.args.get("lat", 28.6139))
        lon    = float(request.args.get("lon", 77.2090))
        tz_str = request.args.get("tz", "Asia/Kolkata")
        date_s = request.args.get("date", date.today().isoformat())
        d      = date.fromisoformat(date_s)
        data   = calculate_panchang(d, lat, lon, tz_str)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@main.route("/api/transit")
def api_transit():
    try:
        lat    = float(request.args.get("lat", session.get("birth_lat", 28.6139)))
        lon    = float(request.args.get("lon", session.get("birth_lon", 77.2090)))
        tz_str = request.args.get("tz", session.get("birth_tz", "Asia/Kolkata"))
        data   = calculate_transit_chart(lat, lon, tz_str)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@main.route("/api/saved-charts")
def api_saved_charts():
    return jsonify(list_charts())


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def _build_nak_house_map(transit_data: dict, natal_chart: dict | None) -> list:
    """
    For each transit planet: which natal house it occupies,
    which nakshatra it's in, and warning level.
    """
    from .astrology.predictions import TRANSIT_NAKSHATRA_WARNINGS, NAKSHATRA_MEANINGS, NAK_SPAN
    from .astrology.calculator import NAKSHATRA_NAMES, NAKSHATRA_LORDS, PLANET_COLORS

    if not natal_chart:
        return []

    lagna_house_map = {h["rashi"]: h["house"] for h in natal_chart["houses"]}
    result = []

    for p_name, p_data in transit_data["planets"].items():
        t_rashi     = p_data["rashi"]
        natal_house = lagna_house_map.get(t_rashi)
        nak_idx     = int(p_data["longitude"] / NAK_SPAN)
        nak_name    = NAKSHATRA_NAMES[nak_idx]
        nak_lord    = NAKSHATRA_LORDS[nak_idx]
        nak_meaning = NAKSHATRA_MEANINGS.get(nak_name, "")
        nak_warning = TRANSIT_NAKSHATRA_WARNINGS.get(nak_name)

        # Natal planet in same house?
        natal_house_occupants = []
        if natal_house:
            natal_house_occupants = natal_chart["house_occupants"].get(natal_house, [])

        result.append({
            "planet":      p_name,
            "symbol":      p_data.get("symbol", ""),
            "color":       PLANET_COLORS.get(p_name, "#fff"),
            "rashi":       p_data["rashi_name"],
            "longitude":   round(p_data["longitude"], 2),
            "dms":         p_data["dms"],
            "retrograde":  p_data.get("retrograde", False),
            "natal_house": natal_house,
            "natal_occupants": natal_house_occupants,
            "nakshatra":   nak_name,
            "nak_pada":    int((p_data["longitude"] % (360/27)) / (360/108)) + 1,
            "nak_lord":    nak_lord,
            "nak_meaning": nak_meaning,
            "nak_warning": nak_warning,
            "warning_level": (
                nak_warning[0] if nak_warning else
                "warning" if p_name in ("Saturn","Rahu","Ketu") else
                "positive" if p_name in ("Jupiter","Venus") else "neutral"
            ),
        })

    return result
