from dotenv import load_dotenv
load_dotenv()

import os
from crewai import Agent

from crewai.tools import BaseTool
from ddgs import DDGS
import requests
import re
# ✅ USE STRING (THIS FIXES EVERYTHING)
llm = "groq/llama3-8b-8192"

def _truncate_text(value: str, max_chars: int = 220) -> str:
    text = value.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def _parse_coords_location(location: str):
    if not isinstance(location, str):
        return None
    match = re.match(r"^coords:([+-]?\d+(?:\.\d+)?),([+-]?\d+(?:\.\d+)?)(?:\|(.*))?$", location.strip())
    if not match:
        return None
    lat = float(match.group(1))
    lon = float(match.group(2))
    label = (match.group(3) or "").strip()
    return lat, lon, label


class DuckDuckGoSearchTool(BaseTool):
    name: str = "duckduckgo_search"
    description: str = "Search medical info"

    def _run(self, query: str) -> str:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                title = _truncate_text(r.get("title", ""), 120)
                body = _truncate_text(r.get("body", ""), 200)
                results.append(f"{title} - {body}")
        return "\n".join(results)

class BraveSearchCompatTool(BaseTool):
    name: str = "brave_search"
    description: str = "Search wrapper"

    def _run(self, query: str) -> str:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                title = _truncate_text(r.get("title", ""), 120)
                body = _truncate_text(r.get("body", ""), 200)
                results.append(f"{title} - {body}")
        return "\n".join(results)


# -----------------------------
# Hospital Search Tool
# -----------------------------
class HospitalSearchTool(BaseTool):

    name: str = "hospital_search"
    description: str = "Find nearby hospitals using OpenStreetMap. Input should be a city/location name."

    @staticmethod
    def _geocode_location(location: str):
        parsed = _parse_coords_location(location)
        if parsed:
            lat, lon, _ = parsed
            return lat, lon

        geocode_url = "https://nominatim.openstreetmap.org/search"
        cleaned = re.sub(r"\bdist\.?\b", "district", location, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = cleaned.replace(",", ", ")
        cleaned = re.sub(r"\s+,", ",", cleaned)
        parts = [p.strip() for p in cleaned.split(",") if p.strip()]
        variants = [cleaned]
        if parts:
            variants.append(", ".join(parts))
        if len(parts) >= 2:
            variants.append(", ".join(parts[-2:]))
        if len(parts) >= 1:
            variants.append(parts[0])

        headers = {"User-Agent": "agentic-ai-healthcare-assistant/1.0"}

        for query in list(dict.fromkeys(variants)):
            params = {
                "q": query,
                "format": "json",
                "limit": 1,
            }
            response = requests.get(geocode_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                continue

            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])

        return None

    @staticmethod
    def _extract_candidate_name(text: str) -> str | None:
        cleaned = re.split(r"\s[-|:]\s", text)[0].strip()
        if len(cleaned) < 4:
            return None
        hospital_keywords = (
            "hospital", "medical", "clinic", "care", "nursing", "health"
        )
        if any(k in cleaned.lower() for k in hospital_keywords):
            return cleaned
        return None

    def _fallback_web_hospitals(self, location: str) -> list[str]:
        parsed = _parse_coords_location(location)
        location_label = parsed[2] if parsed and parsed[2] else location
        queries = [
            f"best hospitals in {location_label}",
            f"government hospital {location_label}",
            f"private hospital near {location_label}",
            f"cardiology hospital in {location_label}",
        ]
        names: list[str] = []
        with DDGS() as ddgs:
            for query in queries:
                for r in ddgs.text(query, max_results=5):
                    candidate = self._extract_candidate_name(r.get("title", ""))
                    if candidate:
                        names.append(candidate)
        return list(dict.fromkeys(names))[:5]

    def _run(self, location: str) -> str:

        url = "https://overpass-api.de/api/interpreter"

        coords = self._geocode_location(location)
        if not coords:
            return f"Could not find location: {location}"

        lat, lon = coords
        query = f"""
        [out:json][timeout:25];
        (
                    node["amenity"="hospital"](around:30000,{lat},{lon});
                    way["amenity"="hospital"](around:30000,{lat},{lon});
                    relation["amenity"="hospital"](around:30000,{lat},{lon});
                    node["healthcare"="hospital"](around:30000,{lat},{lon});
                    way["healthcare"="hospital"](around:30000,{lat},{lon});
                    relation["healthcare"="hospital"](around:30000,{lat},{lon});
        );
        out center;
        """

        try:
            response = requests.get(url, params={'data': query}, timeout=10)

            if response.status_code != 200:
                return f"API Error: {response.status_code}"

            if not response.text.strip():
                return "No data returned"

            data = response.json()

        except Exception as e:
            return f"Error: {str(e)}"

        hospitals = []

        for element in data.get("elements", [])[:5]:
            name = element.get("tags", {}).get("name")
            if name:
                hospitals.append(name)

        if not hospitals:
            fallback_hospitals = self._fallback_web_hospitals(location)
            if fallback_hospitals:
                return "\n".join(fallback_hospitals)
            return f"No hospitals found in {location}"

        return "\n".join(dict.fromkeys(hospitals))


# -----------------------------
# Doctor Search Tool
# -----------------------------
class DoctorSearchTool(BaseTool):

    name: str = "doctor_search"
    description: str = "Find nearby doctors and clinics using OpenStreetMap. Input should be a city/location name."

    @staticmethod
    def _geocode_location(location: str):
        parsed = _parse_coords_location(location)
        if parsed:
            lat, lon, _ = parsed
            return lat, lon

        geocode_url = "https://nominatim.openstreetmap.org/search"
        cleaned = re.sub(r"\bdist\.?\b", "district", location, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = cleaned.replace(",", ", ")
        cleaned = re.sub(r"\s+,", ",", cleaned)
        parts = [p.strip() for p in cleaned.split(",") if p.strip()]
        variants = [cleaned]
        if parts:
            variants.append(", ".join(parts))
        if len(parts) >= 2:
            variants.append(", ".join(parts[-2:]))
        if len(parts) >= 1:
            variants.append(parts[0])

        headers = {"User-Agent": "agentic-ai-healthcare-assistant/1.0"}

        for query in list(dict.fromkeys(variants)):
            params = {
                "q": query,
                "format": "json",
                "limit": 1,
            }
            response = requests.get(geocode_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200:
                continue

            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])

        return None

    @staticmethod
    def _extract_candidate_name(text: str) -> str | None:
        cleaned = re.split(r"\s[-|:]\s", text)[0].strip()
        if len(cleaned) < 4:
            return None
        doctor_keywords = (
            "dr", "doctor", "diabet", "endocrin", "clinic", "physician"
        )
        if any(k in cleaned.lower() for k in doctor_keywords):
            return cleaned
        return None

    def _fallback_web_doctors(self, location: str) -> list[str]:
        parsed = _parse_coords_location(location)
        location_label = parsed[2] if parsed and parsed[2] else location
        queries = [
            f"cardiologist in {location_label}",
            f"diabetologist in {location_label}",
            f"doctor clinic in {location_label}",
            f"specialist doctor near {location_label}",
        ]
        names: list[str] = []
        with DDGS() as ddgs:
            for query in queries:
                for r in ddgs.text(query, max_results=5):
                    candidate = self._extract_candidate_name(r.get("title", ""))
                    if candidate:
                        names.append(candidate)
        return list(dict.fromkeys(names))[:5]

    def _run(self, location: str) -> str:
        url = "https://overpass-api.de/api/interpreter"

        coords = self._geocode_location(location)
        if not coords:
            return f"Could not find location: {location}"

        lat, lon = coords
        query = f"""
        [out:json][timeout:25];
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
                    node["healthcare"="clinic"](around:30000,{lat},{lon});
                    way["healthcare"="clinic"](around:30000,{lat},{lon});
                    relation["healthcare"="clinic"](around:30000,{lat},{lon});
        );
        out center;
        """

        try:
            response = requests.get(url, params={"data": query}, timeout=15)

            if response.status_code != 200:
                return f"API Error: {response.status_code}"

            if not response.text.strip():
                return "No data returned"

            data = response.json()
        except Exception as e:
            return f"Error: {str(e)}"

        doctors = []
        for element in data.get("elements", [])[:5]:
            tags = element.get("tags", {})
            name = tags.get("name")
            specialty = tags.get("healthcare:speciality") or tags.get("healthcare:specialty")

            if name:
                doctors.append(f"{name} ({specialty})" if specialty else name)

        if not doctors:
            fallback_doctors = self._fallback_web_doctors(location)
            if fallback_doctors:
                return "\n".join(fallback_doctors)
            return f"No doctors found in {location}"

        return "\n".join(dict.fromkeys(doctors))


# -----------------------------
# Tool Instances
# -----------------------------
search_tool = DuckDuckGoSearchTool()
brave_search_compat_tool = BraveSearchCompatTool()
hospital_tool = HospitalSearchTool()
doctor_tool = DoctorSearchTool()


# -----------------------------
# Agents (NO TOOLS)
# -----------------------------
research_agent = Agent(
    role="Medical Research Specialist",
    goal="Analyze medical data and provide insights",
    backstory="Expert healthcare researcher",
    tools=[search_tool, brave_search_compat_tool],
    llm=llm,
    verbose=False,
    max_iter=2,
    allow_delegation=False
)

hospital_agent = Agent(
    role="Hospital Analyst",
    goal="Find and list real hospitals in the given location",
    backstory="Expert at finding hospitals using search tools",
    tools=[hospital_tool, search_tool],
    llm=llm,
    verbose=False,
    max_iter=1,
    allow_delegation=False
)

doctor_agent = Agent(
    role="Doctor Analyst",
    goal="Find and list real doctors/clinics in the given location",
    backstory="Expert at finding doctors using search tools",
    tools=[doctor_tool, search_tool],
    llm=llm,
    verbose=False,
    max_iter=1,
    allow_delegation=False
)

scheduler_agent = Agent(
    role="Healthcare Planner",
    goal="Create final treatment plan",
    backstory="Healthcare planning expert",
    llm=llm,
    verbose=False,
    max_iter=1,
    allow_delegation=False
)