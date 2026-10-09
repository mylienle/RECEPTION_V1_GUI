import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from MQTT.subscriber_arrival import ArrivalSubscriberThread
from manager.manager_base import BaseManager
from mqtt_config import MQTTConfig

ARRIVAL_CONFIG = MQTTConfig.get_config("arrival")

class ArrivalManager(BaseManager):
    def __init__(self, ui):
        super().__init__(ui, ArrivalSubscriberThread, ARRIVAL_CONFIG)
        self.arrival = False
        self.has_arrived = False

    def _connect_signals(self):
        self.subscriber_thread.arrival_update.connect(self.handle_arrival_update)

    def start_arrival_subscriber(self):
        self.start_subscriber()
        self.reset_arrival_state()

    def stop_arrival_subscriber(self):
        self.stop_subscriber()

    def reset_arrival_state(self):
        """Clear the arrival state when a navigation is cancelled or restarted."""
        self.arrival = False
        self.has_arrived = False

    def handle_arrival_update(self, arrived):
        # ArrivalSubscriberThread emits bools.  Do not emit this same signal again:
        # emitting it recursively made the state impossible to reset reliably.
        self.arrival = bool(arrived)
        if self.arrival:
            self.has_arrived = True
        else:
            self.has_arrived = False
