def api_violations(
    package: str,
    imports: list[tuple[str, str]],
    public: tuple = ("api",),
    roots: tuple = ("app", "cli"),
    open_units: tuple = ("shared",),
) -> list[str]:
    def get_unit(module: str) -> str | None:
        parts = module.split(".")
        if len(parts) >= 2 and parts[0] == package:
            return parts[1]
        return None

    violations: list[str] = []
    seen: set[str] = set()

    for src, dst in imports:
        src_unit = get_unit(src)
        dst_unit = get_unit(dst)

        if src_unit is None or dst_unit is None:
            continue

        if src_unit == dst_unit or src_unit in roots:
            continue

        dst_parts = dst.split(".")
        if (
            dst_unit in open_units
            or len(dst_parts) == 2
            or (len(dst_parts) >= 3 and dst_parts[2] in public)
        ):
            continue

        msg = f"{src} -> {dst}: імпорт нутрощів модуля {dst_unit}"
        if msg not in seen:
            seen.add(msg)
            violations.append(msg)

    return violations