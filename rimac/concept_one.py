# Rimac Concept One — heartbeat monitor, checks if everything is alive

import logging
import time

log = logging.getLogger("concept_one")

_registry = {}


def register(name: str, fn: callable):
    """Register a component to monitor."""
    _registry[name] = fn
    log.info(f"Concept One: monitoring {name}")


def pulse() -> dict:
    """Check all registered components. Returns status report."""
    report = {}
    for name, fn in _registry.items():
        try:
            fn()
            report[name] = "alive"
        except Exception as e:
            report[name] = f"dead: {str(e)}"
            log.error(f"Concept One: {name} is down — {e}")
    return report


def heartbeat():
    """Called by Nevera every N minutes."""
    log.info("Concept One: running pulse check")
    report = pulse()
    for name, status in report.items():
        log.info(f"  {name}: {status}")
    return report