# ignition.py — turns the key, everything starts

import logging
import os
from flask import Flask
from pit_lane.fuel import init as fuel_up
from rimac.nevera import start as nevera_start, stop as nevera_stop
from rimac.concept_one import heartbeat, register

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S"
)

log = logging.getLogger("ignition")

app = Flask(__name__, template_folder="templates", static_folder="static")


def boot():
    log.info("NEXUS: ignition sequence started")

    # fuel the pit lane
    fuel_up()

    # register heartbeat
    register("heartbeat", heartbeat)

    # define scheduled jobs
    jobs = [
        {
            "fn": heartbeat,
            "minutes": 10,
            "name": "concept_one_heartbeat"
        }
    ]

    nevera_start(jobs)
    log.info("NEXUS: Nevera is online")


@app.route("/")
def index():
    from flask import render_template
    return render_template("index.html")


if __name__ == "__main__":
    boot()
    try:
        app.run(debug=False, use_reloader=False, port=5000)
    except (KeyboardInterrupt, SystemExit):
        nevera_stop()
        log.info("NEXUS: shutdown complete")