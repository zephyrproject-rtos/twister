# twister v2

[![Run tests](https://github.com/PerMac/TwisterV2/actions/workflows/main.yaml/badge.svg?branch=poc)](https://github.com/PerMac/TwisterV2/actions/workflows/main.yaml)

Pytest plugin to run Zephyr tests and collect results.

## Installation

Installation from github:
```
pip install git+https://github.com/PerMac/TwisterV2.git
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
pytest tests/kernel/common -vv --zephyr-base=path_to_zephyr --platform=native_posix --results-json=twister-out/results.json --log-level=DEBUG
```

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
pytest tests --platform=qemu_x86 --platform=nrf51dk_nrf51422
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
  * --tags=~@tag1
* tag1 and tag2:
  * --tags=@tag1 --tags=@tag2
* tag1 or tag2
  * --tags=@tag1,@tag2
* (tag1 or tag2) and tag3 and not tag4
  * --tags=@tag1,@tag2 --tags=@tag3 --tags=~@tag4

## Tools

Scan connected devices and create hardware map:
```
twister_tools --generate-hardware-map hardware_map.yaml
```

Scan connected devices and list hardware map:
```
twister_tools --list-hardware-map
```

List default platforms:
```
twister_tools --list-default-platforms
```
