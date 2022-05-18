import textwrap

pytest_plugins = ['pytester']


def test_filter_plugin(testdir):
    testdir.makepyfile(
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

            @pytest.mark.slow
            def test_slow():
                assert True
            """)
    )
    result = testdir.runpytest(
        '--tags=@tag1',
        '--tags=~@tag3',
        '-v',
        '--zephyr-base=.'
    )
    assert result.ret == 0
    result.assert_outcomes(passed=2, deselected=3)
    result.stdout.fnmatch_lines([
        '*test_filter_plugin.py::test_tag1 PASSED*',
        '*test_filter_plugin.py::test_tag1_tag2 PASSED*',
    ])
