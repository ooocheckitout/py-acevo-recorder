from __future__ import annotations

import gzip
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from types import TracebackType

logger = logging.getLogger(__name__)


class Session:
    def __init__(self) -> None:
        output_folder = Path(
            r"C:\Users\feelsgood\Documents\py-assettocorsa-recorder\Recordings"
        )
        output_folder.mkdir(parents=True, exist_ok=True)
        timestamp = format(datetime.now(tz=timezone.utc), "%Y%m%d%H%M%S%f")
        output_path = output_folder / (f"{timestamp}.jsonl")
        self._output = output_path.open("w", encoding="utf-8")
        logger.info("Start recording to %s", self._output.name)

    def __enter__(self) -> Session:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._output.close()
        compressed_path = Path(self._output.name).with_suffix(".jsonl.gz")
        with (
            open(self._output.name, "rb") as source,
            gzip.open(compressed_path, "wb") as compressed,
        ):
            shutil.copyfileobj(source, compressed)
        Path(self._output.name).unlink()
        logger.info("Compressed recording to %s", compressed_path)

    def append(self, page: dict[str, object]) -> None:
        self._output.write(json.dumps(page, separators=(",", ":")) + "\n")
