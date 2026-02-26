import tkinter as tk
from tkinter import filedialog
import sys
import io

root = tk.Tk()
root.withdraw()
"""
This is the rather clunky attempt to create a terminal based vrsion of calliope, INERTIAL,
before i realised that python, though powerful, was woefully incapable of editing terminals in my deired way.
I have kept it in case the terminal wiping and the original run function would be useful along the line.
"""
def run(script_lines: list[str], input_provider: callable |None = None):
    """
    Runs a Python script provided as a list of lines.
    Redirects print output, handles input calls, and captures exceptions.

    :param script_lines: List of strings containing Python code lines
    :param input_provider: Function that provides input when input() is called
    :return: A tuple (output, error)
    """
    
    script_code = "\n".join(script_lines)
    output_buffer = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdin = sys.__stdin__ 
    sys.stdout = output_buffer

    def custom_input(prompt=""):
        sys.stdout = sys_stdout 
        user_input = input_provider(prompt) if input_provider else input(prompt)
        sys.stdout = output_buffer
        return user_input

    exec_globals = {"input": custom_input, "__builtins__": __builtins__}
    error = None
    """
    code_str = "".join(code_lines)
    namespace = {}
    errors = []
    try:
        exec(code_str, {}, namespace)
    except Exception as e:
        errors.append(str(e))
    return errors, namespace
    """
    try:
        exec(script_code, exec_globals)
    except Exception as e:
        error = str(e)

    sys.stdout = sys_stdout

    return output_buffer.getvalue(), error

def clear(old:int ,new: list[str]) -> None:
    for i in range(old):
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")

    for i in new:
        print(i)
def display_lines() -> None:
    path = filedialog.askopenfilename(
    title="Open Python File",
    filetypes=[("Python files", "*.py"), ("All files", "*.*")])

    try:
        with open(path, "r") as f:
            lines = f.readlines()

        max_num_width = len(str(len(lines)))

        for i, line in enumerate(lines, start=1):
            print(f"{str(i).rjust(max_num_width)} | {line.rstrip()}")

    except Exception as e:
        print(f"Error: {e}")