import ctypes
import logging
from pathlib import Path
from time import sleep

from acevo import ACEvoSharedMemory
from acevo.models.static import StaticPage
from acevo.models.enums import ACEVO_SESSION_TYPE, ACEVO_STATUS

from session import Session

logger = logging.getLogger(__name__)


def serialize_page(value: object) -> object:
    if isinstance(value, ctypes.Structure):
        return {
            name: serialize_page(getattr(value, name)) for name, *_ in value._fields_
        }
    if isinstance(value, ctypes.Array):
        return [serialize_page(item) for item in value]
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def capture_driving(
    memory: ACEvoSharedMemory, static: StaticPage, *, retry_capture_in_sec: float
) -> None:
    logger.info("Capturing the driving events...")
    with Session() as session:
        session.append(serialize_page(static))

        while True:
            sleep(retry_capture_in_sec)
            snapshot = memory.read_snapshot()

            if snapshot.static.session == ACEVO_SESSION_TYPE.AC_UNKNOWN:
                logger.info("Session '%s' has ended.", static.session_name)
                return

            if snapshot.graphics.status != ACEVO_STATUS.AC_LIVE:
                continue

            if snapshot.graphics.is_in_pit_box:
                continue

            session.append(serialize_page(snapshot.physics))
            session.append(serialize_page(snapshot.graphics))


def discover_session(memory: ACEvoSharedMemory, *, retry_discovery_in_sec: float):
    logger.info("Discovering sessions...")
    while True:
        static = memory.read_static()

        if static.session == ACEVO_SESSION_TYPE.AC_UNKNOWN:
            sleep(retry_discovery_in_sec)
            continue

        logger.info("Found '%s' session.", static.session_name)
        yield static


def connect_to_shared_memory(*, retry_connect_in_sec: int) -> None:
    logger.info("Connecting to shared memory...")
    while True:
        try:
            with ACEvoSharedMemory() as memory:
                logger.info("Connected to shared memory.")
                for static in discover_session(memory, retry_discovery_in_sec=10):
                    capture_driving(memory, static, retry_capture_in_sec=1 / 30)
        except FileNotFoundError:
            pass

        sleep(retry_connect_in_sec)


def main() -> None:
    log_folder = Path(r"C:\Users\feelsgood\Documents\py-acevo-recorder\Logs")
    log_folder.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_folder / "py-acevo-recorder.log", encoding="utf-8"),
        ],
    )
    logger.info("Waiting for an Assetto Corsa Evo session. Press Ctrl+C to stop.")
    try:
        connect_to_shared_memory(retry_connect_in_sec=30)
    except KeyboardInterrupt:
        logger.info("Session monitor stopped.")
    except Exception:
        logger.exception("Session monitor failed.")
        raise


if __name__ == "__main__":
    main()
