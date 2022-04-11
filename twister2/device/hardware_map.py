from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class HardwareMap:
    product: str
    runner: str
    id: str = ''
    available: bool = False
    connected: bool = True
    notes: str = ''
    platform: str = ''
    probe_id: str = ''
    serial: Optional[str] = None
    baud: str = '115200'
    pre_script: str = ''
    post_script: str = ''
    post_flash_script: str = ''
    fixtures: dict = field(default_factory=dict)

    @classmethod
    def read_from_file(cls, filename: str | Path) -> list[HardwareMap]:
        with open(filename, 'r', encoding='UTF-8') as file:
            data = yaml.safe_load(file)
        return [cls(**hardware) for hardware in data]

    def asdict(self):
        """Return hardware map dict valid for map file."""
        return dict(
            connected=self.connected,
            id=self.id,
            platform=self.platform,
            product=self.product,
            runner=self.runner,
            serial=self.serial
        )
