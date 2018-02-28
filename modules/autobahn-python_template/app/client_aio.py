import os
import argparse
import six
import txaio

try:
    import asyncio
except ImportError:
    import trollius as asyncio

from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


# process everything that is received
class SubscribeProcessor:
    def __init__(self, log):
        self.log = log

    def message_handler(self, counter, id, type):
        print('----------------------------')
        self.log.info("'oncounter' event, counter value: {counter}", counter=counter)
        self.log.info("from component {id} ({type})", id=id, type=type)


# publish what this node contributes
class PublishProcessor:
    def __init__(self, log, call, publish):  # client
        # self.client = client
        self.log = log
        self.call = call
        self.publish = publish
        self.x = 0
        self.counter = -1

    async def publishing(self):
        self.counter += 1

        # CALL
        # try:
        res = await self.call('com.example.add2', self.x, 3)
        print('----------------------------')
        self.log.info("add2 result: {result}",
                      result=res[0])
        self.log.info("from component {id} ({type})", id=res[1], type=res[2])
        self.x += 1
        # except ApplicationError as e:
        #     ## ignore errors due to the frontend not yet having
        #     ## registered the procedure we would like to call
        #     if e.error != 'wamp.error.no_such_procedure':
        #         raise e

        print('----------------------------')
        self.log.info("published to 'oncounter' with counter {counter}",
                      counter=self.counter)

        # return self.counter
        self.publish('com.example.oncounter', self.counter)  # , self._ident, self._type


# class with registered functions, that returns result directly to invoker
class Responder:
    def __init__(self, id, type):
        self._ident = id
        self._type = type

    def add2(self, a, b):
        print('----------------------------')
        print("add2 called on {}".format(self._ident))
        return [a + b, self._ident, self._type]
        # return a+b


# client to message broker server
class ClientSession(ApplicationSession):
    """
    Our WAMP session class .. setup register/subscriber/publisher here
    """
    def __init__(self, config):
        ApplicationSession.__init__(self, config)

        # special class to handle subscribe events, put all code in that class
        self.subscribe_processor = SubscribeProcessor(self.log)
        # special class to handle subscribe events, put all code in that class
        self.publish_processor = PublishProcessor(self.log, self.call, self.publish)

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
        self.responder = Responder(self._ident, self._type)

        self.log.info("Component ID is  {ident}", ident=self._ident)
        self.log.info("Component type is  {type}", type=self._type)

        # def add2(a, b):
        #     print('----------------------------')
        #     print("add2 called on {}".format(self._ident))
        #     return [ a + b, self._ident, self._type]

        # REGISTER; creates a topic
        # invoke options: u'single', u'first', u'last', u'roundrobin' (equal time every node), u'random'
        await self.register(self.responder.add2, u'com.example.add2', options=RegisterOptions(invoke=u'roundrobin'))
        print('----------------------------')
        print('procedure registered: com.myexample.add2')


        # # SUBSCRIBE
        # def oncounter(counter, id, type):
        #     print('----------------------------')
        #     self.log.info("'oncounter' event, counter value: {counter}", counter=counter)
        #     self.log.info("from component {id} ({type})", id=id, type=type)

        # await self.subscribe(oncounter, u'com.example.oncounter')
        # Pass all subscribed info
        await self.subscribe(self.subscribe_processor.message_handler, u'com.example.oncounter')

        print('----------------------------')
        self.log.info("subscribed to topic 'oncounter'")

        # keep calling publisher functions
        while True:
            #
            # # CALL
            # try:
            #     res = await self.call('com.example.add2', x, 3)
            #     print('----------------------------')
            #     self.log.info("add2 result: {result}",
            #     result=res[0])
            #     self.log.info("from component {id} ({type})", id=res[1], type=res[2])
            #     x += 1
            # except ApplicationError as e:
            #     ## ignore errors due to the frontend not yet having
            #     ## registered the procedure we would like to call
            #     if e.error != 'wamp.error.no_such_procedure':
            #         raise e

            try:
                await self.publish_processor.publishing()

            except ApplicationError as e:
                ## ignore errors due to the frontend not yet having
                ## registered the procedure we would like to call
                if e.error != 'wamp.error.no_such_procedure':
                    raise e

            # PUBLISH
            # self.publish('com.example.oncounter', counter, self._ident, self._type)
            # message = self.publish_processor.publishing()
            # self.publish('com.example.oncounter', message, self._ident, self._type)

            await asyncio.sleep(2)

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
