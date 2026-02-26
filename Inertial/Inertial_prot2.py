import tkinter as tk
from tkinter import filedialog, messagebox


class Inertial(tk.Tk):
    def __init__(self, name):
        super().__init__()

        self.title(name)
        self.geometry("800x420")

        self.path = None
        self.code = []

        menu = tk.Menu(self)
        self.config(menu=menu)

        files = tk.Menu(menu, tearoff=0)
        run = tk.Menu(menu, tearoff=0)

        menu.add_cascade(label="File", menu=files)
        menu.add_cascade(label="Run", menu=run)

        files.add_command(label="Open File", command=self.open_file)
        files.add_command(label="Save", command=self.save_file)

        frame = tk.Frame(self)
        frame.pack(expand=True, fill="both")

        scroll = tk.Scrollbar(frame)
        scroll.pack(side="right", fill="y")

        self.text = tk.Text(
            frame,
            undo=True,
            yscrollcommand=scroll.set,
            font=("Consolas", 12)
        )
        self.text.pack(side="left", expand=True, fill="both")

        scroll.config(command=self.text.yview)

    def load_file(self):
        content = "".join(self.code)
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )

        if not path:
            return

        try:
            with open(path, "r") as f:
                self.code = f.readlines()

            self.path = path
            self.load_file()

        except Exception as e:
            messagebox.showerror("Open Error", str(e))

    def save_file(self):
        if not self.path:
            messagebox.showwarning("No file", "Open a file first.")
            return

        try:
            content = self.text.get("1.0", "end-1c")
            with open(self.path, "w") as f:
                f.write(content)

        except Exception as e:
            messagebox.showerror("Save Error", str(e))


# ---------- run ----------
if __name__ == "__main__":
    app = Inertial("My Code Editor")
    app.mainloop()
