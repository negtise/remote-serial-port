from threading import Thread
import serial
import time
import requests
from threading import Thread
import sys
import traceback

SERVER_ADDRESS = 'http://negtise2.appspot.com'
#SERVER_ADDRESS = 'http://localhost:8088'

class ServerPost(Thread):
    def __init__(self,counter,data):
        Thread.__init__(self)
        self.data = data
        self.counter = counter
    def run(self):
        ipaddr = SERVER_ADDRESS + '/server_post' 
        try: 
            r = requests.post(ipaddr, data={'counter':self.counter,'data':self.data})
        except requests.ConnectionError,e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
#            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
            traceback.print_exception(exc_type, exc_value, exc_traceback)#,limit=2, file=sys.stdout)

    #    time.sleep(0.1)
#        print self.data,r.text

class ReadThread(Thread):
    def __init__(self,serial):
        Thread.__init__(self)
        self.serial = serial
        self.isStop = False
        self.counter = 0
    def run(self):
        line = []
        ignore_str = '\x1B\x5B\x30\x6D\x20\x20\x1B\x5B\x31\x3B\x33\x34\x6D'
        ipaddr = SERVER_ADDRESS + '/server_post'
        while not self.isStop:
            #line = self.serial.readline()
            #print line
            if self.serial.inWaiting():
                a = self.serial.read()
                line.append(a)
            else:
                if line:
                    line = ''.join(line)
                    line = line.replace(ignore_str,'')
                    t = ServerPost(self.counter,line)
                    t.start()
                    self.counter += 1
                    line = []
                else:
                    time.sleep(0.1)
        print 'close'
    def stop(self):
        self.serial.write('\n')
        self.isStop = True

class WriteThread(Thread):
    def __init__(self,serial):
        Thread.__init__(self)
        self.serial = serial
        self.isStop = False
    def run(self):
        ipaddr = SERVER_ADDRESS + '/server_get'
        while not self.isStop:
            try:
                r = requests.get(ipaddr)
                if r.text:
                    text = r.text.encode('utf8')
                    self.serial.write(text)
                else:
                    time.sleep(0.1)
            except requests.ConnectionError,e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
    #            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
                traceback.print_exception(exc_type, exc_value, exc_traceback)#,limit=2, file=sys.stdout)


#                self.serial.write('\n')
    def stop(self):
        self.write('\n')
        self.isStop = True

ser = serial.Serial()
ser.baudrate = 115200
ser.port = 4
ser.parity = serial.PARITY_NONE
ser.open()

r = ReadThread(ser)
w = WriteThread(ser)
r.start()
w.start()

w.join()

r.stop()
r.join()

ser.close()
