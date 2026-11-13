import ctypes
import logging
from time import sleep

from ac import ACSharedMemory
from ac.models.graphics import GraphicsPage
from ac.models.enums import AC_SESSION_TYPE, AC_STATUS

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
    memory: ACSharedMemory, graphics: GraphicsPage, *, retry_capture_in_sec: float
) -> None:
    session_type = AC_SESSION_TYPE(graphics.session).name
    logger.info("Capturing Assetto Corsa '%s' session.", session_type)

    with Session() as session:
        static = memory.read_static()
        session.append(serialize_page(static))

        while True:
            sleep(retry_capture_in_sec)
            snapshot = memory.read_snapshot()

            if snapshot.graphics.status == AC_STATUS.AC_OFF:
                logger.info(
                    "Session '%s' has ended.",
                    AC_SESSION_TYPE(graphics.session).name,
                )
                return

            if snapshot.graphics.status != AC_STATUS.AC_LIVE:
                continue

            if snapshot.graphics.is_in_pit:
                continue

            session.append(serialize_page(snapshot.physics))
            session.append(serialize_page(snapshot.graphics))


def connect_and_capture() -> None:
    with ACSharedMemory() as memory:
        graphics = memory.read_graphics()

        if graphics.status != AC_STATUS.AC_LIVE:
            return

        capture_driving(memory, graphics, retry_capture_in_sec=1 / 30)
