"""HTTP server and utilities"""

import os
import os.path
import resource


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
            self.get_cache_stats()

    def get_cache_stats(self):
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
        return '\n'.join(self.get_cache_stats())

def print_usage_stats(rusage_struct):

    return    '\
0	{ru_utime}	time in user mode (float)\n \
1	{ru_stime}	time in system mode (float)\n \
2	{ru_maxrss}	maximum resident set size\n \
3	{ru_ixrss}	shared memory size\n \
4	{ru_idrss}	unshared memory size\n \
5	{ru_isrss}	unshared stack size\n \
6	{ru_minflt}	page faults not requiring I/O\n \
7	{ru_majflt}	page faults requiring I/O\n \
8	{ru_nswap}	number of swap outs\n \
9	{ru_inblock}	block input operations\n \
10	{ru_oublock}	block output operations\n \
11	{ru_msgsnd}	messages sent\n \
12	{ru_msgrcv}	messages received\n \
13	{ru_nsignals}	signals received\n \
14	{ru_nvcsw}	voluntary context switches\n \
15	{ru_nivcsw}	involuntary context switches\n \
'.format (
	ru_utime   = rusage_struct.ru_utime,
	ru_stime   = rusage_struct.ru_stime,
	ru_maxrss  = rusage_struct.ru_maxrss,
	ru_ixrss   = rusage_struct.ru_ixrss,
	ru_idrss   = rusage_struct.ru_idrss,
	ru_isrss   = rusage_struct.ru_isrss,
	ru_minflt  = rusage_struct.ru_minflt,
	ru_majflt  = rusage_struct.ru_majflt,
	ru_nswap   = rusage_struct.ru_nswap,
	ru_inblock = rusage_struct.ru_inblock,
	ru_oublock = rusage_struct.ru_oublock,
	ru_msgsnd  = rusage_struct.ru_msgsnd,
	ru_msgrcv  = rusage_struct.ru_msgrcv,
	ru_nsignals= rusage_struct.ru_nsignals,
	ru_nvcsw   = rusage_struct.ru_nvcsw,
	ru_nivcsw  = rusage_struct.ru_nivcsw  )
if __name__ == '__main__':
    cache = FileCache('/home/jeff/code/blug/generated/', 1)
    print (cache)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    print (print_usage_stats(usage))
