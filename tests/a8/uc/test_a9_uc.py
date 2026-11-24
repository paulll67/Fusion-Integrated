from tests.a8._a9_design import assert_frozen_design


def test_a9_uc_design_is_frozen_and_traceable():
    assert_frozen_design("uc", "UC", ("EL-UC-",))
