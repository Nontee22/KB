## 模式 1：提取字段 → 批量查询（防 N+1）

**场景**：查主表后，需要拿子表/关联表数据。逐行查库是 N+1 问题（N 行 = N 次 SQL），标准做法是先收齐 id、一次 `IN` 查询。

```java
// 第一步：从订单行列表提取所有行 id
List<Long> orderLineIds = orderLines.stream()
        .map(JtOrderLine::getId)          // 对象 → id
        .filter(Objects::nonNull)         // 剔除 null，防止 IN 列表脏数据
        .distinct()                       // 去重
        .collect(Collectors.toList());    // 收成 List

// 第二步：一次 IN 查询拿全部关联数据
List<JtOrderLineMaterialCharacteristic> characteristics =
        materialCharacteristicRepository.selectByCondition(
                Condition.builder(JtOrderLineMaterialCharacteristic.class)
                        .andWhere(Sqls.custom().andIn("orderLineId", orderLineIds))
                        .build());
```

**执行过程**：`[4个对象] → map → [101,102,null,101] → filter → [101,102,101] → distinct → [101,102]`

**注意**：id 列表可能为空，拼 `IN` 前必须判空，否则生成 `IN ()` 直接 SQL 报错（Oracle ORA-00936）。

---

## 模式 2：条件过滤

**场景**：从列表里留下满足条件的元素。等价于 for 循环里写 if + add。

```java
// 保留"五种值形态任一有值"的特性行，丢弃空行
characteristics = characteristics.stream()
        .filter(o -> o.getCharacteristicValueNumber() != null
                || o.getCharacteristicValueSingle() != null
                || !StringUtils.isEmpty(o.getCharacteristicValueText())
                || multiValueIds.contains(o.getId()))
        .collect(Collectors.toList());    // 就地重赋值
```

**说明**：filter 的 lambda 必须返回 boolean，true 留、false 丢。多条件用 `||` / `&&` 组合，复杂条件建议抽成私有方法保持可读。

**注意**：`characteristics = ...` 是重新赋值，不是原地修改；Stream 不会改变原集合。

---

## 模式 3：收成 Map 当查找表（toMap）

**场景**：循环里要反复按 key 查值时，先把 List 转成 Map，把 O(n) 查找降为 O(1)。

```java
// 特性 id → 特性编码
Map<Long, String> featureMap = featureList.stream()
        .collect(Collectors.toMap(
                JtFeature::getId,            // key：特性id
                JtFeature::getFeatureCode    // value：特性编码
        ));

// 后续循环里直接查，不用再遍历
String code = featureMap.get(characteristicDTO.getRelateFeature());
```

**注意（规范级）**：key 重复时默认直接抛 `IllegalStateException`。大项目要求必须写第三个参数声明冲突策略：

```java
Collectors.toMap(X::getId, X::getName, (first, second) -> first)  // 重复时保留第一个
```

另一个坑：**value 为 null 会 NPE**，value 可能空的字段换 for 循环填 Map。

---

## 模式 4：收成 Set 做 contains 判断

**场景**：只需要回答“在不在”时用 Set——`contains` 是 O(1)，List 是 O(n)；且自动去重。

```java
// 有字典行的特性行 id = 多选特性行
Set<Long> multiValueIds = characteristicMulRows.stream()
        .map(CharacteristicDTO::getId)
        .collect(Collectors.toSet());

// 后续 filter 里逐行判断，Set 查找快
.filter(o -> ... || multiValueIds.contains(o.getId()))
```

**注意**：HashSet 不保序。需要“去重 + 保序”时用 `LinkedHashSet`：`collect(Collectors.toCollection(LinkedHashSet::new))`。

---

## 模式 5：就地转换重赋值

**场景**：对列表做一次“净化”（过滤/转换）后替换原变量，省一个新变量名。

```java
// 原变量被过滤后的版本替换
characteristicDTOList = characteristicDTOList.stream()
        .filter(dto -> matchedFeatureIds.contains(dto.getRelateFeature()))
        .collect(Collectors.toList());
```

**说明**：本质是“新列表覆盖旧引用”。多步加工时比 `list2 = list1...`、`list3 = list2...` 的流水账清晰。

**注意**：只适用于变量是普通局部变量的情况；如果是方法入参或集合元素，重新赋值不影响调用方。

---

## 模式 6：分组（groupingBy）

**场景**：把列表按某个 key 拆成若干组，报表、归类、按父单聚合子行时的首选。

```java
// 按订单 id 把所有订单行分组
Map<Long, List<JtOrderLine>> linesByOrderId = allLines.stream()
        .collect(Collectors.groupingBy(JtOrderLine::getOrderId));
// 结果：{ 1001=[行1,行2], 1002=[行3] }
```

**进阶**：分组后再对组内做转换，`groupingBy` + `mapping` 组合：

```java
// 按订单分组，组内只要行号不要整个对象
Map<Long, List<String>> lineNosByOrder = allLines.stream()
        .collect(Collectors.groupingBy(
                JtOrderLine::getOrderId,
                Collectors.mapping(JtOrderLine::getLineNumber, Collectors.toList())));
```

---

## 模式 7：存在性判断（anyMatch / noneMatch / allMatch）

**场景**：只需要“是/否”结论时，替代 for + break + flag 三件套。

```java
// 旧写法：for 循环 + boolean 标志 + break
// 新写法：一行
boolean hasEmptyPrice = orderLines.stream()
        .anyMatch(line -> line.getUnitPrice() == null);   // 任一行没价格 → true

// 全部满足用 allMatch；全不满足用 noneMatch
boolean allPushed = orders.stream().allMatch(o -> o.getSalesOrderNumber() != null);
```

**说明**：anyMatch 找到第一个满足就短路返回，不会遍历全量。

---

## 模式 8：排序（sorted）

**场景**：流内排序，替代 `Collections.sort()`。

```java
// 按创建时间倒序
List<JtOrder> recent = orders.stream()
        .sorted(Comparator.comparing(JtOrder::getCreationDate).reversed())
        .collect(Collectors.toList());

// 多字段排序：先按状态，再按日期
Comparator.comparing(JtOrder::getStatus)
          .thenComparing(JtOrder::getCreationDate)
```

**注意**：`comparing` 的 key 为 null 会 NPE，可空字段用 `Comparator.comparing(X::getDate, Comparator.nullsLast(Comparator.naturalOrder()))`。简单排序直接用 `list.sort(...)` 更直接，不必开流。

---

## 模式 9：字符串拼接（joining）

**场景**：把 id 列表拼成逗号串（日志、SQL、外部接口参数）。

```java
String idStr = orderLineIds.stream()
        .map(String::valueOf)                              // Long → String
        .collect(Collectors.joining(",", "[", "]"));       // 分隔符, 前缀, 后缀
// 结果："[101,102,103]"
```

**说明**：替代手写循环 + 判断“最后一项不加逗号”的旧套路。

---

## 模式 10：扁平化（flatMap）

**场景**：一层套一层的结构（订单→行）拍平成一层。map 是“一对一”，flatMap 是“一对多摊开”。

```java
// 每个订单有多行，把所有订单的行拍平成一个大列表
List<ItemDTO> allItems = orders.stream()
        .flatMap(order -> order.getItems().stream())   // 每个订单贡献一个流
        .collect(Collectors.toList());
```

**对比记忆**：
- `map`：1 进 1 出（对象 → id）
- `flatMap`：1 进 N 出（订单 → 它的所有行）

---

## 模式 11：求和与统计

**场景**：合计、均值、最大最小。

```java
// BigDecimal 金额合计（金额必须用 reduce，不能用 mapToInt）
BigDecimal totalAmount = lines.stream()
        .map(X::getAmount)
        .reduce(BigDecimal.ZERO, BigDecimal::add);

// int 求和 / 统计
int totalQty = lines.stream().mapToInt(X::getQty).sum();
IntSummaryStatistics stat = lines.stream().mapToInt(X::getQty).summaryStatistics();
// stat.getMax() / getMin() / getAverage() / getCount()
```

**注意**：BigDecimal 求和要用 `reduce` + `BigDecimal::add`，初值给 `BigDecimal.ZERO` 防空列表 NPE。

---

## 模式 12：语法糖选择（toList / toSet / collect）

**场景**：收尾写法的选择。

| 写法 | 产物 | 可变性 | 版本 |
|------|------|--------|------|
| `.collect(Collectors.toList())` | List | ✅ 可改 | Java 8+ |
| `.toList()` | List | ❌ 不可变 | Java 16+ |
| `.collect(Collectors.toSet())` | Set | ✅ 可改 | Java 8+ |

**项目实例**（`getSapDTO` 里的血泪注释）：

```java
// 不直接toList而是Collectors.toList()，防止集合不可变导致add失败
toAddcharacteristicDTOList.addAll(characteristicDTOList.stream()
        .filter(o -> !idWithMulti.contains(o.getId()))
        .collect(Collectors.toList()));   // 收完还要 add，必须可变
```

**规则**：收完还要改 → `collect(Collectors.toList())`；收完只读 → `.toList()`；要判重/查存在 → `toSet()`。

---

## 附：大项目 Stream 纪律（code review 共识）

1. **一条链只做一件事**——超过 3-4 步、或中间要打日志/多层判空的，拆成两段或退回 for 循环。`getSapDTO` 里多选拆行用 for 写是正确的，硬塞进一条流是灾难。
2. **Stream 里不放副作用**——不改外部变量、不发查询、不写库。Stream 是纯转换管道。
3. **toMap 必写冲突策略**、**value 防 null**。
4. **超大数据量（几十万行导出）慎用流**——装箱、lambda 调用有开销，老老实实 for。
5. **优先 `filter(Objects::nonNull)` 而不是 `filter(x -> x != null)`**——语义更明确，可读性好。