from __future__ import annotations

import time
import re
from typing import Any
import requests
from threading import Lock
from concurrent.futures import Future, TimeoutError as FutureTimeoutError

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from crew_setup import crew


MAX_OUTPUT_CHARS = 2200
PLAN_CACHE_TTL_SECONDS = 180


class PlanRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    location: str = ""
    latitude: float | None = None
    longitude: float | None = None
    location_mode: str = "manual"


class PlanResponse(BaseModel):
    summary: dict[str, Any]
    hospitals: list[dict[str, Any]]
    doctors: list[dict[str, Any]]
    location_confidence: dict[str, str]
    plan: str


class CachedPlanEntry(BaseModel):
    response: PlanResponse
    created_at: float


_plan_cache: dict[str, CachedPlanEntry] = {}
_plan_cache_lock = Lock()
_inflight_requests: dict[str, Future[PlanResponse]] = {}
_inflight_lock = Lock()


def _format_concise_output(text: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return (
        cleaned[:max_chars].rstrip()
        + "\n\n[Output truncated for readability. Run again with a more specific city/topic for tighter results.]"
    )


def _normalize_line(line: str) -> str:
    cleaned = line.strip()
    cleaned = re.sub(r"^[#\-*•\d\.\)\s]+", "", cleaned)
    cleaned = cleaned.replace("**", "").strip()
    return cleaned


def _is_heading(line: str) -> str | None:
    heading = _normalize_line(line).rstrip(":").lower()
    aliases = {
        "condition summary": "condition_summary",
        "description": "condition_summary",
        "symptoms": "symptoms",
        "treatment guidance": "treatments",
        "treatments": "treatments",
        "recommended specialist": "specialist",
        "specialist": "specialist",
        "hospital names": "hospitals",
        "doctor/clinic names": "doctors",
        "doctor clinic names": "doctors",
        "doctors": "doctors",
    }
    return aliases.get(heading)


def _extract_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {
        "condition_summary": [],
        "symptoms": [],
        "treatments": [],
        "specialist": [],
        "hospitals": [],
        "doctors": [],
    }
    current: str | None = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        heading_key = _is_heading(line)
        if heading_key:
            current = heading_key
            continue

        if current:
            value = _normalize_line(line)
            if value:
                sections[current].append(value)

    return sections


def _dedupe(items: list[str], limit: int = 5) -> list[str]:
    out: list[str] = []
    for item in items:
        if item and item not in out:
            out.append(item)
        if len(out) >= limit:
            break
    return out


def _parse_summary(sections: dict[str, list[str]]) -> dict[str, Any]:
    description = " ".join(sections["condition_summary"]).strip() or "No description provided"
    symptoms = _dedupe(sections["symptoms"], limit=8)
    treatments = _dedupe(sections["treatments"], limit=8)
    specialist = " ".join(sections["specialist"]).strip() or "General Practitioner"
    return {
        "description": description,
        "symptoms": symptoms,
        "treatments": treatments,
        "specialist": specialist,
    }


def _parse_hospitals(sections: dict[str, list[str]], fallback_location: str) -> list[dict[str, str]]:
    return [
        {
            "name": name,
            "location": fallback_location,
            "timing": "Timing not available",
            "specialistDoctors": [],
        }
        for name in _dedupe(sections["hospitals"], limit=5)
    ]


def _parse_doctors(sections: dict[str, list[str]]) -> list[dict[str, str]]:
    doctors: list[dict[str, str]] = []
    for raw in _dedupe(sections["doctors"], limit=5):
        name = raw
        specialization = ""
        m = re.match(r"^(.*?)\s*\((.*?)\)\s*$", raw)
        if m:
            name = m.group(1).strip()
            specialization = m.group(2).strip()
        doctors.append(
            {
                "name": name,
                "specialization": specialization,
                "timing": "",
                "hospital": "",
            }
        )
    return doctors


def _attach_doctors_to_hospitals(
    hospitals: list[dict[str, Any]],
    doctors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not hospitals:
        return hospitals

    if not doctors:
        for hospital in hospitals:
            hospital["specialistDoctors"] = []
        return hospitals

    # Deterministic round-robin assignment so each hospital card shows specialist doctors.
    for index, doctor in enumerate(doctors):
        hospital_index = index % len(hospitals)
        name = (doctor.get("name") or "").strip()
        specialization = (doctor.get("specialization") or "").strip()
        label = f"{name} ({specialization})" if specialization else name
        if label:
            hospitals[hospital_index].setdefault("specialistDoctors", []).append(label)

    return hospitals


def _run_crew_with_retry(topic: str, location: str) -> str:
    max_attempts = 5
    result: Any = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = crew.kickoff(inputs={"topic": topic, "location": location})
            break
        except Exception as exc:
            error_text = str(exc)
            is_rate_limit = "rate_limit_exceeded" in error_text or "Rate limit reached" in error_text
            if is_rate_limit and attempt < max_attempts:
                wait_seconds = 8 * attempt
                match = re.search(r"try again in\s+([0-9]+(?:\.[0-9]+)?)s", error_text, flags=re.IGNORECASE)
                if match:
                    wait_seconds = max(wait_seconds, int(float(match.group(1))) + 2)
                time.sleep(wait_seconds)
                continue
            raise

    return _format_concise_output(str(result))


def _cache_key(topic: str, tool_location: str) -> str:
    return f"{topic.strip().lower()}|{tool_location.strip().lower()}"


def _get_cached_plan(key: str) -> PlanResponse | None:
    now = time.time()
    with _plan_cache_lock:
        entry = _plan_cache.get(key)
        if not entry:
            return None
        if now - entry.created_at > PLAN_CACHE_TTL_SECONDS:
            _plan_cache.pop(key, None)
            return None
        return entry.response


def _set_cached_plan(key: str, response: PlanResponse) -> None:
    with _plan_cache_lock:
        _plan_cache[key] = CachedPlanEntry(response=response, created_at=time.time())


def _begin_or_join_inflight(key: str) -> tuple[Future[PlanResponse], bool]:
    with _inflight_lock:
        existing = _inflight_requests.get(key)
        if existing:
            return existing, False
        created: Future[PlanResponse] = Future()
        _inflight_requests[key] = created
        return created, True


def _finish_inflight(key: str, future: Future[PlanResponse]) -> None:
    with _inflight_lock:
        # Remove only when this exact future is still the active one for the key.
        if _inflight_requests.get(key) is future:
            _inflight_requests.pop(key, None)


def _resolve_location_context(payload: PlanRequest) -> tuple[str, str]:
    has_coords = payload.latitude is not None and payload.longitude is not None
    location_text = (payload.location or "").strip()

    if payload.location_mode == "current" and has_coords:
        lat = float(payload.latitude)
        lon = float(payload.longitude)
        if not location_text:
            location_text = f"{lat:.4f}, {lon:.4f}"
        tool_location = f"coords:{lat},{lon}|{location_text}"
        return location_text, tool_location

    if location_text:
        return location_text, location_text

    if has_coords:
        lat = float(payload.latitude)
        lon = float(payload.longitude)
        fallback_label = f"{lat:.4f}, {lon:.4f}"
        return fallback_label, f"coords:{lat},{lon}|{fallback_label}"

    raise HTTPException(status_code=400, detail="location text or coordinates are required")


def _coords_from_tool_location(tool_location: str) -> tuple[float, float] | None:
    match = re.match(r"^coords:([+-]?\d+(?:\.\d+)?),([+-]?\d+(?:\.\d+)?)(?:\|.*)?$", tool_location)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def _geocode_location(location_text: str) -> tuple[float, float] | None:
    geocode_url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "agentic-ai-healthcare-assistant/1.0"}
    params = {
        "q": location_text,
        "format": "json",
        "limit": 1,
    }
    try:
        response = requests.get(geocode_url, params=params, headers=headers, timeout=8)
        if response.status_code != 200:
            return None
        data = response.json()
        if not data:
            return None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None


def _probe_osm_availability(lat: float, lon: float) -> tuple[bool, bool]:
    overpass_url = "https://overpass-api.de/api/interpreter"
    hospital_query = f"""
    [out:json][timeout:12];
    (
      node["amenity"="hospital"](around:30000,{lat},{lon});
      way["amenity"="hospital"](around:30000,{lat},{lon});
      relation["amenity"="hospital"](around:30000,{lat},{lon});
      node["healthcare"="hospital"](around:30000,{lat},{lon});
      way["healthcare"="hospital"](around:30000,{lat},{lon});
      relation["healthcare"="hospital"](around:30000,{lat},{lon});
    );
    out tags 1;
    """
    doctor_query = f"""
    [out:json][timeout:12];
    (
      node["amenity"="clinic"](around:30000,{lat},{lon});
      way["amenity"="clinic"](around:30000,{lat},{lon});
      relation["amenity"="clinic"](around:30000,{lat},{lon});
      node["amenity"="doctors"](around:30000,{lat},{lon});
      way["amenity"="doctors"](around:30000,{lat},{lon});
      relation["amenity"="doctors"](around:30000,{lat},{lon});
      node["healthcare"="doctor"](around:30000,{lat},{lon});
      way["healthcare"="doctor"](around:30000,{lat},{lon});
      relation["healthcare"="doctor"](around:30000,{lat},{lon});
    );
    out tags 1;
    """

    def _has_elements(query: str) -> bool:
        try:
            response = requests.get(overpass_url, params={"data": query}, timeout=10)
            if response.status_code != 200:
                return False
            data = response.json()
            return bool(data.get("elements"))
        except Exception:
            return False

    return _has_elements(hospital_query), _has_elements(doctor_query)


def _build_location_confidence(
    *,
    payload: PlanRequest,
    location_label: str,
    tool_location: str,
    hospitals_found: int,
    doctors_found: int,
) -> dict[str, str]:
    coords = _coords_from_tool_location(tool_location) or _geocode_location(location_label)
    hospital_osm = False
    doctor_osm = False

    if coords:
        hospital_osm, doctor_osm = _probe_osm_availability(coords[0], coords[1])

    base_confidence = "Exact GPS" if payload.location_mode == "current" and payload.latitude is not None and payload.longitude is not None else "City-level"

    hospital_confidence = base_confidence if hospital_osm and hospitals_found > 0 else "Fallback Web"
    doctor_confidence = base_confidence if doctor_osm and doctors_found > 0 else "Fallback Web"

    overall = "Exact GPS" if hospital_confidence == "Exact GPS" and doctor_confidence == "Exact GPS" else "City-level"
    if "Fallback Web" in {hospital_confidence, doctor_confidence}:
        overall = "Fallback Web"

    return {
        "overall": overall,
        "hospitals": hospital_confidence,
        "doctors": doctor_confidence,
        "location": location_label,
    }


app = FastAPI(title="Healthcare Planning API", version="1.0.0")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Healthcare API running 🚀"}

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate-plan", response_model=PlanResponse)
def generate_plan(payload: PlanRequest) -> PlanResponse:
    topic = payload.topic.strip()
    location_label, tool_location = _resolve_location_context(payload)

    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    cache_key = _cache_key(topic, tool_location)
    cached = _get_cached_plan(cache_key)
    if cached:
        return cached

    inflight_future, is_leader = _begin_or_join_inflight(cache_key)
    if not is_leader:
        try:
            return inflight_future.result(timeout=190)
        except FutureTimeoutError as exc:
            raise HTTPException(status_code=504, detail="Timed out waiting for in-flight request") from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to generate healthcare plan: {exc}") from exc

    try:
        final_text = _run_crew_with_retry(topic, tool_location)

        sections = _extract_sections(final_text)
        summary = _parse_summary(sections)
        hospitals = _parse_hospitals(sections, location_label)
        doctors = _parse_doctors(sections)
        hospitals = _attach_doctors_to_hospitals(hospitals, doctors)
        location_confidence = _build_location_confidence(
            payload=payload,
            location_label=location_label,
            tool_location=tool_location,
            hospitals_found=len(hospitals),
            doctors_found=len(doctors),
        )

        response_payload = PlanResponse(
            summary=summary,
            hospitals=hospitals,
            doctors=doctors,
            location_confidence=location_confidence,
            plan=final_text,
        )
        _set_cached_plan(cache_key, response_payload)
        if not inflight_future.done():
            inflight_future.set_result(response_payload)
        return response_payload
    except Exception as exc:
        if isinstance(exc, HTTPException):
            http_exc = exc
        else:
            error_text = str(exc)
            is_rate_limit = "rate_limit_exceeded" in error_text or "Rate limit reached" in error_text
            if is_rate_limit:
                retry_wait = "30-90"
                match = re.search(r"try again in\s+([0-9]+(?:\.[0-9]+)?)s", error_text, flags=re.IGNORECASE)
                if match:
                    retry_wait = str(max(15, int(float(match.group(1))) + 2))
                http_exc = HTTPException(
                    status_code=429,
                    detail=(
                        f"LLM rate limit reached. Please wait about {retry_wait} seconds and retry, "
                        "or use a lower-frequency model/account tier."
                    ),
                )
            else:
                http_exc = HTTPException(status_code=500, detail=f"Failed to generate healthcare plan: {exc}")

        if not inflight_future.done():
            inflight_future.set_exception(http_exc)
        raise http_exc from exc
    finally:
        _finish_inflight(cache_key, inflight_future)