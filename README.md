# 果汁批次谱系核对

果汁工厂质量追溯员可在工作台上传来源 CSV，对照规则判断差异，签发合格批次或记录暂缓意见。

沿混批有向图追踪真实投料来源，识别环与余额超投。同一原料批被多组共同领用时，按跨组累计占用给出放行结论，超占批次一律停发。

## 启动

```sh
docker compose up --build -d --wait
```

打开 <http://localhost:18305>。页面预览带异常样例。选中阶段查看计算证据，选择可签发样例并执行批次，然后提交复核意见。

## 核验

```sh
docker compose exec -T app pytest -q
```

[输入字段](docs/DATA-DICTIONARY.md) · [阶段接口](docs/HTTP.md) · [操作步骤](docs/OPERATIONS.md) · [规则与测试](docs/DEPTH.md)
