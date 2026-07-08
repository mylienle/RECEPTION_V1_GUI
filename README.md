# 🤖 Autonomous Mobile Receptionist Robot - Core System

Welcome to the centralized repository for the Receptionist Robot project! This system provides a comprehensive Graphical User Interface (GUI) and the core navigational logic required to operate an Autonomous Mobile Robot (AMR) in a reception/building environment.

## ✨ Key Features
*   **Custom Path Planning:** Implements a robust Node Graph and Dijkstra's algorithm based on fixed waypoints, featuring an "Snap-to-Waypoint" mechanism and fallback routing.
*   **Real-time Telemetry & Control:** Monitors robot status, battery, velocity, and coordinates via MQTT protocol.
*   **Interactive Map GUI:** Built with PyQt6, allowing operators to visually track the robot, draw optimal routes, and send movement goals seamlessly.
*   **Attendance & Multi-Manager Systems:** Integrated modules for managing logs, user sessions, and task queues.

## 🕰️ Development History & Project Heritage
This repository is the final, consolidated version of the project's codebase, marking a fresh and optimized milestone. 

**Important Note on Authorship:** 
The core logic, algorithms, and GUI development of this system were engineered and authored by me (Thu). During the earlier stages of the project, the foundational code was distributed across different repositories created by my team members for collaborative setup. 

To view the complete commit history and the evolution of the early development phases that I contributed to, please refer to the original legacy repositories:
*   📦 **Phase 1 Repository:** ProjectReceptionRobot - (https://github.com/hcmutduygit/ProjectReceptionRobot)
*   📦 **Phase 2 Repository:** UI_MONITORING - (https://github.com/hoaiphu1002/UI_MONITORING)

This new repository is created to unify my work, establish proper ownership, and provide a clean, maintainable architecture moving forward.
