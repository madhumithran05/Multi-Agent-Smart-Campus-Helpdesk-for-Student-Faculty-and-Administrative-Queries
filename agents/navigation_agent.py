"""
Navigation Agent
Guides users to classrooms, labs, offices and other campus locations on the
real Bannari Amman Institute of Technology (BIT) campus map.
"""
import random
from data_store import get_buildings, find_building, CAMPUS


def respond(query: str) -> str:
    q = query.lower()
    match = find_building(q)
    if match:
        gmaps = (f"https://www.google.com/maps/dir/?api=1&destination={match['lat']},{match['lng']}"
                 "&travelmode=walking")
        return (
            f"Routing you now to <b>{match['name']}</b> on the BIT campus — I've marked the walking path "
            f"on the live Campus Navigator map, about {3 + hash(match['id']) % 6} minutes from the main gate. "
            f"<a href=\"{gmaps}\" target=\"_blank\" rel=\"noopener\">Open in Google Maps</a>"
        )

    buildings = get_buildings()
    names = ", ".join(b["name"] for b in buildings if b["id"] != "gate")
    fallback = [
        f"I can guide you to any of these places on the {CAMPUS['name']} campus: {names}. Which one do you need?",
        "Switch to the Campus Navigator tab and I'll highlight the exact path on the real campus map for you.",
    ]
    return random.choice(fallback)
