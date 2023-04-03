"""
This module implements adapter class for real device (DK board).
"""
from __future__ import annotations

import logging
import os
import pty
import re
import shutil
import subprocess
from pathlib import Path
from typing import Generator

import serial

from twister2.device.device_abstract import DeviceAbstract
from twister2.device.hardware_map import HardwareMap
from twister2.exceptions import TwisterFlashException
from twister2.helper import log_command
from twister2.log_files.log_file import DeviceLogFile, HandlerLogFile
from twister2.twister_config import TwisterConfig

logger = logging.getLogger(__name__)


class HardwareAdapter(DeviceAbstract):
    """Adapter class for real device."""

    def __init__(
        self, twister_config: TwisterConfig, *, hardware_map: HardwareMap, **kwargs
    ) -> None:
        """
        :param twister_config: twister configuration
        :param hardware_map: device hardware map
        """
        super().__init__(twister_config, **kwargs)
        self.hardware_map = hardware_map
        self.connection: serial.Serial | None = None
        self.command: list[str] = []
        self.process_kwargs: dict = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'cwd': self.twister_config.zephyr_base,
            'env': self.env,
        }
        self.serial_pty_proc: subprocess.Popen | None = None

    def connect(self, timeout: float = 1) -> None:
        """
        Open serial connection.

        :param timeout: Read timeout value in seconds
        """
        if self.connection:
            # already opened
            return

        serial_name = self._open_serial_pty() or self.hardware_map.serial
        logger.info('Opening serial connection for %s', serial_name)
        try:
            self.connection = serial.Serial(
                serial_name,
                baudrate=self.hardware_map.baud,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=timeout
            )
        except serial.SerialException as e:
            logger.exception('Cannot open connection: %s', e)
            self._close_serial_pty()
            raise

        self.connection.flush()

    def disconnect(self) -> None:
        """Close serial connection."""
        if self.connection:
            serial_name = self.connection.port
            self.connection.close()
            self.connection = None
            logger.info('Closed serial connection for %s', serial_name)
        self._close_serial_pty()

    def _open_serial_pty(self) -> str | None:
        """Open a pty pair, run process and return tty name"""
        if not self.hardware_map.serial_pty:
            return None
        master, slave = pty.openpty()
        try:
            self.serial_pty_proc = subprocess.Popen(
                re.split(',| ', self.hardware_map.serial_pty),
                stdout=master,
                stdin=master,
                stderr=master
            )
        except subprocess.CalledProcessError as e:
            logger.exception('Failed to run subprocess %s, error %s',
                             self.hardware_map.serial_pty, str(e))
            raise
        return os.ttyname(slave)

    def _close_serial_pty(self) -> None:
        """Terminate the process opened for serial pty script"""
        if self.serial_pty_proc:
            self.serial_pty_proc.terminate()
            self.serial_pty_proc.communicate()
            logger.info('Process %s terminated', self.hardware_map.serial_pty)
            self.serial_pty_proc = None

    def generate_command(self, build_dir: Path | str) -> None:
        """
        Return command to flash.

        :param build_dir: build directory
        :return: command to flash
        """
        west = shutil.which('west')
        if west is None:
            raise TwisterFlashException('west not found')

        command = [
            west,
            'flash',
            '--skip-rebuild',
            '--build-dir', str(build_dir),
        ]

        command_extra_args = []
        if self.twister_config.west_flash:
            command_extra_args.extend(self.twister_config.west_flash)

        runner = self.hardware_map.runner or self.twister_config.west_runner
        if runner:
            command.extend(['--runner', runner])

            board_id: str = self.hardware_map.probe_id or self.hardware_map.id
            if board_id:
                if runner == 'pyocd':
                    command_extra_args.append('--board-id')
                    command_extra_args.append(board_id)
                elif runner == 'nrfjprog':
                    command_extra_args.append('--dev-id')
                    command_extra_args.append(board_id)
                elif runner == 'openocd' and self.hardware_map.product == 'STM32 STLink':
                    command_extra_args.append('--cmd-pre-init')
                    command_extra_args.append(f'hla_serial {board_id}')
                elif runner == 'openocd' and self.hardware_map.product == 'STLINK-V3':
                    command_extra_args.append('--cmd-pre-init')
                    command_extra_args.append(f'hla_serial {board_id}')
                elif runner == 'openocd' and self.hardware_map.product == 'EDBG CMSIS-DAP':
                    command_extra_args.append('--cmd-pre-init')
                    command_extra_args.append(f'cmsis_dap_serial {board_id}')
                elif runner == 'jlink':
                    command.append(f'--tool-opt=-SelectEmuBySN {board_id}')
                elif runner == 'stm32cubeprogrammer':
                    command.append(f'--tool-opt=sn={board_id}')

        if command_extra_args:
            command.append('--')
            command.extend(command_extra_args)
        self.command = command

    def flash_and_run(self, timeout: float = 60.0) -> None:
        if not self.command:
            msg = 'Flash command is empty, please verify if it was generated properly.'
            logger.error(msg)
            raise TwisterFlashException(msg)
        if self.hardware_map.id:
            logger.info('Flashing device %s', self.hardware_map.id)
        log_command(logger, 'Flashing command', self.command, level=logging.INFO)
        try:
            process = subprocess.Popen(
                self.command,
                **self.process_kwargs
            )
        except subprocess.CalledProcessError:
            logger.error('Error while flashing device %s', self.hardware_map.id)
            raise TwisterFlashException(f'Could not flash device {self.hardware_map.id}')
        else:
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
            else:
                for line in stdout.decode('utf-8').split('\n'):
                    if line:
                        logger.info(line)
            if process.returncode == 0:
                logger.info('Flashing finished')
            else:
                if stderr:
                    self.device_log_file.handle(data=stderr)
                raise TwisterFlashException(f'Could not flash device {self.hardware_map.id}')

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
            stream = self.connection.readline()
            self.handler_log_file.handle(data=stream)
            yield stream.decode('UTF-8').strip()

    def initialize_log_files(self, build_dir: str | Path) -> None:
        self.handler_log_file = HandlerLogFile.create(build_dir=build_dir)
        self.device_log_file = DeviceLogFile.create(build_dir=build_dir)
