from threading import Thread
import time
import requests
from threading import Thread

import sys
import traceback

SERVER_ADDRESS = 'http://negtise2.appspot.com'
#SERVER_ADDRESS = 'http://localhost:8088'

class ClientPost(Thread):
    def __init__(self,counter,data):
        Thread.__init__(self)
        self.data = data
        self.counter = counter
    def run(self):
        ipaddr = SERVER_ADDRESS + '/client_post'
        try:
            r = requests.post(ipaddr, data={'counter':self.counter,'data':self.data})
        except requests.ConnectionError,e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
#            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
            traceback.print_exception(exc_type, exc_value, exc_traceback,file=sys.stdout)#,limit=2, file=sys.stdout)

    #    time.sleep(0.1)
#        print r.text

class ReadThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.isStop = False
    def run(self):
        ipaddr = SERVER_ADDRESS + '/client_get'
        while not self.isStop:
            try:
                r = requests.get(ipaddr)
                if r.text:
                    print r.text.encode('utf8')
                else:
                    time.sleep(0.1)
            except requests.ConnectionError,e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
    #            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
                traceback.print_exception(exc_type, exc_value, exc_traceback)#,limit=2, file=sys.stdout)

        print 'close'

    def stop(self):
        self.isStop = True

class WriteThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.isStop = False
        self.counter = 0
    def run(self):
        post = ClientPost(self.counter,'\n')
        post.start()
        self.counter += 1
        while not self.isStop:
            line = raw_input('')
            if line.strip() == 'exit':
                break
            post = ClientPost(self.counter,line+'\n')
            post.start()
            self.counter += 1

    def stop(self):
        self.write('\n')
        self.isStop = True

def test():
    post = ClientPost(1,'123')
    post.start()
    post.join()

def main():
    r = ReadThread()
    w = WriteThread()
    r.start()
    w.start()
    
    w.join()
    
    r.stop()
    r.join()

if __name__ == '__main__':
    main()

