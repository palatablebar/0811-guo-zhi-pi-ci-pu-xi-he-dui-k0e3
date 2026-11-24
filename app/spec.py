COLUMNS = ("batch", "parent", "grams")
KINDS = ("stock", "blend", "feed", "check")
PROJECT = {
    "name": "果汁批次谱系核对",
    "actor": "果汁工厂质量追溯员",
    "stages": [
        ("intake", "样例采信"),
        ("prepare", "混批建图"),
        ("calculate", "祖先追踪"),
        ("policy", "投料平衡"),
        ("balance", "运行对账"),
    ],
    "chart": "批次投料量",
}
