import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from MQTT.subscriber_goal import GoalSubscriberThread
from manager.manager_base import BaseManager
from mqtt_config import MQTTConfig

GOAL_CONFIG = MQTTConfig.get_config("goal")

class GoalManager(BaseManager):
    def __init__(self, ui, location_tab=None):
        super().__init__(ui, GoalSubscriberThread, GOAL_CONFIG)
        self.ui = ui 
        self.goal = None
        self.location_tab = location_tab

    def _connect_signals(self):
        # robot/goal no longer starts planning: every GUI on the broker received it, so a second
        # GUI could plan the same goal and send the robot a second copy of the route
        pass

    def start_goal_subscriber(self):
        self.start_subscriber()

    def stop_goal_subscriber(self):
        self.stop_subscriber()

    def start_navigation(self, name):
        """Plan the goal picked on this GUI and send its route to the robot."""
        self.handle_goal_update(name)

    def cancel_navigation(self):
        self.goal = None

    def handle_goal_update(self, name):
        if name:
            self.goal = name
            self.location_tab.plan_path(name)
            self.ui.robot_status.setText("Guidance")
            self.ui.robot_status_2.setText("Guidance")
            self.ui.robot_mode_2.setCurrentWidget(self.ui.page_log)
            self.ui.label_log.setText(f"Robot is moving to {name}")
        else:
            self.goal = None
