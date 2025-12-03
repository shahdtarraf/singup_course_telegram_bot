import json
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
COURSES_FILE = DATA_DIR / "courses.json"
GROUP_LINKS_FILE = DATA_DIR / "group_links.json"

try:
    # Primary source provided by user
    from .catalog import COURSES as CATALOG_COURSES, MATERIALS as CATALOG_MATERIALS
except Exception:
    CATALOG_COURSES, CATALOG_MATERIALS = {}, {}


def _read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _course_from_catalog(cid: str) -> Optional[Dict[str, Any]]:
    c = CATALOG_COURSES.get(cid)
    if not c:
        return None
    content = c.get("syllabus") or c.get("topics") or []
    return {
        "id": c.get("id", cid),
        "name": c.get("name", cid),
        "description": c.get("description", ""),
        "duration": c.get("duration"),
        "content": content,
        "lectures_count": len(content) if isinstance(content, list) else None,
        "price": c.get("price"),
        "level": c.get("level"),
        "category": c.get("category"),
    }


def _build_professional_courses(_: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Always build from catalog if available
    courses: List[Dict[str, Any]] = []
    if CATALOG_COURSES:
        for cid in CATALOG_COURSES.keys():
            unified = _course_from_catalog(cid)
            if unified:
                courses.append(unified)
        return courses
    # Fallback to courses.json schema
    data = _read_json(COURSES_FILE)
    course_info = data.get("course_info", {})
    levels = data.get("levels", {})
    id_map = {"beginner": "nlp_beginner", "intermediate": "nlp_intermediate", "advanced": "nlp_expert"}
    for key, level in levels.items():
        cid = id_map.get(key, f"nlp_{key}")
        name = f"{course_info.get('name', 'الدورة الاحترافية')} - {level.get('name', key)}"
        description = level.get("goal") or course_info.get("description", "")
        duration = level.get("duration", course_info.get("total_duration"))
        content = level.get("topics", [])
        courses.append({
            "id": cid,
            "name": name,
            "description": description,
            "duration": duration,
            "content": content,
            "lectures_count": len(content) if isinstance(content, list) else None,
            "price": None,
        })
    return courses


def _nice_material_name(material_key: str) -> str:
    key = material_key.lower()
    if "neural_networks" in key:
        return "الشبكات العصبونية"
    if key.endswith("_os") or key.endswith("_operating_systems") or key == "os":
        return "نظم تشغيل"
    if "multimedia" in key:
        return "ملتميديا"
    if "ai_principles" in key or "ai101" in key:
        return "مبادئ الذكاء الصنعي"
    if "algorithms" in key:
        return "الخوارزميات"
    if "python" in key:
        return "بايثون"
    if "concurrent" in key or "parallel" in key:
        return "برمجة متزامنة"
    return material_key.replace("_", " ")


def _material_from_catalog(mid: str) -> Optional[Dict[str, Any]]:
    m = CATALOG_MATERIALS.get(mid)
    if not m:
        return None
    return {
        "id": m.get("id", mid),
        "name": m.get("name", mid),
        "description": m.get("description", ""),
        "duration": None,
        "content": [],
        "lectures_count": None,
        "price": 75000,  # default single-material price
        "year": m.get("year"),
        "semester": m.get("semester"),
        "instructor": m.get("instructor"),
    }


def _build_university_courses(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Prefer building from group_links materials if available so IDs match links
    links = _read_json(GROUP_LINKS_FILE)
    materials = (links or {}).get("materials") or {}
    courses: List[Dict[str, Any]] = []
    if materials:
        for mid in materials.keys():
            unified = _material_from_catalog(mid)
            if unified:
                courses.append(unified)
            else:
                courses.append({
                    "id": mid,
                    "name": _nice_material_name(mid),
                    "description": "",
                    "duration": None,
                    "content": [],
                    "lectures_count": None,
                    "price": None,
                })
        return courses
    # Fallback to subjects in courses.json
    for subj in data.get("university_subjects", []):
        code = subj.get("code", "").lower()
        cid = f"uni_{code}" if code else subj.get("name", "subject").lower().replace(" ", "_")
        courses.append({
            "id": cid,
            "name": subj.get("name", cid),
            "description": subj.get("description", ""),
            "duration": None,
            "content": [],
            "lectures_count": None,
            "price": None,
        })
    return courses


def get_courses(category: str) -> List[Dict[str, Any]]:
    data = _read_json(COURSES_FILE)
    if category == "professional":
        return _build_professional_courses(data)
    if category == "university":
        return _build_university_courses(data)
    return []


def get_course_by_id(course_id: str) -> Optional[Dict[str, Any]]:
    # Prefer catalog first
    if CATALOG_COURSES.get(course_id):
        return _course_from_catalog(course_id)
    if CATALOG_MATERIALS.get(course_id):
        return _material_from_catalog(course_id)
    # Fallback to derived lists
    data = _read_json(COURSES_FILE)
    for c in _build_professional_courses(data):
        if c.get("id") == course_id:
            return c
    for c in _build_university_courses(data):
        if c.get("id") == course_id:
            return c
    return None


def get_group_link(course_id: str) -> Optional[str]:
    links = _read_json(GROUP_LINKS_FILE) or {}
    # flat mapping support
    if course_id in links:
        return links.get(course_id)
    # nested mapping support
    for section in ("courses", "materials"):
        sec = links.get(section)
        if isinstance(sec, dict) and course_id in sec:
            return sec.get(course_id)
    return None
