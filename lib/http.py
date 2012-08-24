"""HTTP server and utilities"""

import os
import os.path
import socketserver
import socket
from http import server

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


class FileCacheRequestHandler(server.SimpleHTTPRequestHandler):

    def do_GET(self):
        path = self.translate_path(self.path)

        if os.path.isdir(path):
            self.path = os.path.join(self.path, 'index.html')

        self.path = self.path.split('?', 1)[0]
        self.path = self.path.split('#', 1)[0]
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

    def log_request(self, code='-', size='-'):
        pass


class BlugHttpServer(server.HTTPServer):

    def __init__(self, root, *args, **kwargs):
        self.file_cache = FileCache(root)
        server.HTTPServer.__init__(self, *args, **kwargs)


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
