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

BG      = "#0d0d1a"; PANEL  = "#111128"; BORDER = "#1a1d3a"
ACCENT  = "#e94560"; ABTN   = "#0f1535"; CYAN   = "#00d4ff"
GREEN   = "#00e676"; AMBER  = "#ffab40"; DANGER = "#ff5252"
TXT     = "#e8eaf6"; TXT2   = "#7986cb"; TXT3   = "#8898c8"
PID_BG  = "#07071a"; PIPE_OFF = "#1a1d3a"; PIPE_ON = "#00d4ff"
V_OFF   = "#2a2d4a"; V_ON   = "#00e676"; V_WARN  = "#ffab40"; V_CLOSE = "#ff5252"
RED_HOT = "#ff6030"


def return_to_main(root):
    main_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "main.py")
    subprocess.Popen([sys.executable, main_file])
    root.destroy()


def diamond(c, x, y, s=11, fill=None):
    f = fill or V_OFF
    pts = [x, y - s, x + s, y, x, y + s, x - s, y]
    return c.create_polygon(pts, fill=f, outline="#3a3d6a", width=1.5)


def sensor_circle(c, x, y, lbl, r=11):
    item = c.create_oval(x - r, y - r, x + r, y + r, fill=ABTN, outline="#3a3d6a", width=1.2)
    c.create_text(x, y, text=lbl, fill=TXT2, font=("Courier", 9, "bold"))
    return item


def main():
    root = tk.Tk()
    root.title("Engine — Ignition & Combustion")
    root.geometry("1440x960")
    root.configure(bg=BG)
    root.resizable(True, True)
    root.minsize(1050, 780)

    # ── Header ────────────────────────────────────────────────────────
    hdr = tk.Frame(root, bg=BG)
    hdr.pack(fill="x", padx=50, pady=(18, 0))
    badge = tk.Frame(hdr, bg=ACCENT, padx=12, pady=9)
    badge.pack(side="left", anchor="n", padx=(0, 16))
    tk.Label(badge, text="ENG", font=("Helvetica", 14, "bold"), fg=TXT, bg=ACCENT).pack()
    tk.Label(badge, text="IGN", font=("Courier", 9, "bold"), fg="#ffa0b0", bg=ACCENT).pack()
    info = tk.Frame(hdr, bg=BG)
    info.pack(side="left")
    tk.Label(info, text="Engine", font=("Helvetica", 30, "bold"), fg=TXT, bg=BG).pack(anchor="w")
    tk.Label(info, text="Ignition & Combustion  ·  Components: Pyrograin · PB4 (LOX RV) · PB8 (Fuel RV)",
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
    steps = [
        ("0:02:00", "ACTIVATE PYROGRAIN",           "Igniter for the engine"),
        ("0:01:45", "OPEN RUN VALVES  PB4 + PB8",   "Run valves"),
        ("0:01:25", "CONFIRM NOMINAL SHUTDOWN",      "Confirm no anomaly for engine shutdown"),
        ("+0:30  ", "VERIFY Pc, LOX & FUEL ~0 PSI", "Post-test manifold pressure confirmed safe"),
    ]
    step_states = [False] * len(steps)
    step_btns   = []
    step_labels = []

    tk.Label(left, text="COUNTDOWN CHECKLIST", font=("Courier", 14, "bold"),
             fg=TXT2, bg=BG).pack(anchor="w", pady=(0, 8))
    tbl = tk.Frame(left, bg=BG)
    tbl.pack(fill="x")
    for col, (txt, w) in enumerate([("TIME", 8), ("STEP", 30), ("DESCRIPTION", 34),
                                     ("ACTION", 10), ("STATUS", 12)]):
        tk.Label(tbl, text=txt, font=("Courier", 12, "bold"), fg=TXT3,
                 bg=BG, width=w, anchor="w").grid(row=0, column=col, padx=4, pady=(0, 4), sticky="w")
    tk.Frame(tbl, bg=BORDER, height=1).grid(row=1, column=0, columnspan=5,
                                             sticky="ew", pady=(0, 6))

    # ── Physics state ─────────────────────────────────────────────────
    UPDATE_MS    = 50
    WINDOW_SECS  = 30
    tick         = [0]
    IDLE_TEMP    = 80.0
    PEAK_TEMP    = 2285.0
    CHAMBER_STEADY = 350.0

    pyro_active       = [False]; pyro_tick     = [None]
    valves_active     = [False]; valve_open_tick = [None]; valve_close_tick = [None]
    cooling_down      = [False]; cooldown_tick = [None]; cooldown_start_temp = [IDLE_TEMP]
    valve_close_pres  = [0.0]

    temp_t = []; temp_v = []; pres_t = []; pres_v = []

    def next_chamber_pressure():
        t = tick[0]
        if pyro_active[0] and valve_open_tick[0] is None and pyro_tick[0] is not None:
            dt = (t - pyro_tick[0]) * (UPDATE_MS / 1000.0)
            blip = 22 * (1 - math.exp(-8 * dt)) * math.exp(-1.5 * dt)
            return max(0.0, blip + random.gauss(0, 0.5))
        if valve_open_tick[0] is None:
            return max(0.0, random.gauss(0, 0.3))
        if valves_active[0]:
            vdt = (t - valve_open_tick[0]) * (UPDATE_MS / 1000.0)
            P1, P2, P3 = 0.35, 1.1, 2.8; PEAK = CHAMBER_STEADY * 1.04; DIP = CHAMBER_STEADY * 0.38
            if vdt <= P1:   p = PEAK * (vdt / P1)
            elif vdt <= P2: p = PEAK + (DIP - PEAK) * ((vdt - P1) / (P2 - P1))
            elif vdt <= P3: p = DIP + (CHAMBER_STEADY - DIP) * (1 - math.exp(-3.0 * ((vdt - P2) / (P3 - P2))))
            else:           p = CHAMBER_STEADY
            p += 8 * math.sin(2 * math.pi * 1.2 * vdt) + 3 * math.sin(2 * math.pi * 2.8 * vdt)
            p += random.gauss(0, 14)
            if random.random() < 0.005: p += random.uniform(15, 40)
            return max(0.0, p)
        if valve_close_tick[0] is not None:
            cdt = (t - valve_close_tick[0]) * (UPDATE_MS / 1000.0)
            return max(0.0, valve_close_pres[0] * math.exp(-2.2 * cdt) +
                       48 * math.exp(-40 * cdt) + random.gauss(0, max(0.3, 6 * math.exp(-cdt))))
        return max(0.0, random.gauss(0, 0.3))

    def next_temp():
        t = tick[0]
        if not pyro_active[0]:
            return IDLE_TEMP + random.gauss(0, 0.6)
        dt = (t - pyro_tick[0]) * (UPDATE_MS / 1000.0)
        noise_scale = 8 + 30 * math.exp(-dt * 0.12)
        if cooling_down[0] and cooldown_tick[0] is not None:
            cdt = (t - cooldown_tick[0]) * (UPDATE_MS / 1000.0)
            base = IDLE_TEMP + (cooldown_start_temp[0] - IDLE_TEMP) * math.exp(-0.22 * cdt)
            base += random.gauss(0, max(0.6, 12 * math.exp(-cdt * 0.6)))
        else:
            flash    = 600 * (1 - math.exp(-5 * dt)) * math.exp(-dt)
            rise     = PEAK_TEMP / (1 + math.exp(-0.49 * (dt - 6.0)))
            overshoot= 80 * math.exp(-0.5 * (dt - 10)) * math.cos(0.6 * (dt - 10)) if dt > 8 else 0
            base     = rise + flash + overshoot + random.gauss(0, noise_scale)
        spike = 0.0
        if valves_active[0] and valve_open_tick[0] is not None:
            vdt = (t - valve_open_tick[0]) * (UPDATE_MS / 1000.0)
            P1, P2, P3 = 0.35, 1.1, 2.8
            if vdt <= P1:   pf = vdt / P1
            elif vdt <= P2: pf = 1.04 + (0.38 - 1.04) * ((vdt - P1) / (P2 - P1))
            elif vdt <= P3: pf = 0.38 + 0.62 * (1 - math.exp(-3.0 * ((vdt - P2) / (P3 - P2))))
            else:           pf = 1.0
            spike = 480.0 * max(0.1, pf) / (1 + math.exp(-3.5 * (vdt - 0.8))) + random.gauss(0, 18)
        elif not valves_active[0] and valve_close_tick[0] is not None:
            cdt = (t - valve_close_tick[0]) * (UPDATE_MS / 1000.0)
            spike = 480.0 * math.exp(-0.9 * cdt) + random.gauss(0, max(1, 12 * math.exp(-cdt)))
        result = max(IDLE_TEMP, base + spike)
        if random.random() < 0.005: result += random.uniform(15, 50)
        return result

    def start_cooldown():
        cooling_down[0] = True; cooldown_tick[0] = tick[0]
        cooldown_start_temp[0] = temp_v[-1] if temp_v else PEAK_TEMP

    def deactivate_valves():
        if not step_states[1]:
            return
        step_states[1] = False
        step_btns[1].config(text="EXECUTE", bg=ABTN, fg=CYAN, activebackground=BORDER)
        step_labels[1].config(text="● CLOSED", fg=AMBER)
        valves_active[0] = False; valve_close_tick[0] = tick[0]
        valve_close_pres[0] = pres_v[-1] if pres_v else 0.0
        start_cooldown()
        update_pid()

    # ── P&ID canvas ───────────────────────────────────────────────────
    tk.Label(right, text="P&ID — ENGINE IGNITION SYSTEM",
             font=("Courier", 12, "bold"), fg=TXT3, bg=BG).pack(anchor="w", pady=(2, 6))
    pid = tk.Canvas(right, width=550, height=370, bg=PID_BG,
                    highlightthickness=1, highlightbackground=BORDER)
    pid.pack(fill="both", expand=True)

    # LOX Tank (top-left)
    pid.create_rectangle(13, 13, 125, 81, fill=ABTN, outline="#2a3060", width=1.5)
    pid.create_text(69, 38, text="LOX", fill=CYAN, font=("Courier", 11, "bold"))
    pid.create_text(69, 58, text="TANK", fill=TXT2, font=("Courier", 10))

    # Fuel Tank (bottom-left)
    pid.create_rectangle(13, 163, 125, 231, fill=ABTN, outline="#2a3060", width=1.5)
    pid.create_text(69, 188, text="FUEL", fill=AMBER, font=("Courier", 11, "bold"))
    pid.create_text(69, 208, text="TANK", fill=TXT2, font=("Courier", 10))

    # PB4 on LOX line
    p_pipe_lox_a = pid.create_line(125, 48, 238, 48, fill=PIPE_OFF, width=3)
    p_pb4 = diamond(pid, 238, 48, s=15)
    pid.create_text(238, 69, text="PB4", fill=TXT2, font=("Courier", 11, "bold"), anchor="n")
    pid.create_text(238, 84, text="LOX RV", fill=TXT3, font=("Courier", 9), anchor="n")
    p_pipe_lox_b = pid.create_line(251, 48, 344, 48, fill=PIPE_OFF, width=3)

    # PB8 on Fuel line
    p_pipe_fuel_a = pid.create_line(125, 198, 238, 198, fill=PIPE_OFF, width=3)
    p_pb8 = diamond(pid, 238, 198, s=15)
    pid.create_text(238, 219, text="PB8", fill=TXT2, font=("Courier", 11, "bold"), anchor="n")
    pid.create_text(238, 234, text="FUEL RV", fill=TXT3, font=("Courier", 9), anchor="n")
    p_pipe_fuel_b = pid.create_line(251, 198, 344, 198, fill=PIPE_OFF, width=3)

    # Converge pipes into engine inlet manifold
    p_pipe_conv_l = pid.create_line(344, 48,  344, 125, fill=PIPE_OFF, width=3)
    p_pipe_conv_f = pid.create_line(344, 198, 344, 125, fill=PIPE_OFF, width=3)
    p_pipe_inlet  = pid.create_line(344, 125, 388, 125, fill=PIPE_OFF, width=3)

   #Engine body (Combustion chamber/throat)
    eng_pts = [
       419, 75, #top left
       469, 75, #top right
       469, 169, #bottom right curve start
       419, 169, #bottom right curve end
   ]

    p_engine_body = pid.create_polygon(eng_pts, fill="#1a2a10", outline="#3a3d6a", width=2)

    # Nozzle
    #Starts at the throat (140) and flares out significantly.
    noz_pts = [
        419, 169, #throat left
        469, 169, #throat right
        500, 250, #nozzle tip right
        388, 250, #nozzle tip left
    ]

    p_nozzle = pid.create_polygon(noz_pts, fill="#0f1a25", outline="#3a3d6a", width=2)

    #Text remains centered
    pid.create_text(444, 123, text="ENGINE", fill=TXT, font=("Courier", 17, "bold"))


    # Pyrograin symbol (star inside engine)
    p_pyro = pid.create_text(444, 145, text="✦", fill=V_OFF, font=("Helvetica", 22, "bold"))
    pid.create_text(444, 163, text="PYRO", fill=TXT3, font=("Courier", 9))

    # PT sensors on manifold
    p_pt5  = sensor_circle(pid, 375, 48,  "PT5",  r=10)
    p_pt15 = sensor_circle(pid, 375, 198, "PT15", r=10)
    pid.create_line(358, 48,  365, 48,  fill=TXT3, width=1, dash=(3, 3))
    pid.create_line(358, 198, 365, 198, fill=TXT3, width=1, dash=(3, 3))

    # Chamber pressure / temp sensors (below engine)
    p_pc  = sensor_circle(pid, 438, 269, "Pc",  r=11)
    p_tc  = sensor_circle(pid, 488, 269, "Tc",  r=11)
    pid.create_text(438, 285, text="PRESS", fill=TXT3, font=("Courier", 9))
    pid.create_text(488, 285, text="TEMP", fill=TXT3, font=("Courier", 9))

    # Live readouts below engine
    p_pc_val = pid.create_text(438, 300, text="0 PSI", fill=TXT3, font=("Courier", 10, "bold"))
    p_tc_val = pid.create_text(488, 300, text="80°F",  fill=TXT3, font=("Courier", 10, "bold"))

    # Legend
    pid.create_line(13, 350, 35, 350, fill=PIPE_ON, width=2)
    pid.create_text(40, 350, text="FLOW", fill=TXT3, font=("Courier", 9), anchor="w")
    pts = [103, 345, 110, 350, 103, 355, 95, 350]
    pid.create_polygon(pts, fill=V_ON, outline="#3a3d6a")
    pid.create_text(115, 350, text="OPEN", fill=TXT3, font=("Courier", 9), anchor="w")
    pts2 = [173, 345, 180, 350, 173, 355, 165, 350]
    pid.create_polygon(pts2, fill=V_WARN, outline="#3a3d6a")
    pid.create_text(185, 350, text="ACTIVE", fill=TXT3, font=("Courier", 9), anchor="w")

    def update_pid():
        pid.itemconfig(p_pb4, fill=V_ON   if valves_active[0] else V_OFF)
        pid.itemconfig(p_pb8, fill=V_ON   if valves_active[0] else V_OFF)
        pid.itemconfig(p_pyro,fill=V_WARN if pyro_active[0] else V_OFF)
        burning = valves_active[0] and pyro_active[0]
        flow_c = PIPE_ON if valves_active[0] else PIPE_OFF
        pid.itemconfig(p_pipe_lox_a,  fill=flow_c)
        pid.itemconfig(p_pipe_lox_b,  fill=flow_c)
        pid.itemconfig(p_pipe_fuel_a, fill=flow_c)
        pid.itemconfig(p_pipe_fuel_b, fill=flow_c)
        pid.itemconfig(p_pipe_conv_l, fill=flow_c)
        pid.itemconfig(p_pipe_conv_f, fill=flow_c)
        pid.itemconfig(p_pipe_inlet,  fill=flow_c)
        eng_color = "#1a2a10" if burning else "#0f1a25"
        pid.itemconfig(p_engine_body, fill=eng_color)
        pid.itemconfig(p_pt5,  fill=CYAN if pyro_active[0] else ABTN)
        pid.itemconfig(p_pt15, fill=CYAN if pyro_active[0] else ABTN)
        cur_p = pres_v[-1] if pres_v else 0.0
        cur_t = temp_v[-1] if temp_v else IDLE_TEMP
        p_color = DANGER if cur_p > 200 else (AMBER if cur_p > 50 else TXT3)
        t_color = RED_HOT if cur_t > 1000 else (AMBER if cur_t > 200 else TXT3)
        pid.itemconfig(p_pc,     fill=p_color)
        pid.itemconfig(p_tc,     fill=t_color)
        pid.itemconfig(p_pc_val, text=f"{cur_p:.0f} PSI", fill=p_color)
        pid.itemconfig(p_tc_val, text=f"{cur_t:.0f}°F",   fill=t_color)

    def make_toggle(idx):
        def toggle():
            step_states[idx] = not step_states[idx]
            if step_states[idx]:
                step_btns[idx].config(text="UNDO", bg="#1a0820", fg=ACCENT, activebackground=ABTN)
                step_labels[idx].config(text="● ACTIVE", fg=GREEN)
                if idx == 0:
                    pyro_active[0] = True; pyro_tick[0] = tick[0]
                elif idx == 1:
                    valves_active[0] = True; valve_open_tick[0] = tick[0]
                    valve_close_tick[0] = None
                    root.after(5000, deactivate_valves)
                elif idx == 3:
                    cur_p = pres_v[-1] if pres_v else 0.0
                    ok = cur_p < 5
                    step_labels[idx].config(text="● SAFE ✓" if ok else "● PRESS REMAIN",
                                            fg=GREEN if ok else DANGER)
            else:
                step_btns[idx].config(text="EXECUTE", bg=ABTN, fg=CYAN, activebackground=BORDER)
                step_labels[idx].config(text="○ READY", fg=TXT3)
                if idx == 0:
                    pyro_active[0] = False
                elif idx == 1:
                    valves_active[0] = False
                    valve_close_tick[0] = tick[0]
                    valve_close_pres[0] = pres_v[-1] if pres_v else 0.0
                    start_cooldown()
            update_pid()
        return toggle

    for i, (ts, name, desc) in enumerate(steps):
        row = i + 2
        tk.Label(tbl, text=ts, font=("Courier", 13), fg=TXT2, bg=BG,
                 width=8, anchor="w").grid(row=row, column=0, padx=4, pady=16, sticky="w")
        tk.Label(tbl, text=name, font=("Courier", 13, "bold"), fg=TXT, bg=BG,
                 width=30, anchor="w").grid(row=row, column=1, padx=4, pady=16, sticky="w")
        tk.Label(tbl, text=desc, font=("Helvetica", 13), fg=TXT2, bg=BG,
                 width=34, anchor="w").grid(row=row, column=2, padx=4, pady=16, sticky="w")
        btn = tk.Button(tbl, text="EXECUTE", font=("Courier", 12, "bold"),
                        bg=ABTN, fg=CYAN, activebackground=BORDER, activeforeground=CYAN,
                        relief="flat", cursor="hand2", padx=14, pady=9, width=9)
        btn.grid(row=row, column=3, padx=4, pady=16)
        step_btns.append(btn)
        sl = tk.Label(tbl, text="○ READY", font=("Courier", 12), fg=TXT3, bg=BG,
                      width=12, anchor="w")
        sl.grid(row=row, column=4, padx=4, pady=16, sticky="w")
        step_labels.append(sl)
        btn.config(command=make_toggle(i))

    # ── Dual graph ────────────────────────────────────────────────────
    tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=50, pady=(8, 0))
    gf = tk.Frame(root, bg=BG)
    gf.pack(fill="x", padx=50, pady=(4, 0))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 3.5))
    fig.patch.set_facecolor(PANEL)
    ax1.set_facecolor("#07071a"); ax2.set_facecolor("#07071a")
    ax1.set_title("Pyro / Chamber Temperature  —  Tc", color=ACCENT, fontsize=11,
                  fontweight="bold", pad=6, fontfamily="monospace")
    ax2.set_title("Chamber Pressure  —  Pc", color=ACCENT, fontsize=11,
                  fontweight="bold", pad=6, fontfamily="monospace")
    for ax, unit in [(ax1, "°F"), (ax2, "PSI")]:
        ax.set_ylabel(unit, color=TXT2, fontsize=10, fontfamily="monospace")
        ax.set_xlabel("Time (s)", color=TXT2, fontsize=10, fontfamily="monospace")
        ax.tick_params(colors=TXT2, labelsize=9)
        for sp in ax.spines.values():
            sp.set_edgecolor(BORDER)
    ax1.axhline(PEAK_TEMP, color=ACCENT, linewidth=0.6, linestyle="--", alpha=0.3)
    ax2.axhline(CHAMBER_STEADY, color=ACCENT, linewidth=0.8, linestyle="--", alpha=0.35)

    (lt,) = ax1.plot([], [], color=CYAN, linewidth=1.6)
    rt = ax1.text(0.98, 0.88, f"{IDLE_TEMP:.0f}°F", transform=ax1.transAxes, ha="right", va="top",
                  color=CYAN, fontsize=11, fontweight="bold", fontfamily="monospace",
                  bbox=dict(facecolor="#07071a", edgecolor="none", alpha=0.85, pad=2))
    (lp,) = ax2.plot([], [], color=GREEN, linewidth=1.6)
    rp = ax2.text(0.98, 0.88, "0 PSI", transform=ax2.transAxes, ha="right", va="top",
                  color=GREEN, fontsize=11, fontweight="bold", fontfamily="monospace",
                  bbox=dict(facecolor="#07071a", edgecolor="none", alpha=0.85, pad=2))
    fig.tight_layout(pad=1.2)
    cplot = FigureCanvasTkAgg(fig, master=gf)
    cplot.get_tk_widget().pack(fill="both", expand=True)

    def update_graph():
        tick[0] += 1
        t = tick[0] * (UPDATE_MS / 1000.0)
        temp_t.append(t); temp_v.append(next_temp())
        pres_t.append(t); pres_v.append(next_chamber_pressure())
        cutoff = t - WINDOW_SECS
        while temp_t and temp_t[0] < cutoff:
            temp_t.pop(0); temp_v.pop(0)
        while pres_t and pres_t[0] < cutoff:
            pres_t.pop(0); pres_v.pop(0)

        lt.set_data(temp_t, temp_v)
        ax1.set_xlim(max(0, t - WINDOW_SECS), max(WINDOW_SECS, t))
        if len(temp_v) > 1:
            mn, mx = min(temp_v), max(temp_v)
            ax1.set_ylim(mn - max(30, (mx-mn)*0.12), mx + max(30, (mx-mn)*0.12))
        cur_t = temp_v[-1] if temp_v else IDLE_TEMP
        tc = DANGER if cur_t > 1000 else (AMBER if cur_t > 200 else CYAN)
        rt.set_text(f"{cur_t:.0f}°F"); rt.set_color(tc); lt.set_color(tc)

        lp.set_data(pres_t, pres_v)
        ax2.set_xlim(max(0, t - WINDOW_SECS), max(WINDOW_SECS, t))
        if len(pres_v) > 1:
            mn, mx = min(pres_v), max(pres_v)
            ax2.set_ylim(mn - max(10, (mx-mn)*0.12), mx + max(10, (mx-mn)*0.12))
        cur_p = pres_v[-1] if pres_v else 0.0
        pc = DANGER if cur_p > 300 else GREEN
        rp.set_text(f"{cur_p:.0f} PSI"); rp.set_color(pc)
        cplot.draw_idle()
        update_pid()
        root.after(UPDATE_MS, update_graph)

    root.after(UPDATE_MS, update_graph)

    tk.Button(root, text="◀  MAIN MENU", font=("Courier", 12, "bold"),
              bg=ABTN, fg=TXT2, activebackground=BORDER, activeforeground=TXT,
              relief="flat", cursor="hand2", padx=16, pady=9,
              command=lambda: return_to_main(root)
              ).place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

    root.mainloop()


if __name__ == "__main__":
    main()
