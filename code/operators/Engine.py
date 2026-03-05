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


def return_to_main(root):
    """Close this window and relaunch the main menu."""
    main_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "main.py"
    )
    subprocess.Popen([sys.executable, main_file])
    root.destroy()


def main():
    root = tk.Tk()
    root.title("Engine")
    root.geometry("1280x720")
    root.configure(bg="#1a1a2e")
    root.resizable(True, True)
    root.minsize(800, 500)

    label = tk.Label(
        root,
        text="Engine",
        font=("Helvetica", 32, "bold"),
        fg="#e94560",
        bg="#1a1a2e",
    )
    label.pack(pady=(40, 10))

    # ── Step definitions: (timestamp, label, description) ───────────
    steps = [
        ("0:02:00", "Activate Pyrograin",          "Igniter for the engine"),
        ("0:01:45", "Open Run Valves (PB4 + PB8)", "Run valves — puts prop into the engine"),
        ("0:01:25", "Confirm Nominal Shutdown",     "Confirms no anomaly for engine shutdown"),
    ]

    # Track state for each step: False = READY, True = ACTIVATED
    step_states = [False] * len(steps)
    step_btns   = []
    step_labels = []

    container = tk.Frame(root, bg="#1a1a2e")
    container.pack(pady=20, padx=60, fill="x")

    # Column headers
    for col, (text, width) in enumerate([
        ("TIME",        8),
        ("STEP",        28),
        ("DESCRIPTION", 38),
        ("ACTION",      18),
        ("STATUS",      12),
    ]):
        tk.Label(
            container,
            text=text,
            font=("Helvetica", 11, "bold"),
            fg="#e94560",
            bg="#1a1a2e",
            width=width,
            anchor="w",
        ).grid(row=0, column=col, padx=6, pady=(0, 8), sticky="w")

    # ── Pyro temperature simulation state ───────────────────────────
    IDLE_TEMP    = 80.0
    PEAK_TEMP    = 2285.0
    WINDOW_SECS  = 30          # seconds of history shown
    UPDATE_MS    = 50          # ms between data points

    pyro_active        = [False]
    activation_tick    = [None]  # tick index when pyrograin was fired
    valves_active      = [False]
    valve_open_tick    = [None]  # tick index when run valves opened
    valve_close_tick   = [None]  # tick index when run valves closed
    cooling_down       = [False]
    cooldown_tick      = [None]  # tick index when cooldown began
    cooldown_start_temp = [IDLE_TEMP]
    temp_times         = []
    temp_values        = []
    tick_counter       = [0]

    VALVE_SPIKE      = 480.0   # extra °F added during combustion
    CHAMBER_STEADY   = 350.0   # PSI at nominal burn
    chamber_times    = []
    chamber_values   = []
    valve_close_pres = [0.0]   # chamber pressure captured at valve close

    def next_chamber_pressure():
        tick = tick_counter[0]
        # true idle — never opened
        if valve_open_tick[0] is None:
            return max(0.0, random.gauss(0, 0.3))
        # active burn
        if valves_active[0]:
            vdt = (tick - valve_open_tick[0]) * (UPDATE_MS / 1000.0)
            # Phase 1 (0–0.35 s): rapid rise to slight overshoot
            # Phase 2 (0.35–1.1 s): characteristic startup dip
            # Phase 3 (1.1–2.8 s): recovery to steady state
            # Phase 4 (2.8 s+):    hold with noise
            P1, P2, P3 = 0.35, 1.1, 2.8
            PEAK = CHAMBER_STEADY * 1.04
            DIP  = CHAMBER_STEADY * 0.38
            if vdt <= P1:
                p = PEAK * (vdt / P1)
            elif vdt <= P2:
                t = (vdt - P1) / (P2 - P1)
                p = PEAK + (DIP - PEAK) * t
            elif vdt <= P3:
                t = (vdt - P2) / (P3 - P2)
                p = DIP + (CHAMBER_STEADY - DIP) * (1 - math.exp(-3.0 * t))
            else:
                p = CHAMBER_STEADY
            return max(0.0, p + random.gauss(0, 14))
        # valves closed — exponential decay from captured pressure
        if valve_close_tick[0] is not None:
            cdt = (tick - valve_close_tick[0]) * (UPDATE_MS / 1000.0)
            p = valve_close_pres[0] * math.exp(-2.2 * cdt)
            return max(0.0, p + random.gauss(0, max(0.3, 6 * math.exp(-cdt))))
        return max(0.0, random.gauss(0, 0.3))

    def next_temp():
        tick = tick_counter[0]
        if not pyro_active[0]:
            return IDLE_TEMP + random.gauss(0, 0.6)

        # base pyro temperature — cooling overrides the rise curve after valves close
        dt = (tick - activation_tick[0]) * (UPDATE_MS / 1000.0)
        noise_scale = 8 + 30 * math.exp(-dt * 0.12)
        if cooling_down[0] and cooldown_tick[0] is not None:
            cdt = (tick - cooldown_tick[0]) * (UPDATE_MS / 1000.0)
            base = IDLE_TEMP + (cooldown_start_temp[0] - IDLE_TEMP) * math.exp(-0.22 * cdt)
            base += random.gauss(0, max(0.6, 12 * math.exp(-cdt * 0.6)))
        else:
            rise = PEAK_TEMP / (1 + math.exp(-0.49 * (dt - 6.0)))
            base = rise + random.gauss(0, noise_scale)

        # combustion spike from run valves
        spike = 0.0
        if valves_active[0] and valve_open_tick[0] is not None:
            vdt = (tick - valve_open_tick[0]) * (UPDATE_MS / 1000.0)
            spike = VALVE_SPIKE / (1 + math.exp(-3.5 * (vdt - 0.8)))
            spike += random.gauss(0, 18)
        elif not valves_active[0] and valve_close_tick[0] is not None:
            cdt = (tick - valve_close_tick[0]) * (UPDATE_MS / 1000.0)
            spike = VALVE_SPIKE * math.exp(-0.9 * cdt) + random.gauss(0, max(1, 12 * math.exp(-cdt)))

        return max(IDLE_TEMP, base + spike)

    # ── Embed matplotlib graph ───────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 2.0))
    fig.patch.set_facecolor("#16213e")
    ax.set_facecolor("#0f3460")
    ax.set_title("Pyro Temperature", color="#e94560", fontsize=11, fontweight="bold", pad=6)
    ax.set_ylabel("°F", color="#cccccc", fontsize=9)
    ax.set_xlabel("Time (s)", color="#cccccc", fontsize=9)
    ax.tick_params(colors="#cccccc", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#334466")
    ax.set_ylim(0, 200)   # initial idle range; updated dynamically each tick
    ax.axhline(IDLE_TEMP, color="#446688", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.axhline(PEAK_TEMP, color="#e94560", linewidth=0.8, linestyle="--", alpha=0.4)
    (line,) = ax.plot([], [], color="#00ccff", linewidth=1.5)
    temp_readout = ax.text(
        0.99, 0.92, f"{IDLE_TEMP:.0f} °F",
        transform=ax.transAxes, ha="right", va="top",
        color="#00ccff", fontsize=10, fontweight="bold",
        bbox=dict(facecolor="#0f3460", edgecolor="none", alpha=0.7, pad=2),
    )
    fig.tight_layout(pad=1.2)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(pady=(0, 4), padx=60, fill="x")

    # ── Chamber pressure graph ───────────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(9, 2.0))
    fig2.patch.set_facecolor("#16213e")
    ax2.set_facecolor("#0f3460")
    ax2.set_title("Chamber Pressure", color="#e94560", fontsize=11, fontweight="bold", pad=6)
    ax2.set_ylabel("PSI", color="#cccccc", fontsize=9)
    ax2.set_xlabel("Time (s)", color="#cccccc", fontsize=9)
    ax2.tick_params(colors="#cccccc", labelsize=8)
    for spine in ax2.spines.values():
        spine.set_edgecolor("#334466")
    ax2.set_ylim(0, 50)
    ax2.axhline(CHAMBER_STEADY, color="#e94560", linewidth=0.8, linestyle="--", alpha=0.4)
    (line2,) = ax2.plot([], [], color="#00ff88", linewidth=1.5)
    pres_readout = ax2.text(
        0.99, 0.92, "0 PSI",
        transform=ax2.transAxes, ha="right", va="top",
        color="#00ff88", fontsize=10, fontweight="bold",
        bbox=dict(facecolor="#0f3460", edgecolor="none", alpha=0.7, pad=2),
    )
    fig2.tight_layout(pad=1.2)

    canvas2 = FigureCanvasTkAgg(fig2, master=root)
    canvas2.get_tk_widget().pack(pady=(0, 10), padx=60, fill="x")

    def update_graph():
        tick_counter[0] += 1
        t = tick_counter[0] * (UPDATE_MS / 1000.0)

        # ── temperature ──
        temp_times.append(t)
        temp_values.append(next_temp())
        cutoff = t - WINDOW_SECS
        while temp_times and temp_times[0] < cutoff:
            temp_times.pop(0)
            temp_values.pop(0)
        line.set_data(temp_times, temp_values)
        ax.set_xlim(max(0, t - WINDOW_SECS), max(WINDOW_SECS, t))
        if len(temp_values) > 1:
            ymin = min(temp_values)
            ymax = max(temp_values)
            pad  = max(30, (ymax - ymin) * 0.12)
            ax.set_ylim(ymin - pad, ymax + pad)
        current_temp = temp_values[-1] if temp_values else IDLE_TEMP
        temp_color = "#ff4444" if current_temp > 500 else "#00ccff"
        temp_readout.set_text(f"{current_temp:.0f} °F")
        temp_readout.set_color(temp_color)
        line.set_color(temp_color)
        canvas.draw_idle()

        # ── chamber pressure ──
        chamber_times.append(t)
        chamber_values.append(next_chamber_pressure())
        while chamber_times and chamber_times[0] < cutoff:
            chamber_times.pop(0)
            chamber_values.pop(0)
        line2.set_data(chamber_times, chamber_values)
        ax2.set_xlim(max(0, t - WINDOW_SECS), max(WINDOW_SECS, t))
        if len(chamber_values) > 1:
            ymin2 = min(chamber_values)
            ymax2 = max(chamber_values)
            pad2  = max(10, (ymax2 - ymin2) * 0.12)
            ax2.set_ylim(ymin2 - pad2, ymax2 + pad2)
        current_pres = chamber_values[-1] if chamber_values else 0.0
        pres_readout.set_text(f"{current_pres:.0f} PSI")
        canvas2.draw_idle()

        root.after(UPDATE_MS, update_graph)

    root.after(UPDATE_MS, update_graph)

    def start_cooldown():
        cooling_down[0]        = True
        cooldown_tick[0]       = tick_counter[0]
        cooldown_start_temp[0] = temp_values[-1] if temp_values else PEAK_TEMP

    def deactivate_valves():
        """Auto-called after 5-second burn to close run valves."""
        if not step_states[1]:
            return  # already closed manually
        step_states[1] = False
        step_btns[1].config(text="ACTIVATE", bg="#16213e", fg="#000000", activebackground="#0f3460")
        step_labels[1].config(text="CLOSED", fg="#ff8800")
        valves_active[0]     = False
        valve_close_tick[0]  = tick_counter[0]
        valve_close_pres[0]  = chamber_values[-1] if chamber_values else 0.0
        start_cooldown()

    def make_toggle(idx):
        def toggle():
            step_states[idx] = not step_states[idx]
            if step_states[idx]:
                step_btns[idx].config(
                    text="UNDO",
                    bg="#0f3460",
                    fg="#e94560",
                    activebackground="#16213e",
                )
                step_labels[idx].config(text="ACTIVATED", fg="#00ff88")
                if idx == 0:   # Activate Pyrograin
                    pyro_active[0]     = True
                    activation_tick[0] = tick_counter[0]
                elif idx == 1:  # Open Run Valves — auto-close after 5 s
                    valves_active[0]    = True
                    valve_open_tick[0]  = tick_counter[0]
                    valve_close_tick[0] = None
                    root.after(5000, deactivate_valves)
            else:
                step_btns[idx].config(
                    text="ACTIVATE",
                    bg="#16213e",
                    fg="#000000",
                    activebackground="#0f3460",
                )
                step_labels[idx].config(text="READY", fg="#aaaaaa")
                if idx == 0:
                    pyro_active[0] = False
                elif idx == 1:
                    valves_active[0]    = False
                    valve_close_tick[0] = tick_counter[0]
                    valve_close_pres[0] = chamber_values[-1] if chamber_values else 0.0
                    start_cooldown()
        return toggle

    for i, (ts, name, desc) in enumerate(steps):
        row = i + 1
        tk.Label(container, text=ts,   font=("Helvetica", 12), fg="#cccccc", bg="#1a1a2e", width=8,  anchor="w").grid(row=row, column=0, padx=6, pady=8, sticky="w")
        tk.Label(container, text=name, font=("Helvetica", 12), fg="#ffffff", bg="#1a1a2e", width=28, anchor="w").grid(row=row, column=1, padx=6, pady=8, sticky="w")
        tk.Label(container, text=desc, font=("Helvetica", 12), fg="#aaaaaa", bg="#1a1a2e", width=38, anchor="w").grid(row=row, column=2, padx=6, pady=8, sticky="w")

        btn = tk.Button(
            container,
            text="ACTIVATE",
            font=("Helvetica", 11, "bold"),
            bg="#16213e",
            fg="#000000",
            activebackground="#0f3460",
            activeforeground="#000000",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            width=10,
        )
        btn.grid(row=row, column=3, padx=6, pady=8)
        step_btns.append(btn)

        status_lbl = tk.Label(
            container,
            text="READY",
            font=("Helvetica", 11, "bold"),
            fg="#aaaaaa",
            bg="#1a1a2e",
            width=12,
            anchor="w",
        )
        status_lbl.grid(row=row, column=4, padx=6, pady=8, sticky="w")
        step_labels.append(status_lbl)

        btn.config(command=make_toggle(i))

    # ── Return to Main Button (bottom-right) ────────────────────────
    back_btn = tk.Button(
        root,
        text="Return to Main",
        font=("Helvetica", 14, "bold"),
        bg="#16213e",
        fg="#e94560",
        activebackground="#0f3460",
        activeforeground="#e94560",
        relief="flat",
        cursor="hand2",
        padx=20,
        pady=10,
        command=lambda: return_to_main(root),
    )
    back_btn.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)

    root.mainloop()


if __name__ == "__main__":
    main()
