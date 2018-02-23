import os
import sys
import argparse
import six
import txaio
import time
import json
import cv2
import glob

try:
    import asyncio
except ImportError:
    import trollius as asyncio

from autobahn.wamp.types import RegisterOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner

# own imports
from openfacefiltercsv import FilterCSV

# global sleep to match video with publisher
global_publish_time = 0.033
global_start_video = False


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
        self.filter_csv = FilterCSV

    async def start_pub(self, file='FE_Stef4_FACS_0.4.0.csv'):
        # global sleep for showing video
        global global_publish_time
        global global_start_video

        self.log.info("Starting publishing")
        # load OpenFace csv as dataframe
        self.df_au = FilterCSV(file).df_au
        print(self.df_au.head())

        # get number of rows in dataframe
        df_au_row_count = self.df_au.shape[0]
        print(df_au_row_count)
        print(type(df_au_row_count))

        # sleep to match video output
        await asyncio.sleep(0.5)

        # get current time to match timestamp when publishing
        timer = time.time()

        # allow video to be played
        global_start_video = True

        # send all rows of data 1 by 1
        # Calculations before sleep, then publish
        for frame_tracker in range(df_au_row_count):
            print("FRAME TRACKER: {}".format(frame_tracker))

            # get AU/other values of 1 frame and transform it to a dict
            msg_dict = self.structure_dict(self.df_au.iloc[frame_tracker])

            # show json contents
            #print(json.dumps(msg_dict, indent=4))

            # # Sleep before sending the messages, so processing time has less influence
            # wait until timer time matches timestamp
            time_sleep = msg_dict['timestamp'] - (time.time() - timer)
            print("waiting {} seconds before sending next FACS".format(time_sleep))

            # set time new frame should be shown
            global_publish_time = time.time() + time_sleep + 0.0025

            # don't sleep negative time
            if time_sleep >= 0:
                # currently can send about 3000 fps
                await asyncio.sleep(time_sleep)  # time_sleep (~0.031)

            # only publish message if we have data
            if msg_dict['data']:
                # publish FACS + gaze to topic; convert to JSON
                await self.publishing(json.dumps(msg_dict))
            else:
                self.log.info("Tracking confidence too low; not publishing message")

    async def publishing(self, msg):
        # cast datarow into JSON format
        #print(type(datarow.to_json()))

        # json.dumps(msg).encode()
        self.publish('eu.surafusoft.facs', msg)  # .to_json() # , self._ident, self._type

    # restructure json message to frame, timestamp, data={head_pose, AU} (send None if confidence <0.6)
    def structure_dict(self, datarow):
        msg_dict = datarow.to_dict()

        # restructure
        msg_dict_re = {}
        msg_dict_re['frame'] = msg_dict['frame']
        msg_dict_re['timestamp'] = msg_dict['timestamp']

        # add data if enough confidence in tracking
        if msg_dict['confidence'] >= 0.6:
            # TODO split FACS and gaze (when data aggregation problem is solved)

            msg_dict_re['data'] = {}  # 'head_pose': {}, 'FACS': {}
            # msg_dict.startswith(query)  # .items()
            # copy dict elements when key starts with 'pose_R'
            msg_dict_re['data']['head_pose'] = {k: v for k, v in msg_dict.items() if k.startswith('pose_R')}
            # copy dict elements when key starts with 'pose_R'; assumes we only have AU**_r
            msg_dict_re['data']['facs'] = {k: v for k, v in msg_dict.items() if k.startswith('AU')}

        # confidence too low --> return None
        else:
            msg_dict_re['data'] = None

        return msg_dict_re


# TODO put video in subscriber node to make it independent; use 1 time function to set right video
# play Open Face recorded video in sync with avatar
class ViewVideo:
    def __init__(self, fn):
        # fn: file name of video

        self.fn = fn
        # stop frame reading when buffer is full
        #self.stopped = False

        loop = asyncio.get_event_loop()
        # no need for run_until_complete(), because event loop doesn't have to be started twice
        asyncio.ensure_future(self.open_video(loop))

    async def open_video(self, loop):
        # loop: asyncio asynchronous event tracker

        vid = cv2.VideoCapture(self.fn)
        # Check if camera opened successfully
        if not vid.isOpened():
            print("Error opening video stream or file")
        else:
            # create new asyncio event loop and pass to new thread
            new_loop = asyncio.new_event_loop()
            # open new thread to play video to not block the main thread
            await loop.run_in_executor(None, self.play_video, new_loop, vid)  # new_loop,

        # if something has to be returned from new thread:
        # https://stackoverflow.com/questions/32059732/send-asyncio-tasks-to-loop-running-in-other-thread

    # new thread; producer / consumer for buffering / showing video
    def play_video(self, loop, vid):
        # get frame rate
        fps = vid.get(cv2.CAP_PROP_FPS)
        print("Playing Open Face video with fps: {}".format(fps))

        # give time for publisher to get ready
        #time.sleep(.11)

        print("\nnew loop: {}\n".format(loop))
        # set new event loop
        asyncio.set_event_loop(loop)
        # get new set event loop
        thread_loop = asyncio.get_event_loop()  # loop

        print("set loop: {}\n".format(thread_loop))

        # set video frame queue
        queue = asyncio.Queue(maxsize=120, loop=thread_loop)
        frame_enqueue_coro = self.frame_enqueue(queue, vid)
        frame_show_coro = self.frame_show(queue, fps)
        print(frame_enqueue_coro)
        print(frame_show_coro)
        thread_loop.run_until_complete(asyncio.gather(frame_enqueue_coro, frame_show_coro))
        thread_loop.close()

    # puts video frames into a queue
    async def frame_enqueue(self, queue, vid):
        while vid.isOpened():
            ret, frame = vid.read()

            # if we still have frames
            if ret:
                # due to maxsize of queue, it should wait with putting in new automatically
                await queue.put(frame)
                #await asyncio.sleep(0.01)
            else:
                await queue.put(None)
                vid.release()

    # display frames from queue
    async def frame_show(self, queue, fps):
        while True:
            # wait until FACS publisher is ready
            if global_start_video:
                frame = await queue.get()
                #print("frame: {}".format(frame))
                # display frames as long as we don't receive None
                if frame is not None:
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    cv2.imshow('frame', frame)
                    # await asyncio.sleep((1/fps)-0.0062)
                    # await asyncio.sleep(global_sleep-0.01)
                    time_sleep = global_publish_time - time.time()
                    if time_sleep >= 0:
                        await asyncio.sleep(time_sleep)
                else:
                    cv2.destroyAllWindows()
                    break

            # wait a bit before checking if publisher is ready
            else:
                await asyncio.sleep(0.02)


# goes through 'openface' folder to find latest .csv
class CrawlerCSV:
    # return latest .csv
    def search(self, folder='openface'):
        csv_list = sorted(glob.glob(os.path.join(folder, '*.csv')))

        # # get latest .csv
        # 2nd or higher run
        if csv_list[-1][-10:-4] == "_clean":
            # remove _clean and .csv
            latest_csv = csv_list[-1][:-10]
        else:
            # remove .csv
            latest_csv = csv_list[-1][:-4]

        print("Reading data from: {}".format(latest_csv))

        # return newest .csv file without extension
        return latest_csv


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
        # self.responder = Responder(self._ident, self._type)

        self.log.info("Component ID is  {ident}", ident=self._ident)
        self.log.info("Component type is  {type}", type=self._type)

        # ask if we use demo video or new recorded one
        if input("Use demo video? y/n: ").lower() == "y":
            file = "Takimoto_demo"
        else:
            file = CrawlerCSV().search()

        # play Open Face video matching .csv file
        #ViewVideo(file+'.avi')

        # read csv and publish FACS
        await self.publish_processor.start_pub(file+'.csv')

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
