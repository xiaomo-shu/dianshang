from socketserver import BaseRequestHandler, TCPServer, ThreadingTCPServer


class EchoHandler(BaseRequestHandler):

    def handle(self):
        print("Got connection from", self.client_address)
        while True:
            msg = self.request.recv(8192)
            if not msg:
                break
            print(msg)
            self.request.send(msg)


if __name__ == '__main__':
    serv = ThreadingTCPServer(('', 20000), EchoHandler)
    serv.serve_forever()
