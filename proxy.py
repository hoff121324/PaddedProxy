import tornado.websocket
import tornado.ioloop
#import tornado.httpclient
from tornado.httpclient import AsyncHTTPClient
import json
import time
import datetime
import Queue
import struct
import random
import string

INCOMING_MESSAGE_SIZE = 256
OUTGOING_MESSAGE_SIZE = 1024
SALT_SIZE = 16
LENGTH_SIZE = 2

class Proxy:
	def __init__(self, client, interval=5000):
		self.client = client
		self.interval = interval
		self.data_queue = Queue.Queue()
		self.current_progress = 0
		self.tick_timeout = None
		tornado.ioloop.IOLoop.instance().add_callback(self.tick)

	#must be called on the main thread
	#sends one packet of size OUTGOING_MESSAGE_SIZE every fixed interval
	def tick(self):
		if self.tick_timeout is not None:
			tornado.ioloop.IOLoop.instance().remove_timeout(self.tick_timeout)
		print("tick")

		salt = self.get_salt()
		data_str = self.get_data_str();
		data_len = struct.pack(">H", len(data_str))
		message_head = salt + data_len + data_str
		padding = self.get_padding(OUTGOING_MESSAGE_SIZE - len(message_head))
		self.client.write_message(message_head + padding);
		delay = datetime.timedelta(seconds=(self.interval/1000.0))
		tornado.ioloop.IOLoop.instance().add_timeout(delay, self.tick)

	def get_data_str(self):
		if self.data_queue.empty():
			return ""
		data = self.data_queue.queue[0]
		max_bytes = (OUTGOING_MESSAGE_SIZE - (SALT_SIZE + LENGTH_SIZE))

		if len(data) - self.current_progress <= max_bytes:
			data_str = data[self.current_progress:]
			self.data_queue.get() #pops element out of queue
			self.current_progress = 0
			return data_str
		else:
			data_str = data[self.current_progress:(max_bytes + self.current_progress)]
			self.current_progress += max_bytes
			return data_str

	#Parse data sent by the client
	def parse_data(self, data):
		try:
			requests = json.loads(data);
		except ValueError, e:
			print("bad json data: " + str(e))

		for request in requests:
			if request["type"] == "fetch":
				hclient = AsyncHTTPClient()
				try:
					hclient.fetch(request["url"], self.parse_response)
					#print("remote response: " + response)
				except Exception as e:
					print("Error: " + str(e))
				hclient.close()
			elif request["type"] == "flush":
				self.flush()
			else:
				print("Bad request type: " + request["type"])

	def parse_response(self, response):
		if response.error:
			print("Error: " + str(response.error))
		else:
			print("Response: " + response.body)
			url_len = struct.pack("B", len(response.request.url))
			data_len = struct.pack(">I", len(response.body))

			#TODO: python automatically tries to convert to ascii, which is unwanted
			#if no clean solution is possible, using an array of bytes may be necessary
			full_str = url_len + response.request.url + data_len + response.body
			#print(response.body)
			self.data_queue.put(full_str)

	def flush(self):
		#TODO
		return

	#http://pythontips.com/2013/07/28/generating-a-random-string/
	def get_salt(self):
		return ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(SALT_SIZE)])

	def get_padding(self, length):
		return "Q" * length;

