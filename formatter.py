import re
from collections import defaultdict

def extract_blocks(txt, mark):
    """
    Extracts blocks of text bounded by 'mark', supporting nested markers.
    Example: mark = "<html>" will look for <html>...<html>.
    """
    start = mark
    end = mark
    stack = []
    blocks = []
    i = 0
    while i < len(txt):
        if txt.startswith(start, i):
            stack.append(i + len(start))
            i += len(start)
        elif txt.startswith(end, i) and stack:
            start_idx = stack.pop()
            if not stack:  # Only add outermost blocks
                blocks.append(txt[start_idx:i])
            i += len(end)
        else:
            i += 1
    return blocks

def process_text(txt: str, mark: str):
    targets = extract_blocks(txt, mark)

    # Extract assignments
    assignment_pattern = re.compile(r"~\|(.*?)\|~", re.DOTALL)
    assignment_block = assignment_pattern.search(txt)
    mapping = {}
    if assignment_block:
        assignments = assignment_block.group(1).splitlines()
        for assign in assignments:
            assign = assign.strip()
            if not assign or "=" not in assign:
                continue
            x, y = map(str.strip, assign.split("=", 1))
            mapping[x] = y

    # Extract blocks for each assignment
    formatted = defaultdict(list)
    for x, y in mapping.items():
        blocks = extract_blocks(txt, x)
        formatted[y].extend(blocks)

    return targets, dict(formatted)


if __name__ == "__main__":
    txt = """
<html>
    Outer block
    <html>Inner block<html>
<html>
~|
a = alpha
b = beta
|~
aHelloa
bWorldb
aNested aInnera aDeepera aEnda
"""
    targets, formatted = process_text(txt, "<html>")
    print("Targets:", targets)
    print("Formatted:", formatted)
