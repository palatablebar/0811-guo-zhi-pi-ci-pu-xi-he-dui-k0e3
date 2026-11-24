from collections import Counter

from app.modules.allocate import allocate


def balance(intake, cases):
    accounted = (
        intake["accepted"] + intake["rejected"] + intake["blank"] + intake["repeated"]
    )
    status = Counter(case["status"] for case in cases)
    ready = status.pop("READY", 0)
    observed = sum(len(case["records"]) for case in cases)
    shared = allocate(cases)
    return dict(
        input=intake["input"],
        accepted=intake["accepted"],
        isolated=intake["rejected"],
        ignored=intake["blank"] + intake["repeated"],
        accounted=accounted,
        balanced=accounted == intake["input"] and observed == intake["accepted"],
        ready=ready,
        pending=len(cases) - ready,
        issues=dict(sorted(status.items())),
        shared=shared["shared"],
        blocked=shared["blocked"],
        releasable=bool(cases)
        and ready == len(cases)
        and not intake["rejected"]
        and not shared["blocked"]
        and accounted == intake["input"]
        and observed == intake["accepted"],
    )
