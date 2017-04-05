import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
   def get(self,url):
      self.redirect("https://%s" % self.request.full_url()[len("http://"):], permanent=True)

if __name__ == "__main__":
   application=tornado.web.Application([
      (r"/(.*)", MainHandler),
   ])
   application.listen(8080)
   tornado.ioloop.IOLoop.current().start()

