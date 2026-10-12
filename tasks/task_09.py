import ast

def analyze_project(
    sources: dict,
    package: str,
    allowed: dict,
    public: tuple = ("api",),
    roots: tuple = ("app", "cli"),
    open_units: tuple = ("shared",),
) -> dict:
    def get_unit(module_name: str) -> str | None:
        parts = module_name.split(".")
        if len(parts) >= 2 and parts[0] == package:
            return parts[1]
        return None

    sorted_modules = sorted(sources.keys())
    edges_set: set[tuple[str, str]] = set()
    violations: list[str] = []
    seen_violations: set[str] = set()

    for mod_name in sorted_modules:
        src_unit = get_unit(mod_name)
        if src_unit is None or src_unit in roots:
            continue

        code = sources[mod_name]
        try:
            tree = ast.parse(code, filename=mod_name)
        except SyntaxError:
            raise ValueError(f"Синтаксична помилка у модулі {mod_name}")

        nodes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                nodes.append(node)

        nodes.sort(key=lambda n: (n.lineno, n.col_offset))

        for node in nodes:
            destinations: list[str] = []
            if isinstance(node, ast.Import):
                for alias in node.names:
                    destinations.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level != 0 or not node.module:
                    continue
                base = node.module
                base_parts = base.split(".")
                if len(base_parts) <= 2:
                    for alias in node.names:
                        destinations.append(f"{base}.{alias.name}")
                else:
                    destinations.append(base)

            for dst in destinations:
                dst_unit = get_unit(dst)
                if dst_unit is None or dst_unit == src_unit:
                    continue

                if dst_unit not in roots:
                    edges_set.add((src_unit, dst_unit))

                if dst_unit in open_units:
                    continue

                allowed_for_src = allowed.get(src_unit, [])
                if dst_unit not in allowed_for_src:
                    msg = f"{mod_name} -> {dst}: залежність {src_unit} -> {dst_unit} не дозволена"
                    if msg not in seen_violations:
                        seen_violations.add(msg)
                        violations.append(msg)
                else:
                    dst_parts = dst.split(".")
                    if len(dst_parts) > 2 and dst_parts[2] not in public:
                        msg = f"{mod_name} -> {dst}: імпорт нутрощів модуля {dst_unit}"
                        if msg not in seen_violations:
                            seen_violations.add(msg)
                            violations.append(msg)

    edges = sorted([f"{u} -> {v}" for u, v in edges_set])

    adj: dict[str, set[str]] = {}
    nodes_all: set[str] = set()
    for u, v in edges_set:
        nodes_all.add(u)
        nodes_all.add(v)
        adj.setdefault(u, set()).add(v)
    for n in nodes_all:
        adj.setdefault(n, set())

    idx = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    sccs: list[list[str]] = []

    def strongconnect(v: str):
        nonlocal idx
        indices[v] = idx
        lowlinks[v] = idx
        idx += 1
        stack.append(v)
        on_stack.add(v)

        for w in adj[v]:
            if w not in indices:
                strongconnect(w)
                lowlinks[v] = min(lowlinks[v], lowlinks[w])
            elif w in on_stack:
                lowlinks[v] = min(lowlinks[v], indices[w])

        if lowlinks[v] == indices[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            if len(scc) >= 2:
                sccs.append(sorted(scc))

    for node in sorted(nodes_all):
        if node not in indices:
            strongconnect(node)

    cycles = sorted(sccs)

    return {
        "edges": edges,
        "violations": violations,
        "cycles": cycles,
    }