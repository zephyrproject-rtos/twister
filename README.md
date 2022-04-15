# Twister v2

[![Run tests](https://github.com/zephyrproject-rtos/twister/actions/workflows/main.yaml/badge.svg?branch=main)](https://github.com/zephyrproject-rtos/twister/actions/workflows/main.yaml)
[![codecov](https://codecov.io/gh/zephyrproject-rtos/twister/branch/main/graph/badge.svg?token=F8DSSX20B5)](https://codecov.io/gh/zephyrproject-rtos/twister)

Pytest plugin to run Zephyr tests and collect results.

## CAUTION

This repository is not used in production and is still under development.
The code for Twister which is used in Zephyr's CIs can be found [here](https://github.com/zephyrproject-rtos/zephyr/blob/main/scripts/twister).

## Installation

Installation from github:
```
pip install git+https://github.com/zephyrproject-rtos/twister.git
```

Installation from the source:
```
pip install .
```

Build wheel package:
```
pip install build
python -m build --wheel
```

## Requirements:

- Python >= 3.8
- pytest >= 7.0.0

## Usage

Show all available options:
```
pytest --help
```

Run tests:
```
pytest <PATH_TO_ZEPHYR>/tests/kernel/common -vv --zephyr-base=<PATH_TO_ZEPHYR> --platform=native_posix --results-json=twister-out/results.json --log-level=DEBUG
```

If environmental variable ZEPHYR_BASE is set, one can omit `--zephyr-base` argument.

Show what fixtures and tests would be executed but don't execute anything:
```
pytest tests --setup-plan
```

List all tests without executing:
```
pytest tests --collect-only
```

Run tests only for specific platforms:
```
pytest tests --platform=native_posix --platform=nrf52840dk_nrf52840
```

Provide directory to search for board configuration files:
```
pytest tests --board-root=path_to_board_dir
```

## Reports

Generate test plan in JSON format:
```
pytest tests --testplan-csv=testplan.csv --collect-only
```

Generate test plan in CSV format:
```
pytest tests --testplan-json=testplan.json --collect-only
```

Generate test results in JSON format:
```
pytest tests --resutls-json=results.json
```

## Filtering tests

Run tests with given tags (`@` is optional and can be omitted):
```
$ pytest tests --tags=@tag1,@tag2
```

Examples of usage:

* not tag1
  * `--tags=~@tag1`
* tag1 and tag2:
  * `--tags=@tag1 --tags=@tag2`
* tag1 or tag2
  * `--tags=@tag1,@tag2`
* (tag1 or tag2) and tag3 and not tag4
  * `--tags=@tag1,@tag2 --tags=@tag3 --tags=~@tag4`

## Tools

Scan connected devices and create hardware map:
```
twister_tools --generate-hardware-map hardware_map.yaml
```

Scan connected devices and list hardware map:
```
twister_tools --list-hardware-map
```

List all platforms:
```
twister_tools --list-platforms
```

List default platforms only:
```
twister_tools --list-platforms --default-only
```
