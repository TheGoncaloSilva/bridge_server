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

@dataclass
class ClientValues:
    writer: asyncio.streams.StreamWriter
    reader: asyncio.streams.StreamReader

@dataclass
class ServerValues:
    server: asyncio.base_events.Server
    ip: str
    port: int

class Server:

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
    

    async def handle_client(self, reader : asyncio.streams.StreamReader, writer : asyncio.streams.StreamWriter) -> None:
        while True:
            msg = await comms.recv_dict(reader)

            if msg == None: break

            addr = writer.get_extra_info('peername')

            print(f"Received {msg!r} from {addr!r}")

            response: dict =  {"msg": "Hello from server"}
            print(f"Send: {response!r}")
            await comms.send_dict(writer, response)

            #print("Close the connection")
            #writer.close()
            #await writer.wait_closed()




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
    #except ValueError and TypeError as e:
    #    print("Error: " + str(e))
