from __future__ import annotations

import asyncio.subprocess
import logging
import subprocess
import time
from pathlib import Path
from queue import Queue
from typing import Generator

from twister2.device.device_abstract import DeviceAbstract
from twister2.device.hardware_map import HardwareMap
from twister2.exceptions import TwisterFlashException

logger = logging.getLogger(__name__)

END_DATA = object()


class NativeSimulatorAdapter(DeviceAbstract):
    """Run tests with zephyr.exe."""

    def __init__(self, twister_config, hardware_map: HardwareMap | None = None, **kwargs):
        super().__init__(twister_config, hardware_map, **kwargs)
        self._process: subprocess.Popen | None = None
        self._process_ended_with_timeout: bool = False
        self.queue: Queue = Queue()
        self._stop_job: bool = False

    @staticmethod
    def _get_command(build_dir: Path | str) -> list[str]:
        """
        Return command to run.

        :param build_dir: build directory
        :return: command to run
        """
        return [str((Path(build_dir) / 'zephyr' / 'zephyr.exe').resolve())]

    def connect(self, timeout: float = 60):
        pass

    async def _run_command(self, command: list[str], timeout: float = 60):
        assert isinstance(command, (list, tuple, set))  # to avoid stupid and  difficult to debug mistakes
        self._process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=self.env
        )
        logger.debug('Started subprocess with PID %s', self._process.pid)
        end_time = time.time() + timeout
        while not self._stop_job:
            try:
                line = await asyncio.wait_for(self._process.stdout.readline(), 0.1)
            except asyncio.TimeoutError:
                pass
            else:
                if line:
                    self.queue.put(line.decode('utf-8').strip())
                    logger.debug(line.decode('utf-8').strip())
            if time.time() > end_time:
                self._process_ended_with_timeout = True
                logger.debug(f'Finished process with PID {self._process.pid} with timeout')
                break

        return await self._process.wait()

    def run(self) -> None:
        command: list[str] = self._get_command(self.build_dir)
        logger.info('Running command: %s', command)
        try:
            self._loop = asyncio.new_event_loop()
            return_code = self._loop.run_until_complete(
                self._run_command(command, timeout=self.timeout)
            )
        except subprocess.SubprocessError as e:
            logger.error('Flashing failed due to subprocess error %s', e)
            self._exc = TwisterFlashException(e.args)
        except FileNotFoundError as e:
            logger.error(f'Flashing failed due to file not found: {e.filename}')
            self._exc = TwisterFlashException(f'File not found: {e.filename}')
        except Exception as e:
            logger.error('Flashing failed: %s', e)
            self._exc = TwisterFlashException(e.args)
        else:
            if return_code == 0:
                logger.info('Flashing finished with success')
            elif return_code > 0:
                self._exc = TwisterFlashException(f'Flashing finished with errors for PID {self._process.pid}')
        finally:
            self.queue.put(END_DATA)
            self.queue.task_done()
            self._process = None

    def disconnect(self):
        """End subprocess."""
        self.stop()

    @property
    def out(self) -> Generator[str, None, None]:
        """Return output from serial."""
        end_time = time.time() + self.timeout
        while True:
            line = self.queue.get()
            if line == END_DATA:
                break
            yield line
            if time.time() > end_time:
                break
