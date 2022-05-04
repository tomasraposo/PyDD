from tornado import gen, web
from tornado.process import Subprocess
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from tornado.websocket import WebSocketHandler
import json

# adapted from https://stackoverflow.com/questions/41431882/live-stream-stdout-and-stdin-with-websocket
class WSHandler(WebSocketHandler):
    def check_origin(self, origin):
        return True
    
    def open(self):
        print("WebSocket opened")
        self.app = Subprocess(['/usr/bin/python3.8', '-u', self.pydd, self.args], 
                              stdout=Subprocess.STREAM, 
                              stdin=Subprocess.STREAM)
        IOLoop.current().spawn_callback(self.stream_output)

    def on_message(self, message):
        print("receiving ", message)
        message += "\n"
        self.app.stdin.write(message.encode('utf-8'))
        
    def on_close(self):
        print("WebSocket closed")

    @gen.coroutine
    def stream_output(self):
        try:
            while True:
                line = yield self.app.stdout.read_bytes(8092, partial=True)
                line = line.decode("utf-8")
                line = line.replace("\n", "")
                print("line ", line)
                self.write_message(line)
        except StreamClosedError:
            pass

def run_server(address='localhost', port=8001):
    application = web.Application([
            (r"/", WSHandler),
        ],
        debug=True,
    )

    application.listen(port, address)
    print('Server listening at http://localhost:8001/')
    IOLoop.current().start()
