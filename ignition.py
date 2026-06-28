# ignition.py — turns the key, everything starts

import logging
from flask import Flask
from pit_lane.fuel import init as fuel_up
from rimac.nevera import start as nevera_start, stop as nevera_stop
from rimac.concept_one import heartbeat, register
from ferrari.sf90 import watch as sf90_watch
from ferrari.f8 import watch as f8_watch
from ferrari.laferrari import watch as laferrari_watch
from koenigsegg.agera_rs import process_pending as agera_process
from koenigsegg.ccxr import deduplicate
from koenigsegg.jesko import route as jesko_route
from bentley.bentayga import enrich_pending as bentayga_enrich
from bentley.mulsanne import rank_pending as mulsanne_rank
from bentley.continental_gt import evaluate_pending as continental_evaluate
from jaguar.e_type import profile_pending as e_type_profile
from jaguar.xj220 import synthesize_angles as xj220_synthesize
from jaguar.f_type import resolve_photos as f_type_resolve
from maserati.gransport import draft_emails as gransport_draft
from maserati.levante import draft_linkedin as levante_draft
from maserati.mc20 import draft_replies as mc20_draft
from bugatti.divo import reprioritize as divo_reprioritize
from rolls_royce.phantom import phantom
from rolls_royce.cullinan import cullinan
from rolls_royce.ghost import ghost

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S"
)

log = logging.getLogger("ignition")

app = Flask(__name__, template_folder="templates", static_folder="static")

app.register_blueprint(phantom)
app.register_blueprint(cullinan)
app.register_blueprint(ghost)


def boot():
    log.info("NEXUS: ignition sequence started")

    fuel_up()

    register("heartbeat", heartbeat)

    jobs = [
        {
            "fn": bentayga_enrich, 
            "minutes": 64, 
            "name": "bentley_bentayga"
        },
        {   
            "fn": mulsanne_rank, 
            "minutes": 65, 
            "name": "bentley_mulsanne"
        },
        {   
            "fn": continental_evaluate, 
            "minutes": 66, 
            "name": "bentley_continental_gt"
        },
        {
            "fn": agera_process,
            "minutes": 61,
            "name": "koenigsegg_agera_rs"
        },
        {
            "fn": deduplicate,
            "minutes": 62,
            "name":"koenigsegg_ccxr"
        },
        {
            "fn": heartbeat,
            "minutes": 10,
            "name": "concept_one_heartbeat"
        },
        {
            "fn": sf90_watch,
            "minutes": 60,
            "name": "ferrari_sf90"
        },
        {
            "fn": jesko_route,
            "minutes": 63,
            "name": "koenigsegg_jesko"
        },
        {
            "fn": e_type_profile,
            "minutes": 67,
            "name": "jaguar_e_type"
        },
        {
            "fn": xj220_synthesize,
            "minutes": 68,
            "name": "jaguar_xj220"
        },
        {
            "fn": f_type_resolve,
            "minutes": 69,
            "name": "jaguar_f_type"
        },
        {
            "fn": gransport_draft,
            "minutes": 70,
            "name": "maserati_gransport"
        },
        {
            "fn": levante_draft,
            "minutes": 71,
            "name": "maserati_levante"
        },
        {
            "fn": mc20_draft,
            "minutes": 72,
            "name": "maserati_mc20"
        },
        {
            "fn": divo_reprioritize,
            "minutes": 73,
            "name": "bugatti_divo"
        },
        {
            "fn": f8_watch,
            "minutes": 74,
            "name": "ferrari_f8"
        },
        {
            "fn": laferrari_watch,
            "minutes": 75,
            "name": "ferrari_laferrari"
        }
    ]

    nevera_start(jobs)
    log.info("NEXUS: Nevera is online")


if __name__ == "__main__":
    boot()
    try:
        app.run(debug=False, use_reloader=False, port=5000)
    except (KeyboardInterrupt, SystemExit):
        nevera_stop()
        log.info("NEXUS: shutdown complete")