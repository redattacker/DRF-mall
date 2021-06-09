import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

#Tornado包括了一个有用的模块（tornado.options）来从命令行中读取设置。我们在这里使用这个模块指定我们的应用监听HTTP请求的端口。
define("port", default=8000, help="run on the given port", type=int)


#这是Tornado的请求处理函数类。当处理一个请求时，Tornado将这个类实例化，并调用与HTTP请求方法所对应的方法
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        greeting = self.get_argument('greeting', 'Hello')
        self.write(greeting + ', friendly user!')

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r"/", IndexHandler)])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()