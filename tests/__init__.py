import time
from binascii import unhexlify

from pylgbst.comms import Connection
from pylgbst.hub import MoveHub
from pylgbst.peripherals import *

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger('test')


class HubMock(MoveHub):
    """
    :type connection: ConnectionMock
    """

    # noinspection PyUnresolvedReferences
    def __init__(self, conn=None):
        super(HubMock, self).__init__(conn if conn else ConnectionMock())
        self.connection = self.connection
        self.notify_mock = self.connection.notifications
        self.writes = self.connection.writes

    def _report_status(self):
        pass


class ConnectionMock(Connection):
    """
    For unit testing purposes
    """

    def __init__(self):
        super(ConnectionMock, self).__init__()
        self.writes = []
        self.notifications = []
        self.notification_handler = None
        self.running = True
        self.finished = False

        self.thr = Thread(target=self.notifier)
        self.thr.setDaemon(True)

    def set_notify_handler(self, handler):
        self.notification_handler = handler
        self.thr.start()

    def notifier(self):
        while self.running or self.notifications:
            if self.notification_handler:
                while self.notifications:
                    data = self.notifications.pop(0)
                    s = unhexlify(data.replace(' ', ''))
                    self.notification_handler(MoveHub.HUB_HARDWARE_HANDLE, bytes(s))
            time.sleep(0.1)

        self.finished = True

    def write(self, handle, data):
        log.debug("Writing to %s: %s", handle, str2hex(data))
        self.writes.append((handle, str2hex(data)))

    def connect(self, hub_mac=None):
        """
        :rtype: ConnectionMock
        """
        super(ConnectionMock, self).connect(hub_mac)
        return self

    def is_alive(self):
        return not self.finished

    def notification_delayed(self, payload, pause):
        def inject():
            time.sleep(pause)
            self.notifications.append(payload)

        Thread(target=inject).start()

    def wait_notifications_handled(self):
        self.running = False
        for _ in range(1, 180):
            time.sleep(0.1)
            log.debug("Waiting for notifications to process...")
            if self.finished:
                log.debug("Done waiting for notifications to process")
                break
