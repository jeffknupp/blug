"""HTTP server and utilities"""

import os
import io
import os.path
import resource
import select
import socketserver
import socket
from http import server
import datetime

RUSAGE = """0	{}	time in user mode (float)
{}	time in system mode (float)
{}	maximum resident set size
{}	shared memory size
{}	unshared memory size
{}	unshared stack size
{}	page faults not requiring I/O
{}	page faults requiring I/O
{}	number of swap outs
{}	block input operations
{}	block output operations
{}	messages sent
{}	messages received
{}	signals received
{}	voluntary context switches
{}	involuntary context switches"""

EOL1 = b'\r\n'
EOL2 = b'\n\n'


class EPollMixin:
    """Mixin for socketserver.BaseServer to use epoll instead of select"""

    def server_activate(self):
        """Increase the request_queue_size and set non-blocking"""
        self.connections = dict()
        self.requests = dict()
        self.responses = dict()
        self.addresses = dict()
        self.status = dict()
        self.socket.listen(75)
        self.socket.settimeout(0.0)
        self.epoll = select.epoll()
        self.epoll.register(self.fileno(), select.EPOLLIN)

    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        self.RequestHandlerClass(request, client_address, self, client_address)

    def handle_request(self):
        """Handle one request, possibly blocking. Does NOT respect timeout.

        To avoid the overhead of select with many client connections,
        use epoll (and later do the same for kqpoll)"""
        events = self.epoll.poll()
        for fd, event in events:
            if fd == self.fileno():
                connection, address = self.socket.accept()
                connection.setblocking(0)
                self.epoll.register(connection.fileno(), select.EPOLLIN)
                self.connections[connection.fileno()] = connection
                self.requests[connection.fileno()] = bytearray(65536)
                self.responses[connection.fileno()] = io.BytesIO()
                self.addresses[connection.fileno()] = address
                self.status[connection.fileno()] = True
            elif event & select.EPOLLIN:
                self.connections[fd].recv_into(self.requests[fd], 1024)
                if EOL1 in self.requests[fd] or EOL2 in self.requests[fd]:
                    self.process_request(self.requests[fd], fd)
                    if self.status[fd]:
                        self.epoll.modify(fd, select.EPOLLOUT)
            elif event & select.EPOLLOUT:
                byteswritten = self.connections[fd].send(self.responses[fd].getvalue())
                self.responses[fd] = self.responses[fd].getbuffer()[byteswritten:]
                if len(self.responses[fd]) == 0:
                    self.epoll.modify(fd, select.EPOLLIN)
            elif event & select.EPOLLHUP:
                self.epoll.unregister(fd)
                self.connections[fd].close()
                del self.connections[fd]

    def close_connection(self, fd):
        print (fd, 'closing')
        self.epoll.modify(fd, 0)
        self.status[fd] = False
        self.connections[fd].close()

    def shutdown_request(self, request):
        pass


class EPollRequestHandlerMixin():
    def setup(self):
        self.rfile = io.BytesIO(self.server.requests[self.fd])
        self.wfile = self.server.responses[self.fd]

    def __init__(self, request, client_address, server, fd):
        self.request = request
        self.server = server
        self.connection = self.server.connections[fd]
        self.client_address = self.server.addresses[fd]
        self.fd = fd
        self.setup()
        self.protocol_version = 'HTTP/1.1'
        try:
            self.handle()
        finally:
            self.finish()

    def finish(self):
        if self.close_connection:
            self.server.close_connection(self.fd)
            self.rfile.close()

    #def log_request(self, code='-', size='-'):
    #    pass


class EPollTCPServer(EPollMixin, socketserver.TCPServer):
    pass


class EPollRequestHandler(EPollRequestHandlerMixin, server.SimpleHTTPRequestHandler):

    def do_GET(self):
        path = self.translate_path(self.path)

        if os.path.isdir(path):
            self.path = os.path.join(self.path, 'index.html')

        self.path = self.path.split('?', 1)[0]
        self.path = self.path.split('#', 1)[0]
        print (path, self.path)
        cType = self.guess_type(self.path)
        file_buffer = self.server.file_cache.get_resource(self.path)
        if not file_buffer:
            self.send_error(404, "File not found")
            return None

        #TODO: Cache header along with file and send directly
        self.send_response(200)
        self.send_header("Content-type", cType)
        self.send_header("Content-Length", len(file_buffer))
        self.send_header("Last-Modified", self.date_time_string())
        self.end_headers()
        self.wfile.write(file_buffer)


class BlugHttpServer(EPollTCPServer):

    def __init__(self, root, *args, **kwargs):
        self.file_cache = FileCache(root)
        print (self.file_cache)
        EPollTCPServer.__init__(self, *args, **kwargs)

    """epoll based http server"""
    def server_bind(self):
        """Override server_bind to store the server name."""
        socketserver.TCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port


def start_server(host='localhost', port=8000,
        handler_class=server.SimpleHTTPRequestHandler):
    address = (host, port)
    http_server = BlugHttpServer(address, handler_class)
    http_server.serve_forever()


class FileCache():
    """An in-memory cache of static files"""

    FILE_TYPES = ['.html', '.js', '.css', '.png']

    def __init__(self, base, debug=0):
        self.base = os.path.normpath(base)
        self.cache = dict()
        self._debug = debug
        self.build_cache(self.base)

    def build_cache(self, base_dir, current_dir=None):
        if not current_dir:
            current_dir = os.path.relpath(base_dir)
        for name in os.listdir(current_dir):
            name = os.path.join(current_dir, name)
            if not os.path.splitext(name)[1] in self.FILE_TYPES:
                if os.path.isdir(name):
                    self.build_cache(base_dir, name)
            else:
                with open(name, 'rb') as input_file:
                    self.cache[name[1:]] = bytes(input_file.read())

    def get_resource(self, path):
        if path in self.cache:
            return memoryview(self.cache[path])
        return None

    def _get_cache_stats(self):
        """Returns statistics of the current cache"""
        stat_list = list()
        for filename, file_buffer in self.cache.items():
            path, name = os.path.split(filename)
            stat_list.append(('{name}: {size} B ({path}'.format(
                name=name,
                path=path,
                size=len(self.cache[filename]))))
        return stat_list

    def __str__(self):
        return '\n'.join(self._get_cache_stats())


def print_usage_stats(rusage_struct):
    return  RUSAGE.format(rusage_struct.ru_utime, rusage_struct.ru_stime,
    rusage_struct.ru_maxrss, rusage_struct.ru_ixrss, rusage_struct.ru_idrss,
    rusage_struct.ru_isrss, rusage_struct.ru_minflt, rusage_struct.ru_majflt,
    rusage_struct.ru_nswap, rusage_struct.ru_inblock, rusage_struct.ru_oublock,
    rusage_struct.ru_msgsnd, rusage_struct.ru_msgrcv,
    rusage_struct.ru_nsignals, rusage_struct.ru_nvcsw,
    rusage_struct.ru_nivcsw)

if __name__ == '__main__':
    start_server()
    #cache = FileCache('/home/jeff/code/blug/generated/', 1)
    #print (cache)
    #usage = resource.getrusage(resource.RUSAGE_SELF)
    #print (print_usage_stats(usage))
