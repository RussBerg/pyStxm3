from example import MultiplyBy

from pizco import Server

server = Server(MultiplyBy(2), 'tcp://127.0.0.1:8000')
server.serve_forever()

