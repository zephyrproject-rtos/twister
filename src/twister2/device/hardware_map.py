from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml


@dataclass
class HardwareMap:
    """Class keeps configuration for connected hardware."""
    id: str
    product: str = ''
    platform: str = ''
    runner: str = ''
    connected: bool = False
    available: bool = False
    notes: str = ''
    probe_id: str = ''
    serial: str = ''
    baud: str = '115200'
    pre_script: str = ''
    post_script: str = ''
    post_flash_script: str = ''
    fixtures: list[str] = field(default_factory=list)

    @classmethod
    def read_from_file(cls, filename: str | Path) -> list[HardwareMap]:
        with open(filename, 'r', encoding='UTF-8') as file:
            data = yaml.safe_load(file)
        return [cls(**hardware) for hardware in data]

    def asdict(self):
        """Return hardware map dict valid for map file."""
        return asdict(self)
