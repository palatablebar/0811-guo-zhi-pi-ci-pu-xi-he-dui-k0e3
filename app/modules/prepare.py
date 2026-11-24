from app.business import DomainIssue, by_kind, prepared, single


def prepare(rows):
    from collections import defaultdict
    from graphlib import CycleError, TopologicalSorter

    check = single(rows, "check")
    nodes = {}
    deps = defaultdict(dict)
    for row in rows:
        if row["kind"] not in ("stock", "blend"):
            continue
        if row["batch"] in nodes or row["grams"] == 0:
            raise DomainIssue("BATCH_CONTRACT")
        nodes[row["batch"]] = (row["kind"], row["grams"])
    for edge in by_kind(rows, "feed"):
        child, parent = edge["batch"], edge["parent"]
        if child not in nodes or parent not in nodes or nodes[child][0] != "blend":
            raise DomainIssue("UNKNOWN_FEED")
        if parent in deps[child]:
            raise DomainIssue("FEED_DUPLICATE")
        deps[child][parent] = edge["grams"]
    if check["batch"] not in nodes:
        raise DomainIssue("UNKNOWN_BATCH")
    try:
        order = list(
            TopologicalSorter({k: deps[k] for k in sorted(nodes)}).static_order()
        )
    except CycleError as error:
        raise DomainIssue("BLEND_CYCLE") from error
    return prepared(
        len(nodes), {"edges": sum(map(len, deps.values()))}, (order, nodes, deps, check)
    )
