import pytest
from common.utils import check_dict_fields

def test_check_dict_fields():
    msg = {"name": "Alice", "age": 25, "gender": "female"}
    expected_fields = ["name", "age", "gender"]

    # Test that check_dict_fields does not raise any exception
    check_dict_fields(msg, expected_fields)

    # Test that ValueError is raised if expected fields are missing
    expected_fields = ["name", "age", "gender", "location"]
    with pytest.raises(ValueError):
        check_dict_fields(msg, expected_fields)

    # Test that ValueError is raised if msg is empty
    msg = {}
    with pytest.raises(ValueError):
        check_dict_fields(msg, expected_fields)

    # Test that ValueError is raised if expected fields are empty
    expected_fields = []
    with pytest.raises(ValueError):
        check_dict_fields(msg, expected_fields)
