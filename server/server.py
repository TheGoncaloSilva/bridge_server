"""
`server` package is used to represent a server entity
"""
import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime
from attr import dataclass

# Check https://www.geeksforgeeks.org/python-import-from-parent-directory/
# For better information
# getting the name of the directory
# where this file is present.
current = os.path.dirname(os.path.realpath(__file__))
 
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
 
# adding the parent directory to
# the sys.path.
sys.path.append(parent)

import common.communication as comms
import common.utils as util

@dataclass
class ClientValues:
    """
    Class used to store the associated values of each client
    """
    writer: asyncio.streams.StreamWriter
    reader: asyncio.streams.StreamReader
    nick: str
    ip: str
    port: int

@dataclass
class ServerValues:
    """
    Class used to store the values of the server
    """
    server: asyncio.base_events.Server
    ip: str
    port: int

INVALID_SEQ_NUMBER: int = -1

def find_seq_number_by_stream_reader(stream: asyncio.streams.StreamReader, streams: dict[int,ClientValues]) -> int:
    """
    Function to get the identification number of a given StreamReader
    Args:
        - stream: Given Stream Reader
        - streams: dictionary of Ids and a ClientValues object
    Returns:
        - integer Id of the ClientValue
    """
    for ids in streams.keys():
        streamReader : asyncio.streams.StreamReader = streams[ids].reader
        if streamReader == stream:
            return ids
    return INVALID_SEQ_NUMBER


def find_seq_number_by_stream_writer(stream: asyncio.streams.StreamWriter, streams: dict[int,ClientValues]) -> int:
    """
    Function to get the identification number of a given StreamWriter
    Args:
        - stream: Given Stream Writer
        - streams: dictionary of Ids and a ClientValues object
    Returns:
        - integer Id of the ClientValues
    """
    for ids in streams.keys():
        streamWriter : asyncio.streams.StreamWriter = streams[ids].writer
        if streamWriter == stream:
            return ids
    return INVALID_SEQ_NUMBER

async def send_to_everyone(streams: dict[int,ClientValues], exceptions: list[asyncio.streams.StreamWriter], payload: dict) -> None:
    """
    Function to send data to all connected streams, excluding exceptions
    Args:
        - streams: dictionary of Ids and a ClientValues object
        - exceptions: list with all the exception streams
        - payload: data to send
    """
    for ids in streams.keys():
        streamWriter : asyncio.streams.StreamWriter = streams[ids].writer
        if streamWriter not in exceptions:
            await comms.send_dict(streamWriter, payload) 


class Server:
    """
    Class that enables the server
    """
    def __init__(self, maxClients: int) -> None:

        self.maxClients: int = maxClients
        self.clients: dict[int, ClientValues] = {} # 
        self.server: ServerValues | None = None
        self.lastId: int = 1
        

    async def create_server(self, ip: str, port: int) -> asyncio.base_events.Server:
        """
        Function that uses class values to create a Server with the 
            designated Ip address and Port
        Args:
            - ip: Ip address of the Server
            - port: Port of the Server to operate on
        Returns:
            - Asyncio Server object
        Raises:
            - ValueError: if Server was already established
            - TypeError: if supplied  attributes are not of correct type  
            - OSError: if connection wasn't established (handled by 
            asyncio.open_connection function)
        """
        if self.server != None: raise ValueError(f"Server already defined")

        if not isinstance(ip, str) or not isinstance(port, int):
            raise TypeError("Wrong usage. Use (str, int) types")
        
        server = await asyncio.start_server(
                                        self.handle_client, 
                                        ip, 
                                        port
                                        )

        return server
    

    async def new_client(self, msg: dict, reader: asyncio.streams.StreamReader, 
                    writer: asyncio.streams.StreamWriter) -> dict | None:
        """
        Function used to process a new connection by a client
        Args:
            - msg: message sent by the client
            - reader: Reader stream of the client
            - writer: Writer stream of the client
        Returns:
            - A dictionary object to send to all clients, excluding the 
                connected client, or None in case it is not necessary
        """
        try:
            util.check_dict_fields(msg, ['option'])

            # {"option": "join", "nick": nick, "ip": ip, "port": port} -> Join message
            if msg["option"] == "join":
                util.check_dict_fields(msg, ['nick', 'ip', 'port'])
                if [client for client in self.clients if self.clients[client].nick == msg['nick']] == []:
                    
                    # Give the new client all current clients
                    for ids in self.clients.keys():
                        client: ClientValues = self.clients[ids]
                        joinMsg: dict = {"option": "join", "nick": client.nick, "ip": client.ip, "port": client.port}
                        logger.debug(f"Sending to {writer.get_extra_info('peername')}: {joinMsg}")
                        await comms.send_dict(writer, joinMsg)


                    self.clients[self.lastId] = (ClientValues(writer, reader, msg["nick"], msg["ip"], msg["port"]))
                    self.lastId = self.lastId + 1
                    logger.warning(f"Client {msg['nick']} with {msg['ip']}:{msg['port']} has entered")
                    return msg
                else:
                    logger.debug(f"Client already registered, message: {msg}")

            else:
                logger.debug("Unknow message option: " + str(msg['option']))
        except ValueError as e:
            logger.debug("Message not in the correct type")
        
        return None
        

    async def process_client(self, msg: dict) ->  dict | None:
        """
        Function used to process a message 
        Args:
            - msg: message sent by the client
        Returns:
            - A dictionary object to send to all clients, excluding the 
                client that sent the message, or None in case it is 
                not necessary
        """
        try:
            util.check_dict_fields(msg, ['option'])

            # {"option": "message", "message": message, "nick": nick} -> Message message
            if msg["option"] == "message":
                util.check_dict_fields(msg, ['message', 'nick'])
                if [client for client in self.clients if self.clients[client].nick == msg['nick']] != []:
                    logger.info(f"Client {msg['nick']} at -> {msg['message']}")
                    return msg
                else:
                    logger.debug(f"Client not registered, message: {msg}")

            else:
                logger.debug("Unknow message option: " + str(msg['option']))
        except ValueError as e:
            logger.debug("Message not in the correct type")

        return None


    async def handle_client(self, reader : asyncio.streams.StreamReader, writer : asyncio.streams.StreamWriter) -> None:
        """
        Main function used to operate clients
        """
        try:
            while True:

                msg = await comms.recv_dict(reader)
                if msg == None: break

                addr = writer.get_extra_info('peername')

                logger.debug(f"Received: {msg!r} from {addr!r}")
                
                seq: int = find_seq_number_by_stream_reader(reader, self.clients)
                # New user
                if seq == INVALID_SEQ_NUMBER:
                    if len(self.clients) == self.maxClients:
                        logger.warning(f"Client from {addr} exceeded the maximum user number")
                        writer.close(); await writer.wait_closed()
                        break
                    else:
                        response: dict | None = await self.new_client(msg, reader, writer)
                # Existing user
                else:
                    response: dict | None = await self.process_client(msg)           

                if response != None:
                    logger.debug(f"Sending to everyone, minus sender: {response}")
                    await send_to_everyone(self.clients, [writer], response)

        except OSError as e:
            logger.debug("Closed connection")
            closedSeq: int = find_seq_number_by_stream_writer(writer , self.clients)
            # New user
            if seq == INVALID_SEQ_NUMBER:
                logger.warning("Unregistered client disconnected")
            # Existing user
            else:
                response: dict = {"option": "disconnect", "nick": self.clients[closedSeq].nick}
                client: ClientValues = self.clients.pop(closedSeq)
                logger.warning(f"Disconnecting {client.nick}")
                logger.debug(f"Sending to everyone: {response}")
                await send_to_everyone(self.clients, [], response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", help="IP address to bind to", default="127.0.0.1")
    parser.add_argument("--port", help="TCP port", type=int, default=8005)
    parser.add_argument("--maxClients", help="Maximum number of clients", type=int, default=5)
    parser.add_argument("--log", help="Log threshold (default=INFO)", type=str, default='INFO')
    args = parser.parse_args()

    # check Logger value
    numericLogLeved = getattr(logging, args.log.upper(), None)
    if not isinstance(numericLogLeved, int):
        raise ValueError('Invalid log level: %s' % numericLogLeved)

    # Creating an object
    logger: logging.Logger= logging.getLogger("Monitor")
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to log argument
    ch = logging.StreamHandler()
    ch.setLevel(numericLogLeved)
    ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    # create file handlet and set level to debug
    if not os.path.exists('./logs'):
        os.mkdir('./logs')
    logName = r'./logs/server_' + str(int(round(datetime.now().timestamp()))) + '.log'
    fh = logging.FileHandler(logName)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - [%(name)s, %(levelname)s]: %(message)s'))

    # add ch to logger
    logger.addHandler(ch)

    # add fh to logger
    logger.addHandler(fh)

    async def main(ip: str, port: int, maxClients: int) -> None:

        # Create the server class
        server: Server = Server(maxClients)

        # Create the server
        serverObj: asyncio.base_events.Server = await server.create_server(ip, port)

        addrs = ', '.join(str(sock.getsockname()) for sock in serverObj.sockets)
        logger.info(f'Serving on {addrs}')

        async with serverObj:
            await serverObj.serve_forever()

    try:
        asyncio.run(main(args.bind, args.port, args.maxClients))
    except KeyboardInterrupt:
        logger.error("\Server Terminated")
    except OSError as e:
        logger.error("Failed to operate server: " + str(e))
    except Exception as e:
        print("Error: " + str(e))
