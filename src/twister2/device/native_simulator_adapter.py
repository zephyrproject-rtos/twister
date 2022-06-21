from __future__ import annotations

import logging
import subprocess
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Generator

from twister2.device.device_abstract import DeviceAbstract
from twister2.device.hardware_map import HardwareMap
from twister2.exceptions import TwisterFlashException, TwisterTimeoutExpired

logger = logging.getLogger(__name__)


class NativeSimulatorAdapter(DeviceAbstract):
    """Run tests with zephyr.exe."""

    def __init__(self, twister_config, hardware_map: HardwareMap | None = None, **kwargs):
        super().__init__(twister_config, hardware_map, **kwargs)
        self._process: subprocess.Popen | None = None
        self._process_ended_with_timeout: bool = False
        self.queue: Queue = Queue()

    @staticmethod
    def get_command(build_dir: Path | str) -> str:
        return str((Path(build_dir) / 'zephyr' / 'zephyr.exe').resolve())

    def connect(self, timeout: float = 60):
        pass

    def disconnect(self):
        """End subprocess."""
        if self._process:
            if self._process.poll() is None:
                self._process.kill()
                logger.debug('Process terminated: %s', self._process.pid)
                self._process = None

    def flash(self, build_dir: str | Path, timeout: float = 60.0) -> None:
        """Run simulation."""
        command: str = self.get_command(build_dir)
        logger.info('Flashing device')
        logger.info('Flashing command: %s', command)
        try:
            self._process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.env,
            )

            t1 = self._collect_process_output(self._process)
            t2 = self._wait_and_terminate_process(self._process, timeout=timeout)
            logger.info('Started process %s', self._process.pid)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
        except subprocess.CalledProcessError as e:
            logger.exception('Flashing failed due to error %s', e)
            raise
        else:
            if self._process.returncode == 0:
                logger.info('Finished flashing %s', build_dir)
            elif self._process_ended_with_timeout:
                raise TwisterTimeoutExpired(f'Process {self._process.pid} terminated after {timeout} seconds')
            else:
                if stderr := self._process.stderr.read():
                    logger.error(stderr.decode())
                raise TwisterFlashException(f'Could not run simulator with PID {self._process.pid}')

    def _collect_process_output(self, process: subprocess.Popen) -> threading.Thread:
        """Create Thread which saves a process output to a file."""
        def _read():
            with process.stdout:
                for line in iter(process.stdout.readline, b''):
                    self.queue.put(line.decode().strip())

        return threading.Thread(target=_read, daemon=True)

    # @staticmethod
    def _wait_and_terminate_process(self, process: subprocess.Popen, timeout: float) -> threading.Thread:
        """Create Thread which kills a process after given time."""
        def _waiting():
            end_time = time.time() + timeout
            while process.poll() is None and time.time() < end_time:
                time.sleep(0.1)
            if process.poll() is None:
                process.kill()
                logger.error('Process %s terminated after %s seconds', process.pid, timeout)
                self._process_ended_with_timeout = True
        return threading.Thread(target=_waiting, daemon=True)

    @property
    def out(self) -> Generator[str, None, None]:
        """Return output from serial."""
        while not self.queue.empty():
            yield self.queue.get()
