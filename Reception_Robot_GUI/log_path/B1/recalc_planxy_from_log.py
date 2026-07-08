import csv
import json
import math

# =========================================================
# FILE PATH
# =========================================================
LOG_FILE = "Reception_Robot_GUI/log_path/B1/07-05-2026_19-06-37.csv"

WAYPOINT_FILE = "Reception_Robot_GUI/resources/Map/B1_config_wp.json"

OUTPUT_FILE = "Reception_Robot_GUI/log_path/B1/07-05-2026_19-05-15_fixed.csv"

# =========================================================
# MAP INFO (TỪ FILE YAML)
# =========================================================
MAP_RESOLUTION = 0.05

MAP_ORIGIN = [-23.371523, -12.247928]

# =========================================================
# MAP SIZE (TỪ FILE .PGM)
# P5
# 1675 1039
# =========================================================
MAP_WIDTH = 1675
MAP_HEIGHT = 1039

# =========================================================
# LOAD JSON
# =========================================================
with open(WAYPOINT_FILE, "r", encoding="utf-8") as f:

    data = json.load(f)

# =========================================================
# GỘP WAYPOINT + GOALS
# =========================================================
wps_raw = {}

wps_raw.update(data["waypoints"])

wps_raw.update(data["goals"])

connections = data["connections"]

# =========================================================
# PIXEL -> ROS MAP COORDINATE
# =========================================================
wps_meter = {}

print("\n==============================")
print("WAYPOINT CONVERSION")
print("==============================")

for name, (px, py) in wps_raw.items():

    # ROS map conversion
    x = MAP_ORIGIN[0] + px * MAP_RESOLUTION

    y = MAP_ORIGIN[1] + (MAP_HEIGHT - py) * MAP_RESOLUTION

    wps_meter[name] = (x, y)

    print(
        f"{name:15s} "
        f"pixel=({px:4d},{py:4d}) "
        f"map=({x:7.3f},{y:7.3f})"
    )

# =========================================================
# BUILD GRAPH SEGMENTS
# =========================================================
segments = []

added = set()

for wp1, neighbors in connections.items():

    for wp2 in neighbors:

        if wp1 not in wps_meter:
            continue

        if wp2 not in wps_meter:
            continue

        key = tuple(sorted([wp1, wp2]))

        # tránh segment trùng
        if key in added:
            continue

        added.add(key)

        x1, y1 = wps_meter[wp1]
        x2, y2 = wps_meter[wp2]

        segments.append({

            "wp1": wp1,
            "wp2": wp2,

            "x1": x1,
            "y1": y1,

            "x2": x2,
            "y2": y2
        })

print("\n==============================")
print("SEGMENTS")
print("==============================")

for i, seg in enumerate(segments):

    print(
        f"[{i:02d}] "
        f"{seg['wp1']} -> {seg['wp2']}"
    )

# =========================================================
# PROJECTION FUNCTION
# =========================================================
def project_to_segment(rx, ry, seg):

    x1 = seg["x1"]
    y1 = seg["y1"]

    x2 = seg["x2"]
    y2 = seg["y2"]

    # =====================================
    # segment vector
    # =====================================
    vx = x2 - x1
    vy = y2 - y1

    # =====================================
    # robot vector
    # =====================================
    wx = rx - x1
    wy = ry - y1

    # =====================================
    # projection coefficient
    # =====================================
    c1 = wx * vx + wy * vy

    c2 = vx * vx + vy * vy

    if c2 == 0:

        t = 0.0

    else:

        t = c1 / c2

    # =====================================
    # clamp inside segment
    # =====================================
    t = max(0.0, min(1.0, t))

    # =====================================
    # interpolation
    # =====================================
    px = x1 + t * vx

    py = y1 + t * vy

    # =====================================
    # tracking error
    # =====================================
    error = math.hypot(rx - px, ry - py)

    return px, py, error

# =========================================================
# LOAD ACTUAL LOG
# =========================================================
with open(LOG_FILE, "r", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    rows = list(reader)

print("\n==============================")
print("TOTAL LOG ROWS:", len(rows))
print("==============================")

# =========================================================
# TRACKING CONTINUITY
# =========================================================
last_segment = None

all_errors = []

for row_idx, row in enumerate(rows):

    try:

        rx = float(row["actual_x"])

        ry = float(row["actual_y"])

        best_error = float("inf")

        best_px = rx
        best_py = ry

        best_seg_idx = None

        # =============================================
        # continuity search
        # tránh nhảy segment lung tung
        # =============================================
        if last_segment is None:

            search_range = range(len(segments))

        else:

            search_range = range(
                max(0, last_segment - 2),
                min(len(segments), last_segment + 3)
            )

        # =============================================
        # SEARCH BEST SEGMENT
        # =============================================
        for idx in search_range:

            seg = segments[idx]

            px, py, err = project_to_segment(
                rx,
                ry,
                seg
            )

            if err < best_error:

                best_error = err

                best_px = px
                best_py = py

                best_seg_idx = idx

        # =============================================
        # UPDATE SEGMENT
        # =============================================
        last_segment = best_seg_idx

        # =============================================
        # SAVE RESULT
        # =============================================
        row["plan_x"] = round(best_px, 3)

        row["plan_y"] = round(best_py, 3)

        row["error_m"] = round(best_error, 3)

        row["segment"] = (
            f"{segments[best_seg_idx]['wp1']}"
            f"->"
            f"{segments[best_seg_idx]['wp2']}"
        )

        all_errors.append(best_error)

        # DEBUG 20 dòng đầu
        if row_idx < 20:

            print(
                f"[{row_idx:03d}] "
                f"actual=({rx:.2f},{ry:.2f}) "
                f"plan=({best_px:.2f},{best_py:.2f}) "
                f"err={best_error:.3f} "
                f"seg={row['segment']}"
            )

    except Exception as e:

        row["plan_x"] = ""

        row["plan_y"] = ""

        row["error_m"] = ""

        row["segment"] = ""

        print("ERROR:", e)

# =========================================================
# SAVE CSV
# =========================================================
with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:

    fieldnames = [

        "time",

        "actual_x",
        "actual_y",

        "plan_x",
        "plan_y",

        "error_m",

        "segment"
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for row in rows:

        writer.writerow({

            k: row.get(k, "")

            for k in fieldnames
        })

# =========================================================
# FINAL REPORT
# =========================================================
if len(all_errors) > 0:

    avg_error = sum(all_errors) / len(all_errors)

    max_error = max(all_errors)

    min_error = min(all_errors)

    print("\n==============================")
    print("TRACKING ERROR REPORT")
    print("==============================")

    print(f"Avg error : {avg_error:.3f} m")

    print(f"Max error : {max_error:.3f} m")

    print(f"Min error : {min_error:.3f} m")

print("\n==============================")
print("PLAN_X PLAN_Y FIXED SUCCESS")
print("==============================")

print("OUTPUT FILE:")

print(OUTPUT_FILE)