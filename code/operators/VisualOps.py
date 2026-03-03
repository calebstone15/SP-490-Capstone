import tkinter as tk
import subprocess
import sys
import os


def return_to_main(root):
    """Close this window and relaunch the main menu."""
    main_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "main.py"
    )
    subprocess.Popen([sys.executable, main_file])
    root.destroy()


def main():
    root = tk.Tk()
    root.title("Operator 8")
    root.geometry("1280x720")
    root.configure(bg="#1a1a2e")
    root.resizable(True, True)
    root.minsize(800, 500)

    label = tk.Label(
        root,
        text="Operator 8",
        font=("Helvetica", 32, "bold"),
        fg="#e94560",
        bg="#1a1a2e",
    )
    label.pack(pady=(80, 10))

    info_label = tk.Label(
        root,
        text="Operator 8 station is active.\nAwaiting further implementation.",
        font=("Helvetica", 16),
        fg="#ffffff",
        bg="#1a1a2e",
        justify="center",
    )
    info_label.pack(pady=20)

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
