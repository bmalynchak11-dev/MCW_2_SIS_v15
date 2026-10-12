import re

def table_violations(queries: dict, modules: list[str]) -> list[str]:
    pattern = re.compile(
        r"\b(?:TABLE\s+IF\s+NOT\s+EXISTS|TABLE|FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        re.IGNORECASE,
    )
    excluded = {"select", "values", "set", "exists", "if", "not"}
    violations: list[str] = []

    for mod, query_list in queries.items():
        if mod not in modules:
            raise ValueError(f"Невідомий модуль: {mod}")

        for idx, q in enumerate(query_list, start=1):
            seen_in_query: set[str] = set()
            for m in pattern.finditer(q):
                tbl_raw = m.group(1)
                tbl_lower = tbl_raw.lower()

                if tbl_lower in excluded:
                    continue
                if tbl_lower in seen_in_query:
                    continue
                seen_in_query.add(tbl_lower)

                if tbl_lower.startswith(f"{mod.lower()}_"):
                    continue

                owner = None
                best_len = -1
                for candidate in modules:
                    prefix = f"{candidate.lower()}_"
                    if tbl_lower.startswith(prefix) and len(candidate) > best_len:
                        owner = candidate
                        best_len = len(candidate)

                if owner:
                    owner_text = f"(власник: {owner})"
                else:
                    owner_text = "(власника немає)"

                # Без пробілу перед дужками: {mod}[{idx}]
                violations.append(
                    f"{mod}[{idx}]: SQL зачіпає таблицю {tbl_raw}, що не належить модулю {mod} {owner_text}"
                )

    return violations