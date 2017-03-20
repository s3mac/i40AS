import sys
import zmq
import logging


class broker(object):


    def __init__(self, config):

        self.context = zmq.Context()
        self.config = config
        logging.basicConfig(format='%(asctime)s %(message)s', filename='log/control.log', level=logging.INFO)

        self.url_HTTPIN = self.config['HTTPIN']['url']
        self.socket_HTTPIN = self.context.socket(zmq.ROUTER)
        self.config['HTTPIN']['socket'] = self.socket_HTTPIN
        self.socket_HTTPIN.bind(self.url_HTTPIN)


        for key in self.config:
            if key != 'HTTPIN':
                exec('self.url_' + key + '=' + 'self.config[key][\'url\']')
                exec('self.socket_' + key + '=' + 'self.context.socket(zmq.DEALER)')
                exec('self.config[key][\'socket\']' + '=' + 'self.socket_' + key)
                exec('self.socket_' + key + '.bind' + '(self.url_' + key + ')' )


        self.poller = zmq.Poller()
        for key in config:
            exec('self.poller.register(self.socket_' + key + ', zmq.POLLIN)')


        for key in self.config:
            self.sysout('established socket', meta=self.config[key])


    def mediate(self):
        count = 0
        while True:
            try:
                self.sysout('completed loop', meta= count)
                sockets = dict(self.poller.poll())

                for key in self.config:

                    if sockets.get(self.config[key]['socket']) == zmq.POLLIN:

                        MESSAGE = self.config[key]['socket'].recv_multipart()
                        self.sysout('received message', current_socket=self.config[key]['socket'], meta = MESSAGE)

                        TO = MESSAGE[-3]

                        for key in self.config:
                            if TO == self.config[key]['identity']:

                                self.config[key]['socket'].send_multipart(MESSAGE)
                                self.sysout('send message', current_socket=self.config[key]['socket'], meta = MESSAGE)
                count += 1

            except KeyboardInterrupt:
                break


    def sysout(self, action, current_socket=False, meta=False):

        sys.stdout.write('\n')
        sys.stdout.write('<> control   #')
        sys.stdout.write(str(action))
        if current_socket:
            sys.stdout.write('\n')
            sys.stdout.write('[')
            sys.stdout.write(str(current_socket))
            sys.stdout.write(']')
        sys.stdout.write('\n')

        if meta:

            sys.stdout.write(str(meta))
            sys.stdout.write('\n')

        sys.stdout.write('</>')
        sys.stdout.write('\n')
        sys.stdout.flush()


        logging.info('\n<> control   #{}\n   [{}]\n   {}\n</>'.format(str(action), str(current_socket) if current_socket else '', str(meta) if meta else ''))


    def destroy(self):
        self.socket.close()
        self.context.destroy()
