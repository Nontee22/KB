# LangChain LCEL 数据流与 Runnable 包装器使用指南

本文档系统性地总结了在 LangChain 表达式语言（LCEL）中，关于数据流传递机制、`RunnableLambda` 与 `RunnablePassthrough.assign` 的核心区别、数据丢失原因及最佳实践。

---

## 一、核心机制：LCEL 的单向数据流

在 LangChain 表达式语言（LCEL）中，链路（Chain）的构建依赖于严格的**单向数据流**和**管道模式（Pipeline Pattern）**。

### 1. 管道操作符 `|` 的本质
在标准的 Python 语法中，`|` 通常用于按位或或字典合并。但在 LCEL 中，LangChain 框架通过**运算符重载**（实现 `__or__` 和 `__ror__` 方法），赋予了 `|` 全新的含义：**管道（Pipe）**。

当你写下 `A | B` 时，其底层逻辑是：**将 A 的运行结果（返回值），作为参数传递给 B 去运行。**

### 2. 核心定律
**“上一个节点的 `return` 结果，就是下一个节点的唯一输入。”**

在 LCEL 链路中，**没有全局变量或上下文缓存的概念**。数据像水流一样顺着管道单向流动。下一个节点能看到的唯一数据，完全取决于上一个节点返回了什么。

---

## 二、数据丢失的真相：`RunnableLambda` 的行为

`RunnableLambda` 的作用是将任意普通的 Python 函数包装成可执行的 Runnable 节点。它的核心行为是：**只输出该函数的返回值**。

这就引出了开发者最常遇到的困惑：为什么用了 `RunnableLambda` 之后，之前的数据不见了？

### 1. 数据并不是被“删除”了，而是被“替换”了
`RunnableLambda` 本身不会主动删除任何数据。但是，如果你的函数只返回了一个全新的字典，那么这个新字典就会**完全替换**掉上游传下来的旧字典，成为下一个节点的输入。从数据流的角度看，旧数据就“丢失”了。

### 2. 代码对比演示

假设上游节点传递下来的输入数据为：
`x = {"name": "小N", "answer": "我喜欢小狗"}`

#### 情况 A：只返回新内容（导致旧数据在数据流中丢失）
```python
def add_new_data(x):
    # 只返回了一个全新的字典
    return {"new_field": "这是新数据"}

# 链路：上游 | RunnableLambda(add_new_data) | 下游
```
**结果**：下游节点收到的输入只有 `{"new_field": "这是新数据"}`。
**结论**：之前的 `name` 和 `answer` 彻底消失。如果你不带上它们，它们就被替换了。

#### 情况 B：手动带上旧数据（数据得以保留）
```python
def add_new_data(x):
    # 使用 **x 把旧数据解包，和新数据合并后返回
    return {
        **x, 
        "new_field": "这是新数据"
    }

# 链路：上游 | RunnableLambda(add_new_data) | 下游
```
**结果**：下游节点收到的输入是 `{"name": "小N", "answer": "我喜欢小狗", "new_field": "这是新数据"}`。
**结论**：你手动把之前的数据带上了，数据流得以完整延续。

---

## 三、官方推荐：`RunnablePassthrough.assign` 的本质

既然在使用 `RunnableLambda` 时，必须手动写 `**x` 才能保留旧数据，那么在复杂的链路中，这种写法不仅繁琐，而且极易出错（忘记写 `**x` 就会导致数据流断裂）。

为了解决这个问题，LangChain 官方提供了 `RunnablePassthrough.assign`。

### 1. `assign` 的底层逻辑
`RunnablePassthrough.assign` 的本质，就是 **LangChain 官方帮你写好并封装好的“情况 B”**。

当你在代码中写：
```python
RunnablePassthrough.assign(new_field=lambda x: "这是新数据")
```
LangChain 在底层自动帮你执行了：
```python
RunnableLambda(lambda x: {**x, "new_field": "这是新数据"})
```

### 2. 为什么 `assign` 是“加字段”的最常用选择？
1. **绝对安全**：框架自动帮你合并旧数据，绝不会因为开发者疏忽而弄丢上游上下文。
2. **语义清晰**：`assign` 这个词明确向阅读代码的人传达：“我要给现有的字典分配/添加一个新字段”，而不是替换整个字典。
3. **代码简洁**：省去了写 `lambda x: {**x, ...}` 的样板代码。
4. **支持并行计算**：可以非常方便地同时挂载多个计算任务，例如 `assign(a=func_a, b=func_b)`。

---

## 四、场景对决：`RunnableLambda` vs `RunnablePassthrough.assign`

在实际开发中，并不是说 `RunnableLambda` 不好，而是它们有各自明确的适用场景。判断使用哪个包装器，只需要问自己一个问题：
**“这个函数处理完后，我还需要保留上游传下来的其他数据吗？”**

### 场景一：使用 `RunnableLambda`（用于“转换”、“替换”或“提取”）
如果你的函数是为了把输入数据**变成另一种形态**，并且链路的下一步**只需要这个新形态**，不需要之前的旧数据了，就用 `RunnableLambda`。

**示例：提取与格式化（字典 -> 字符串）**
```python
def format_mapping(x):
    # 映射处理：将字典映射为特定格式的字符串
    return f"用户 {x['name']} 说：{x['answer']}"

# 使用 RunnableLambda 包装
chain = ... | RunnableLambda(format_mapping) | next_node
```
**结果**：下一个节点收到的是一个纯字符串，旧字典被彻底替换。

### 场景二：使用 `RunnablePassthrough.assign`（用于“增强”、“附加特征”）
如果你的函数是为了**计算出一个新值**，并且你想把这个新值作为一个新字段加到原来的字典里，同时保留原来的所有字段供后续使用，就用 `assign`。

**示例：标签映射与附加（字典 -> 增强后的字典）**
```python
def get_emotion_mapping(x):
    # 映射处理：根据文本映射出情感标签
    if "喜欢" in x["answer"]:
        return "积极"
    return "中性"

# 使用 RunnablePassthrough.assign 包装
# 注意：这里的函数只需要返回新字段的值，不需要返回整个字典
chain = ... | RunnablePassthrough.assign(emotion=get_emotion_mapping) | next_node
```
**结果**：下一个节点收到的是 `{"name": "...", "answer": "...", "emotion": "积极"}`。旧数据保留，新数据增加。

### 针对“映射处理”的特别说明
通常我们说的“映射（Mapping）”，在数据处理中往往意味着形态的转换：
1. **如果是“破坏性/替换性”映射**：比如把 JSON 映射为纯文本，把复杂的对象映射为单一的 ID。-> **用 `RunnableLambda`**。
2. **如果是“建设性/附加性”映射**：比如根据用户 ID 映射出用户画像，并把这个画像作为新字段加到当前上下文中。-> **用 `RunnablePassthrough.assign`**。

### 特殊的结合用法
有时候，你的映射逻辑很复杂，写成了一个普通的函数，这个函数接收整个字典，并且**在函数内部自己完成了合并**（返回了 `{**data, ...}`）。

```python
def complex_mapping(x):
    # 内部处理
    new_val = "计算结果"
    return {**x, "new_val": new_val} # 自己带上了旧数据

# 这时候你可以用 RunnableLambda 包装它
chain = ... | RunnableLambda(complex_mapping) | next_node
```
这种写法也是完全可行的，因为函数内部保证了数据不丢失。但在 LCEL 的最佳实践中，如果仅仅是为了加字段，官方更鼓励把计算逻辑写成小函数，然后直接用 `assign` 挂载，这样代码的“管道”语义更清晰。

---

## 五、最佳实践与总结口诀

在构建复杂的 LangChain 链路时，维持一个不断扩充的“单一状态字典”是标准做法。

### 核心口诀
**“要换数据用 Lambda，要加字段用 assign。”**

*   **要换数据（转换格式、提取内容、不再需要旧数据） -> 用 `RunnableLambda`**
*   **要加字段（保留旧数据、计算新特征、扩充上下文） -> 用 `RunnablePassthrough.assign`**

遵循这一原则，可以确保你的 LCEL 链路数据流清晰、代码可读性高，且永远不会出现意外的数据丢失问题。