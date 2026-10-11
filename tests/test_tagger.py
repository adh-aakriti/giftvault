from tagger import parse_tags


def test_splits_on_commas():
    assert parse_tags("marvel, props") == ["marvel", "props"]


def test_strips_whitespace():
    assert parse_tags("  marvel  ,props  ") == ["marvel", "props"]


def test_lowercases():
    assert parse_tags("Marvel, PROPS") == ["marvel", "props"]


def test_drops_duplicates_within_one_submission():
    assert parse_tags("marvel, Marvel, marvel") == ["marvel"]


def test_ignores_empty_parts():
    assert parse_tags("marvel,,props,") == ["marvel", "props"]


def test_empty_input_returns_empty_list():
    assert parse_tags("") == []
    assert parse_tags(None) == []


def test_preserves_order_of_first_appearance():
    assert parse_tags("props, marvel, props") == ["props", "marvel"]