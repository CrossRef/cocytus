import socketIO_client
from celery import Celery
from tasks import process_change


import crossref_push
import socketIO_client
import time
import signal
import logging
from config import HEARTBEAT_INTERVAL

logging.basicConfig(filename='logs/input.log', level=logging.INFO, format='%(asctime)s %(message)s')
logging.info('cocytus-input launched')

alarm_interval = HEARTBEAT_INTERVAL

celery_service =  Celery('cocytus-tasks', broker='redis://localhost')

def alarm_handle(signal_number, current_stack_frame):
  process_change.delay(crossref_push.heartbeat)
  logging.info('enqueued heartbeat')
  signal.alarm(alarm_interval)

signal.signal(signal.SIGALRM, alarm_handle)
signal.siginterrupt(signal.SIGALRM, False)
signal.alarm(alarm_interval)

class AllWikiNamespace(socketIO_client.BaseNamespace):

  def on_change(self, change):
    try:
      process_change.delay(change)
    except Exception as e:
      print("Exception" + str(e))
      logging.error(e.message)

  def on_connect(self):
    self.emit(u"subscribe", u"*")

import socketIO_client

socketIO = socketIO_client.SocketIO('stream.wikimedia.org', 80)
socketIO.define(AllWikiNamespace, '/rc')

socketIO.wait()