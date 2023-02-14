import asyncio
import argparse
import os
import sys
import logging
import aioconsole
from attr import dataclass
from datetime import datetime

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
class Connection:
    reader: asyncio.streams.StreamReader
    writer: asyncio.streams.StreamWriter
    ip: str
    port: int

@dataclass
class ClientValues:
    nick: str
    ip: str
    port: int 

class Client:

    def __init__(self, nick: str) -> None:

        self.clients: list[ClientValues] = [] 
        self.connection: Connection | None = None
        self.nick = nick
        

    async def connect_client(self, ip: str, port: int) -> tuple:
        """
        Function that uses class values to Connect a client with the 
            designated Ip address and Port
        Args:
            - ip: Ip address of the Server
            - port: Port of the Server to operate on
        Returns:
            - A tupple object with the asyncio.streams.StreamReader
            and asyncio.streams.StreamWriter
        Raises:
            - ValueError: if Client was already established
            - TypeError: if supplied  attributes are not of correct type  
            - OSError: if connection wasn't established (handled by 
            asyncio.open_connection function)
        """
        if self.connection != None: raise ValueError(f"Client already initialized")

        if not isinstance(ip, str) or not isinstance(port, int):
            raise TypeError("Wrong usage. Use (str, int) types")
        
        reader, writer = await asyncio.open_connection(ip, port)

        self.connection = Connection(reader, writer, ip, port)

        return (reader, writer)


    async def receive_client(self) -> None:
        while True:
            msg: dict = await comms.recv_dict(self.connection.reader)
            
            if msg == None: break
            logger.info("Received: " + str(msg))

            #print('Close the connection')
            #self.connection.writer.close()

    async def send_client(self) -> None:

        while True:
            await asyncio.sleep(0.5)
            input_str: str = await aioconsole.ainput("MSG-> ")
            msg: dict = {"msg": input_str}
            await comms.send_dict(self.connection.writer, msg)

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", help="IP address to bind to", default="127.0.0.1")
    parser.add_argument("--port", help="TCP port", type=int, default=8005)
    parser.add_argument("--maxClients", help="Maximum number of clients", type=int, default=5)
    parser.add_argument("--log", help="Log threshold (default=INFO)", type=str, default='INFO')
    parser.add_argument("--nick", help="Nick for the player (Max 20 characters)", type=str, default="player")
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
    logName = r'./logs/client_' + args.nick + "_" + str(int(round(datetime.now().timestamp()))) + '.log'
    fh = logging.FileHandler(logName)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - [%(name)s, %(levelname)s]: %(message)s'))

    # add ch to logger
    logger.addHandler(ch)

    # add fh to logger
    logger.addHandler(fh)

    async def main(ip: str, port: int, nick: str) -> None:

        # Check and resize caller nick (max characters of 20)
        if len(nick) > 20:
            nick = nick[:20]

        # Create the caller class
        client: Client = Client(nick)

        # Connect the caller to the playing_area (server)
        await client.connect_client(ip, port)

        logger.info(f'Listenning on {ip}:{port}')

        t1 = loop.create_task(client.receive_client())
        t2 = loop.create_task(client.send_client())
        await asyncio.wait([t1, t2])

    try:
        if sys.version_info < (3, 10):
            loop = asyncio.get_event_loop()
        else:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()

        loop.run_until_complete(main(args.bind, args.port, args.nick))
        loop.close()
    except KeyboardInterrupt:
        logger.error("\Client Terminated")
    except OSError as e:
        logger.error("No Connection to Server: " + str(e))
    #except ValueError and TypeError as e:
    #    print("Error: " + str(e))
