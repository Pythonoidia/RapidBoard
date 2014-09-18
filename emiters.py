


class Emiters(object):
    def __init__(self):
        self.prev=None
        self.filename='/home/teamspeak/teamspeak3-server_linux-x86/logs/ts3server_2014-07-28__16_46_55.187196_1.log', 'rb/home/teamspeak/teamspeak3-server_linux-x86/logs/ts3server_2014-07-28__16_46_55.187196_1.log'

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        

    def get_last_line(self):
        with open(self.filename, 'rb') as fh:
            fh.seek(-1024, 2)
            last_line = fh.readlines()[-1].decode()
        if self.prev==last_line:
            pass
        else:
            PREV=last_line
            print(last_line)






