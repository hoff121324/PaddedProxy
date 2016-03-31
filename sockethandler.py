import tornado.web
import tornado.websocket
import struct

from proxy import *

class ProxySocketHandler(tornado.websocket.WebSocketHandler):
	def open(self, *args):
		self.proxy = Proxy(self)

	def on_message(self, message):
		if len(message) != INCOMING_MESSAGE_SIZE:
			print("Bad message size: " + len(message))
		salt = message[0:SALT_SIZE] #unused
		data_size = struct.unpack(">H", message[SALT_SIZE:(SALT_SIZE+LENGTH_SIZE)])[0]

		if data_size == 0:
			print("no data");
			return;

		if data_size > (INCOMING_MESSAGE_SIZE - (SALT_SIZE + LENGTH_SIZE)):
			print("Bad data size: " + data_size)
		data = message[(SALT_SIZE+LENGTH_SIZE):(SALT_SIZE+LENGTH_SIZE + data_size)]
		self.proxy.parse_data(data)

	def on_close(self):
		return

