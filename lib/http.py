"""HTTP server and utilities"""

import os
import os.path
import resource

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


class FileCache():
    """An in-memory cache of static files"""

    FILE_TYPES = ['.html', '.js', '.css']

    def __init__(self, base, debug=0):
        self.base = os.path.normpath(base)
        self.cache = dict()
        self._debug = debug
        self.build_cache(self.base)

    def build_cache(self, base_dir):
        for name in os.listdir(base_dir):
            name = os.path.join(base_dir, name)
            if not os.path.splitext(name)[1] in self.FILE_TYPES:
                if os.path.isdir(name):
                    self.build_cache(name)
            else:
                with open(name, 'r') as input_file:
                    self.cache[name] = input_file.read()

        if self._debug >= 1:
            self._get_cache_stats()

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
    cache = FileCache('/home/jeff/code/blug/generated/', 1)
    print (cache)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    print (print_usage_stats(usage))
