import pytest

from twister2.filter.tag_filter import TagMatcher


@pytest.mark.parametrize(
    'tags, include, exclude',
    [
        ([], [], []),
        (['@tag1,@tag2', '@tag3,~tag4'],
         [{'tag1', 'tag2'}, {'tag3'}], [{'tag4'}]),

    ]
)
def test_tags_parser(tags, include, exclude):
    tags_filter = TagMatcher(tags=tags)
    assert tags_filter.deselected == exclude
    assert tags_filter.selected == include


@pytest.mark.parametrize(
    'include, exclude, test_tags',
    [
        ([{1, 2}, {3}], [{4}], {1, 3}),
        ([{1, 2}, {3}], [{4}], {2, 3}),
        ([{1, 2}, {3}], [{4}], {1, 2, 3}),

    ]
)
def test_should_run_with_tags(include, exclude, test_tags):
    tags_filter = TagMatcher([])
    tags_filter.deselected = exclude
    tags_filter.selected = include
    assert tags_filter.should_run_with(test_tags)


@pytest.mark.parametrize(
    'include, exclude, test_tags',
    [
        ([{1, 2}, {3}], [{4}], {1}),
        ([{1, 2}, {3}], [{4}], {1, 5}),
        ([{1, 2}, {3}], [{4}], {1, 3, 4}),

    ]
)
def test_should_not_run_with_tags(include, exclude, test_tags):
    tags_filter = TagMatcher([])
    tags_filter.deselected = exclude
    tags_filter.selected = include
    assert tags_filter.should_run_with(test_tags) is False


@pytest.mark.parametrize(
    'tag1,tag2',
    [
        ({'tag1'}, {'tag1', 'tag2'}),
        ({'tag2'}, {'tag1', 'tag3', 'tag2'})
    ]
)
def test_if_item_with_tags_should_be_included(tag1, tag2):
    assert TagMatcher()._should_be_selected(tag1, tag2)


@pytest.mark.parametrize(
    'tag1,tag2',
    [
        ({'tag2'}, {'tag1', 'tag2'}),
        ({'tag3'}, {'tag1', 'tag3', 'tag2'}),
        ({'tag1', 'tag4'}, {'tag1', 'tag3', 'tag2'}),
    ]
)
def test_if_item_with_tags_should_be_excluded(tag1, tag2):
    assert TagMatcher()._should_be_deselected(tag1, tag2)
