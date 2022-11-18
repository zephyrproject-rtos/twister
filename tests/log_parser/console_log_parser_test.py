import textwrap
from pathlib import Path

from twister2.log_parser.console_log_parser import ConsoleLogParser


def test_if_console_log_parser_passes_for_one_line_type():
    harness_config = {
        'type': 'one_line',
        'regex': [
            'Hello World!(.*)'
        ]
    }
    log = textwrap.dedent("""\
        *** Booting Zephyr OS build zephyr-v3.0.0-2567-g70c48417c7a0  ***
        Hello World!
        mylib says: Hello World!
    """).split('\n')
    parser = ConsoleLogParser(stream=iter(log), harness_config=harness_config)
    list(parser.parse())
    assert parser.state == parser.STATE.PASSED
    assert parser.matched_lines == ['Hello World!']


def test_if_console_log_parser_fails_for_one_line_type():
    harness_config = {
        'type': 'one_line',
        'regex': [
            'Hello World! (.*)'
        ]
    }
    log = textwrap.dedent("""\
        *** Booting Zephyr OS build zephyr-v3.0.0-2567-g70c48417c7a0  ***
        The Zen of Python, by Tim Peters
        Beautiful is better than ugly.
        Explicit is better than implicit.
    """).split('\n')
    parser = ConsoleLogParser(stream=iter(log), harness_config=harness_config)
    list(parser.parse())
    assert parser.state == parser.STATE.FAILED


def test_if_console_log_parser_passes_for_not_ordered_multi_line(resources: Path):
    log_file = resources.joinpath('console_log_pass.txt')
    harness_config = {
        'type': 'multi_line',
        'ordered': False,
        'regex': [
            '.*STARVING.*',
            '.*DROPPED ONE FORK.*',
            '.*THINKING.*',
            '.*EATING.*'
        ]
    }
    with open(log_file, encoding='UTF-8') as file:
        parser = ConsoleLogParser(stream=iter(file), harness_config=harness_config)
        list(parser.parse())
        assert parser.state == parser.STATE.PASSED
        assert parser.matched_lines == [
            'Philosopher 4 [C:-1]        STARVING\n',
            'Philosopher 4 [C:-1]   EATING  [  25 ms ]\n',
            'Philosopher 4 [C:-1]    DROPPED ONE FORK\n',
            'Philosopher 4 [C:-1]  THINKING [  25 ms ]\n'
        ]


def test_if_console_log_parser_fails_for_not_ordered_multi_line(resources: Path):
    log_file = resources.joinpath('console_log_pass.txt')
    harness_config = {
        'type': 'multi_line',
        'ordered': False,
        'regex': [
            '.*STARVING.*',
            '.*DROPPED ONE FORK.*',
            '.*DUMMY LINE.*',
            '.*EATING.*'
        ]
    }
    with open(log_file, encoding='UTF-8') as file:
        parser = ConsoleLogParser(stream=iter(file), harness_config=harness_config)
        list(parser.parse())
        assert parser.state == parser.STATE.FAILED


def test_if_console_log_parser_passes_for_ordered_multi_line(resources: Path):
    log_file = resources.joinpath('console_log_pass.txt')
    harness_config = {
        'type': 'multi_line',
        'ordered': True,
        'regex': [
            '.*STARVING.*',
            '.*DROPPED ONE FORK.*',
            '.*THINKING.*',
            '.*EATING.*'
        ]
    }
    with open(log_file, encoding='UTF-8') as file:
        parser = ConsoleLogParser(stream=iter(file), harness_config=harness_config)
        list(parser.parse())
        assert parser.state == parser.STATE.PASSED


def test_if_console_log_parser_fails_for_ordered_multi_line():
    log = textwrap.dedent("""\
        The Zen of Python, by Tim Peters
        Beautiful is better than ugly.
        Simple is better than complex.
        Complex is better than complicated.
        Explicit is better than implicit.
        Flat is better than nested.
        Sparse is better than dense.
    """).split('\n')
    harness_config = {
        'type': 'multi_line',
        'ordered': True,
        'regex': [
            '.*Beautiful is better than ugly.*',
            '.*Explicit is better than implicit.*',
            '.*Simple is better than complex.*'
        ]
    }
    parser = ConsoleLogParser(stream=iter(log), harness_config=harness_config)
    list(parser.parse())
    assert parser.state == parser.STATE.FAILED
