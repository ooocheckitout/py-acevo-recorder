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
    logger.info("Capturing Assetto Corsa Evo '%s' session.", static.session_name)

    with Session() as session:
        session.append(serialize_page(static))

        while True:
            sleep(retry_capture_in_sec)
            snapshot = memory.read_snapshot()

            if snapshot.static.session == ACEVO_SESSION_TYPE.AC_UNKNOWN:
                logger.info("Session '%s' has ended.", snapshot.static.session_name)
                return

            if snapshot.graphics.status != ACEVO_STATUS.AC_LIVE:
                continue

            if snapshot.graphics.is_in_pit_box:
                continue

            session.append(serialize_page(snapshot.physics))
            session.append(serialize_page(snapshot.graphics))


def connect_and_capture() -> None:
    with ACEvoSharedMemory() as memory:
        static = memory.read_static()

        if static.session == ACEVO_SESSION_TYPE.AC_UNKNOWN:
            return

        capture_driving(memory, static, retry_capture_in_sec=1 / 30)
