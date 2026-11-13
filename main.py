import logging
from time import sleep
from pathlib import Path

from integrations import assettocorsa, assettocorsaevo

logger = logging.getLogger(__name__)


def monitor_games(*, retry_connect_in_sec: int) -> None:
    logger.info("Monitoring supported games...")
    while True:
        for game in (
            assettocorsa,
            assettocorsaevo,
        ):
            try:
                game.connect_and_capture()
            except FileNotFoundError:
                continue
            except Exception:
                logger.exception("'%s' capture failed.", game.__name__)

        sleep(retry_connect_in_sec)


def main() -> None:
    log_folder = Path(r"C:\Users\feelsgood\Documents\py-assettocorsa-recorder\Logs")
    log_folder.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                log_folder / "py-assettocorsa-recorder.log", encoding="utf-8"
            ),
        ],
    )
    logger.info("Waiting for an Assetto Corsa session. Press Ctrl+C to stop.")
    try:
        monitor_games(retry_connect_in_sec=15)
    except KeyboardInterrupt:
        logger.info("Session monitor stopped.")
    except Exception:
        logger.exception("Session monitor failed.")
        raise


if __name__ == "__main__":
    main()
