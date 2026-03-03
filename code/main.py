# Hello World

import tkinter as tk
import subprocess
import sys
import os


def launch_operator(root, operator_number):
    """Launch the corresponding operator file and close the main window."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    operator_file = os.path.join(
        script_dir, "operators", f"operator{operator_number}.py"
    )
    subprocess.Popen([sys.executable, operator_file])
    root.destroy()


def on_enter(btn, border_frame):
    btn.config(bg="#0f3460")
    border_frame.config(bg="#e94560")


def on_leave(btn, border_frame):
    btn.config(bg="#16213e")
    border_frame.config(bg="#2a2a4a")


def main():
    root = tk.Tk()
    root.title("ERPL Rocket Engine Test Fire Simulation")
    root.geometry("1280x720")
    root.configure(bg="#1a1a2e")
    root.resizable(True, True)
    root.minsize(800, 500)

    # ── Welcome Header ──────────────────────────────────────────────
    header_frame = tk.Frame(root, bg="#1a1a2e")
    header_frame.pack(pady=(55, 10))

    title_label = tk.Label(
        header_frame,
        text="Welcome to the ERPL\nRocket Engine Test Fire Simulation",
        font=("Helvetica", 32, "bold"),
        fg="#e94560",
        bg="#1a1a2e",
        justify="center",
    )
    title_label.pack()

    subtitle_label = tk.Label(
        header_frame,
        text="Select your operator position to begin.",
        font=("Helvetica", 16),
        fg="#aaaacc",
        bg="#1a1a2e",
    )
    subtitle_label.pack(pady=(12, 0))

    # ── Separator ───────────────────────────────────────────────────
    tk.Frame(root, bg="#e94560", height=2).pack(fill="x", padx=120, pady=(18, 0))

    # ── Operator Buttons ────────────────────────────────────────────
    button_frame = tk.Frame(root, bg="#1a1a2e")
    button_frame.pack(pady=32)

    for i in range(1, 9):
        row = (i - 1) // 4
        col = (i - 1) % 4

        # Colored border frame gives a subtle highlight around each button
        border_frame = tk.Frame(button_frame, bg="#2a2a4a", padx=2, pady=2)
        border_frame.grid(row=row, column=col, padx=12, pady=10)

        btn = tk.Button(
            border_frame,
            text=f"Operator {i}",
            font=("Helvetica", 16, "bold"),
            width=14,
            height=3,
            bg="#16213e",
            fg="#e94560",
            activebackground="#0f3460",
            activeforeground="#e94560",
            relief="flat",
            cursor="hand2",
            command=lambda n=i: launch_operator(root, n),
        )
        btn.pack()

        btn.bind("<Enter>", lambda _, b=btn, f=border_frame: on_enter(b, f))
        btn.bind("<Leave>", lambda _, b=btn, f=border_frame: on_leave(b, f))

    # ── Footer ──────────────────────────────────────────────────────
    tk.Label(
        root,
        text="ERPL Simulation  \u2022  v1.0  \u2022  Capstone 2026",
        font=("Helvetica", 10),
        fg="#555577",
        bg="#1a1a2e",
    ).pack(side="bottom", pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
