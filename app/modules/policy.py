from app.business import decision


def policy(result):
    return decision(result, "MASS_BALANCE" if result["flag"] else None)
