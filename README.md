# NEXUS

> Autonomous intelligence and outreach automation. Built for speed, named for machines that deserve the name.

NEXUS watches the web so you don't have to. It pulls signals from across the internet, profiles targets, scores opportunities, and drafts outreach — all on a schedule, all without you lifting a finger.

Built for the **AMD Developer Hackathon ACT II** — Track 3.

---

## Architecture

NEXUS is organized like a racing garage. Every component has a name it earned.

```
nexus/
├── rimac/          # The engine room — scheduler and heartbeat
│   ├── nevera.py       # Job scheduler, always running
│   └── concept_one.py  # System heartbeat and monitoring
│
├── ferrari/        # Signal sources — fast, always watching
│   └── sf90.py         # GitHub trending watcher
│
├── jaguar/         # Target profiling
├── maserati/       # Outreach drafting
├── pit_lane/       # Infrastructure
│   ├── fuel.py         # Database initializer
│   ├── podium.db       # Central data store
│   └── race_brief.json # System configuration
│
└── ignition.py     # Turn the key. Everything starts.
```

---

## How It Works

1. **Ignition** — `ignition.py` boots the system, fuels the database, and hands control to Nevera
2. **Nevera schedules the grid** — each manufacturer module runs on its own interval
3. **Ferrari watches** — signal sources pull live data and write to `podium.db`
4. **Jaguar profiles** — builds intel on targets from accumulated signals
5. **Maserati drafts** — turns intel into outreach, ready for review

---

## Stack

- Python 3.11
- Flask
- APScheduler
- SQLite (`podium.db`)
- GitHub API
- Groq / LLaMA 3.3 70B

---

## Quickstart

```bash
git clone https://github.com/azlaan428/NEXUS.git
cd NEXUS
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env        # add your keys
python ignition.py
```

NEXUS boots at `http://localhost:5000`

---

## Status

See [STATUS.md](STATUS.md) for current build state and what's coming next.

---

Built by [@azlaan428](https://github.com/azlaan428)
