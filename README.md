# Quadrant — Multi-Agent Smart Campus Helpdesk

A Flask + vanilla JS implementation of a multi-agent campus helpdesk. A
**Coordinator Agent** classifies each incoming query and routes it to one
or more of five specialist agents, which can visibly collaborate on
complex questions.

## Features

- **Coordinator Agent** — classifies queries by keyword/intent and routes
  to the right specialist(s), merging multi-agent answers.
- **Student Agent** — attendance, exam schedule, assignments, attendance prediction.
- **Faculty Agent** — real BIT Sathyamangalam faculty names/designations (from bitsathy.ac.in); availability, rooms and free slots are simulated demo data until connected to a real timetable feed.
- **Administrative Agent** — fees, certificates, AI-generated complaint tickets,
  smart queue status.
- **Navigation Agent** — campus map with routing between the main gate and
  any building.
- **Event Agent** — workshops, seminars, hackathons, placement drives,
  filterable by interest.
- **Admin Dashboard** — live analytics: query volume per agent, complaint
  status, response-time trend, per-agent accuracy/performance.
- **Live Agent Network view** — animated diagram showing the Coordinator
  handing a query to each specialist in real time, with a running
  communication log.
- Voice input (Web Speech API), emergency SOS flow, predictive notifications,
  lost-and-found reporting.

## Project structure

```
campus-helpdesk-app/
├── app.py                  # Flask app & REST API routes
├── data_store.py           # in-memory "database" layer (swap for real DB later)
├── requirements.txt
├── agents/
│   ├── coordinator.py      # classifies + routes + merges responses
│   ├── student_agent.py
│   ├── faculty_agent.py
│   ├── admin_agent.py
│   ├── navigation_agent.py
│   └── event_agent.py
├── data/                   # seed JSON data (faculty, events, buildings, students)
├── templates/
│   └── index.html          # single-page UI shell
└── static/
    ├── css/style.css
    └── js/main.js           # fetches the API, renders chat/network/dashboard/etc.
```

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## How the multi-agent routing works

1. The frontend POSTs the raw text to `POST /api/query`.
2. `agents/coordinator.py` runs a regex/keyword classifier (`classify()`)
   against the query and returns a list of matching agent keys — a query
   like *"I lost my ID card near the library, raise a complaint"* matches
   only `admin`, while *"Show me hackathons and guide me to the auditorium"*
   matches both `event` and `navigation`.
3. For every matched agent, the coordinator calls that agent's `respond()`
   function (each agent reads from `data_store.py`, never straight from
   the JSON files) and collects the answers plus a step-by-step log.
4. The API returns `{agents, agent_meta, responses, log, collab}` as JSON.
5. The frontend replays this as a typing → response animation per agent in
   the chat, and as a pulse animation along the matching edges in the
   Agent Network view.

## Extending it with a real LLM

Each agent's `respond(query)` function is the only place that needs to
change to go from templated/rule-based answers to real LLM-generated ones —
for example, calling the Anthropic API from `student_agent.py` instead of
picking from a canned list, while keeping the same function signature so
`coordinator.py` and `app.py` don't need to change at all.

## Notes on this demo build

- Data is stored **in memory** (`data_store.py`) and resets on server
  restart — swap in Postgres/MongoDB behind the same functions for a real
  deployment.
- Query classification is keyword-based for transparency and speed; a
  production system would likely replace `coordinator.classify()` with an
  LLM-based intent classifier.
- Charts use Chart.js via CDN; fonts via Google Fonts CDN — both need
  internet access in the browser.
