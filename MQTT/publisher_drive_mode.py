#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from MQTT.mqtt_publisher_config import MQTTTemplate, get_topic

class DriveModePublisher(MQTTTemplate):
    """Publish the robot drive mode to robot/drive_mode: 1 = gamepad, 2 = autonomous."""
    def __init__(self):
        super().__init__()
        self.topic = get_topic("drive_mode")  # robot/drive_mode

    def publish_mode(self, mode):
        if mode not in (1, 2):
            print(f"Invalid drive mode {mode}, expected 1 or 2")
            return
        try:
            self.publish_and_exit(self.topic, str(mode), delay=self.delay)
            print(f"Published drive mode {mode} to {self.topic}")
        except Exception as e:
            print(f"Failed to publish drive mode: {e}")
