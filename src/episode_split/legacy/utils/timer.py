from contextlib import contextmanager

import time


@contextmanager
def timer():
    start = time.time()
    yield
    end = time.time()
    print("Time elapsed: {}".format(end - start))
