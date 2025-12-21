import queue
import threading


class QueueWrapper:
    def __init__(
            self,
            qmaxsize=1000,
            put_timeout=0.1,
            get_timeout=0.1
    ):
        self._name = self.__class__.__name__
        self.queue = queue.Queue(maxsize=qmaxsize)
        self.put_timeout = put_timeout
        self.get_timeout = get_timeout
        self.stop = threading.Event()

    def __del__(self):
        self.queue = None

    def terminate(self):
        self.stop.set()

    def qsize(self):
        return self.queue.qsize()

    def put(self, item):
        warning = False
        while not self.stop.is_set():
            try:
                self.queue.put(item, timeout=self.put_timeout)
                break
            except queue.Full:
                if not warning:
                    warning = True
                    print(f"[{self._name}] WARNING: queue is full!")

    def get(self):
        while not self.stop.is_set():
            try:
                item = self.queue.get(timeout=self.get_timeout)
                self.queue.task_done()
                return item
            except queue.Empty:
                pass

        return None
