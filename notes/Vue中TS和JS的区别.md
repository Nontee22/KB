# Vue3 中 JS 与 TS 写法全面对比指南

通过对比纯 JS 和 TS 的代码，你可以最直观地看到：TS 并没有改变 Vue3 的核心逻辑，它只是在关键位置加上了“类型说明书”。

以下所有代码均基于 `<script setup>` 语法。

---

## 一、 基础变量与数据类型

在 JS 中，变量可以随时改变数据类型；在 TS 中，变量一旦声明，就必须遵守规定的类型。

### 1. 基础类型与数组
```javascript
// 【纯 JS 写法】
let username = "张三"
let age = 25
let hobbies = ["阅读", "游泳"]
```

```typescript
// 【Vue3 TS 写法】
let username: string = "张三"
let age: number = 25
let hobbies: string[] = ["阅读", "游泳"] 
// 差异解析：在变量名后加冒号和类型。数组可以在类型后加 []。
```

### 2. 对象与联合类型
```javascript
// 【纯 JS 写法】
let userInfo = { name: "李四", age: 30 }
let status = "loading" // 后续可能会变成 "success" 或 "error"
```

```typescript
// 【Vue3 TS 写法】
let userInfo: { name: string; age: number } = { name: "李四", age: 30 }
let status: "loading" | "success" | "error" = "loading"
// 差异解析：TS 可以限制对象的具体结构，也可以用 | 限制变量只能是某几个特定字符串之一。
```

---

## 二、 Vue3 响应式 API (ref / reactive)

### 1. ref 包装数据
```javascript
// 【纯 JS 写法】
import { ref } from 'vue'

const count = ref(0)
const userList = ref([])
const currentProduct = ref(null)

userList.value.push("张三")
currentProduct.value = { id: 1, title: "手机" }
```

```typescript
// 【Vue3 TS 写法】
import { ref } from 'vue'

const count = ref(0) // 基础类型 TS 会自动推断，无需改动
const userList = ref<string[]>([]) // 空数组必须用尖括号 < > 告诉 TS 里面装什么
const currentProduct = ref<{ id: number; title: string } | null>(null) 

userList.value.push("张三") // 正确
// userList.value.push(123) // 报错：类型不匹配
currentProduct.value = { id: 1, title: "手机" } 
// 差异解析：当 ref 初始值为空数组或 null 时，TS 无法猜测你未来要存什么，必须手动加泛型 < >。
```

### 2. reactive 包装对象
```javascript
// 【纯 JS 写法】
import { reactive } from 'vue'

const form = reactive({
  username: "",
  password: ""
})

form.username = "admin"
```

```typescript
// 【Vue3 TS 写法】
import { reactive } from 'vue'

const form = reactive({
  username: "",
  password: ""
})

form.username = "admin"
// 差异解析：reactive 传入的是具体对象，TS 会根据初始值自动推断类型，所以写法和 JS 完全一样，无需额外加类型。
```

---

## 三、 组件通信：Props 与 Emits (核心差异)

这是 Vue3 中 JS 和 TS 写法区别最大的地方。TS 抛弃了运行时的对象配置，改用基于类型的声明。

### 1. defineProps (父传子)
```javascript
// 【纯 JS 写法】
// 使用运行时声明，通过构造函数 (String, Number) 来限制
const props = defineProps({
  title: String,
  count: {
    type: Number,
    default: 0
  }
})
```

```typescript
// 【Vue3 TS 写法】
// 使用基于类型的声明，配合 withDefaults 设置默认值
const props = withDefaults(defineProps<{
  title?: string
  count?: number
}>(), {
  title: '默认标题',
  count: 0
})
// 差异解析：JS 用大写的 String/Number，TS 用小写的 string/number。TS 写法能提供更好的代码自动补全。
```

### 2. defineEmits (子传父)
```javascript
// 【纯 JS 写法】
// 只声明事件名称，不限制参数
const emit = defineEmits(['change', 'update'])

function handleSave() {
  emit('change', 101)
  emit('update', '新数据', 1690000000)
}
```

```typescript
// 【Vue3 TS 写法】
// 声明事件名称，同时严格限制每个事件能传递的参数类型和数量
const emit = defineEmits<{
  change: [id: number]
  update: [value: string, timestamp: number]
}>()

function handleSave() {
  emit('change', 101) // 正确
  // emit('change', '字符串') // 报错：类型必须是 number
}
// 差异解析：JS 只管事件名，TS 连事件携带的参数类型和个数都管，避免了子组件乱传参数。
```

---

## 四、 事件处理与函数参数

在模板中绑定事件时，处理函数接收的事件对象 (Event) 在 TS 中需要特别处理。

### 1. 普通点击事件
```javascript
// 【纯 JS 写法】
function handleButtonClick(e) {
  console.log("点击坐标:", e.clientX, e.clientY)
}
```

```typescript
// 【Vue3 TS 写法】
function handleButtonClick(e: MouseEvent) {
  console.log("点击坐标:", e.clientX, e.clientY)
}
// 差异解析：必须给参数 e 加上 MouseEvent 类型，否则 TS 不认识 e.clientX。
```

### 2. 输入框事件 (新手最常遇到的报错)
```javascript
// 【纯 JS 写法】
function handleInput(e) {
  // JS 中可以直接访问 e.target.value
  console.log("输入的值是:", e.target.value) 
}
```

```typescript
// 【Vue3 TS 写法】
function handleInput(e: Event) {
  // TS 中 e.target 默认可能是任何元素，不一定有 value 属性
  // 必须使用 as 进行“类型断言”，明确告诉 TS 这是一个输入框
  const target = e.target as HTMLInputElement
  console.log("输入的值是:", target.value) 
}
// 差异解析：TS 非常严谨，它不知道触发事件的具体是哪个 HTML 标签，所以需要你手动“断言”它是 HTMLInputElement。
```

---

## 五、 获取 DOM 元素 (Template Ref)

在 JS 中直接 `ref(null)` 即可，但在 TS 中，必须明确告诉编译器这个 ref 未来会绑定到什么 HTML 标签上。

```javascript
// 【纯 JS 写法】
import { ref, onMounted } from 'vue'

const inputRef = ref(null)

onMounted(() => {
  // JS 中直接调用 focus，不检查 inputRef 是否为空
  inputRef.value.focus() 
})
```

```typescript
// 【Vue3 TS 写法】
import { ref, onMounted } from 'vue'

// 必须加上 | null，因为组件刚初始化时 DOM 还不存在，值确实是 null
const inputRef = ref<HTMLInputElement | null>(null)

onMounted(() => {
  // 使用 ?. 可选链操作符，防止 inputRef.value 为 null 时导致程序崩溃
  inputRef.value?.focus() 
})
// 差异解析：TS 强制你考虑 DOM 还没渲染出来的“空值”情况，使用 <HTMLInputElement | null> 和 ?. 能让代码更健壮。
```

---

## 六、 总结：如何平滑过渡？

1. **先写 JS 逻辑，再补 TS 类型**：如果你刚开始不习惯，可以先按照 JS 的思维把逻辑写完，然后看着编辑器里的红色报错提示，一步步把缺失的类型补上。
2. **遇到实在不知道什么类型的情况**：在 TS 中可以使用 `any` 类型（例如 `let data: any`）。这相当于告诉 TS “闭嘴，别管这个变量”，它能让你暂时绕过类型检查。但建议只在极个别复杂场景下使用，不要滥用。
3. **多看提示**：VS Code 等编辑器在你输入 `props.` 或 `emit(` 时，弹出的提示框就是 TS 在发挥作用，习惯看这些提示，你的开发效率会比纯 JS 更高。