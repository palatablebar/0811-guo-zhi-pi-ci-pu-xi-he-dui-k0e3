EXPECTED = {
    "0001": (4, 60, "READY"),
    "0002": (2, 10, "READY"),
    "0003": (0, None, "BLEND_CYCLE"),
    "0004": (2, 60, "MASS_BALANCE"),
}
EVIDENCE = {
    "0001": {
        "origins_g": {"1": "75/2", "2": "45/2"},
        "overdrawn": [],
        "unbalanced": [],
    },
    "0004": {"origins_g": {"1": "60"}, "overdrawn": [1], "unbalanced": []},
}
