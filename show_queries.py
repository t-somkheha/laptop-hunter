import ast, itertools

for f in ("sweep_gpu.py", "sweep_oled2.py", "sweep_all.py"):
    tree = ast.parse(open(f).read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "QUERIES":
            vals = ast.literal_eval(node.value)
            print(f"--- {f}: {len(vals)} queries")
            print("   " + ", ".join(vals))
            print()
