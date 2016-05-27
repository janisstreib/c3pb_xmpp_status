import logging
import threading
import subprocess
import time
import configparser

from sleekxmpp import ClientXMPP
import requests


class Subraum(ClientXMPP):
    def __init__(self, jid, password):
        ClientXMPP.__init__(self, jid, password)

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.last_state = False
        self.last_check = 0

    def session_start(self, event):
        self.send_presence(pnick='c3pb_status')
        self.check()

    def is_open(self):
        if self.last_check + 60 > time.time():
            return self.last_state

        r = requests.get('https://www.c3pb.de/uptime.json')
        self.last_check = time.time()
        self.last_state = 'open' == r.json()['state'].lower()
        return self.last_state

    @staticmethod
    def quote(long=False):
        return (subprocess.check_output(["fortune", '-a']) if long else subprocess.check_output(
            ["fortune", '-n', '80'])).decode('UTF-8')

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            body = msg['body'].lower()
            if body == "status":
                msg.reply("Subraum is {}.".format("open" if self.is_open() else "closed")).send()
            elif body == "quote":
                msg.reply(self.quote(True)).send()
            else:
                msg.reply(
                    "Command help:\nstatus - the status of the space (open/closed)\nquote - some wise words").send()

    def check(self):
        threading.Timer(60, self.check).start()
        self.send_presence(pnick='c3pb_status',
                           pstatus="[{}] {}".format("open" if self.is_open() else "closed", self.quote()),
                           pshow='availiabe' if self.is_open() else 'dnd')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-8s %(message)s')
    conf = configparser.ConfigParser()
    conf.read("config.ini")

    xmpp = Subraum(conf.get("xmpp", "jid"), conf.get("xmpp", "pass"))
    xmpp.auto_authorize = True
    xmpp.connect()
    xmpp.process(block=True)
