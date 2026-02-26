from tkinter.filedialog import askopenfilename as dialog
import ast
from pathlib import Path
# ---------- C++ FILE WRAPPER ----------

def file_maker(lines: list[str]):
    output = []
    output.append("#include <iostream>")
    output.append("#include <string>")
    output.append("#include <cmath>")
    output.append("")
    output.append("int main() {")
    for line in lines:
        output.append("    " + line)
    output.append("    return 0;")
    output.append("}")
    return "\n".join(output)


# ---------- EXPRESSION TRANSLATION ----------

def translate_expr(node, declared_vars):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return f'"{node.value}"'
        return str(node.value)

    elif isinstance(node, ast.Name):
        if node.id not in declared_vars:
            raise NameError(f"Variable '{node.id}' used before assignment")
        return node.id

    elif isinstance(node, ast.BinOp):
        left = translate_expr(node.left, declared_vars)
        right = translate_expr(node.right, declared_vars)

        if isinstance(node.op, ast.Add):
            return f"{left} + {right}"
        elif isinstance(node.op, ast.Sub):
            return f"{left} - {right}"
        elif isinstance(node.op, ast.Mult):
            return f"{left} * {right}"
        elif isinstance(node.op, ast.Div):
            return f"{left} / {right}"
        elif isinstance(node.op, ast.Pow):
            return f"pow({left}, {right})"
        else:
            raise NotImplementedError(f"Operator {type(node.op)} not supported")

    raise NotImplementedError(f"Expression type {type(node)} not supported")


# ---------- TYPE INFERENCE ----------

def det_type(node, declared_vars):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int):
            return "int"
        elif isinstance(node.value, float):
            return "double"
        elif isinstance(node.value, str):
            return "std::string"

    elif isinstance(node, ast.Name):
        return declared_vars[node.id]

    elif isinstance(node, ast.BinOp):
        left_type = det_type(node.left, declared_vars)
        right_type = det_type(node.right, declared_vars)

        if left_type == "double" or right_type == "double":
            return "double"
        return left_type

    raise NotImplementedError(f"Cannot infer type for {type(node)}")


# ---------- STATEMENT TRANSLATION ----------

def translate(node, declared_vars):

    # Assignment
    if isinstance(node, ast.Assign):
        var_name = node.targets[0].id
        value_node = node.value

        value_code = translate_expr(value_node, declared_vars)

        if var_name not in declared_vars:
            var_type = det_type(value_node, declared_vars)
            declared_vars[var_name] = var_type
            return f"{var_type} {var_name} = {value_code};"
        else:
            return f"{var_name} = {value_code};"

    # Print
    elif isinstance(node, ast.Expr):
        if isinstance(node.value, ast.Call):
            call = node.value

            if isinstance(call.func, ast.Name) and call.func.id == "print":
                parts = []
                for arg in call.args:
                    parts.append(translate_expr(arg, declared_vars))

                joined = ' << " " << '.join(parts)
                return f"std::cout << {joined} << std::endl;"

    raise NotImplementedError(f"Unsupported statement: {type(node)}")


# ---------- MAIN ----------

def main():
    path = dialog(
        title="Open File",
        filetypes=[("Python files", "*.py"), ("All files", "*.*")]
    )
    if not path:
        return  # user cancelled

    p = Path(path)

    filename = p.stem          # name without extension
    cpp_path = p.with_suffix(".cpp")  # same folder, .cpp extension


    with open(path, "r") as f:
        tree = ast.parse(f.read())

    declared_vars = {}
    cpp_lines = []

    for node in tree.body:
        line = translate(node, declared_vars)
        cpp_lines.append(line)

    final_code = file_maker(cpp_lines)

    print("\n--- Generated C++ ---\n")
    
    with open(cpp_path,"w") as f:
        f.write(final_code)

    print(f"\nSaved to: {cpp_path}")


if __name__ == "__main__":
    main()
