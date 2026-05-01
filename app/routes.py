from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime, date
import pytz
import traceback

from .astrology.calculator import calculate_full_chart, calculate_transit_chart, get_sunrise_sunset_moonrise
from .astrology.dasha import calculate_vimshottari, dasha_summary
from .astrology.panchang import calculate_panchang
from .api.external import geocode_place, get_ip_location

main = Blueprint("main", __name__)


# ─────────────────────────────────────────────
#  Home — birth-data input form
# ─────────────────────────────────────────────
@main.route("/")
def index():
    ip_loc = get_ip_location()
    return render_template("index.html", ip_loc=ip_loc)


# ─────────────────────────────────────────────
#  Kundli (birth chart)
# ─────────────────────────────────────────────
@main.route("/kundli", methods=["GET", "POST"])
def kundli():
    error = None
    chart = None
    dasha = None
    nav_chart = None

    if request.method == "POST":
        try:
            name   = request.form.get("name", "").strip()
            dob    = request.form.get("dob", "")          # YYYY-MM-DD
            tob    = request.form.get("tob", "")          # HH:MM
            place  = request.form.get("place", "").strip()
            lat    = request.form.get("lat", "")
            lon    = request.form.get("lon", "")
            tz_str = request.form.get("timezone", "Asia/Kolkata")

            if not dob or not tob:
                raise ValueError("Date and time of birth are required.")

            # Geocode if lat/lon not provided
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
            chart = calculate_full_chart(birth_dt, float(lat), float(lon), tz_str, name=name, place=place)

            moon_lon   = chart["planets"]["Moon"]["longitude"]
            dasha_data = calculate_vimshottari(moon_lon, birth_dt)
            dasha      = dasha_data

            # Store in session for transit comparison
            session["birth_lat"]  = float(lat)
            session["birth_lon"]  = float(lon)
            session["birth_tz"]   = tz_str
            session["birth_name"] = name
            session["birth_place"]= place
            session["birth_dob"]  = dob
            session["birth_tob"]  = tob

        except Exception as e:
            error = str(e)
            traceback.print_exc()

    return render_template("kundli.html", chart=chart, dasha=dasha, error=error)


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

    # Natal chart for comparison
    natal_chart = None
    dob = session.get("birth_dob")
    tob = session.get("birth_tob")
    if dob and tob:
        try:
            birth_dt = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
            natal_chart = calculate_full_chart(birth_dt, float(lat), float(lon), tz_str,
                                               name=name, place=place)
        except Exception:
            pass

    return render_template("transit.html",
                           transit=transit_data,
                           natal=natal_chart,
                           tz_str=tz_str)


# ─────────────────────────────────────────────
#  Dasha chart
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
#  Panchang
# ─────────────────────────────────────────────
@main.route("/panchang", methods=["GET", "POST"])
def panchang():
    error      = None
    panchang_data = None
    sky_data   = None

    # Default to today + user location
    today     = date.today()
    lat       = session.get("birth_lat", 28.6139)
    lon       = session.get("birth_lon", 77.2090)
    tz_str    = session.get("birth_tz", "Asia/Kolkata")
    place     = session.get("birth_place", "New Delhi")

    # Birth nakshatra for Tarabala / Chandra Bala
    birth_nak_idx = None
    dob = session.get("birth_dob")
    tob = session.get("birth_tob")
    if dob and tob:
        try:
            birth_dt = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
            from .astrology.calculator import datetime_to_jd, get_planet_position
            import swisseph as swe_mod
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

            target_date = date.fromisoformat(date_str)
            panchang_data = calculate_panchang(target_date, float(lat), float(lon), tz_str, birth_nak_idx)
            sky_data = panchang_data["sky"]

        except Exception as e:
            error = str(e)
            traceback.print_exc()
    else:
        try:
            panchang_data = calculate_panchang(today, float(lat), float(lon), tz_str, birth_nak_idx)
            sky_data = panchang_data["sky"]
        except Exception as e:
            error = str(e)

    return render_template("panchang.html",
                           panchang=panchang_data,
                           sky=sky_data,
                           place=place,
                           today=today.isoformat(),
                           error=error)


# ─────────────────────────────────────────────
#  JSON API endpoints
# ─────────────────────────────────────────────
@main.route("/api/geocode")
def api_geocode():
    q = request.args.get("q", "")
    if not q:
        return jsonify({"error": "No query"}), 400
    return jsonify(geocode_place(q))


@main.route("/api/sky")
def api_sky():
    """Real-time sunrise/sunset/moonrise for a location."""
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
