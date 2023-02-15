import textwrap

import pytest


@pytest.mark.parametrize('extra_args', ['', '-n 2'], ids=['no_xdist', 'xdist'])
def test_if_all_filters_are_correctly_applied(pytester, extra_args):
    pytester.makepyfile(
        textwrap.dedent(
            """\
            import pytest

            @pytest.mark.tags('tag1')
            def test_tag1():
                assert True

            @pytest.mark.tags('tag2')
            def test_tag2():
                assert True

            @pytest.mark.tags('tag1', 'tag2')
            def test_tag1_tag2():
                assert True

            @pytest.mark.tags('tag1', 'tag3')
            def test_tag1_tag3():
                assert True
            """)
    )
    result = pytester.runpytest(
        '--tags=@tag1',
        '--tags=~@tag3',
        '-v',
        '--zephyr-base=.',
        extra_args
    )
    assert result.ret == 0
    result.assert_outcomes(passed=2, failed=0, errors=0, skipped=0)
    result.stdout.fnmatch_lines([
        '*test_if_all_filters_are_correctly_applied.py::test_tag1*',
        '*test_if_all_filters_are_correctly_applied.py::test_tag1_tag2*',
    ])
