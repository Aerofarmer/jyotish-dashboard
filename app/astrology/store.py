"""
Chart persistence — save/load/delete Kundli charts to a local JSON store.
File: data/charts.json
"""
import json, os, uuid
from datetime import datetime
from pathlib import Path

STORE_PATH = Path(__file__).parent.parent.parent / "data" / "charts.json"


def _load_all() -> dict:
    if STORE_PATH.exists():
        try:
            return json.loads(STORE_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_all(data: dict):
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(data, indent=2, default=str))


def save_chart(chart: dict) -> str:
    """Persist a chart dict and return its unique ID."""
    charts = _load_all()
    cid = str(uuid.uuid4())[:8]
    charts[cid] = {
        "id": cid,
        "saved_at": datetime.now().isoformat(),
        "name": chart.get("name", "Unknown"),
        "place": chart.get("place", ""),
        "birth_datetime": chart.get("birth_datetime", ""),
        "timezone": chart.get("timezone", ""),
        "latitude": chart.get("latitude", 0),
        "longitude_coord": chart.get("longitude_coord", 0),
        "lagna": chart.get("lagna", {}),
        "planets": chart.get("planets", {}),
        "houses": chart.get("houses", []),
        "house_occupants": chart.get("house_occupants", {}),
        "navamsa": chart.get("navamsa", {}),
        "ayanamsa": chart.get("ayanamsa", 0),
    }
    _save_all(charts)
    return cid


def list_charts() -> list:
    """Return all saved charts as a sorted list (newest first)."""
    charts = _load_all()
    result = list(charts.values())
    result.sort(key=lambda c: c.get("saved_at", ""), reverse=True)
    return result


def get_chart(cid: str) -> dict | None:
    return _load_all().get(cid)


def delete_chart(cid: str) -> bool:
    charts = _load_all()
    if cid in charts:
        del charts[cid]
        _save_all(charts)
        return True
    return False
