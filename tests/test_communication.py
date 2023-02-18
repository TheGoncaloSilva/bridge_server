import pytest
from common.communication import json_to_bytes, bytes_to_json, send_dict

def test_json_to_bytes():
    dictObj = {'key1': 1, 'key2': 'value2'}
    expectedBytes = b'eyJrZXkxIjogMSwgImtleTIiOiAidmFsdWUyIn0='
    assert json_to_bytes(dictObj) == expectedBytes


def test_bytes_to_json():
    bytesObj = b'eyJrZXkxIjogMSwgImtleTIiOiAidmFsdWUyIn0='
    expectedDict = {'key1': 1, 'key2': 'value2'}
    assert bytes_to_json(bytesObj) == expectedDict


@pytest.mark.anyio
async def test_send_dict_wrong_type():
    with pytest.raises(TypeError):
        testObj = 'invalid writer object'
        await send_dict(testObj, {'key1': 'value1'})

@pytest.mark.anyio
async def test_send_dict_wrong_json():
    with pytest.raises(TypeError):
        await send_dict(None, 'invalid json')
