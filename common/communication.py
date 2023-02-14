"""
`communication` package has methods used for exchanging messages between
the game entities
"""
import json
import asyncio
import base64


def json_to_bytes(jsonDict: dict) -> bytes:
    """ 
    Convert a JSON dictionary to a bytes object 
    Args:
        - jsonDict: JSON dict object to transform
    Returns
        - converted dictionary to bytes
    """
    strDict = json.dumps(jsonDict)
    byteDict = strDict.encode() # default encoding type is utf-8
    return base64.b64encode(byteDict)


def bytes_to_json(dictByte: bytes) -> dict:
    """ 
    Function to convert a bytes objects into a JSON dictionary 
    Args:
        - dictByte: JSON Dictionary in bytes object
    Returns:
        - Bytes object converted to dictionary
    """
    decodeB64 = base64.b64decode(dictByte)
    strData = decodeB64.decode() # default decoding is utf-8
    return json.loads(strData)
    

async def exact_recv(reader: asyncio.streams.StreamReader, nBytes: int) -> bytes | None:
    """ 
    Function to receive a given amount of data from a stream 
    Args:
        - reader: StreamReader wich contains the stream to read from
        - nBytes: Number of bytes to read
    Returns:
        - Bytes read or None if it fails
    """
    try:
        byteData = bytearray(0)
        while nBytes > 0:
            msg = await reader.read(nBytes)
            if len(msg) == 0: return None

            byteData += msg
            nBytes -= len(byteData) # make sure that the data is read
        return byteData
    except OSError as e:
        # Maybe add log here
        return None


async def exact_send(writer: asyncio.streams.StreamWriter, byteData: bytes) -> bool:
    """
    Function to send a given amount of data to a stream
    Args:
        - writer: StreamWriter wich contains the stream to write on
        - byteData: bytes to send
    Returns:
        - True if the data was sent, false otherwise
    """
    try:
        writer.write(byteData)
        await writer.drain()
    except OSError as e:
        # Maybe add log here
        return False
    return True


async def recv_dict(reader: asyncio.streams.StreamReader) -> dict | None:
    """ 
    Function to receive a dictionary message from a stream

    Args:

        reader: StreamReader wich contains the stream to read from
        pubkey: public key used to verify the signature, if None, it's assumed that the message isn't signed.
    Returns:
        Dictionary received from the client or None if anything wrong happened.

    Raises:
        SyntaxError if the signature provided is invalid
    """
    header = await exact_recv(reader, 4)

    if header == None: return None

    msgLength = int.from_bytes(header, 'big')
    message: bytes | None = await exact_recv(reader, msgLength)

    if message == None: return None

    return bytes_to_json(message)
    

async def send_dict(writer: asyncio.streams.StreamWriter, jsonDict: dict) -> bool:
    """
    Function to send a dictionary message to a stream. Transmits 1
    header with the length (in bytes) of a JSON dict object and then 
    the object itself (in bytes)

    Args:
        writer: StreamWriter object that contains the stream to write on
        jsonDict: JSON dictionary to send
        privkey: Private key used to sign the message, if not provided (None) the message isn't signed.
        cheat_signature: When True, the signature will be wrong.
        
    Returns:
        True or False given the status of the operation

    Raises:
        TypeError: If any of the given arguments does not match their supposed types.
    """
    if not isinstance(writer , asyncio.streams.StreamWriter):
        raise TypeError(f"Invalid writer parameter, expected asyncio.streams.StreamWriter, received {type(writer)}")

    if not isinstance(jsonDict , dict):
        raise TypeError(f"Invalid jsonDict parameter, expected 'dict', received {type(jsonDict)}")


    byteData: bytes = json_to_bytes(jsonDict)

    headerAndData: bytes = len(byteData).to_bytes(4, 'big') + byteData
    
    return await exact_send(writer, headerAndData)

async def sendRecv_dict(writer: asyncio.streams.StreamWriter, 
                    reader: asyncio.streams.StreamReader, 
                    jsonDict: dict) -> dict | None :
    """
    Function to send and receive a JSON dictionary to/from a stream
    Args:
        - writer: StreamWriter wich contains the stream to write on
        - reader: StreamReader wich contains the stream to read from
        - jsonDict: Json dictionary to send
    Returns:
        - Received JSON dictionary or None if the status failed
    """
    if await send_dict(writer, jsonDict):
        return await recv_dict(reader)
    else:
        return None

    

