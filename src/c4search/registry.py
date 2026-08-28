from pathlib import Path
from typing import Callable, Protocol

from c4search.models import Doc, VideoMeta


class Extractor(Protocol):
    """One modality extractor: reads prepared media assets, emits Docs."""

    name: str

    def run(self, video: VideoMeta, workdir: Path) -> list[Doc]: ...


EXTRACTORS: dict[str, Callable[[dict], Extractor]] = {}


def register_extractor(name: str):
    def add(factory: Callable[[dict], Extractor]):
        EXTRACTORS[name] = factory
        return factory

    return add


def build_extractors(config: dict) -> list[Extractor]:
    """Instantiate the extractors the config enables, in config order.

    Each config entry is {impl: <registered name>, ...options}; the options
    dict is passed to the factory, so the YAML is the wiring diagram.
    """
    built = []
    for entry in config.get("extractors", []):
        options = {key: value for key, value in entry.items() if key != "impl"}
        built.append(EXTRACTORS[entry["impl"]](options))
    return built
