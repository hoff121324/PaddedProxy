import os
import tornado.ioloop
import tornado.web

from sockethandler import *

class IndexHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	def get(request):
		request.render("index.html")

settings = {
	"debug" : True
}

app = tornado.web.Application([
	(r"/socket", ProxySocketHandler),
	(r"/", IndexHandler),
	(r"/static/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "static")})
], settings)
app.listen(8888)
tornado.ioloop.IOLoop.instance().start()

