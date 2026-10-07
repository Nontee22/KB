合同 ─1:N─► 合同版本 ─┬─ 合同行 / 账期 / 送货地址 / 担保方 / 流程 / 附件
                     └─1:N─► 订单  ─┬─  订单行 ─┬─ 物料特性
                                    │          ├─ 生产明细
                                    │          ├─ 价格表
                                    │          └─ 点价关联订单行
                                    └─1:N─► 交货单 ── 交货单行 ──► 点价关联发货

{
  "esbInfo": { "instId": "…", "requestTime": "…" },

  "ZOMSDH": "OMS 订单号",
  "AUART": "订单类型",
  "KUNNR": "客户编码",
  "STONR": "40",
  "ZVGBEL_BS": "G",
  "VBELN": "参考订单的 SAP 单号",
  "KTXT1": "开票文本",
  "TESTRUN": "",

  "ITEM": [
    { "POSNR": "10", "MATNR": "物料编码", "KWMENG": "30", "VRKME": "销售单位",
      "WERKS": "工厂", "UEBTO": "…", "UNTTO": "…" }
  ],
  "DJ": [
    { "POSNR": "10", "KSCHA": "ZJ01", "WAERS": "CNY", "KPEIN": "1", "PRICE": "销售单价" }
  ],
  "SX": [
    { "POSNR": "10", "…": "物料特性" }
  ],
  "ZQH": [
    { "POSNR": "1", "ZKXLX": "款项类型", "…": "…" }
  ]
}


