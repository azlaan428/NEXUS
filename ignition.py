# ignition.py — turns the key, everything starts

import logging
from flask import Flask
from pit_lane.fuel import init as fuel_up
from rimac.nevera import start as nevera_start, stop as nevera_stop
from rimac.concept_one import heartbeat, register
from ferrari.sf90 import watch as sf90_watch
from koenigsegg.agera_rs import process_pending as agera_process

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S"
)

log = logging.getLogger("ignition")

app = Flask(__name__, template_folder="templates", static_folder="static")


def boot():
    log.info("NEXUS: ignition sequence started")

    fuel_up()

    register("heartbeat", heartbeat)

    jobs = [
        # in jobs list:
        {
            "fn": agera_process,
            "minutes": 61,
            "name": "koenigsegg_agera_rs"
        }
        {
            "fn": heartbeat,
            "minutes": 10,
            "name": "concept_one_heartbeat"
        },
        {
            "fn": sf90_watch,
            "minutes": 60,
            "name": "ferrari_sf90"
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