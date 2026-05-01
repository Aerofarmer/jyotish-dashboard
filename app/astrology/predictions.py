"""
Full-spectrum daily prediction engine.
Sections: Overall, Mana Ki Baat (emotional), Love, Career,
          Major Changes, Enemy/Friend planets, Planet-by-planet.
"""
from datetime import datetime, date
from .calculator import (
    RASHI_NAMES, NAKSHATRA_NAMES, NAKSHATRA_LORDS,
    PLANET_COLORS, PLANET_SYMBOLS, WEEKDAYS, WEEKDAY_LORDS,
)
from .panchang import calculate_panchang

NAK_SPAN = 360 / 27

# ── Planetary friendships ─────────────────────────────────────────────────────
NATURAL_FRIENDS = {
    "Sun":     ["Moon", "Mars", "Jupiter"],
    "Moon":    ["Sun", "Mercury"],
    "Mars":    ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus":   ["Mercury", "Saturn"],
    "Saturn":  ["Mercury", "Venus", "Rahu"],
    "Rahu":    ["Venus", "Saturn", "Mercury"],
    "Ketu":    ["Venus", "Saturn", "Mercury"],
}
NATURAL_ENEMIES = {
    "Sun":     ["Venus", "Saturn", "Rahu", "Ketu"],
    "Moon":    ["Rahu", "Ketu"],
    "Mars":    ["Mercury", "Rahu", "Ketu"],
    "Mercury": ["Moon", "Rahu"],
    "Jupiter": ["Mercury", "Venus", "Rahu", "Ketu"],
    "Venus":   ["Sun", "Moon"],
    "Saturn":  ["Sun", "Moon", "Mars"],
    "Rahu":    ["Sun", "Moon", "Mars", "Jupiter"],
    "Ketu":    ["Sun", "Moon", "Mars", "Jupiter"],
}

NATURAL_BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}
NATURAL_MALEFICS = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}

# ── Vara lord (weekday) ───────────────────────────────────────────────────────
VARA_LORDS = {0:"Sun",1:"Moon",2:"Mars",3:"Mercury",4:"Jupiter",5:"Venus",6:"Saturn"}
VARA_COLORS = {
    "Sun":"#FF6B35", "Moon":"#C8D8E8", "Mars":"#FF4444",
    "Mercury":"#00CC88", "Jupiter":"#FFD700", "Venus":"#FF69B4", "Saturn":"#9CA3AF",
}
VARA_FAVORABLE = {
    "Sun":["#FF6B35","Orange","1","Aditya Hridayam"],
    "Moon":["#C8D8E8","White/Silver","2","Om Namah Shivaya"],
    "Mars":["#FF4444","Red","9","Hanuman Chalisa"],
    "Mercury":["#00CC88","Green","5","Vishnu Sahasranamam"],
    "Jupiter":["#FFD700","Yellow","3","Guru Stotram"],
    "Venus":["#FF69B4","Pink/White","6","Lakshmi Sahasranamam"],
    "Saturn":["#9CA3AF","Dark Blue/Black","8","Shani Stotra"],
}

# ── House keywords (for life areas) ──────────────────────────────────────────
HOUSE_AREAS = {
    1:"Self", 2:"Finance", 3:"Courage", 4:"Home/Property",
    5:"Education/Children", 6:"Enemies/Health", 7:"Relationships",
    8:"Longevity/Occult", 9:"Luck/Dharma", 10:"Career",
    11:"Gains/Income", 12:"Spirituality/Losses",
}

# ── Love house list ───────────────────────────────────────────────────────────
LOVE_HOUSES     = {5, 7}
CAREER_HOUSES   = {2, 6, 10, 11}
CHANGE_PLANETS  = {"Saturn", "Rahu", "Ketu"}
EMOTIONAL_PLANETS = {"Moon", "Venus", "Ketu"}

# ── Transit in house: domain-specific texts ───────────────────────────────────
LOVE_TRANSIT_TEXTS = {
    "Venus": {
        5:"Venus in your romance house — love blossoms naturally. Ideal for confessions, dates, and deepening bonds.",
        7:"Venus activates your marriage house. Harmony with partner. Strong attraction and desire for commitment.",
        1:"Venus on your Lagna — you radiate charm and magnetism. Admirers drawn to you.",
        12:"Venus in the 12th — secret romance possible. Spiritual love deepens.",
    },
    "Moon": {
        5:"Moon in the house of romance — emotions run high. Follow your heart but keep perspective.",
        7:"Moon activates partnerships. Emotional bonding with spouse or partner is highlighted.",
    },
    "Mars": {
        5:"Mars in the romance house — passion is intense. Physical attraction strong. Control impulsiveness.",
        7:"Mars in 7th — conflicts possible in relationships. Channel energy into positive engagement.",
    },
    "Jupiter": {
        5:"Jupiter blesses romance, creativity, and children. Auspicious for new relationships.",
        7:"Jupiter in the marriage house — blessings for partnerships and legal unions.",
    },
    "Saturn": {
        5:"Saturn in romance house — emotional distance or delays in love. Karmic relationships.",
        7:"Saturn in the 7th — challenges in marriage. Work through difficulties patiently.",
    },
    "Rahu": {
        5:"Rahu in the 5th — unusual romantic experiences. Foreign or unconventional partner.",
        7:"Rahu in the 7th — intense, obsessive relationships. Exercise discernment.",
    },
}

CAREER_TRANSIT_TEXTS = {
    "Sun": {
        10:"Sun on your career house — recognition, authority, and leadership are highlighted.",
        6:"Sun in the 6th — competitive advantage in workplace. Hard work is rewarded.",
        11:"Sun in gains house — income from authority figures or government.",
    },
    "Mars": {
        10:"Mars activates career — driven, ambitious, competitive. Avoid conflicts with superiors.",
        6:"Mars conquers workplace challenges. Energy directed toward service excels.",
        11:"Mars in gains — active pursuit of goals pays off.",
    },
    "Saturn": {
        10:"Saturn transiting career house — results through sustained, disciplined effort.",
        6:"Saturn in 6th — hard work defeats enemies and clears debts.",
    },
    "Jupiter": {
        10:"Jupiter blesses career with wisdom, recognition, and expansion. Promotions possible.",
        11:"Jupiter in gains — abundant income and fulfilled professional goals.",
        9:"Jupiter in dharma — career aligned with higher purpose.",
    },
    "Mercury": {
        10:"Mercury in career — intellect, communication, and skills shine professionally.",
        11:"Mercury in gains — business networking pays dividends.",
    },
    "Rahu": {
        10:"Rahu in career — rapid but unconventional career rise. Foreign opportunities.",
        11:"Rahu in gains — large but sudden gains. Handle with discipline.",
    },
    "Venus": {
        10:"Venus in career — arts, beauty, luxury, or entertainment sectors favored.",
        11:"Venus in gains — income through pleasurable or creative work.",
    },
}

# ── Nakshatra warning table ───────────────────────────────────────────────────
TRANSIT_NAKSHATRA_WARNINGS = {
    "Ardra":    ("warning", "Storms and turmoil possible. Be patient."),
    "Ashlesha": ("warning", "Deception and hidden enemies. Trust carefully."),
    "Jyeshtha": ("warning", "Power struggles and ego clashes. Stay humble."),
    "Mula":     ("danger",  "Uprooting energy — unexpected losses or changes."),
    "Purva Bhadrapada": ("warning", "Intense fiery period. Control anger."),
    "Vishakha": ("caution", "Goal-driven but beware obsession and rivalry."),
    "Atiganda": ("caution", "Obstacles in path. Slow down and re-evaluate."),
    "Ganda":    ("caution", "Rough period — avoid major decisions."),
    "Vyatipata":("danger",  "Highly inauspicious yoga. Avoid new ventures."),
}

NAKSHATRA_MEANINGS = {
    "Ashwini":"New beginnings, healing, speed.",
    "Bharani":"Transformation, creativity, Yama's energy.",
    "Krittika":"Sharp, purifying, Sun's nakshatra — fame and courage.",
    "Rohini":"Growth, beauty, fertility — material pleasures.",
    "Mrigashira":"Searching, gentle, curious — good for research.",
    "Ardra":"Storms and renewal, Rudra's energy — transformation through destruction.",
    "Punarvasu":"Restoration, abundance — return of light and hope.",
    "Pushya":"Nourishment, prosperity — most auspicious nakshatra.",
    "Ashlesha":"Serpent energy, mysticism, clinging — intense.",
    "Magha":"Royal ancestors, power, authority — ancestral blessings.",
    "Purva Phalguni":"Pleasure, creativity, romance and artistic expression.",
    "Uttara Phalguni":"Patronage, contracts — good for alliances.",
    "Hasta":"Skill, dexterity, craftsmanship — healing and work.",
    "Chitra":"Brilliance, artistry — creativity and architecture.",
    "Swati":"Independence, trade — business and travel favored.",
    "Vishakha":"Goal-oriented — achievement through effort.",
    "Anuradha":"Devotion, friendship, loyalty and cooperation.",
    "Jyeshtha":"Power, seniority, Indra — leadership but watch arrogance.",
    "Mula":"Root destruction — uprooting for new growth.",
    "Purva Ashadha":"Victory, purification — early wins and optimism.",
    "Uttara Ashadha":"Final victory — lasting achievements.",
    "Shravana":"Listening, learning, Vishnu — knowledge and fame.",
    "Dhanishtha":"Wealth, music, abundance.",
    "Shatabhisha":"Healing, mystery, Varuna — medicine and secrets.",
    "Purva Bhadrapada":"Fiery transformation — intensity and wisdom.",
    "Uttara Bhadrapada":"Depth, wisdom, spiritual maturity.",
    "Revati":"Safe journey, compassion — completion and nourishment.",
}

# ── Dasha lord predictions ────────────────────────────────────────────────────
DASHA_PREDICTIONS = {
    "Sun":     "The Sun Mahadasha brings focus on authority, career, government dealings, and self-expression. Father's influence is strong. Health of the heart and eyes needs attention.",
    "Moon":    "The Moon Mahadasha favors emotional growth, public recognition, and mother's blessings. Mind and intuition are heightened. Travel near water is favorable.",
    "Mars":    "The Mars Mahadasha gives energy, courage, and competitive drive. Property and land dealings are highlighted. Be cautious of accidents and conflicts.",
    "Mercury": "The Mercury Mahadasha excels in communication, business, intellect, and writing. Education and trade flourish. Nervous system health needs attention.",
    "Jupiter": "The Jupiter Mahadasha is one of the most auspicious periods — wisdom, prosperity, children, and spiritual growth expand. Guru's blessings are present.",
    "Venus":   "The Venus Mahadasha brings luxury, romance, creative arts, and material comforts. Marriage and partnerships are in focus. Enjoy beauty and culture.",
    "Saturn":  "The Saturn Mahadasha demands discipline, hard work, and patience. Material rewards come through sustained effort. Delays are temporary blessings in disguise.",
    "Rahu":    "The Rahu Mahadasha is intense — ambition, foreign connections, and unconventional paths dominate. Avoid deception. Transformation is the theme.",
    "Ketu":    "The Ketu Mahadasha is deeply spiritual — past-life karma resolves. Detachment from material world grows. Occult and metaphysical interests deepen.",
}

ANTARDASHA_OVERLAY = {
    "Sun":     "Sun Antardasha adds vitality, authority, and governmental support.",
    "Moon":    "Moon Antardasha brings emotional sensitivity and mother's blessings.",
    "Mars":    "Mars Antardasha energizes and increases drive. Caution with conflicts.",
    "Mercury": "Mercury Antardasha sharpens intellect and business acumen.",
    "Jupiter": "Jupiter Antardasha is auspicious — wisdom and expansion prevail.",
    "Venus":   "Venus Antardasha brings pleasures, romance, and material gains.",
    "Saturn":  "Saturn Antardasha requires discipline. Delays eventually reward.",
    "Rahu":    "Rahu Antardasha intensifies ambition and creates unusual events.",
    "Ketu":    "Ketu Antardasha deepens spirituality and karmic resolution.",
}

# ── Emotional states by Moon transit house from natal Moon ───────────────────
EMOTIONAL_BY_HOUSE = {
    1: ("Introspective & self-aware", "You feel deeply in touch with yourself today. Ideal for self-reflection and journaling."),
    2: ("Financially anxious", "Concerns around money or family may weigh on your mind. Ground yourself in gratitude."),
    3: ("Bold & communicative", "Your mind is sharp and expressive. Great day for conversations and creative writing."),
    4: ("Home-loving & nostalgic", "A longing for comfort and home. Connect with family or spend time in nature."),
    5: ("Joyful & romantic", "Heart is light and playful. Creative inspiration flows. Good day for love and art."),
    6: ("Anxious & competitive", "You may feel challenged or irritated by others. Channel this into productive effort."),
    7: ("Socially warm", "You crave connection and harmony. Reach out to loved ones and partners."),
    8: ("Intense & transformative", "Deep emotions surface today. Avoid suppression — let feelings guide insight."),
    9: ("Optimistic & philosophical", "You feel expansive and hopeful. Good day for learning, travel, or worship."),
    10: ("Ambitious & driven", "Career energy is high. You feel purposeful and want to achieve. Act on it."),
    11: ("Social & aspirational", "Desire for recognition and fulfillment is strong. Friends bring good news."),
    12: ("Withdrawn & dreamy", "You feel quiet, spiritual, or sleepy. Honor the need for solitude and rest."),
}

MOON_PHASE_MOOD = {
    "New Moon":        "New beginnings energy — set intentions. You may feel a quiet, inward pull.",
    "Waxing Crescent": "Momentum building — optimism and enthusiasm grow.",
    "First Quarter":   "Action and decisions — inner tension between comfort and growth.",
    "Waxing Gibbous":  "Refinement and effort — hard work brings results.",
    "Full Moon":       "Emotions peak — heightened sensitivity, revelation, and culmination.",
    "Waning Gibbous":  "Gratitude and sharing — release what no longer serves.",
    "Last Quarter":    "Release and forgiveness — letting go of old patterns.",
    "Waning Crescent": "Rest and surrender — introspection before a new cycle.",
}

# ── Enemy/friend of the day ───────────────────────────────────────────────────
def get_planet_of_day(today: date) -> dict:
    """Vara (weekday) lord and its friends/enemies."""
    # Python weekday: Monday=0, but Indian week: Sunday=0
    idx = (today.weekday() + 1) % 7
    lord = VARA_LORDS[idx]
    friends = NATURAL_FRIENDS.get(lord, [])
    enemies = NATURAL_ENEMIES.get(lord, [])
    color, fav_color, fav_num, mantra = VARA_FAVORABLE.get(lord, ["#fff","","",""])
    return {
        "vara_lord": lord,
        "color": PLANET_COLORS.get(lord, "#fff"),
        "favorable_color": fav_color,
        "lucky_number": fav_num,
        "mantra": mantra,
        "friends": friends,
        "enemies": enemies,
        "enemy_planet": enemies[0] if enemies else None,
        "friend_planet": friends[0] if friends else None,
    }


# ── Sade Sati / Kantaka Shani ─────────────────────────────────────────────────
def check_sade_sati(saturn_rashi: int, natal_moon_rashi: int) -> dict | None:
    h = (saturn_rashi - natal_moon_rashi) % 12
    if h == 11:
        phase, severity = "Rising Phase (12th from Moon)", "Moderate"
    elif h == 0:
        phase, severity = "Peak Phase (on natal Moon)", "High"
    elif h == 1:
        phase, severity = "Setting Phase (2nd from Moon)", "Moderate"
    else:
        return None
    return {
        "active": True, "phase": phase, "severity": severity,
        "message": (
            f"Sade Sati Active ({phase}) — Saturn's 7.5-year trial. "
            "Demands patience, discipline, and spiritual practice. "
            "Delays and obstacles are temporary and character-building."
        ),
    }


def check_kantaka_shani(saturn_rashi: int, natal_moon_rashi: int) -> dict | None:
    h = (saturn_rashi - natal_moon_rashi) % 12
    labels = {3:"4th", 6:"7th", 7:"8th", 9:"10th"}
    if h in labels:
        return {
            "active": True,
            "message": f"Kantaka Shani Active — Saturn in {labels[h]} from natal Moon. Career and emotional challenges need patience.",
        }
    return None


# ── Transit aspect checker ────────────────────────────────────────────────────
def transit_aspects(transit_planets: dict, natal_planets: dict) -> list:
    aspects = []
    for t_name, t_data in transit_planets.items():
        for n_name, n_data in natal_planets.items():
            diff = abs(t_data["longitude"] - n_data["longitude"]) % 360
            if diff > 180:
                diff = 360 - diff
            if diff <= 10:
                atype = "Conjunction"
            elif abs(diff - 180) <= 10:
                atype = "Opposition"
            else:
                continue
            is_bad = t_name in NATURAL_MALEFICS
            sev = "danger" if t_name in ("Saturn","Rahu") else "warning" if is_bad else "positive"
            aspects.append({
                "transit_planet": t_name, "natal_planet": n_name,
                "aspect": atype, "orb": round(diff, 2), "severity": sev,
                "transit_color": PLANET_COLORS.get(t_name, "#fff"),
                "natal_color":   PLANET_COLORS.get(n_name, "#fff"),
                "message": (
                    f"Transit {t_name} {atype.lower()}s natal {n_name} "
                    f"({'challenging' if is_bad else 'blessing'} — "
                    f"{'pressure and karmic lessons' if is_bad else 'grace and expansion'})."
                ),
            })
    return aspects


# ── Master function ───────────────────────────────────────────────────────────
def generate_predictions(natal_chart: dict, transit_chart: dict,
                          dasha_data: dict, lat: float, lon: float,
                          tz_str: str) -> dict:

    natal_planets   = natal_chart["planets"]
    transit_planets = transit_chart["planets"]
    natal_moon_rashi = natal_planets["Moon"]["rashi"]
    lagna_house_map  = {h["rashi"]: h["house"] for h in natal_chart["houses"]}

    today    = date.today()
    panchang = calculate_panchang(
        today, lat, lon, tz_str,
        birth_nak_idx=int(natal_planets["Moon"]["longitude"] / NAK_SPAN)
    )

    # ── Vara (day lord) ───────────────────────────────────────────────────────
    day_info = get_planet_of_day(today)

    # ── Dasha lords ───────────────────────────────────────────────────────────
    maha  = dasha_data.get("current_maha")
    antar = dasha_data.get("current_antar")
    prat  = dasha_data.get("current_pratyantar")
    maha_lord  = maha["lord"]  if maha  else "Unknown"
    antar_lord = antar["lord"] if antar else "Unknown"
    prat_lord  = prat["lord"]  if prat  else "Unknown"

    # ── Sade Sati / Kantaka ───────────────────────────────────────────────────
    saturn_rashi  = transit_planets["Saturn"]["rashi"]
    sade_sati     = check_sade_sati(saturn_rashi, natal_moon_rashi)
    kantaka_shani = check_kantaka_shani(saturn_rashi, natal_moon_rashi) if not sade_sati else None

    # ── Transit planet → natal house map ─────────────────────────────────────
    t_in_house = {}
    for p, d in transit_planets.items():
        h = lagna_house_map.get(d["rashi"])
        if h:
            t_in_house[p] = h

    # ── Emotional / Mana Ki Baat ──────────────────────────────────────────────
    transit_moon_rashi = transit_planets["Moon"]["rashi"]
    moon_house_from_natal = ((transit_moon_rashi - natal_moon_rashi) % 12) + 1
    emo_label, emo_detail = EMOTIONAL_BY_HOUSE.get(moon_house_from_natal,
                                                    ("Neutral","Steady emotional state."))
    moon_nak_name = NAKSHATRA_NAMES[int(transit_planets["Moon"]["longitude"] / NAK_SPAN)]
    moon_phase    = panchang["sky"].get("moon_phase_name","")
    moon_phase_mood = MOON_PHASE_MOOD.get(moon_phase, "")
    moon_house_natal = t_in_house.get("Moon")

    # Ruling emotion planet: the planet that controls the current moon nakshatra lord
    moon_nak_lord = NAKSHATRA_LORDS[int(transit_planets["Moon"]["longitude"] / NAK_SPAN)]

    # ── Love predictions ──────────────────────────────────────────────────────
    love_texts = []
    love_severity = "neutral"
    for p in ["Venus","Moon","Mars","Jupiter","Saturn","Rahu"]:
        h = t_in_house.get(p)
        if h and h in LOVE_TRANSIT_TEXTS.get(p, {}):
            txt = LOVE_TRANSIT_TEXTS[p][h]
            sev = "positive" if p in NATURAL_BENEFICS else "warning" if p in ("Saturn","Rahu","Ketu") else "caution"
            love_texts.append({"planet": p, "house": h, "text": txt, "severity": sev,
                                "color": PLANET_COLORS.get(p,"#fff"),
                                "symbol": PLANET_SYMBOLS.get(p,"")})
            if sev in ("warning","danger") and love_severity == "neutral":
                love_severity = sev
            elif sev == "positive" and love_severity == "neutral":
                love_severity = "positive"

    # Venus & 5th/7th house lord general
    venus_house  = t_in_house.get("Venus")
    venus_retro  = transit_planets["Venus"].get("retrograde", False)
    love_overall = (
        "Venus is retrograde — avoid starting new relationships or making major love decisions." if venus_retro else
        "Venus in a love/marriage house — romance and connection favored today." if venus_house in (5,7) else
        "Love energy is steady. Small gestures of affection go a long way today."
    )

    # ── Career predictions ────────────────────────────────────────────────────
    career_texts = []
    career_severity = "neutral"
    for p in ["Sun","Mars","Saturn","Jupiter","Mercury","Rahu","Venus"]:
        h = t_in_house.get(p)
        if h and h in CAREER_TRANSIT_TEXTS.get(p, {}):
            txt = CAREER_TRANSIT_TEXTS[p][h]
            sev = "positive" if p in NATURAL_BENEFICS else "warning" if p in ("Saturn","Rahu") else "caution"
            career_texts.append({"planet": p, "house": h, "text": txt, "severity": sev,
                                  "color": PLANET_COLORS.get(p,"#fff"),
                                  "symbol": PLANET_SYMBOLS.get(p,"")})
            if sev == "warning" and career_severity != "danger":
                career_severity = sev
            elif sev == "positive" and career_severity == "neutral":
                career_severity = "positive"

    # Dasha lord and career
    if maha_lord in ("Jupiter","Venus","Mercury","Sun"):
        dasha_career = f"{maha_lord} Mahadasha supports career advancement and recognition."
    elif maha_lord in ("Saturn","Rahu"):
        dasha_career = f"{maha_lord} Mahadasha demands sustained effort — shortcuts won't work."
    else:
        dasha_career = f"{maha_lord} Mahadasha brings energy and drive to professional goals."

    # ── Major changes ─────────────────────────────────────────────────────────
    change_alerts = []
    for p in ["Saturn","Rahu","Ketu"]:
        h = t_in_house.get(p)
        if not h:
            continue
        if p == "Saturn" and h in (1,4,7,10):
            change_alerts.append({
                "planet": p, "house": h, "severity": "warning",
                "color": PLANET_COLORS[p],
                "message": f"Saturn in house {h} ({HOUSE_AREAS[h]}) — major karmic restructuring. "
                           f"Discipline and patience bring long-term reward. This is a defining transit.",
            })
        elif p == "Rahu" and h in (1,4,7,10):
            change_alerts.append({
                "planet": p, "house": h, "severity": "warning",
                "color": PLANET_COLORS[p],
                "message": f"Rahu in house {h} ({HOUSE_AREAS[h]}) — unconventional and sudden changes. "
                           f"Foreign influence, ambition, and disruption. Stay grounded.",
            })
        elif p == "Ketu" and h in (1,4,7,10):
            change_alerts.append({
                "planet": p, "house": h, "severity": "caution",
                "color": PLANET_COLORS[p],
                "message": f"Ketu in house {h} ({HOUSE_AREAS[h]}) — spiritual detachment and karmic release. "
                           f"Past-life patterns surface. Great for spiritual progress.",
            })
    if sade_sati:
        change_alerts.insert(0, {"planet":"Saturn","house":0,"severity":"danger",
                                  "color":PLANET_COLORS["Saturn"],"message":sade_sati["message"]})
    if kantaka_shani:
        change_alerts.insert(0, {"planet":"Saturn","house":0,"severity":"warning",
                                  "color":PLANET_COLORS["Saturn"],"message":kantaka_shani["message"]})

    # ── Planet-by-planet forecasts ────────────────────────────────────────────
    planet_forecasts = _build_planet_forecasts(transit_planets, natal_chart, lagna_house_map)

    # ── Transit aspects ───────────────────────────────────────────────────────
    aspects = transit_aspects(transit_planets, natal_planets)

    # ── Panchang summary ──────────────────────────────────────────────────────
    yoga_name  = panchang["yoga"]["name"]
    tithi_name = f"{panchang['tithi']['paksha']} {panchang['tithi']['name']}"
    is_auspicious = panchang.get("is_auspicious", True)

    # ── Overall score (1–10) ──────────────────────────────────────────────────
    score = 5
    if is_auspicious:         score += 1
    if maha_lord == "Jupiter":score += 1
    if maha_lord in ("Venus","Moon","Mercury"): score += 1
    if maha_lord in ("Saturn","Rahu","Ketu"):   score -= 1
    if antar_lord in ("Jupiter","Venus"):        score += 1
    if antar_lord in ("Saturn","Rahu","Ketu"):   score -= 1
    if sade_sati:             score -= 2
    if yoga_name in ("Siddhi","Vriddhi","Priti","Shubha","Brahma","Indra"): score += 1
    if yoga_name in ("Vishkamba","Atiganda","Vyatipata","Vaidhriti","Ganda","Shula"): score -= 1
    if moon_house_from_natal in (1,5,9):         score += 1
    if moon_house_from_natal in (6,8,12):        score -= 1
    score = max(1, min(10, score))
    score_color = (
        "#22c55e" if score >= 8 else
        "#FFD700" if score >= 6 else
        "#FF6B35" if score >= 4 else "#ef4444"
    )
    score_label = (
        "Highly Auspicious" if score >= 9 else "Auspicious" if score >= 7 else
        "Moderate"          if score >= 5 else "Challenging" if score >= 3 else "Difficult"
    )

    return {
        "date": today.strftime("%A, %d %B %Y"),
        "score": score,
        "score_label": score_label,
        "score_color": score_color,

        # Day lord
        "day_info": day_info,

        # Dasha
        "maha_lord": maha_lord,
        "antar_lord": antar_lord,
        "prat_lord": prat_lord,
        "dasha_text": DASHA_PREDICTIONS.get(maha_lord,""),
        "antar_text": ANTARDASHA_OVERLAY.get(antar_lord,""),
        "maha_color": PLANET_COLORS.get(maha_lord,"#fff"),
        "antar_color": PLANET_COLORS.get(antar_lord,"#fff"),
        "prat_color":  PLANET_COLORS.get(prat_lord,"#fff"),
        "maha_end":  maha["end"]  if maha  else "—",
        "antar_end": antar["end"] if antar else "—",

        # Alerts
        "sade_sati":     sade_sati,
        "kantaka_shani": kantaka_shani,

        # Emotional / Mana Ki Baat
        "emo_label":        emo_label,
        "emo_detail":       emo_detail,
        "moon_phase":       moon_phase,
        "moon_phase_mood":  moon_phase_mood,
        "moon_nak":         moon_nak_name,
        "moon_nak_lord":    moon_nak_lord,
        "moon_house_from_natal": moon_house_from_natal,
        "moon_nak_lord_color": PLANET_COLORS.get(moon_nak_lord,"#fff"),
        "moon_nak_meaning": NAKSHATRA_MEANINGS.get(moon_nak_name,""),
        "moon_nak_warning": TRANSIT_NAKSHATRA_WARNINGS.get(moon_nak_name),

        # Love
        "love_texts":   love_texts,
        "love_overall": love_overall,
        "love_severity":love_severity,
        "venus_house":  venus_house,
        "venus_retro":  venus_retro,

        # Career
        "career_texts":    career_texts,
        "career_severity": career_severity,
        "dasha_career":    dasha_career,

        # Major changes
        "change_alerts": change_alerts,

        # Planet forecasts
        "planet_forecasts": planet_forecasts,

        # Aspects
        "aspects": aspects,

        # Panchang
        "panchang": panchang,
        "panchang_ok": is_auspicious,
        "yoga_name": yoga_name,
        "tithi_name": tithi_name,
    }


# ── Per-planet forecast builder ───────────────────────────────────────────────
TRANSIT_IN_HOUSE = {
    "Sun":     {1:"Strong vitality. Good for health and authority.",2:"Financial focus. Watch speech.",3:"Courage and communication boosted.",4:"Home/property matters active. Mother's health.",5:"Creative expression and romance active.",6:"Defeating enemies. Health improves.",7:"Partnership focus. Legal matters.",8:"Research and transformation.",9:"Auspicious for spirituality and travel.",10:"Career advancement. Recognition from authorities.",11:"Gains and income favored.",12:"Foreign links. Spiritual retreat."},
    "Moon":    {1:"Emotional sensitivity high. Good public image.",2:"Family gains. Emotional spending.",3:"Travel and communication favored.",4:"Comfort at home. Mother's influence strong.",5:"Romance and creativity flourish.",6:"Emotional health challenges.",7:"Emotional connection with partner.",8:"Avoid emotional decisions. Intuition heightened.",9:"Spiritual inclinations. Good fortune.",10:"Public recognition. Career satisfaction.",11:"Social gains. Desires fulfilled.",12:"Introspection. Emotional expenditure."},
    "Mars":    {1:"High energy. Accident-prone. Assertive.",2:"Financial aggression. Family disputes.",3:"Courage and boldness. Sports and competition.",4:"Property disputes possible. Tension at home.",5:"Passionate romance. Speculation risk.",6:"Excellent for defeating enemies.",7:"Conflicts in marriage. Legal disputes.",8:"Surgery risk. Inheritance possible.",9:"Aggressive beliefs. Long journeys.",10:"Career driven. High ambition.",11:"Income from efforts. Goals achieved.",12:"Hidden enemies active. Secret efforts."},
    "Mercury": {1:"Sharp intellect. Good for learning.",2:"Financial planning. Business negotiations.",3:"Excellent for writing and speaking.",4:"Intellectual home environment.",5:"Academic success. Creative writing.",6:"Analytical in dealing with disputes.",7:"Smart partnerships. Negotiations succeed.",8:"Research and investigation favored.",9:"Higher studies and philosophy.",10:"Career through intellect. Media favored.",11:"Networking brings gains.",12:"Private communications. Foreign language."},
    "Jupiter": {1:"Excellent — wisdom, health, and prosperity expand.",2:"Financial gains and family harmony.",3:"Courage and optimism. Spiritual journeys.",4:"Home expansion. Property gains.",5:"Children's blessings. Educational success.",6:"Health improves. Enemies subdued.",7:"Blessed partnerships and marriage.",8:"Spiritual transformation. Inheritance possible.",9:"Highly auspicious — dharma and luck flow.",10:"Career growth and recognition.",11:"Large gains and fulfilled aspirations.",12:"Spiritual liberation. Foreign blessings."},
    "Venus":   {1:"Charm, beauty, and social grace enhanced.",2:"Financial prosperity. Family harmony.",3:"Creative communication. Short journeys.",4:"Home beautification. Domestic harmony.",5:"Romance and creative arts flourish.",6:"Health through beauty. Overcoming rivals.",7:"Marriage and partnerships highly favored.",8:"Gains through partner or inheritance.",9:"Spiritual pleasures. Luxury travel.",10:"Career in arts or entertainment shines.",11:"Social gains and pleasures.",12:"Sensual pleasures. Foreign romance."},
    "Saturn":  {1:"Health challenges. Delays. Discipline needed.",2:"Financial restrictions. Family burdens.",3:"Hard work with siblings. Slow progress.",4:"Property delays. Home repairs.",5:"Children require attention. Study through effort.",6:"Hard work defeats enemies.",7:"Delays in partnerships. Work harder.",8:"Longevity concerns. Transformation.",9:"Disciplined spiritual practice.",10:"Career rewards after hard work.",11:"Gains through sustained effort.",12:"Spiritual discipline. Foreign isolation."},
    "Rahu":    {1:"Unusual experiences. Ambition intensified.",2:"Unconventional income. Family disruption.",3:"Bold unconventional communication.",4:"Property through unusual means.",5:"Speculative gains. Unusual romance.",6:"Defeating enemies through strategy.",7:"Unconventional partnerships.",8:"Occult experiences. Hidden gains.",9:"Unusual spiritual path. Foreign travel.",10:"Career success through unconventional means.",11:"Gains from foreigners. Ambitious goals.",12:"Foreign travel. Hidden spirituality."},
    "Ketu":    {1:"Spiritual detachment. Unusual health.",2:"Detachment from wealth. Spiritual speech.",3:"Past-life courage. Solitary journeys.",4:"Detachment from home. Ancestral property.",5:"Past-life intelligence. Detachment from romance.",6:"Spiritual defeat of enemies.",7:"Karmic partnerships. Spiritual spouse.",8:"Deep spiritual transformation.",9:"Spiritual dharma from past lives.",10:"Career through spiritual or technical skills.",11:"Past-life gains. Detachment from friendships.",12:"Liberation and moksha. Past-life spiritual merit."},
}


def _build_planet_forecasts(transit_planets, natal_chart, lagna_house_map) -> list:
    forecasts = []
    natal_planets = natal_chart["planets"]
    house_occupants = natal_chart["house_occupants"]

    for p_name, p_data in transit_planets.items():
        t_rashi     = p_data["rashi"]
        natal_house = lagna_house_map.get(t_rashi)
        nak_idx     = int(p_data["longitude"] / NAK_SPAN)
        nak_name    = NAKSHATRA_NAMES[nak_idx]
        nak_lord    = NAKSHATRA_LORDS[nak_idx]
        pred_text   = TRANSIT_IN_HOUSE.get(p_name, {}).get(natal_house, "") if natal_house else ""

        # Natal planets in same house (conjunction effect)
        conjoined_natal = house_occupants.get(natal_house, []) if natal_house else []

        sev = (
            "danger"   if p_name in ("Saturn","Rahu") and natal_house in (1,4,7,8) else
            "warning"  if p_name in NATURAL_MALEFICS else
            "positive" if p_name in NATURAL_BENEFICS else
            "neutral"
        )
        nak_warning = TRANSIT_NAKSHATRA_WARNINGS.get(nak_name)

        forecasts.append({
            "planet": p_name,
            "symbol": p_data.get("symbol",""),
            "color": PLANET_COLORS.get(p_name,"#fff"),
            "rashi": p_data["rashi_name"],
            "dms": p_data["dms"],
            "retrograde": p_data.get("retrograde", False),
            "natal_house": natal_house,
            "house_area": HOUSE_AREAS.get(natal_house,"") if natal_house else "",
            "nakshatra": nak_name,
            "nak_lord": nak_lord,
            "nak_lord_color": PLANET_COLORS.get(nak_lord,"#fff"),
            "nak_meaning": NAKSHATRA_MEANINGS.get(nak_name,""),
            "nak_warning": nak_warning,
            "prediction": pred_text,
            "severity": sev,
            "conjoined_natal": conjoined_natal,
        })

    return forecasts
