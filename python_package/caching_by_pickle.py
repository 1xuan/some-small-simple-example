"""
The caching mechanism:
Using pickle package by serializing and de-serializing object
we can store object into file.
"""

import os
import time
import pickle


def cached(cachefile):
    def deco(func):
        def wrapped(*args, **kwargs):
            if not os.path.exists(cachefile):
                with open(cachefile, 'wb') as fp:
                    print(f'store cache to file {cachefile}')
                    res = func(*args, **kwargs)
                    pickle.dump(res, fp)
                return res
            with open(cachefile, 'rb') as fp:
                print(f'use cache from file { cachefile }')
                res = pickle.load(fp)
                return res
        return wrapped
    return deco


@cached('cachefile')
def whatever():
    time.sleep(3)
    return 'have fun'

result = whatever()
print(result)
