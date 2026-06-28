# ferrari/roma.py — Twitter/X watcher stub

import logging

log = logging.getLogger("roma")


def watch():
    log.info("roma: Twitter/X watcher: API not configured")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    watch()
