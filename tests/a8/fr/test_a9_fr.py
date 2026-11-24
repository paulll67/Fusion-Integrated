from tests.a8._a9_design import assert_frozen_design


def test_a9_fr_design_is_frozen_and_traceable():
    assert_frozen_design("fr", "FR", ("AFR-EL-",))
