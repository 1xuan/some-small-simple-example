from concurrent import futures
from flags import save_flag, get_flag, show, main
import time
MAX_WORKERS = 20


def download_one(cc):
    image = get_flag(cc)
    show(cc)
    save_flag(image, cc.lower() + '.gif')
    return cc


def download_many(cc_list):
    cc_list = cc_list[:5]
    with futures.ThreadPoolExecutor(max_workers=3) as executor:
        to_do = []
        for cc in sorted(cc_list):
            # For example, the Executor.submit() method takes a callable,
            # schedules it to run, and returns a future.
            future = executor.submit(download_one, cc)
            to_do.append(future)
            msg = 'Scheduled for {}: {}'
            print(msg.format(cc, future))
        results = []
        for future in futures.as_completed(to_do):
            # it returns the result of the callable,
            # invoking f.result() will block the caller’s thread until the result is ready.
            res = future.result()
            msg = '{} result: {!r}'
            print(msg.format(futures, res))
            results.append(res)

    return len(results)


if __name__ == '__main__':
    main(download_many)