import os
import argparse
import six
import txaio
import json
from copy import deepcopy

try:
    import asyncio
except ImportError:
    import trollius as asyncio

from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

# own imports
from au2blendshapes_mb import AUtoBlendShapes  # when using Manuel Bastioni models
#from au2blendshapes_mh import AUtoBlendShapes  # when using FACSHuman models


# process everything that is received
class SubscribeProcessor:
    def __init__(self, log, publish):
        # log: logging from crossbar
        # publish: object to publish message to crossbar's message broker

        self.log = log
        self.publish = publish
        #self.pub_process = PublishProcessor(log, publish)
        self.au_to_blendshapes = AUtoBlendShapes()

    def message_handler(self, facs_json):  # , id_cb, type_cb
        # facs_json: received facs values in JSON format

        print("----------------------------")
        print(type(facs_json))
        # change JSON to Python internal dict
        facs_dict = json.loads(facs_json)
        print(type(facs_dict))
        print("---")
        # pretty printing
        #print(json.dumps(facs_dict, indent=4))  # , indent=4, sort_keys=True

        # change facs to blendshapes
        # TODO if None (should not receive any None prob)
        blend_dict = self.au_to_blendshapes.output_blendshapes(facs_dict['data']['facs'])
        # print(blend_dict)

        # add blend dict under 'data' to received message and remove FACS
        msg_dict = self.structure_dict(facs_dict, blend_dict)

        # publish blendshapes
        # TODO double json.dump
        print(json.dumps(msg_dict, indent=4))
        self.publish('eu.surafusoft.blend', json.dumps(msg_dict))

    # restructure to frame, timestamp, data={head_pose, blendshape}
    def structure_dict(self, facs_dict, blend_dict):
        #   restructure
        # copy whole message except data part
        msg_dict = {k: v for k, v in facs_dict.items() if k is not 'data'}
        # init key 'data' again
        msg_dict['data'] = {}
        # copy 'head_pose' back into data
        msg_dict['data']['head_pose'] = deepcopy(facs_dict['data']['head_pose'])
        msg_dict['data']['blend_shape'] = deepcopy(blend_dict)

        return msg_dict


# client to message broker server
class ClientSession(ApplicationSession):
    """
    Our WAMP session class .. setup register/subscriber/publisher here
    """
    def __init__(self, config):
        ApplicationSession.__init__(self, config)

        # special class to handle subscribe events, put all code in that class
        self.subscribe_processor = SubscribeProcessor(self.log, self.publish)
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
        await self.subscribe(self.subscribe_processor.message_handler, u'eu.surafusoft.facs')

        print('----------------------------')
        self.log.info("subscribed to topic 'facs'")

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
