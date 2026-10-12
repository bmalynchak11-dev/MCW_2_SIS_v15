def layer_violations(
    package: str,
    order: list[str],
    edges: list[tuple[str, str]],
    closed: bool = True,
) -> list[str]:
    def get_layer(module: str) -> str | None:
        parts = module.split(".")
        if len(parts) >= 3 and parts[0] == package:
            return parts[1]
        return None

    violations: list[str] = []

    for src, dst in edges:
        src_layer = get_layer(src)
        dst_layer = get_layer(dst)

        if src_layer is None or dst_layer is None:
            continue

        if src_layer not in order:
            raise ValueError(f"Невідомий шар: {src_layer}")
        if dst_layer not in order:
            raise ValueError(f"Невідомий шар: {dst_layer}")

        if src_layer == dst_layer:
            continue

        src_idx = order.index(src_layer)
        dst_idx = order.index(dst_layer)

        if dst_idx < src_idx:
            violations.append(
                f"{src} -> {dst}: залежність угору ({src_layer} -> {dst_layer})"
            )
        elif closed and dst_idx > src_idx + 1:
            violations.append(
                f"{src} -> {dst}: пропуск шару ({src_layer} -> {dst_layer})"
            )

    return violations