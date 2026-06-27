# NEXUS

> Autonomous intelligence and outreach automation. Built for speed, named for machines that deserve the name.

NEXUS watches the web so you don't have to. It pulls signals from across the internet, profiles targets, scores opportunities, and drafts outreach — all on a schedule, all without you lifting a finger.

Built for the **AMD Developer Hackathon ACT II** — Track 3.

---

## Architecture

NEXUS is organized like a racing garage. Every component has a name it earned.

```
nexus/
│
├── ignition.py                  # Turn the key. Everything starts.
│
├── rimac/                       # The engine room
│   ├── nevera.py                    # Background scheduler, always on
│   └── concept_one.py               # Heartbeat monitor, checks everything is alive
│
├── ferrari/                     # Signal sources — fast, always watching
│   ├── sf90.py                      # GitHub trending watcher
│   ├── roma.py                      # Twitter/X watcher
│   ├── f8.py                        # Reddit watcher
│   └── laferrari.py                 # ArXiv watcher
│
├── koenigsegg/                  # Signal processing pipeline
│   ├── jesko.py                     # Signal router, directs incoming feeds
│   ├── agera_rs.py                  # Feed parser, cleans raw signal into structured data
│   └── ccxr.py                      # Deduplication, kills noise
│
├── bentley/                     # Scoring and ranking
│   ├── continental_gt.py            # Opportunity scorer
│   ├── mulsanne.py                  # Relevance ranker
│   └── bentayga.py                  # Signal to score converter
│
├── jaguar/                      # Target intelligence
│   ├── e_type.py                    # Web intel, finds people
│   ├── xj220.py                     # Deep search, finds what people don't want found
│   └── f_type.py                    # Image resolver, finds faces
│
├── porsche/                     # Agent core — the thinking layer
│   ├── 911_gt3.py                   # Profiler agent
│   ├── gt2_rs.py                    # Escalation agent
│   ├── cayman_gt4.py                # Gap analyzer agent
│   ├── cayenne_turbo.py             # Panel mode agent
│   └── 718_boxster.py               # Document writer agent
│
├── mercedes/                    # CV and skill analysis
│   ├── s_class.py                   # CV parser
│   ├── amg_gt.py                    # Gap detector
│   └── eqs.py                       # Skill extractor
│
├── bmw/                         # Recommendation engine
│   ├── m3.py                        # Recommendation engine core
│   ├── m5.py                        # Action suggester, what move to make
│   └── i8.py                        # Reasoning attacher, explains every suggestion
│
├── lamborghini/                 # Escalation system
│   ├── aventador.py                 # Escalation level generator
│   ├── huracan.py                   # Escalation tone calibrator
│   └── revuelto.py                  # Escalation channel selector
│
├── maserati/                    # Outreach drafting
│   ├── gransport.py                 # Email drafter
│   ├── levante.py                   # LinkedIn message drafter
│   └── mc20.py                      # Reply drafter, responds to posts
│
├── pagani/                      # Output and formatting
│   ├── huayra.py                    # Cover letter crafter
│   ├── zonda.py                     # Resume tailor
│   └── utopia.py                    # Output formatter, makes everything beautiful
│
├── bugatti/                     # Queue management
│   ├── chiron.py                    # Queue storage, writes to SQLite
│   ├── veyron.py                    # Queue retrieval, reads and serves
│   └── divo.py                      # Queue prioritizer, ranks by urgency
│
├── rolls_royce/                 # Frontend routes
│   ├── phantom.py                   # Main UI routes
│   ├── ghost.py                     # Judge panel routes
│   └── cullinan.py                  # Queue review routes
│
├── apollo/                      # Raw terminal access
│   ├── ie.py                        # Terminal mode, no UI no guardrails
│   └── evo.py                       # Terminal output formatter
│
├── aston_martin/                # Configuration and auth
│   ├── db12.py                      # Config loader
│   ├── vantage.py                   # Environment variables and API keys
│   └── valkyrie.py                  # Authentication handler
│
├── audi/                        # Observability
│   ├── r8.py                        # System logger
│   ├── rs6.py                       # Error monitor
│   └── e_tron_gt.py                 # Performance tracker
│
├── lexus/                       # Caching layer
│   ├── lfa.py                       # Profile cache, remembers who we already profiled
│   ├── lc500.py                     # Signal cache, avoids reprocessing seen feeds
│   └── rx.py                        # Session memory, keeps context between runs
│
├── nissan/                      # Testing and validation
│   ├── gtr_r35.py                   # Output validator, checks agent responses are sane
│   ├── skyline_r34.py               # Integration tester, end to end checks
│   └── 370z.py                      # Feed health checker, are sources still alive
│
└── pit_lane/                    # Infrastructure
    ├── fuel.py                      # Database initializer
    ├── podium.db                    # Central data store
    └── race_brief.json              # System configuration
```

---

## How It Works

1. **Ignition** — `ignition.py` boots the system, fuels the database, and hands control to Nevera
2. **Ferrari watches** — signal sources pull live data on a schedule and write to `podium.db`
3. **Koenigsegg processes** — raw signals get parsed, cleaned, and deduplicated
4. **Bentley scores** — every signal gets ranked by relevance and opportunity value
5. **Jaguar profiles** — builds deep intel on targets from accumulated signals
6. **Porsche thinks** — agents analyze, gap-check, and decide what to do
7. **Maserati drafts** — turns intel into outreach, ready for your review
8. **Bugatti queues** — approved actions line up in priority order
9. **Rolls-Royce serves** — everything surfaces through the dashboard

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
