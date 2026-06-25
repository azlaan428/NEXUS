# Rimac Nevera — background scheduler, always on, silent until it fires

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

log = logging.getLogger("nevera")

scheduler = BackgroundScheduler()


def start(jobs: list):
    """
    jobs: list of dicts with keys:
        - fn: callable
        - minutes: int
        - name: str
    """
    for job in jobs:
        scheduler.add_job(
            func=job["fn"],
            trigger=IntervalTrigger(minutes=job["minutes"]),
            id=job["name"],
            name=job["name"],
            replace_existing=True
        )
        log.info(f"Nevera: {job['name']} scheduled every {job['minutes']} min")

    scheduler.start()
    log.info("Nevera: online")


def stop():
    scheduler.shutdown()
    log.info("Nevera: offline")