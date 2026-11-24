"""跨批次原料占用汇总。

同一原料批号被多个业务组（果汁批次）共同领用时，单组平衡不代表
库存足够：把各组对同一批号的领用累计起来，对照该批号的可用量，
超占时所有领用组都不得签发。
"""


def order(key):
    try:
        return (0, int(key), key)
    except ValueError:
        return (1, 0, key)


def allocate(cases):
    declared = {}
    consumed = {}
    users = {}
    for case in cases:
        measure = case.get("measure") or {}
        for material, grams in (measure.get("stocks") or {}).items():
            declared[material] = max(declared.get(material, 0), grams)
        for material, grams in (measure.get("draws") or {}).items():
            if grams <= 0:
                continue
            consumed[material] = consumed.get(material, 0) + grams
            users.setdefault(material, [])
            if case["case"] not in users[material]:
                users[material].append(case["case"])
    shared = []
    blocked = set()
    for material in sorted(set(declared) | set(consumed), key=order):
        available = declared.get(material, 0)
        drawn = consumed.get(material, 0)
        over = drawn > available
        cases = sorted(users.get(material, []))
        if over:
            blocked.update(cases)
        shared.append(
            dict(
                material=material,
                available=available,
                consumed=drawn,
                surplus=available - drawn,
                over=over,
                cases=cases,
            )
        )
    shared.sort(key=lambda row: (not row["over"], order(row["material"])))
    return {"shared": shared, "blocked": sorted(blocked)}
