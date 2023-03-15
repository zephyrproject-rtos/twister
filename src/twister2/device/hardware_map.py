from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml


@dataclass
class HardwareMap:
    """Class keeps configuration for connected hardware."""
    id: str = ''
    product: str = ''
    platform: str = ''
    runner: str = ''
    connected: bool = False
    available: bool = False
    notes: str = ''
    probe_id: str = ''
    serial: str = ''
    serial_pty: str = ''
    baud: int = 115200
    pre_script: str = ''
    post_script: str = ''
    post_flash_script: str = ''
    fixtures: list[str] = field(default_factory=list)

    @classmethod
    def read_from_file(cls, filename: str | Path) -> list[HardwareMap]:
        with open(filename, 'r', encoding='UTF-8') as file:
            data = yaml.safe_load(file)
        if not data:
            return []
        return [cls(**hardware) for hardware in data]

    def asdict(self):
        """Return hardware map dict valid for map file."""
        not_excluded = ['connected', 'serial']
        return asdict(
            self,
            dict_factory=lambda x: {
                k: v for (k, v) in x if v or k in not_excluded
            }
        )
