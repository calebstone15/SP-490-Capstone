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


def main():
    root = tk.Tk()
    root.title("ERPL Rocket Engine Test Fire Simulation")
    root.geometry("1280x720")
    root.configure(bg="#1a1a2e")
    root.resizable(True, True)
    root.minsize(800, 500)

    # ── Welcome Header ──────────────────────────────────────────────
    header_frame = tk.Frame(root, bg="#1a1a2e")
    header_frame.pack(pady=(80, 20), expand=True)

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
        text="Select your operator position.",
        font=("Helvetica", 18),
        fg="#ffffff",
        bg="#1a1a2e",
    )
    subtitle_label.pack(pady=(15, 0))

    # ── Operator Buttons ────────────────────────────────────────────
    button_frame = tk.Frame(root, bg="#1a1a2e")
    button_frame.pack(pady=40)

    for i in range(1, 9):
        row = (i - 1) // 4
        col = (i - 1) % 4

        btn = tk.Button(
            button_frame,
            text=f"Operator {i}",
            font=("Helvetica", 18, "bold"),
            width=16,
            height=3,
            bg="#16213e",
            fg="#e94560",
            activebackground="#0f3460",
            activeforeground="#e94560",
            relief="flat",
            cursor="hand2",
            command=lambda n=i: launch_operator(root, n),
        )
        btn.grid(row=row, column=col, padx=15, pady=12)

    root.mainloop()


if __name__ == "__main__":
    main()
