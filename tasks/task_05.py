def ring_violations(
    rings: list[str],
    modules: dict,
    imports: list[tuple[str, str]],
    forbidden: dict,
    ports: list[tuple[str, str]] = (),
    root: str | None = None,
) -> list[str]:
    for mod, r in modules.items():
        if r not in rings:
            raise ValueError(f"Невідоме коло: {r}")

    for src, dst in imports:
        if src != root and src not in modules:
            raise ValueError(f"Невідомий модуль: {src}")

    for p_port, p_impl in ports:
        if p_port not in modules:
            raise ValueError(f"Невідомий модуль: {p_port}")
        if p_impl not in modules:
            raise ValueError(f"Невідомий модуль: {p_impl}")

    violations: list[str] = []
    seen: set[str] = set()

    for src, dst in imports:
        if src == root:
            continue

        src_ring = modules[src]
        src_idx = rings.index(src_ring)

        if dst in modules:
            dst_ring = modules[dst]
            dst_idx = rings.index(dst_ring)
            if dst_idx > src_idx:
                msg = f"{src} -> {dst}: внутрішнє коло ({src_ring}) знає зовнішнє ({dst_ring})"
                if msg not in seen:
                    seen.add(msg)
                    violations.append(msg)
        else:
            first_part = dst.split(".")[0]
            if first_part in forbidden.get(src_ring, []):
                msg = f"{src} імпортує {dst}: інфраструктура у внутрішньому колі ({src_ring})"
                if msg not in seen:
                    seen.add(msg)
                    violations.append(msg)

    for p_port, p_impl in ports:
        if p_impl == root:
            continue

        port_ring = modules[p_port]
        impl_ring = modules[p_impl]
        port_idx = rings.index(port_ring)
        impl_idx = rings.index(impl_ring)

        if port_idx >= impl_idx:
            msg = f"{p_impl} реалізує порт з {p_port}: порт ({port_ring}) не лежить глибше за реалізацію ({impl_ring})"
            if msg not in seen:
                seen.add(msg)
                violations.append(msg)

    return violations