from app.business import measured


def compute(data):
    from collections import defaultdict
    from fractions import Fraction

    order, nodes, deps, check = data
    lineage = {}
    issued = defaultdict(int)
    imbalanced = []
    for k in order:
        kind, size = nodes[k]
        source = defaultdict(Fraction)
        if kind == "stock":
            source[k] = Fraction(size)
        elif sum(deps[k].values()) != size:
            imbalanced.append(k)
        for parent, grams in deps[k].items():
            issued[parent] += grams
            for origin, quantity in lineage[parent].items():
                source[origin] += quantity * Fraction(grams, nodes[parent][1])
        lineage[k] = source
    negative = sorted(k for k, v in issued.items() if v > nodes[k][1])
    result = lineage[check["batch"]]
    return measured(
        nodes[check["batch"]][1],
        check["grams"],
        "克",
        {
            "origins_g": {str(k): str(v) for k, v in result.items()},
            "overdrawn": negative,
            "unbalanced": imbalanced,
        },
        bool(negative or imbalanced),
    )
