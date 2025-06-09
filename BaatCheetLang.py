import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import re

variables = {}
functions = {}
output_lines = []

def gui_print(*args):
    line = " ".join(str(a) for a in args)
    output_lines.append(line)

def eval_expr(expr):
    expr = expr.strip()
    def repl_var(match):
        var = match.group(0)
        if var in variables:
            return str(variables[var])
        else:
            raise Exception(f"Variable '{var}' not defined")
    expr = re.sub(r"[a-zA-Z_]\w*", repl_var, expr)
    try:
        return eval(expr)
    except Exception as e:
        raise Exception(f"Expression error: {e}")

def parse_assignment(line):
    m = re.match(r"Mujhe ek number chahiye jiska naam ho '(\w+)' aur value ho (.+)", line)
    if m:
        var_name, value_expr = m.group(1), m.group(2)
        val = eval_expr(value_expr)
        variables[var_name] = val
        return True
    return False

def parse_print(line):
    m = re.match(r"Mujhe batao '(.+)'", line)
    if m:
        text = m.group(1)
        for v in variables:
            text = text.replace(v, str(variables[v]))
        gui_print(text)
        return True
    m = re.match(r"Mujhe batao (\w+)", line)
    if m:
        var = m.group(1)
        if var in variables:
            gui_print(variables[var])
        else:
            gui_print(f"Variable '{var}' nahi mila")
        return True
    return False

def parse_condition(line):
    m = re.match(r"Agar '(\w+)' bada ho (.+) se toh", line)
    if m:
        var, val_expr = m.group(1), m.group(2)
        val = eval_expr(val_expr)
        return ('if', lambda: variables.get(var, 0) > val)
    m = re.match(r"Agar '(\w+)' chhota ho (.+) se toh", line)
    if m:
        var, val_expr = m.group(1), m.group(2)
        val = eval_expr(val_expr)
        return ('if', lambda: variables.get(var, 0) < val)
    m = re.match(r"Agar '(\w+)' barabar ho (.+) se toh", line)
    if m:
        var, val_expr = m.group(1), m.group(2)
        val = eval_expr(val_expr)
        return ('if', lambda: variables.get(var, 0) == val)
    return None

def parse_else(line):
    return line.strip() == "Nahi toh"

def parse_loop(line):
    m = re.match(r"Jab tak '(\w+)' chhota ho (.+) se", line)
    if m:
        var, val_expr = m.group(1), m.group(2)
        val = eval_expr(val_expr)
        return ('while', var, '<', val)
    m = re.match(r"Jab tak '(\w+)' bada ho (.+) se", line)
    if m:
        var, val_expr = m.group(1), m.group(2)
        val = eval_expr(val_expr)
        return ('while', var, '>', val)
    return None

def parse_function_def(lines, index):
    m = re.match(r"Function banaiye '(\w+)' jo (.*)", lines[index])
    if not m:
        return None, index
    fname = m.group(1)
    params_text = m.group(2).strip()
    params = []
    if "kisi ka" in params_text:
        params.append("naam")
    body = []
    i = index + 1
    while i < len(lines) and lines[i].strip() != "Khatam function":
        body.append(lines[i])
        i += 1
    functions[fname] = (params, body)
    return ('function', fname), i

def run_function(fname, args):
    if fname not in functions:
        gui_print(f"Function '{fname}' nahi mila")
        return
    params, body = functions[fname]
    backup_vars = variables.copy()
    for p, a in zip(params, args):
        variables[p] = a
    run_program(body)
    for p in params:
        variables.pop(p, None)
    for k in backup_vars:
        variables[k] = backup_vars[k]

def parse_function_call(line):
    m = re.match(r"Call karo '(\w+)' (.+)", line)
    if m:
        fname = m.group(1)
        arg_text = m.group(2).strip()
        arg_val = None
        if arg_text in variables:
            arg_val = variables[arg_text]
        else:
            arg_val = arg_text
        run_function(fname, [arg_val])
        return True
    return False

def run_program(lines):
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        func_def = parse_function_def(lines, i)
        if func_def:
            _, end_i = func_def
            i = end_i + 1
            continue

        try:
            if parse_assignment(line):
                i += 1
                continue
            if parse_print(line):
                i += 1
                continue
            if parse_function_call(line):
                i += 1
                continue

            cond = parse_condition(line)
            if cond:
                cond_type, cond_lambda = cond
                i += 1
                if cond_lambda():
                    if i < len(lines):
                        inner_line = lines[i].strip()
                        parse_assignment(inner_line) or parse_print(inner_line) or parse_function_call(inner_line)
                    i += 1
                    if i < len(lines) and parse_else(lines[i].strip()):
                        i += 2
                    continue
                else:
                    i += 1
                    if i < len(lines) and parse_else(lines[i].strip()):
                        i += 1
                        if i < len(lines):
                            inner_line = lines[i].strip()
                            parse_assignment(inner_line) or parse_print(inner_line) or parse_function_call(inner_line)
                        i += 1
                    else:
                        i += 1
                    continue

            loop = parse_loop(line)
            if loop:
                _, var, op, val = loop
                i += 1
                while True:
                    condition_met = False
                    if var in variables:
                        if op == '<':
                            condition_met = variables[var] < val
                        elif op == '>':
                            condition_met = variables[var] > val
                    if not condition_met:
                        break
                    body_line = lines[i].strip()
                    parse_assignment(body_line) or parse_print(body_line) or parse_function_call(body_line)
                    variables[var] += 1 if op == '<' else -1
                i += 1
                continue

            gui_print(f"Samajh nahi aaya: {line}")
            i += 1
        except Exception as e:
            gui_print(f"Error: {e}")
            i += 1

def run_code():
    global variables, functions, output_lines
    code = code_text.get("1.0", tk.END).strip()
    variables = {}
    functions = {}
    output_lines = []
    lines = code.split('\n')
    run_program(lines)
    output_text.config(state='normal')
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "\n".join(output_lines))
    output_text.config(state='disabled')

def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("BaatCheetLang files", "*.pranjit")])
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            code_text.delete("1.0", tk.END)
            code_text.insert(tk.END, content)
            messagebox.showinfo("File Loaded", f"File loaded successfully:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"File open karne mein error: {e}")

def save_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".pranjit", filetypes=[("BaatCheetLang files", "*.pranjit")])
    if file_path:
        try:
            content = code_text.get("1.0", tk.END)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("File Saved", f"File saved successfully:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"File save karne mein error: {e}")

def create_icon():
    # Create a simple unique icon (16x16) with colored squares using tkinter.PhotoImage
    icon = tk.PhotoImage(width=16, height=16)

    # Colors and pattern (simple chat bubble style icon)
    colors = {
        'b': "#2e86de",  # blue
        'w': "#ffffff",  # white
        'd': "#1b4f72",  # dark blue
    }

    pattern = [
        "................",
        ".......bb.......",
        ".....bbbbbb.....",
        "....bwwwwwwb....",
        "....bwwwwwwb....",
        "....bwwwwwwb....",
        "....bwwwwwwb....",
        "....bwwwwwwb....",
        "....bbbbbbbb....",
        "....b......b....",
        "....b..dd..b....",
        ".....b..b.b.....",
        "......bbb.......",
        "................",
        "................",
        "................"
    ]

    for y, row in enumerate(pattern):
        for x, ch in enumerate(row):
            if ch == 'b':
                icon.put(colors['b'], (x, y))
            elif ch == 'w':
                icon.put(colors['w'], (x, y))
            elif ch == 'd':
                icon.put(colors['d'], (x, y))
            else:
                # Transparent (default)
                pass
    return icon

root = tk.Tk()
root.title("BaatCheetLang Interpreter")
root.geometry("700x600")

# Set unique icon
icon = create_icon()
root.iconphoto(False, icon)

# Menu
menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Open .pranjit File", command=open_file)
file_menu.add_command(label="Save As .pranjit File", command=save_file)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)
root.config(menu=menu_bar)

# Code input box
code_label = tk.Label(root, text="Apna BaatCheetLang Code Yahan Likho:", font=("Helvetica", 12))
code_label.pack(pady=5)

code_text = scrolledtext.ScrolledText(root, height=20, font=("Consolas", 12))
code_text.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

# Run button
run_button = tk.Button(root, text="Run Code", command=run_code, bg="#4caf50", fg="white", font=("Helvetica", 14))
run_button.pack(pady=10)

# Output box
output_label = tk.Label(root, text="Output:", font=("Helvetica", 12))
output_label.pack(pady=5)

output_text = scrolledtext.ScrolledText(root, height=10, font=("Consolas", 12), state='disabled', bg="#f0f0f0")
output_text.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

root.mainloop()
