"""
This module implements adapter class for a device simulator.
"""
from __future__ import annotations

import asyncio
import asyncio.subprocess
import logging
import os
import signal
import subprocess
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Generator

from twister2.device.device_abstract import DeviceAbstract
from twister2.device.hardware_map import HardwareMap
from twister2.exceptions import TwisterRunException

logger = logging.getLogger(__name__)

END_DATA = object()


class NativeSimulatorAdapter(DeviceAbstract):
    """Adapter class for a device simulator."""

    def __init__(self, twister_config, hardware_map: HardwareMap | None = None, **kwargs):
        super().__init__(twister_config, hardware_map, **kwargs)
        self._process: subprocess.Popen | None = None
        self._process_ended_with_timeout: bool = False
        self.queue: Queue = Queue()
        self._stop_job: bool = False
        self._exc: Exception | None = None  #: store any exception which appeared running this thread
        self._thread: threading.Thread | None = None

    @staticmethod
    def _get_command(build_dir: Path | str) -> list[str]:
        """
        Return command to run.

        :param build_dir: build directory
        :return: command to run
        """
        return [str((Path(build_dir) / 'zephyr' / 'zephyr.exe').resolve())]

    def connect(self, timeout: float = 1) -> None:
        pass

    def run(self, build_dir: str | Path, timeout: float = 60.0) -> None:
        self._thread = threading.Thread(target=self._run_simulation, args=(build_dir, timeout), daemon=True)
        self._thread.start()
        # Give a time to start subprocess before test is executed
        time.sleep(0.1)

    async def _run_command(self, command: list[str], timeout: float = 60.):
        assert isinstance(command, (list, tuple, set))  # to avoid stupid and difficult to debug mistakes
        # we are using asyncio to run subprocess to be able to read from stdout
        # without blocking while loop (readline with timeout)
        self._process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=self.env
        )
        logger.debug('Started subprocess with PID %s', self._process.pid)
        end_time = time.time() + timeout
        while not self._stop_job and not self._process.stdout.at_eof():
            try:
                line = await asyncio.wait_for(self._process.stdout.readline(), timeout=0.1)
            except asyncio.TimeoutError:
                pass
            else:
                if line:
                    self.queue.put(line.decode('utf-8').strip())
            if time.time() > end_time:
                self._process_ended_with_timeout = True
                logger.debug(f'Finished process with PID {self._process.pid} after {timeout} seconds timeout')
                break

        self.queue.put(END_DATA)  # indicate to the other threads that there will be no more data in queue
        return await self._process.wait()

    def _run_simulation(self, build_dir: str | Path, timeout: float) -> None:
        command: list[str] = self._get_command(build_dir)
        logger.info('Running command: %s', command)
        try:
            return_code: int = asyncio.run(
                self._run_command(command, timeout=timeout)
            )
        except subprocess.SubprocessError as e:
            logger.error('Running simulation failed due to subprocess error %s', e)
            self._exc = TwisterRunException(e.args)
        except FileNotFoundError as e:
            logger.error(f'Running simulation failed due to file not found: {e.filename}')
            self._exc = TwisterRunException(f'File not found: {e.filename}')
        except Exception as e:
            logger.error('Running simulation failed: %s', e)
            self._exc = TwisterRunException(e.args)
        else:
            if return_code == 0:
                logger.info('Running simulation finished with return code %s', return_code)
            else:
                logger.warning('Running simulation finished with return code %s', return_code)
        finally:
            self.queue.put(END_DATA)  # indicate to the other threads that there will be no more data in queue

    def disconnect(self):
        pass

    def stop(self) -> None:
        """Stop device."""
        self._stop_job = True
        time.sleep(0.1)  # give a time to end while loop in running simulation
        if self._process is not None:
            # kill subprocess if it is still running
            try:
                os.kill(self._process.pid, signal.SIGINT)
            except ProcessLookupError:
                pass  # process is not running
        if self._thread is not None:
            self._thread.join(timeout=1)  # Should end immediately, but just in case we set timeout for 1 sec
        if self._exc:
            raise self._exc

    @property
    def iter_stdout(self) -> Generator[str, None, None]:
        """Return output from serial."""
        while True:
            line = self.queue.get()
            if line == END_DATA:
                logger.debug('No more data from running process')
                break
            yield line
            self.queue.task_done()
