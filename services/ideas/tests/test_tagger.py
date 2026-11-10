import pytest

from tagger import parse_tags


@pytest.mark.parametrize("raw,expected", [
    ("marvel, props",        ["marvel", "props"]),
    ("  marvel  ,props  ",   ["marvel", "props"]),
    ("Marvel, PROPS",        ["marvel", "props"]),
    ("marvel, Marvel, marvel", ["marvel"]),
    ("marvel,,props,",       ["marvel", "props"]),
    ("",                     []),
    (None,                   []),
    ("props, marvel, props", ["props", "marvel"]),
    ("marvel",               ["marvel"]),
    ("   ",                  []),
])
def test_parse_tags(raw, expected):
    assert parse_tags(raw) == expected