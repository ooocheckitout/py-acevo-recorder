import ctypes
import logging
from time import sleep

from ac import ACSharedMemory
from ac.models.enums import AC_SESSION_TYPE, AC_STATUS
from ac.models.graphics import GraphicsPage

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
    memory: ACSharedMemory, static: StaticPage, *, retry_capture_in_sec: float
) -> None:
    logger.info("Capturing the driving events...")
    with Session() as session:
        session.append(serialize_page(static))

        while True:
            sleep(retry_capture_in_sec)
            snapshot = memory.read_snapshot()

            if snapshot.graphics.status == AC_STATUS.AC_OFF:
                logger.info(
                    "Session '%s' has ended.", AC_SESSION_TYPE(graphics.session).name
                )
                return

            if snapshot.graphics.status != AC_STATUS.AC_LIVE:
                continue

            if snapshot.graphics.is_in_pit:
                continue

            session.append(serialize_page(snapshot.physics))
            session.append(serialize_page(snapshot.graphics))


def discover_session(memory: ACSharedMemory, *, retry_discovery_in_sec: float):
    logger.info("Discovering sessions...")
    while True:
        graphics = memory.read_graphics()

        if graphics.status != AC_STATUS.AC_LIVE:
            sleep(retry_discovery_in_sec)
            continue

        logger.info("Found '%s' session.", AC_SESSION_TYPE(graphics.session).name)
        yield memory.read_static()


def connect_and_capture() -> None:
    with ACSharedMemory() as memory:
        logger.info("Connected to Assetto Corsa shared memory.")
        for static in discover_session(memory, retry_discovery_in_sec=10):
            capture_driving(memory, static, retry_capture_in_sec=1 / 30)
