"""HTTP server and utilities"""

import os
from http import server
import resource
import datetime
import time
import gzip
import socketserver
import logging
import logging.handlers

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

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
file_logger = logging.handlers.RotatingFileHandler('blug.log', maxBytes=100000000, backupCount=5)
file_logger.setLevel(logging.INFO)
file_logger.setFormatter(formatter)
logger.addHandler(file_logger)


class FileCacheRequestHandler(server.SimpleHTTPRequestHandler):
    """Request handler that serves cached versions of static files"""

    server_version = 'Blug/1.0'
    expire_time = datetime.datetime.now() + datetime.timedelta(days=365)
    timestamp = time.time()

    def parse_request(self):
        """Parse a request (internal).

        The request should be stored in self.raw_requestline; the results
        are in self.command, self.path, self.request_version and
        self.headers.

        Return True for success, False for failure; on failure, an
        error is sent back.

        """
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = 1
        requestline = str(self.raw_requestline, 'iso-8859-1')
        requestline = requestline.rstrip('\r\n')
        self.requestline = requestline
        words = requestline.split()
        if len(words) == 3:
            command, path, version = words
            if version[:5] != 'HTTP/':
                self.send_error(400, "Bad request version (%r)" % version)
                return False
        elif len(words) == 2:
            command, path = words
            if command != 'GET':
                self.send_error(400,
                                "Bad HTTP/0.9 request type (%r)" % command)
                return False
        elif not words:
            return False
        else:
            self.send_error(400, "Bad request syntax (%r)" % requestline)
            return False
        self.command, self.path, self.request_version = command, path, version

        # Examine the headers and look for a Connection directive.
        self.headers = self.parse_headers(self.rfile)

        return True

    def parse_headers(self, header_file):
        headers = {}
        while True:
            line = header_file.readline()
            if line in (b'\r\n', b'\n', b''):
                break
            key, _, value = line.decode('iso-8859-1').partition(':')
            headers[key] = value.strip()
        return headers

    def do_GET(self):
        """Return the cached buffer created during initialization"""
        path = self.translate_path(self.path)

        if os.path.isdir(path):
            self.path = os.path.join(self.path, 'index.html')

        self.path = self.path.split('?', 1)[0]
        self.path = self.path.split('#', 1)[0]
        cType = self.guess_type(self.path)
        use_gzip = 'gzip' in self.headers.get('Accept-Encoding', '')
        file_buffer = self.server.file_cache.get_resource(self.path, zipped=use_gzip)
        if not file_buffer:
            self.send_error(404, "File not found")
            return None

        self.send_response(200)
        self.send_header("Content-type", cType + '; charset=UTF-8')
        if cType != 'text/html':
            self.send_header('Expires', self.expire_time)
        if use_gzip:
            self.send_header('Content-Encoding', 'gzip')
        self.send_header("Content-Length", len(file_buffer))
        self.send_header("Last-Modified", self.date_time_string(self.timestamp))
        self.end_headers()
        try:
            self.wfile.write(file_buffer)
            file_buffer.release()
        except IOError:
            pass

    def log_request(self, code='-', size='-'):
        logger.info('{} - {}'.format(self.address_string(), self.headers))


class BlugHttpServer(socketserver.ThreadingMixIn, server.HTTPServer):
    """An extension to http.server.HTTPServer utilizing the FileCacheRequestHandler"""

    def __init__(self, root, *args, **kwargs):
        self.file_cache = FileCache(root)
        server.HTTPServer.__init__(self, *args, **kwargs)


class FileCache():
    """An in-memory cache of static files"""

    FILE_TYPES = ['.html', '.js', '.gif', '.css', '.png', '.xml']

    def __init__(self, base, debug=0):
        self.base = os.path.normpath(base)
        self.cache = dict()
        self.gzip_cache = dict()
        self._debug = debug
        self.build_cache(self.base)

    def build_cache(self, base_dir, current_dir=None):
        """Builds a cache of file contents recursively from the base_dir"""
        if not current_dir:
            current_dir = os.path.relpath(base_dir)
        for name in os.listdir(current_dir):
            name = os.path.join(current_dir, name)
            if not os.path.splitext(name)[1] in self.FILE_TYPES:
                if os.path.isdir(name):
                    self.build_cache(base_dir, name)
            else:
                with open(name, 'rb') as input_file:
                    data = bytes(input_file.read())
                    self.cache[name[1:]] = data
                    self.gzip_cache[name[1:]] = gzip.compress(data)

    def get_resource(self, path, zipped=False):
        """Returns the cached version of the file"""
        if zipped and path in self.gzip_cache:
            return memoryview(self.gzip_cache[path])
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
    """Display resource usage statistics for the file cache"""
    return  RUSAGE.format(rusage_struct.ru_utime,
                          rusage_struct.ru_stime,
                          rusage_struct.ru_maxrss,
                          rusage_struct.ru_ixrss,
                          rusage_struct.ru_idrss,
                          rusage_struct.ru_isrss,
                          rusage_struct.ru_minflt,
                          rusage_struct.ru_majflt,
                          rusage_struct.ru_nswap,
                          rusage_struct.ru_inblock,
                          rusage_struct.ru_oublock,
                          rusage_struct.ru_msgsnd,
                          rusage_struct.ru_msgrcv,
                          rusage_struct.ru_nsignals,
                          rusage_struct.ru_nvcsw,
                          rusage_struct.ru_nivcsw)

if __name__ == '__main__':
    cache = FileCache('/home/jeff/code/my_git_repos/blug/generated/', 1)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    print (print_usage_stats(usage))
    print (cache)
