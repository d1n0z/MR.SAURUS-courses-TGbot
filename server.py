import json
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from data import db
from urllib import parse


class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        data = parse.parse_qs(parse.urlparse(self.path).query)
        if self.client_address[0] == '121.127.46.166':
            db.NicepayPayments.create(
                result=data['result'][0],
                payment_id=data['payment_id'][0],
                merchant_id=data['merchant_id'][0],
                order_id=data['order_id'][0],
                amount=data['amount'][0],
                amount_currency=data['amount_currency'][0],
                profit=data['profit'][0],
                profit_currency=data['profit_currency'][0],
                method=data['method'][0],
                hash=data['hash'][0]
            ).save()
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), post_data)

        self._set_response()
        self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=S, port=443):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.socket = ssl.wrap_socket(httpd.socket, keyfile='./privkey.pem', certfile='./fullchain.pem')
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')
