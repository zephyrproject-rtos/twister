from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Generator

import serial

from twister2.device.device_abstract import DeviceAbstract
from twister2.device.hardware_map import HardwareMap
from twister2.exceptions import TwisterException, TwisterFlashException

logger = logging.getLogger(__name__)


class HardwareAdapter(DeviceAbstract):

    def __init__(self, twister_config, hardware_map: HardwareMap | None = None) -> None:
        if hardware_map is None:
            raise TwisterException('Hardware map must be provided for hardware adapter')
        super().__init__(twister_config, hardware_map=hardware_map)
        self.connection: serial.Serial | None = None
        self._exc: Exception | None = None

    def connect(self) -> serial.Serial:
        """Open serial connection."""
        if self.connection:
            # already opened
            return self.connection

        logger.info('Opening serial connection for %s', self.hardware_map.serial)
        try:
            self.connection = serial.Serial(
                self.hardware_map.serial,
                baudrate=self.hardware_map.baud,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=self.timeout
            )
        except serial.SerialException as e:
            logger.exception('Cannot open connection: %s', e)
            raise

        self.connection.flush()
        return self.connection

    def disconnect(self) -> None:
        """Close serial connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info('Closed serial connection for %s', self.hardware_map.serial)
        self.stop()

    def _get_command(self, build_dir: str) -> list[str]:
        west = shutil.which('west')
        if west is None:
            raise TwisterFlashException('west not found')

        command = [
            west,
            'flash',
            '--skip-rebuild',
            '--build-dir', build_dir,
        ]

        board_id: str = self.hardware_map.probe_id or self.hardware_map.id
        if self.hardware_map.runner and board_id:
            command.extend(['--runner', self.hardware_map.runner])
            command_extra_args = []
            if self.hardware_map.runner == 'pyocd':
                command_extra_args.append('--board-id')
                command_extra_args.append(board_id)
            elif self.hardware_map.runner == 'nrfjprog':
                command_extra_args.append('--dev-id')
                command_extra_args.append(board_id)
            elif self.hardware_map.runner == 'openocd' and self.hardware_map.product == 'STM32 STLink':
                command_extra_args.append('--cmd-pre-init')
                command_extra_args.append(f'hla_serial {board_id}')
            elif self.hardware_map.runner == 'openocd' and self.hardware_map.product == 'STLINK-V3':
                command_extra_args.append('--cmd-pre-init')
                command_extra_args.append(f'hla_serial {board_id}')
            elif self.hardware_map.runner == 'openocd' and self.hardware_map.product == 'EDBG CMSIS-DAP':
                command_extra_args.append('--cmd-pre-init')
                command_extra_args.append(f'cmsis_dap_serial {board_id}')
            elif self.hardware_map.runner == 'jlink':
                command.append(f'--tool-opt=-SelectEmuBySN {board_id}')
            elif self.hardware_map.runner == 'stm32cubeprogrammer':
                command.append(f'--tool-opt=sn={board_id}')

            if command_extra_args:
                command.append('--')
                command.extend(command_extra_args)
        return command

    def flash(self, build_dir: str | Path, timeout: float = 60.0) -> None:
        self.build_dir = build_dir
        self.timeout = self.timeout

        command = self._get_command(str(self.build_dir))

        logger.info('Flashing device %s', self.hardware_map.id)
        logger.info('Flashing command: %s', ' '.join(command))
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.twister_config.zephyr_base,
                env=self.env,
            )
        except subprocess.CalledProcessError:
            logger.error('Error while flashing device %s', self.hardware_map.id)
            self._exc = TwisterFlashException(f'Could not flash device {self.hardware_map.id}')
        else:
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
            else:
                for stdout in stdout.decode('utf-8').split('\n'):
                    if stdout:
                        logger.info(stdout)

            if process.returncode == 0:
                logger.info('Finished flashing %s', self.build_dir)
            else:
                # logger.error(process.stderr.decode())
                self._exc = TwisterFlashException(f'Could not flash device {self.hardware_map.id}')

    def save_serial_output_to_file(self, filename: str | Path) -> None:
        """Dump serial output to file."""
        with open(filename, 'w', encoding='UTF-8') as file:
            while self.connection:
                line = self.connection.readline()
                file.write(line.decode('utf-8'))

    @property
    def iter_stdout(self) -> Generator[str, None, None]:
        """Return output from serial."""
        if not self.connection:
            return
        logger.debug('Start listening on serial port %s', self.hardware_map.serial)
        self.connection.flush()
        while self.connection and self.connection.is_open:
            yield self.connection.readline().decode('UTF-8').strip()
