import tornado.ioloop
import tornado.web

if __name__ == "__main__":
   application=make_app()
   application.listen(80, address='127.0.0.1')
   tornado.ioloop.IOLoop.current().start()

