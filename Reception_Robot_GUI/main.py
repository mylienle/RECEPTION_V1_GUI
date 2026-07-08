import os, sys, json
from typing import Optional
import numpy as np
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import QTimer   

from ui.font_configurator import apply_custom_fonts
from ui.style import QMSGBOX_STYLE
from ui.main_ui import Ui_MainWindow
from user import handle_login, handle_signup
from attendance import AttendanceTab

from manager.manager_attendance import AttendanceManager
from manager.manager_battery import BatteryManager
from manager.manager_location import LocationManager 
from manager.manager_arrival import ArrivalManager 
from manager.manager_velocity import VelocityManager 
from manager.manager_telemetry import TelemetryManager
from manager.manager_goal import GoalManager

from location import LocationTab
from map_settings import get_map_id, set_map_id, VALID_MAP_IDS
from camera import CameraController, CameraTab
from robot_telemetry import PlotTelemetry

from MQTT.publisher_goal import GoalPublisher 
from MQTT.publisher_angle import AnglePublisher
from MQTT.mqtt_publisher_config import get_topic


def run_map_selection_dialog(parent: Optional[QWidget] = None) -> str:
    """Sau đăng nhập: chọn B1/B2 và ghi Reception_Robot_GUI/selected_map.json."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Chọn bản đồ robot")
    layout = QVBoxLayout(dlg)

    layout.addWidget(QLabel("Chọn tầng / map để dùng (ảnh .pgm, waypoint, thư mục log sẽ khớp map này):"))
    combo = QComboBox()
    for mid in VALID_MAP_IDS:
        combo.addItem(mid)
    combo.setCurrentText(get_map_id())
    layout.addWidget(combo)

    row = QHBoxLayout()
    btn_ok = QPushButton("Xác nhận")
    btn_cancel = QPushButton("Giữ cấu hình hiện tại")
    row.addWidget(btn_ok)
    row.addWidget(btn_cancel)
    layout.addLayout(row)

    chosen = [get_map_id()]

    def on_ok():
        chosen[0] = combo.currentText()
        dlg.accept()

    def on_cancel():
        chosen[0] = get_map_id()
        dlg.reject()

    btn_ok.clicked.connect(on_ok)
    btn_cancel.clicked.connect(on_cancel)

    dlg.exec()
    if dlg.result() == QDialog.DialogCode.Accepted:
        set_map_id(chosen[0])
        return chosen[0]
    return get_map_id()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        apply_custom_fonts(self.ui)

        self.selected_map_id = get_map_id()

        # Đặt giá trị mặc định cho label góc lệch để luôn hiển thị trên GUI
        if hasattr(self.ui, 'label_deviation_angle_2'):
            self.ui.label_deviation_angle_2.setText("Góc lệch (robot so với đường Home→wp15): --°")

        # ===== AUTO RETURN =====
        self.auto_return_timer = QTimer()
        self.auto_return_timer.setSingleShot(True)
        self.auto_return_timer.timeout.connect(self.auto_return_home)

        self.last_goal = None
        self.HOME_NAME = "Home"   

        # Rotate 
        self.home_rotation_timer = QTimer()
        self.home_rotation_timer.setSingleShot(True)

        # list user
        self.registered_users = [
            {
            "username": "hoaiphu",
            "password": "123",
            "fullname": "Admin User",
            "phone": "0123456789",
            "verify": "fablab"
        },
        {
            "username": "bthw",
            "password": "123",
            "fullname": "Admin User",
            "phone": "0987654321",
            "verify": "fablab"
        }]

        # ===== STATUS =====
        self.battery_manager = BatteryManager(self.ui)
        self.battery_manager.start_battery_subscriber()

        # ===== CONTROL =====
        # self.camera_controller = CameraController()
        # self.shared_browser = self.camera_controller.get_browser()

        self.velocity_manager = VelocityManager(self.ui)
        self.velocity_manager.start_velocity_subscriber()

        self.arrival_manager = ArrivalManager(self.ui)
        self.arrival_manager.start_arrival_subscriber()

        self.ui.mode_select_2.currentTextChanged.connect(self.handle_mode_switch)

        # ===== ATTENDANCE =====
        self.attendance_tab = AttendanceTab(self.ui)
        self.attendance_manager = AttendanceManager(self.ui, self.attendance_tab)
        self.attendance_manager.start_attendance_subscriber()

        # ===== TELEMETRY =====
        self.telemetry_tab = PlotTelemetry(self.ui)
        self.telemetry_manager = TelemetryManager(self.ui, self.telemetry_tab)
        self.telemetry_manager.start_telemetry_subscriber()

        # ===== INIT UI =====
        self.ui.stackedWidget.setCurrentWidget(self.ui.login)
        self.ui.Page.setCurrentWidget(self.ui.Page_signin)
        self.ui.Dashboard.setCurrentWidget(self.ui.Dashboard_signin)

        # ===== LOGIN EVENTS =====
        self.ui.Signin_btn_signup.clicked.connect(lambda: self.ui.Page.setCurrentWidget(self.ui.Page_signup))
        self.ui.Signin_btn_signin.clicked.connect(lambda: self.ui.Page.setCurrentWidget(self.ui.Page_signin))
        self.ui.Signin_btn_guest.clicked.connect(self._handle_guest)
        self.ui.Signin_btn_login.clicked.connect(self._handle_login)
        self.ui.Signup_btn_signup.clicked.connect(self._handle_signup)

        # ===== AFTER LOGIN =====
        self.ui.comboBox_2.currentTextChanged.connect(self.handle_page_switch)
        self.ui.logout.clicked.connect(self._handle_logout)
        self.ui.logout_2.clicked.connect(self._handle_logout)
        self.ui.mode_select_2.currentTextChanged.connect(self.handle_mode_switch)

    # ================= LOGIN =================
    def _handle_login(self):
        success = handle_login(self.ui, self.registered_users, main_window=self)
        if success:
            self.selected_map_id = run_map_selection_dialog(self)

            self.ui.stackedWidget.setCurrentWidget(self.ui.robot)
            self.ui.stackedWidget_2.setCurrentWidget(self.ui.page_control_2)

            # self.admin_camera_tab = CameraTab(self.ui.camera_2, self.shared_browser)
    
            self.admin_location_tab = LocationTab(self.ui.view_map_2, self.selected_map_id)
            self.admin_location_tab.logger.cte_signal.connect(self.telemetry_tab.update_cte)

            self.add_path_planning_buttons(self.admin_location_tab)

            self.arrival_manager.subscriber_thread.arrival_update.connect(
                lambda arrived: self.handle_arrival_signal(arrived)
            )

            self.location_manager = LocationManager(self.ui)
            self.location_manager.location_tab = self.admin_location_tab
            self.location_manager.start_location_subscriber()

            self.goal_manager = GoalManager(self.ui)
            self.goal_manager.location_tab = self.admin_location_tab
            self.goal_manager.start_goal_subscriber()

    def _handle_signup(self):
        success = handle_signup(self.ui, self.registered_users, main_window=self)
        if success:
            self.ui.stackedWidget.setCurrentWidget(self.ui.login)

    def _handle_guest(self):
        self.selected_map_id = run_map_selection_dialog(self)

        self.ui.stackedWidget.setCurrentWidget(self.ui.guest)

        self.guest_camera_tab = CameraTab(self.ui.camera_4, self.shared_browser)
        self.guest_location_tab = LocationTab(self.ui.view_map, self.selected_map_id)

        self.add_path_planning_buttons(self.guest_location_tab)

        self.location_manager = LocationManager(self.ui)
        self.location_manager.location_tab = self.guest_location_tab
        self.location_manager.start_location_subscriber()

    # ================= LOGOUT =================
    def _handle_logout(self):
        msgbox = QMessageBox(self)
        msgbox.setWindowTitle("Confirm Logout")
        msgbox.setText("Are you sure you want to log out?")
        msgbox.setIcon(QMessageBox.Icon.Question)
        msgbox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msgbox.setStyleSheet(QMSGBOX_STYLE)

        if msgbox.exec() == QMessageBox.StandardButton.Yes:
            self._shutdown_all_services()
            self.ui.stackedWidget.setCurrentWidget(self.ui.login)

    # ================= UI =================
    def handle_page_switch(self, text):
        if text == "Control Panel":
            self.ui.stackedWidget_2.setCurrentWidget(self.ui.page_control_2)
        elif text == "Attendance":
            self.ui.stackedWidget_2.setCurrentWidget(self.ui.page_attendance_2)
        elif text == "Robot Telemetry":
            self.ui.stackedWidget_2.setCurrentWidget(self.ui.page_data)

    def handle_mode_switch(self, text):
        if text == "Manual":
            self.ui.robot_mode_2.setCurrentWidget(self.ui.page_5)
        elif text == "Auto":
            self.ui.robot_mode_2.setCurrentWidget(self.ui.page_6)

    # ================= BUTTON =================
    def add_path_planning_buttons(self, location_tab):
        goals = location_tab.get_goal_names()
        buttons = [
            self.ui.btn_goal_A,
            self.ui.btn_goal_B,
            self.ui.btn_goal_C,
            self.ui.btn_goal_D,
            self.ui.btn_goal_E,
            self.ui.btn_goal_F,
            self.ui.btn_goal_G,
            self.ui.btn_goal_H,
            self.ui.btn_goal_I        
        ]

        for btn, name in zip(buttons, goals):
            btn.setText(name)
            btn.clicked.connect(lambda checked=False, n=name: self.send_goal(n))

    # ================= GOAL =================
    def send_goal(self, place: str):
        goal_json = json.dumps(place)
        print(f"Goal: {goal_json}")

        publisher = GoalPublisher()
        publisher.publish_goal(goal_json)

        # ===== AUTO RETURN =====
        self.last_goal = place
        self.auto_return_timer.stop()  # reset timer
        self.home_rotation_timer.stop()

    # ================= ARRIVAL =================
    def handle_arrival_signal(self, arrived):
        if arrived == 1 and hasattr(self, 'admin_location_tab'):
            if getattr(self, '_is_processing_arrival', False):
                return
            self._is_processing_arrival = True
            QTimer.singleShot(3000, lambda: setattr(self, '_is_processing_arrival', False))

            self.ui.robot_mode_2.setCurrentWidget(self.ui.page_6)
            self.admin_location_tab.logger.stop_logging()
            self.ui.robot_status.setText("Idle")
            self.ui.robot_status_2.setText("Idle")

            # ===== START TIMER =====
            if self.last_goal != self.HOME_NAME:
                print("⏱ Start 30s auto return timer")
                self.auto_return_timer.start(30000)

            # If we just arrived at Home, compute deviation using real heading vs Home->wp15 (0-degree reference).
            if self.last_goal == self.HOME_NAME:
                try:
                    angle_to_publish = self.admin_location_tab.calculate_home_rotation_angle()
                    if angle_to_publish is not None:
                        # Hiển thị góc lệch lên GUI
                        if hasattr(self.ui, 'label_deviation_angle_2'):
                            self.ui.label_deviation_angle_2.setText(f"Xoay (robot so với đường Home→wp15): {angle_to_publish}°")
                            font = self.ui.label_deviation_angle_2.font()
                            font.setPointSize(12)
                            self.ui.label_deviation_angle_2.setFont(font)

                        # Gửi tín hiệu xoay 2 lần, mỗi lần cách nhau 5 giây
                        try:
                            self.home_rotation_timer.timeout.disconnect()
                        except TypeError:
                            pass

                        # Gửi lần đầu ngay khi về Home
                        AnglePublisher().publish_angle(angle_to_publish)
                        print(f"[Xoay] Heading at Home (lần 1): {angle_to_publish}")
                        # Sau 5s gửi lần 2
                        QTimer.singleShot(5000, lambda: (
                            AnglePublisher().publish_angle(angle_to_publish),
                            print(f"[Xoay] Heading at Home (lần 2): {angle_to_publish}")
                        ))

                except Exception as e:
                    print(f"[MQTT ANGLE] Compute/publish on arrival failed: {e}")

    # ================= AUTO RETURN =================
    def auto_return_home(self):
        print("🏠 Auto return HOME")
        if self.last_goal == self.HOME_NAME:
            return
        self.send_goal(self.HOME_NAME)

    # ================= SHUTDOWN =================
    def _shutdown_all_services(self):
        self.battery_manager.stop_battery_subscriber()
        self.attendance_manager.stop_attendance_subscriber()
        self.location_manager.stop_location_subscriber()
        self.velocity_manager.stop_velocity_subscriber()
        self.arrival_manager.stop_arrival_subscriber()
        self.telemetry_manager.stop_telemetry_subscriber()
        self.goal_manager.stop_goal_subscriber()

    def closeEvent(self, event):
        print("Closinggg...")
        self._shutdown_all_services()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.showMaximized()
    sys.exit(app.exec())