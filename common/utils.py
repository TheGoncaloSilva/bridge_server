"""
`utils` packages has functions that can be used by client and server
"""
def check_dict_fields(msg: dict , expectedFields: list[str]) -> None:
    """
    Function to check if the given dictionaries has the expected keys
    Args:
        - msg: given dictionary
        - expectedFields: list with the expected keys
    Raises:
        - ValueError: if expectedFields values are not in msg keys and/or
        msg is empty
    """
    if msg == {}: 
        raise ValueError(f"msg cannot be empty")
    
    for f in expectedFields:
        if f not in msg.keys():
            raise ValueError(f"Missing argument {(f)}")
        