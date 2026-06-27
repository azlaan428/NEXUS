# STATUS

> Last updated: June 27, 2026

---

## Current Build

| Component | Status | Notes |
|---|---|---|
| `rimac/nevera.py` | ✅ Live | Scheduler running, jobs firing |
| `rimac/concept_one.py` | ✅ Live | Heartbeat registered, 10-min interval |
| `pit_lane/fuel.py` | ✅ Live | podium.db initialized with all tables |
| `pit_lane/podium.db` | ✅ Live | signals, targets, queue, profiles, outreach tables ready |
| `ferrari/sf90.py` | ✅ Live | GitHub trending watcher, 60-min interval, writing to podium |
| `ignition.py` | ✅ Live | Full boot sequence operational |

---

## Signal Sources

| Source | Module | Interval | Status |
|---|---|---|---|
| GitHub Trending | `ferrari/sf90.py` | 60 min | ✅ Active |

---

## In Progress

- [ ] Target profiling — `jaguar/`
- [ ] Outreach drafting — `maserati/`
- [ ] Additional signal sources — `ferrari/`
- [ ] Frontend dashboard — `templates/`

---

## Known Limitations

- GitHub signal source uses search API rather than a true trending endpoint — returns high-star repos as a proxy
- No deduplication on signals yet — repeated runs will insert duplicate rows
- Relevance scoring is stars-based only, no semantic scoring yet

---

## Hackathon

**AMD Developer Hackathon ACT II — Track 3**
Deadline: July 11, 2026
