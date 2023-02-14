"""
`client` package is used to represent a client entity
"""
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
import common.utils as util

@dataclass
class Connection:
    """
    Class used to save a connection between the client and the server
    """
    reader: asyncio.streams.StreamReader
    writer: asyncio.streams.StreamWriter
    ip: str
    port: int

@dataclass
class ClientValues:
    """
    Class used to store the associated values of each client
    """
    nick: str
    ip: str
    port: int 

class Client:
    """
    Class that enables the client
    """
    def __init__(self, nick: str) -> None:

        self.clients: list[ClientValues] = [] 
        self.connection: Connection | None = None
        self.nick: str = nick
        self.ip: str = ""
        self.port: int = 0
        

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
    

    async def process_message(self, msg: dict) -> None:
        """
        Function to process a message received from the server
        Args:
            - msg: Received message
        """
        try:
            util.check_dict_fields(msg, ['option'])

            # {"option": "join", "nick": nick, "ip": ip, "port": port} -> Join message
            if msg["option"] == "join":
                util.check_dict_fields(msg, ['nick', 'ip', 'port'])
                if [client for client in self.clients if client.nick == msg['nick']] == []:
                    self.clients.append(ClientValues(msg["nick"], msg["ip"], msg["port"]))
                    logger.info(f"Client {msg['nick']} with {msg['ip']}:{msg['port']} has entered")

            # {"option": "message", "message": message, "nick": nick} -> Message message
            elif msg["option"] == "message":
                util.check_dict_fields(msg, ['message', 'nick'])
                if [client for client in self.clients if client.nick == msg['nick']] != []:
                    logger.info(f"Client {msg['nick']}-> {msg['message']}")
                else:
                    logger.debug(f"Client not registered, message: {msg}")

            # {"option": "disconnect", "nick": nick} -> Disconnect message
            elif msg["option"] == "disconnect":
                util.check_dict_fields(msg, ['nick'])
                if [client for client in self.clients if client.nick == msg['nick']] != []:     
                    self.clients.remove([client for client in self.clients if client == msg["nick"]][0])
                    logger.info(f"Client {msg['nick']} with {msg['ip']}:{msg['port']} has left")
                else:
                    logger.debug(f"Client not recognized, message: {msg}")

            else:
                logger.debug("Unknow message option: " + str(msg['option']))
        except ValueError as e:
            logger.debug("Message not in the correct type")
            return
            

    async def receive_client(self) -> None:
        """
        Main Function used to just handle the reception of data from the    
            server
        """
        ipRaw: tuple= self.connection.writer.get_extra_info('peername')
        self.ip: str = ipRaw[0]
        self.port: int = ipRaw[1]
        joinMsg: dict =  {
                        "option": "join", 
                        "nick": self.nick, 
                        "ip": self.ip, 
                        "port": self.port
                        }
        await comms.send_dict(self.connection.writer, joinMsg)

        while True:
            msg: dict = await comms.recv_dict(self.connection.reader)
            
            if msg == None: break

            logger.debug("Received: " + str(msg))

            await self.process_message(msg)


            #print('Close the connection')
            #self.connection.writer.close()

    async def send_client(self) -> None:
        """
        Main Function used to just handle the sending of data to the    
            server
        """
        while True:
            await asyncio.sleep(0.5)
            input_str: str = await aioconsole.ainput("MSG-> ")
            msg: dict = {
                        "option": "message", 
                        "message": input_str, 
                        "nick": self.nick
                        }
            logger.debug("sending: " + str(msg))
            await comms.send_dict(self.connection.writer, msg)

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", help="IP address to bind to", default="127.0.0.1")
    parser.add_argument("--port", help="TCP port", type=int, default=8005)
    parser.add_argument("--maxClients", help="Maximum number of clients", 
                            type=int, default=5)
    parser.add_argument("--log", help="Log threshold (default=INFO)", 
                            type=str, default='INFO')
    parser.add_argument("--nick", help="Nick for the player (Max 20 characters)", 
                    type=str, default="player")
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
    logName = (r'./logs/client_' + args.nick + "_" 
                + str(int(round(datetime.now().timestamp()))) + '.log')
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
    except Exception as e:
        print("Error: " + str(e))
