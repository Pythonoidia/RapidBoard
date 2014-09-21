

class GetLastLineFromLog(object):
    def __init__(self, queue, filename):
        self.PREV=None
        self.queue = queue
        self.filename=filename

    def get_last_line(self):
        with open(self.filename, 'rb') as fh:
            fh.seek(-1024, 2)
            last_line = fh.readlines()[-1].decode()
        if self.PREV==last_line:
            pass
        else:
            self.PREV=last_line
            self.queue.put({'content':last_line, 'severity':3})






