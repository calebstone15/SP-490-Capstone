import tkinter as tk
import subprocess
import sys
import os
import random
import math
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ── Color palette ──────────────────────────────────────────────────────────────
# Dark background/panel colors for the overall UI theme
BG      = "#0d0d1a"; PANEL  = "#111128"; BORDER = "#1a1d3a"
# Accent/button colors; CYAN used for active highlights
ACCENT  = "#e94560"; ABTN   = "#0f1535"; CYAN   = "#00d4ff"
# Status colors: green=nominal, amber=caution, danger=alert
GREEN   = "#00e676"; AMBER  = "#ffab40"; DANGER = "#ff5252"
# Text hierarchy: TXT=primary, TXT2=secondary, TXT3=tertiary/dim
TXT     = "#e8eaf6"; TXT2   = "#7986cb"; TXT3   = "#8898c8"
# P&ID canvas background and element state colors
PID_BG  = "#07071a"; PIPE_OFF = "#1a1d3a"; PIPE_ON = "#00d4ff"
# Camera/component state colors: off, active, warning, closed
V_OFF   = "#2a2d4a"; V_ON   = "#00e676"; V_WARN  = "#ffab40"; V_CLOSE = "#ff5252"


def return_to_main(root):
    """Close this operator screen and relaunch the main menu."""
    main_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "main.py")
    subprocess.Popen([sys.executable, main_file])
    root.destroy()


def main():
    # ── Window setup ──────────────────────────────────────────────────
    root = tk.Tk()
    root.title("Visual Control — Camera & System Oversight")
    root.geometry("1440x960")
    root.configure(bg=BG)
    root.resizable(True, True)
    root.minsize(1050, 780)

    # ── Header ────────────────────────────────────────────────────────
    hdr = tk.Frame(root, bg=BG)
    hdr.pack(fill="x", padx=50, pady=(18, 0))
    badge = tk.Frame(hdr, bg=ACCENT, padx=12, pady=9)
    badge.pack(side="left", anchor="n", padx=(0, 16))
    tk.Label(badge, text="VIS", font=("Helvetica", 14, "bold"), fg=TXT, bg=ACCENT).pack()
    tk.Label(badge, text="CTL", font=("Courier", 9, "bold"), fg="#ffa0b0", bg=ACCENT).pack()
    info = tk.Frame(hdr, bg=BG)
    info.pack(side="left")
    tk.Label(info, text="Visual Control", font=("Helvetica", 30, "bold"), fg=TXT, bg=BG).pack(anchor="w")
    tk.Label(info, text="Camera & System Oversight  ·  Components: CAM-A (North) · CAM-B (East) · CAM-C (South) · CAM-D (West)",
             font=("Courier", 12), fg=TXT2, bg=BG).pack(anchor="w", pady=(3, 0))
    tk.Frame(root, bg=ACCENT, height=2).pack(fill="x", padx=50, pady=(8, 0))
    tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=50)

    content = tk.Frame(root, bg=BG)
    content.pack(fill="both", expand=True, padx=50, pady=(10, 0))
    content.columnconfigure(0, weight=3)
    content.columnconfigure(1, weight=2)
    content.rowconfigure(0, weight=1)
    left = tk.Frame(content, bg=BG)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    right = tk.Frame(content, bg=BG)
    right.grid(row=0, column=1, sticky="nsew")

    # ── Steps ─────────────────────────────────────────────────────────
    # Each step is (countdown_time, step_name, description).
    # step_states tracks whether each step has been executed (toggled on).
    steps = [
        ("0:05:00", "START CAMERAS",         "Start Test Control Cameras"),
        ("0:03:45", "VERIFY SYSTEM GO",       "Verify System is GO"),
        ("+0:50   ", "VERIFY SYSTEM SAFED",  "Verify system is safed"),
        ("POST    ", "DATA COLLECTION",       "Proceed with data collection"),
    ]
    step_states = [False] * len(steps)
    step_btns   = []   # EXECUTE/UNDO button widgets, indexed by step
    step_labels = []   # status label widgets (e.g. "● ACTIVE"), indexed by step

    # Build the checklist table header
    tk.Label(left, text="COUNTDOWN CHECKLIST", font=("Courier", 14, "bold"),
             fg=TXT2, bg=BG).pack(anchor="w", pady=(0, 8))
    tbl = tk.Frame(left, bg=BG)
    tbl.pack(fill="x")
    for col, (txt, w) in enumerate([("TIME", 8), ("STEP", 22), ("DESCRIPTION", 34),
                                     ("ACTION", 10), ("STATUS", 14)]):
        tk.Label(tbl, text=txt, font=("Courier", 12, "bold"), fg=TXT3,
                 bg=BG, width=w, anchor="w").grid(row=0, column=col, padx=4, pady=(0, 4), sticky="w")
    tk.Frame(tbl, bg=BORDER, height=1).grid(row=1, column=0, columnspan=5,
                                             sticky="ew", pady=(0, 6))

    # ── Camera/system state ───────────────────────────────────────────
    UPDATE_MS   = 50           # graph/sensor refresh interval in milliseconds
    WINDOW_SECS = 30           # rolling time window shown on plots
    tick        = [0]          # current simulation tick counter

    # Mutable single-element lists for closure access across toggle callbacks
    cameras_active = [False]   # True once cameras are started
    system_go      = [False]   # True once operator confirms system GO
    system_safed   = [False]   # True once post-test safing is confirmed

    # Per-camera rolling time-series buffers for live signal quality plots
    # Index 0=CAM-A (North), 1=CAM-B (East), 2=CAM-C (South), 3=CAM-D (West)
    cam_t = [[], [], [], []]
    cam_v = [[], [], [], []]

    def next_signal(cam_idx):
        """Compute simulated signal quality (0–100%) for camera cam_idx.

        When cameras are offline, returns near-zero noise.
        When active, returns a high-quality signal with occasional dropout spikes
        and per-camera baseline variation to represent real-world positioning.
        """
        if not cameras_active[0]:
            return max(0.0, random.gauss(2, 1))
        # Each camera has a distinct baseline quality based on positioning/distance
        baselines = [94, 85, 91, 78]
        baseline  = baselines[cam_idx]
        noise     = random.gauss(0, 2.5)
        dropout  = -random.uniform(8, 25) if random.random() < 0.008 else 0.0
        return max(0.0, min(100.0, baseline + noise + dropout))

    # ── P&ID canvas — top-down test stand camera coverage map ─────────
    tk.Label(right, text="P&ID — TEST STAND CAMERA COVERAGE MAP",
             font=("Courier", 12, "bold"), fg=TXT3, bg=BG).pack(anchor="w", pady=(2, 6))
    pid = tk.Canvas(right, width=550, height=370, bg=PID_BG,
                    highlightthickness=1, highlightbackground=BORDER)
    pid.pack(fill="both", expand=True)

    # Test stand center reference point
    cx, cy = 275, 185

    # ── Test stand structure (top-down footprint) ──────────────────────
    # Outer boundary ring
    pid.create_oval(cx-70, cy-70, cx+70, cy+70,
                    fill="#0a0a18", outline="#2a3060", width=1.5, dash=(6, 3))
    # Stand pad rectangle
    pid.create_rectangle(cx-38, cy-55, cx+38, cy+55,
                         fill="#141428", outline="#2a3060", width=2)
    pid.create_text(cx, cy - 30, text="TEST",  fill=TXT3, font=("Courier", 10, "bold"))
    pid.create_text(cx, cy - 15, text="STAND", fill=TXT3, font=("Courier", 10, "bold"))

    # Engine mount point at center of stand
    pid.create_oval(cx-13, cy-13, cx+13, cy+13,
                    fill="#1a2a10", outline="#3a5a20", width=2)
    pid.create_text(cx, cy, text="ENG", fill=GREEN, font=("Courier", 9, "bold"))

    # ── Camera definitions: (x, y, label, compass, angle_toward_center) ─
    # Each camera points toward the engine (cx, cy)
    cam_defs = [
        (cx,       cy - 158, "CAM-A", "NORTH"),
        (cx + 158, cy,       "CAM-B", "EAST"),
        (cx,       cy + 158, "CAM-C", "SOUTH"),
        (cx - 158, cy,       "CAM-D", "WEST"),
    ]

    # Draw FOV cone lines for each camera (two bounding rays)
    p_fov = []
    FOV_LEN = 120; FOV_HALF = math.radians(18)
    for cam_x, cam_y, cam_lbl, _ in cam_defs:
        angle = math.atan2(cy - cam_y, cx - cam_x)
        l1 = pid.create_line(
            cam_x, cam_y,
            cam_x + FOV_LEN * math.cos(angle + FOV_HALF),
            cam_y + FOV_LEN * math.sin(angle + FOV_HALF),
            fill=V_OFF, width=1, dash=(5, 3))
        l2 = pid.create_line(
            cam_x, cam_y,
            cam_x + FOV_LEN * math.cos(angle - FOV_HALF),
            cam_y + FOV_LEN * math.sin(angle - FOV_HALF),
            fill=V_OFF, width=1, dash=(5, 3))
        p_fov.append((l1, l2))

    # Draw camera body rectangles and lens icon
    p_cams = []
    for cam_x, cam_y, cam_lbl, compass in cam_defs:
        body = pid.create_rectangle(cam_x-15, cam_y-10, cam_x+15, cam_y+10,
                                     fill=ABTN, outline="#3a3d6a", width=1.5)
        icon = pid.create_text(cam_x, cam_y, text="◉",
                                fill=V_OFF, font=("Helvetica", 14, "bold"))
        pid.create_text(cam_x, cam_y + 19, text=cam_lbl,
                        fill=TXT2, font=("Courier", 10, "bold"))
        pid.create_text(cam_x, cam_y + 31, text=compass,
                        fill=TXT3, font=("Courier", 9))
        p_cams.append((body, icon))

    # Signal quality readout text above each camera
    p_sig = []
    for cam_x, cam_y, _, _ in cam_defs:
        sv = pid.create_text(cam_x, cam_y - 23, text="OFFLINE",
                              fill=DANGER, font=("Courier", 9, "bold"))
        p_sig.append(sv)

    # System status banner at bottom of P&ID
    p_status = pid.create_text(cx, 353, text="● CAMERAS OFFLINE",
                                fill=DANGER, font=("Courier", 12, "bold"))

    # Legend
    pid.create_rectangle(13, 336, 25, 346, fill=V_ON,   outline="#3a3d6a")
    pid.create_text(30,  341, text="ACTIVE",  fill=TXT3, font=("Courier", 9), anchor="w")
    pid.create_rectangle(88, 336, 100, 346, fill=V_OFF, outline="#3a3d6a")
    pid.create_text(105, 341, text="OFFLINE", fill=TXT3, font=("Courier", 9), anchor="w")
    pid.create_line(163, 341, 183, 341, fill=CYAN, width=1, dash=(5, 3))
    pid.create_text(188, 341, text="FOV",     fill=TXT3, font=("Courier", 9), anchor="w")
    pid.create_oval(cx-6, cy+145, cx+6, cy+155, fill=GREEN, outline="#3a3d6a")
    pid.create_text(cx+12, cy+150, text="ENGINE",  fill=TXT3, font=("Courier", 9), anchor="w")

    def update_pid():
        """Refresh all P&ID canvas elements to reflect the current camera/system state.

        Updates camera body colors, lens icons, FOV line colors, per-camera signal
        quality readouts, and the system status banner.
        """
        for i, (body, icon) in enumerate(p_cams):
            if cameras_active[0]:
                sig = cam_v[i][-1] if cam_v[i] else 0.0
                col = V_ON if sig > 70 else (AMBER if sig > 40 else DANGER)
                pid.itemconfig(body, fill="#0a1a0a")
                pid.itemconfig(icon, fill=col)
                pid.itemconfig(p_sig[i], text=f"{sig:.0f}%", fill=col)
                pid.itemconfig(p_fov[i][0], fill=CYAN if sig > 70 else AMBER)
                pid.itemconfig(p_fov[i][1], fill=CYAN if sig > 70 else AMBER)
            else:
                pid.itemconfig(body, fill=ABTN)
                pid.itemconfig(icon, fill=V_OFF)
                pid.itemconfig(p_sig[i], text="OFFLINE", fill=DANGER)
                pid.itemconfig(p_fov[i][0], fill=V_OFF)
                pid.itemconfig(p_fov[i][1], fill=V_OFF)

        # System status banner priority: safed > go > cameras active > offline
        if system_safed[0]:
            pid.itemconfig(p_status, text="● SYSTEM SAFED — DATA COLLECTION READY", fill=GREEN)
        elif system_go[0]:
            pid.itemconfig(p_status, text="● SYSTEM GO — TEST IN PROGRESS", fill=AMBER)
        elif cameras_active[0]:
            pid.itemconfig(p_status, text="● CAMERAS ACTIVE — AWAITING GO", fill=CYAN)
        else:
            pid.itemconfig(p_status, text="● CAMERAS OFFLINE", fill=DANGER)

    def make_toggle(idx):
        """Return a toggle callback for checklist step idx.

        When activated (EXECUTE pressed):
          - idx 0: starts cameras; begins signal quality simulation.
          - idx 1: marks system GO (cameras must be active first).
          - idx 2: confirms post-test safing; locks GO state to false.
          - idx 3: marks data collection as active.
        When deactivated (UNDO pressed):
          - Resets the relevant state flag and reverts button/label styling.
        """
        def toggle():
            step_states[idx] = not step_states[idx]
            if step_states[idx]:
                # Step executed: switch button to UNDO, mark status ACTIVE
                step_btns[idx].config(text="UNDO", bg="#1a0820", fg=ACCENT, activebackground=ABTN)
                step_labels[idx].config(text="● ACTIVE", fg=GREEN)
                if idx == 0:
                    # Start cameras — enable signal simulation
                    cameras_active[0] = True
                elif idx == 1:
                    # Verify system GO
                    system_go[0] = True
                elif idx == 2:
                    # System safed post-test
                    system_safed[0] = True
                    system_go[0]    = False
                    step_labels[idx].config(text="● SAFED ✓", fg=GREEN)
                elif idx == 3:
                    # Proceed with data collection
                    step_labels[idx].config(text="● COLLECTING", fg=CYAN)
            else:
                # Step undone: revert button and status label
                step_btns[idx].config(text="EXECUTE", bg=ABTN, fg=CYAN, activebackground=BORDER)
                step_labels[idx].config(text="○ READY", fg=TXT3)
                if idx == 0:
                    cameras_active[0] = False
                elif idx == 1:
                    system_go[0] = False
                elif idx == 2:
                    system_safed[0] = False
            update_pid()
        return toggle

    # Populate checklist rows; each row gets time, name, description, an EXECUTE
    # button (wired to make_toggle), and a status label.
    for i, (ts, name, desc) in enumerate(steps):
        row = i + 2
        tk.Label(tbl, text=ts, font=("Courier", 13), fg=TXT2, bg=BG,
                 width=8, anchor="w").grid(row=row, column=0, padx=4, pady=16, sticky="w")
        tk.Label(tbl, text=name, font=("Courier", 13, "bold"), fg=TXT, bg=BG,
                 width=22, anchor="w").grid(row=row, column=1, padx=4, pady=16, sticky="w")
        tk.Label(tbl, text=desc, font=("Helvetica", 13), fg=TXT2, bg=BG,
                 width=34, anchor="w").grid(row=row, column=2, padx=4, pady=16, sticky="w")
        btn = tk.Button(tbl, text="EXECUTE", font=("Courier", 12, "bold"),
                        bg=ABTN, fg=CYAN, activebackground=BORDER, activeforeground=CYAN,
                        relief="flat", cursor="hand2", padx=14, pady=9, width=9)
        btn.grid(row=row, column=3, padx=4, pady=16)
        step_btns.append(btn)
        sl = tk.Label(tbl, text="○ READY", font=("Courier", 12), fg=TXT3, bg=BG,
                      width=14, anchor="w")
        sl.grid(row=row, column=4, padx=4, pady=16, sticky="w")
        step_labels.append(sl)
        btn.config(command=make_toggle(i))

    # ── Dual graph ────────────────────────────────────────────────────
    # Two side-by-side matplotlib plots embedded in the Tk window:
    #   ax1 – CAM-A and CAM-B signal quality (0–100%)
    #   ax2 – CAM-C and CAM-D signal quality (0–100%)
    # A dashed 70% reference line indicates minimum acceptable signal quality.
    tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=50, pady=(8, 0))
    gf = tk.Frame(root, bg=BG)
    gf.pack(fill="x", padx=50, pady=(4, 0))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.5))
    fig.patch.set_facecolor(PANEL)
    ax1.set_facecolor("#07071a"); ax2.set_facecolor("#07071a")
    ax1.set_title("CAM-A (North) & CAM-B (East)  —  Signal Quality %", color=ACCENT, fontsize=11,
                  fontweight="bold", pad=6, fontfamily="monospace")
    ax2.set_title("CAM-C (South) & CAM-D (West)  —  Signal Quality %", color=ACCENT, fontsize=11,
                  fontweight="bold", pad=6, fontfamily="monospace")
    for ax in [ax1, ax2]:
        ax.set_ylabel("%", color=TXT2, fontsize=10, fontfamily="monospace")
        ax.set_xlabel("Time (s)", color=TXT2, fontsize=10, fontfamily="monospace")
        ax.tick_params(colors=TXT2, labelsize=9)
        ax.set_ylim(0, 110)
        for sp in ax.spines.values():
            sp.set_edgecolor(BORDER)
    # Dashed 70% reference line indicating minimum acceptable signal quality
    ax1.axhline(70, color=GREEN, linewidth=0.6, linestyle="--", alpha=0.35,
                label="_nolegend_")
    ax2.axhline(70, color=GREEN, linewidth=0.6, linestyle="--", alpha=0.35,
                label="_nolegend_")

    # Live plot line objects for each camera; updated each tick via set_data()
    CAM_COLORS = [CYAN, GREEN, AMBER, ACCENT]
    (la,) = ax1.plot([], [], color=CAM_COLORS[0], linewidth=1.6, label="CAM-A")
    (lb,) = ax1.plot([], [], color=CAM_COLORS[1], linewidth=1.6, label="CAM-B")
    (lc,) = ax2.plot([], [], color=CAM_COLORS[2], linewidth=1.6, label="CAM-C")
    (ld,) = ax2.plot([], [], color=CAM_COLORS[3], linewidth=1.6, label="CAM-D")
    ax1.legend(facecolor=PANEL, edgecolor=BORDER, labelcolor=TXT2, fontsize=9, loc="upper left")
    ax2.legend(facecolor=PANEL, edgecolor=BORDER, labelcolor=TXT2, fontsize=9, loc="upper left")

    # Corner readout text objects showing latest value per camera
    ra = ax1.text(0.98, 0.96, "A: OFFLINE", transform=ax1.transAxes, ha="right", va="top",
                  color=CAM_COLORS[0], fontsize=10, fontweight="bold", fontfamily="monospace",
                  bbox=dict(facecolor="#07071a", edgecolor="none", alpha=0.85, pad=2))
    rb = ax1.text(0.98, 0.80, "B: OFFLINE", transform=ax1.transAxes, ha="right", va="top",
                  color=CAM_COLORS[1], fontsize=10, fontweight="bold", fontfamily="monospace",
                  bbox=dict(facecolor="#07071a", edgecolor="none", alpha=0.85, pad=2))
    rc = ax2.text(0.98, 0.96, "C: OFFLINE", transform=ax2.transAxes, ha="right", va="top",
                  color=CAM_COLORS[2], fontsize=10, fontweight="bold", fontfamily="monospace",
                  bbox=dict(facecolor="#07071a", edgecolor="none", alpha=0.85, pad=2))
    rd = ax2.text(0.98, 0.80, "D: OFFLINE", transform=ax2.transAxes, ha="right", va="top",
                  color=CAM_COLORS[3], fontsize=10, fontweight="bold", fontfamily="monospace",
                  bbox=dict(facecolor="#07071a", edgecolor="none", alpha=0.85, pad=2))
    fig.tight_layout(pad=1.2)
    cplot = FigureCanvasTkAgg(fig, master=gf)
    cplot.get_tk_widget().pack(fill="both", expand=True)

    def update_graph():
        """Advance the simulation by one tick and refresh the live plots and P&ID.

        Called every UPDATE_MS milliseconds via root.after. Appends new signal
        quality values to the per-camera rolling buffers, trims data outside the
        WINDOW_SECS window, redraws both axes, and color-codes the readout text.
        """
        tick[0] += 1
        t = tick[0] * (UPDATE_MS / 1000.0)
        # Sample signal quality for all four cameras
        for i in range(4):
            cam_t[i].append(t)
            cam_v[i].append(next_signal(i))
        # Trim data points outside the visible rolling window
        cutoff = t - WINDOW_SECS
        for i in range(4):
            while cam_t[i] and cam_t[i][0] < cutoff:
                cam_t[i].pop(0); cam_v[i].pop(0)

        # Push new data to plot lines
        la.set_data(cam_t[0], cam_v[0])
        lb.set_data(cam_t[1], cam_v[1])
        lc.set_data(cam_t[2], cam_v[2])
        ld.set_data(cam_t[3], cam_v[3])
        for ax in [ax1, ax2]:
            ax.set_xlim(max(0, t - WINDOW_SECS), max(WINDOW_SECS, t))

        # Update corner readout text with latest signal values
        cur = [cam_v[i][-1] if cam_v[i] else 0.0 for i in range(4)]
        if cameras_active[0]:
            def sig_color(v): return GREEN if v > 70 else (AMBER if v > 40 else DANGER)
            ra.set_text(f"A: {cur[0]:.0f}%"); ra.set_color(sig_color(cur[0]))
            rb.set_text(f"B: {cur[1]:.0f}%"); rb.set_color(sig_color(cur[1]))
            rc.set_text(f"C: {cur[2]:.0f}%"); rc.set_color(sig_color(cur[2]))
            rd.set_text(f"D: {cur[3]:.0f}%"); rd.set_color(sig_color(cur[3]))
        else:
            for r in [ra, rb, rc, rd]:
                r.set_text("OFFLINE"); r.set_color(DANGER)

        cplot.draw_idle()
        update_pid()
        root.after(UPDATE_MS, update_graph)

    # Kick off the recurring update loop
    root.after(UPDATE_MS, update_graph)

    tk.Button(root, text="◀  MAIN MENU", font=("Courier", 12, "bold"),
              bg=ABTN, fg=TXT2, activebackground=BORDER, activeforeground=TXT,
              relief="flat", cursor="hand2", padx=16, pady=9,
              command=lambda: return_to_main(root)
              ).place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

    root.mainloop()


if __name__ == "__main__":
    main()
