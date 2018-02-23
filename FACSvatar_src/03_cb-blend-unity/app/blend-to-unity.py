import os
import argparse
import six
import txaio
import json

try:
    import asyncio
except ImportError:
    import trollius as asyncio

from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

# own imports
#from au2blendshapes import AUtoBlendShapes


# process everything that is received
class SubscribeProcessor:
    def __init__(self, log):
        self.log = log

        # test
        self.counter = 0

        # unity connection
        self.writer = None
        self.reader = None

    # just forward json directly to Unity
    async def message_handler(self, blend_json):  # , id_cb, type_cb
        # blend_json: received blend values in JSON format

        print('----------------------------')
        print(type(blend_json))
        print(blend_json)

        await self.tcp_echo_client(blend_json)  # {'welcome': f"Hello World {self.counter}!"}

        self.counter += 1

    # Asynchronous communication with Unity 3D over TCP
    async def tcp_echo_client(self, blend_json):  # , message
        if not self.writer:
            # open connection with Unity 3D
            self.reader, self.writer = await asyncio.open_connection('127.0.0.1', 8052)  # , loop=self.loop  # 0.0.0.0

        # convert JSON to bytes
        blend_bytes = blend_json.encode()
        # send message
        self.writer.write(blend_bytes)

        # await self.writer.drain()  # sometimes gives crashes

        # wait for data from Unity 3D
        data = await self.reader.read(100)
        # we expect data to be JSON formatted
        data_json = json.loads(data.decode())
        print('Received:\n%r' % data_json)

        # TODO close writer
        #await asyncio.sleep(0.05)
        # print('Close the socket')
        # writer.close()


# client to message broker server
class ClientSession(ApplicationSession):
    """
    Our WAMP session class .. setup register/subscriber/publisher here
    """
    def __init__(self, config):
        ApplicationSession.__init__(self, config)

        # special class to handle subscribe events, put all code in that class
        self.subscribe_processor = SubscribeProcessor(self.log)  #  self.publish
        # special class to handle subscribe events, put all code in that class
        #self.publish_processor = PublishProcessor(self.log, self.call, self.publish)

    def onConnect(self):
        self.log.info("Client connected: {klass}", klass=ApplicationSession)
        self.join(self.config.realm, [u'anonymous'])

    def onChallenge(self, challenge):
        self.log.info("Challenge for method {authmethod} received", authmethod=challenge.method)
        raise Exception("We haven't asked for authentication!")

    async def onJoin(self, details):

        self.log.info("Client session joined {details}", details=details)

        self.log.info("Connected:  {details}", details=details)

        self._ident = details.authid
        self._type = u'Python'
        # functions that return results the invoker; similar to server
        #self.responder = Responder(self._ident, self._type)

        self.log.info("Component ID is  {ident}", ident=self._ident)
        self.log.info("Component type is  {type}", type=self._type)

        # SUBSCRIBE: Pass all subscribed info
        await self.subscribe(self.subscribe_processor.message_handler, u'eu.surafusoft.blend')

        print('----------------------------')
        self.log.info("subscribed to topic 'blend'")

    def onLeave(self, details):
        self.log.info("Router session closed ({details})", details=details)
        self.disconnect()

    def onDisconnect(self):
        self.log.info("Router connection closed")
        try:
            asyncio.get_event_loop().stop()
        except:
            pass


if __name__ == '__main__':

    # Crossbar.io connection configuration, if not found, use manual specified
    url = os.environ.get('CBURL', u'ws://localhost:8080/ws')
    # url = u'ws://localhost:9090/ws'
    realm = os.environ.get('CBREALM', u'realm1')

    # parse command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output.')
    parser.add_argument('--url', dest='url', type=six.text_type, default=url, help='The router URL (default: "ws://localhost:8080/ws").')
    parser.add_argument('--realm', dest='realm', type=six.text_type, default=realm, help='The realm to join (default: "realm1").')

    args = parser.parse_args()

    # start logging
    if args.debug:
        txaio.start_logging(level='debug')
    else:
        txaio.start_logging(level='info')

    # any extra info we want to forward to our ClientSession (in self.config.extra)
    extra = {
        u'foobar': u'A custom value'
    }

    # now actually run a WAMP client using our session class ClientSession
    runner = ApplicationRunner(url=args.url, realm=args.realm, extra=extra)
    runner.run(ClientSession)
