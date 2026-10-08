## 第一章 先搞清楚：为什么单机锁不够用

### 1.1 单机时代：`synchronized` 就够了

假设你的订单服务只部署在一台机器上，只有一个 JVM 进程：

```java
public void submitOrder(Long orderId) {
    synchronized (this) {          // 同一时刻只有一个线程能进来
        // 1. 查订单状态，判断是否已提交
        // 2. 调 OA 接口
        // 3. 改订单状态
    }
}
```

`synchronized` 和 `ReentrantLock` 这类锁，本质上是**在 JVM 进程的内存里记一个标记**：谁拿到了，别人就得排队。

问题在于——这个标记**只存在于当前这一个 JVM 的内存里**。

### 1.2 多实例时代：单机锁直接失效

真实项目里，为了扛住流量和容错，同一个服务通常会部署多份：

```
         用户点两次「提交 OA」
                 │
      ┌──────────┴──────────┐
      │                     │
  Nginx 负载均衡（可能把两次请求分到不同机器）
      │                     │
┌─────▼─────┐         ┌─────▼─────┐
│  实例 A   │         │  实例 B   │
│ (JVM 1)   │         │ (JVM 2)   │
│ lock=已占 │         │ lock=空闲 │   ← 各记各的，互相看不见
└───────────┘         └───────────┘
```

- 请求 1 落到实例 A，拿到 A 内存里的锁，开始干活。
- 请求 2 落到实例 B，看到 B 内存里的锁是空闲的，**也拿到锁了**。

结果就是：**两个实例同时在处理同一个订单**，`synchronized` 形同虚设。

```
❌ 错误方案：把 synchronized 换成 ReentrantLock 加个 static —— 还是只在一个 JVM 内有效。
❌ 错误方案：把 Object 换成 static final —— 同上，static 也是"每个 JVM 一份"。
```

### 1.3 解法：把「锁」放到一个大家都能看见的地方

既然问题出在「锁标记只在一个 JVM 里」，那解法就很自然了：

> **把锁标记放到一个所有实例都能访问的外部系统里。**

这个外部系统需要满足几个条件：

| 需求 | 为什么 |
| --- | --- |
| 所有实例都能访问 | 不然还是各记各的 |
| 读写足够快 | 锁是在业务主流程上的，不能成为瓶颈 |
| 支持「只有一个人能成功占位」的原子操作 | 否则两个请求可能同时占位成功 |
| 能自动释放（超时） | 万一持锁的机器宕机/进程被 kill，不能锁一辈子 |

Redis 恰好全中。这就是 Redis 分布式锁。

### 1.4 一句话总结本章

> 单机锁锁的是「JVM 内存里的一个标记」，多实例部署时每个 JVM 各有一份，互相看不见。
> 分布式锁就是把这个标记挪到 Redis 这个公共的地方，让所有实例看到同一份。

---

## 第二章 Redis 凭什么能当锁

### 2.1 Redis 的命令执行是串行的

Redis 处理客户端命令时，**命令执行这条线是单线程的**（Redis 6 之后网络 IO 用了多线程，但真正执行命令还是串行）。

这带来一个极其重要的结果：

> **任何一条 Redis 命令，在执行过程中不可能被别的命令插队。**

这条性质是所有 Redis 锁方案的基石。它意味着：只要我们用**一条命令**完成「判断 + 占位」，就不可能出现两个人同时占位成功。

### 2.2 「key 存在」就等于「锁被占用」

Redis 是 Key-Value 数据库。我们借用一个 key 来表示一把锁：

```
key   = "oms:oa:submit:order:1001"     ← 锁名（要锁谁）
value = "3f2a...:14"                    ← 持有者标识（谁锁的）

这个 key 在 Redis 里存在  →  说明锁被占用了
这个 key 不存在          →  说明锁是空闲的
```

「加锁」= 想办法把这个 key 写进去；
「解锁」= 把这个 key 删掉。

### 2.3 为什么要设 NX（不存在才写）

如果直接 `SET key value`，那不管有没有人占着，都会把你写的值覆盖上去——等于没锁。

所以我们要求 Redis：**只有当这个 key 不存在时，才允许写入。** 这个条件就是 `NX`（Not eXists）。

```
SET lockKey holderId NX   →  没人占，我占上了 ✅
                            有人占，我写不进去 ❌
```

因为这是一条命令，Redis 内部串行执行，所以「检查 + 写入」这两步之间不可能被别人插队——这就是**原子性**。

### 2.4 为什么必须带过期时间

假设不加过期时间，考虑这个场景：

```
1. 实例 A 拿到了锁
2. 实例 A 所在机器被运维重启 / 进程被 kill -9 / 网络断了
3. 锁还留在 Redis 里，但没有任何人会去删它（因为持有者已经死了）
4. 从此以后，这个订单永远提交不了 —— 死锁 💥
```

给 key 加上过期时间（TTL），等于给锁装了一个「保险丝」：**即使持有者意外死掉，锁也会在到期后自动释放。**

Redis 提供 `EX`（秒）和 `PX`（毫秒）两种单位。

### 2.5 把 2.3 和 2.4 合起来：一条命令搞定

```
SET lockKey holderId NX EX 120
     ↑        ↑      ↑  ↑   ↑
   锁名    持有者  不存在 过期  120 秒
                   才写   单位是秒
```

这一条命令同时完成了「不存在才写」+「设置过期时间」，而且整个过程是原子的。

> ⚠️ 千万不要写成两条命令：
> ```
> SETNX lockKey holderId     ← 第一条成功
> EXPIRE lockKey 120         ← 还没执行，进程挂了
> ```
> 中间这一瞬间如果进程崩了，就产生了一把**没有过期时间的锁**——死锁。
> 更糟的是，如果程序逻辑写错（比如判断返回值写反），可能连 EXPIRE 都不会执行。
> 所以永远用 `SET ... NX EX ...` 这一条命令。

### 2.6 一句话总结本章

> Redis 能当锁，靠三件事：**命令串行（不会插队）** + **NX（不抢别人的坑）** + **EX（防止死锁）**。
> 这三样合成一条 `SET key value NX EX seconds`，就是 Redis 锁的全部地基。

---

## 第三章 加锁：一条 SET 命令拆开讲

```java
String result = jedis.set(lockKey, holderId, "NX", "EX", 120);
boolean locked = "OK".equals(result);
```

一行代码，逐段拆解：

| 位置 | 值 | 含义 | 新手最容易搞错的点 |
| --- | --- | --- | --- |
| 参数1 `lockKey` | `"oms:oa:submit:order:1001"` | **锁名**：锁的是哪一份资源 | 粒度要细到「资源 ID」，不能写成固定的 `"order:lock"`，否则所有订单互相阻塞 |
| 参数2 `holderId` | `"3f2a-...-98b:14"` | **持有者标识**：谁锁的 | 不是随便填的常量！见[第五章](#第五章-value-到底存什么) |
| 参数3 `"NX"` | | **不存在才设置** | 只要有别人占着，就写不进去 |
| 参数4 `"EX"` | | 过期时间**单位是秒** | 换成 `"PX"` 就是毫秒，别混用 |
| 参数5 `120` | | **过期时间 = 120 秒** | 必须大于你的业务最长执行时间 |
| 返回值 | `"OK"` / `null` | `"OK"` = 抢到锁；`null` = 没抢到 | **不是布尔值！**写成 `if (result)` 编译都过不去 |

### 3.1 一把锁的完整生命周期

```
时间线 ──────────────────────────────────────────────────────►

T0  请求1: SET oms:submit:1001 "uuid1:14" NX EX 120  →  "OK"   抢到了
T1  请求2: SET oms:submit:1001 "uuid1:15" NX EX 120  →  null   抢不到
T2  请求1: 执行业务逻辑……
T3  请求1: 业务做完，执行 Lua 解锁 → key 被删掉
T4  请求2: 再次尝试 → "OK"  （或者 T2 时直接失败返回给用户）
```

### 3.2 加锁失败了应该怎么办？

这不是 Redis 的问题，是业务设计问题。常见三种处理：

| 策略 | 代码表现 | 适用场景 |
| --- | --- | --- |
| **快速失败**（最常用） | `throw new CommonException("订单正在提交OA，请勿重复操作")` | 重复提交就该被拒绝，比如按钮防重点 |
| **等待重试** | 带 `waitTime` 参数，排队等一会儿 | 资源竞争激烈但用户能接受等待，比如抢库存 |
| **放弃但静默** | 直接 return，不报错 | 定时任务类，比如「这一轮跳过，下一轮再来」 |

### 3.3 一句话总结本章

> `SET lockKey holderId NX EX 120` 返回 `"OK"` 就是拿到锁。
> 记住四个关键词：**锁名、持有者、不存在才写、过期时间**。

---

## 第四章 解锁：为什么必须用 Lua

这是 Redis 分布式锁里**最容易写错、后果最严重**的一环。

### 4.1 先看错误写法

```java
// ❌ 新手最常见的错误解锁
jedis.del(lockKey);
// 或
redisTemplate.delete(lockKey);
```

看起来没毛病：我加锁了，我解锁，删掉那个 key，收工。

但考虑这个时间线：

```
时间 ──────────────────────────────────────────────────────────────►
T0   请求1 加锁成功，租约 120 秒
T1   请求1 开始执行业务（这个业务因为慢 SQL / 第三方接口超时，跑了 150 秒）
T120 锁自动过期了！key 被 Redis 删除                    💀 分水岭
T121 请求2 尝试加锁 → 成功（因为 key 已经不存在了）
T121 请求2 开始执行它自己的业务
T150 请求1 终于跑完了，执行 jedis.del(lockKey)          💥
     └─ 删掉的不是自己的锁，是请求2 刚加的锁！
T151 请求3 来加锁 → 又成功了
     └─ 结果：请求2 和 请求3 同时在处理同一个订单
```

**核心问题：`del` 是无差别的。它不看你删的是谁的锁，只要 key 在就删。**

### 4.2 解法：删之前先验明身份

既然 `del` 不看身份，那我们在删之前自己看一眼：**这个锁里的 value 是不是我写的？**

```java
// ❌ 这样写仍然有问题（虽然逻辑对了）
String value = jedis.get(lockKey);
if (holderId.equals(value)) {      // 是我的锁吗？
    jedis.del(lockKey);            // 是，删掉
}
```

问题在于：**`get` 和 `del` 是两条独立命令，中间有缝隙。**

```
T1  请求1: GET lockKey  →  "uuid1:14"   （是我的！准备删）
T2  ┌─ 就在这一瞬间，锁过期了，请求2 抢到了锁，value 变成 "uuid2:15" ─┐
T3  请求1: DEL lockKey  →  删掉了请求2 的锁 💥
```

只要我们用了「多条命令」，就永远存在这个窗口。**唯一可靠的解法是把「判断 + 删除」合成一个不可分割的操作——这就是 Lua 脚本。**

### 4.3 正确的解锁：Lua 脚本

```lua
if redis.call('get', KEYS[1]) == ARGV[1] then   -- 锁里的 value 是我的吗？
    return redis.call('del', KEYS[1])            -- 是 → 删掉，返回 1
else
    return 0                                      -- 不是 → 什么都不做，返回 0
end
```

**Lua 脚本在 Redis 里是原子执行的**：脚本执行期间，Redis 不会去执行别的命令。所以「判断」和「删除」之间不可能被插入任何操作，那个时间窗口被彻底堵死。

参数对应关系：

```
Redis 的 EVAL 命令格式：EVAL "脚本" 1 key1 arg1
                              ↑   ↑   ↑    ↑
                          脚本  几个key  锁名  持有者标识

脚本里：KEYS[1] → 锁名        （KEYS 装的是 key 名）
        ARGV[1] → 持有者标识   （ARGV 装的是普通参数）
```

> 注意 Lua 的下标从 **1** 开始，不是从 0。

### 4.4 为什么 value 存 holderId，以及解锁要传同样的 holderId

因为解锁的那一刻，我们要回答的问题是：

> **「现在这个 key 上挂着的 value，和当初加锁的我，是同一个人吗？」**

只有加锁时写入的 value 和解锁时传进去的 value 一致，才说明「这把锁从头到尾都是我的，没有被别人接手过」。

这就是为什么 value **不能是一个固定常量**——如果所有请求都写 `"lock"`，那么任何人解锁都会校验通过，防误删机制直接失效。

### 4.5 一句话总结本章

> 解锁必须「先校验身份、再删除」，且这两步必须**原子**（用 Lua 实现）。
> 原因：锁会超时过期，过期后可能已经易主，无脑 `del` 会删掉别人的锁。

---

## 第五章 value 到底存什么

### 5.1 一个自然的想法：存线程 ID 行不行？

```java
String holderId = String.valueOf(Thread.currentThread().getId()); // ❌ 不够
```

看起来挺合理——「谁加的锁」不就是「哪个线程加的锁」吗？

但它有两个致命问题：

#### 问题一：多实例部署时会撞车

```
实例 A（JVM 1）的线程 14  → holderId = "14"
实例 B（JVM 2）的线程 14  → holderId = "14"   ← 完全一样！

场景：实例 A 的线程 14 加的锁超时过期了，实例 B 的线程 14 抢到了锁。
     这时候实例 A 的线程 14 跑完业务来解锁，Lua 校验：
     Redis 里的 value "14" == 我算出来的 "14"  →  校验通过！
     → 删掉了实例 B 的锁 💥
```

**线程 ID 只在单个 JVM 内唯一，不是全局唯一。** 而 Redis 锁是全局的。

#### 问题二：线程池会复用线程 ID

线程池里的线程是循环使用的。虽然「同一个线程同时干两件事」不可能发生，但在「锁已经易主」的场景下，仅靠线程 ID 无法区分「是不是我这一次的加锁」。

### 5.2 标准答案：UUID + 线程 ID

```java
// 在应用启动时生成一次，代表「这个 JVM 进程 / 这个客户端实例」
private static final String INSTANCE_ID = UUID.randomUUID().toString();

// 每次加锁时拼上当前线程 ID
String holderId = INSTANCE_ID + ":" + Thread.currentThread().getId();
// 例如："3f2a8c91-4b7e-4d02-9a55-7c1e0f2b98b3:14"
```

- **UUID 段**：保证跨实例唯一（每个 JVM 启动时随机生成，几乎不可能重复）。
- **线程 ID 段**：保证同实例内跨线程唯一。

拼起来就是一个**全局唯一**的持有者标识。

> 💡 这正是 Redisson 内部的做法。Redisson 在 `RedissonClient` 初始化时生成一个 UUID 存为 `id`，加锁时用的就是 `id + ":" + threadId`。

#### 为什么每次加锁不重新生成 UUID？

也可以，但没必要：

- 复用同一把锁的时候（比如同一个线程重复加锁做可重入判断），需要「同一个线程算出来的 holderId 是稳定的」。
- UUID 生成虽然快，但没必要每次加锁都生成。
- 用「实例 UUID + 线程 ID」的方案，同一个线程在任何时刻算出来的 holderId 都是同一个值，方便做重入计数。

#### 更严格的做法：单调递增的锁 ID

如果你的场景真的非常敏感（同一个线程在不同时刻加同一把锁必须被区分开），可以在实例 UUID 之外再加一个原子递增计数器：

```java
private static final AtomicLong SEQUENCE = new AtomicLong(0);
String holderId = INSTANCE_ID + ":" + Thread.currentThread().getId()
                + ":" + SEQUENCE.incrementAndGet();
```

不过说实话，**加了线程 ID 之后，绝大多数场景已经足够了**，因为同一个线程不会同时在两个地方用同一把锁。

### 5.3 复杂版本：value 存 JSON

有些项目会把 value 写成 JSON：

```json
{
  "jvmPid": 22224,
  "threadId": 14,
  "count": 1,
  "expireAt": 147506817232
}
```

这种写法一般是为了：

| 字段 | 用途 |
| --- | --- |
| `count` | 支持**可重入**：同一个线程再次加锁时 `count++`，解锁时 `count--`，减到 0 才真正删 key |
| `jvmPid` | 排查问题：出事了能知道是哪个进程锁的 |
| `expireAt` | 监控：还能持有多久 |

这其实就是 Redisson 用 Hash 结构做的事（`hset lockKey uuid:threadId 1` → `hincrby ... 1` → `hincrby ... -1` → 减到 0 才 `del`）。

**但对新手来说：自己手写锁时，用 `UUID + ":" + threadId` 这个字符串就够了，不要一上来就搞 JSON 和可重入。** 需要重入和续租的时候，直接用 Redisson，别自己造轮子。

### 5.4 一句话总结本章

> value = `实例UUID + ":" + 线程ID`。
> 只写线程 ID 会在多实例部署时失去防误删能力；写固定常量等于没写。
> Redisson 内部用的就是这个格式。

---

## 第六章 三种加锁写法（Jedis / RedisTemplate / Redisson）

三种方式**本质完全一样**——都是往 Redis 里占一个带过期时间的坑。区别只在于**封装程度**：

```
底层 ←───────────────────────────────────────────────► 封装程度
Jedis         RedisTemplate         Redisson
自己拼命令     用 Spring 的模板       用现成的锁对象
```

### 方式 1：Jedis（最底层，最透明）

#### 加锁

```java
import redis.clients.jedis.Jedis;
import java.util.Collections;
import java.util.UUID;

public class JedisLockDemo {

    private static final String INSTANCE_ID = UUID.randomUUID().toString();

    /** 解锁脚本：Lua 保证「校验身份 + 删除」是原子的 */
    private static final String UNLOCK_LUA =
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "  return redis.call('del', KEYS[1]) " +
            "else return 0 end";

    public boolean submitOrder(Jedis jedis, Long orderId) {
        String lockKey = "oms:oa:submit:order:" + orderId;
        String holderId = INSTANCE_ID + ":" + Thread.currentThread().getId();
        String lockValue = holderId;
        boolean locked = false;

        try {
            // ① 加锁：一条命令，NX 不存在才写，EX 120 秒过期
            String result = jedis.set(lockKey, lockValue, "NX", "EX", 120);
            locked = "OK".equals(result);

            if (!locked) {
                // 没抢到锁
                throw new RuntimeException("订单正在提交OA，请勿重复操作");
            }

            // ② 业务逻辑
            doBusiness(orderId);
            return true;

        } finally {
            // ③ 解锁：只有确实持锁了才尝试解锁
            if (locked) {
                jedis.eval(UNLOCK_LUA,
                        Collections.singletonList(lockKey),   // KEYS[1] = 锁名
                        Collections.singletonList(holderId)); // ARGV[1] = 持有者标识
            }
        }
    }

    private void doBusiness(Long orderId) {
        // 查状态、调 OA、更新状态……
    }
}
```

#### 逐行讲解

| 代码 | 说明 |
| --- | --- |
| `INSTANCE_ID = UUID.randomUUID()` | 应用启动时生成一次，代表当前 JVM 进程 |
| `holderId = INSTANCE_ID + ":" + threadId` | 全局唯一的持有者标识 |
| `jedis.set(key, value, "NX", "EX", 120)` | 一条原子的 SET 命令 |
| `"OK".equals(result)` | Jedis 返回 `"OK"` 或 `null`，**注意用 `"OK".equals(...)`，常量写在前面防 NPE** |
| `jedis.eval(lua, keys, args)` | 执行 Lua；`singletonList` 是单元素列表，因为 EVAL 的 KEYS/ARGV 都要传 List |
| `finally` 里解锁 | **必须放 finally**，否则业务抛异常就永远不解锁，只能等超时 |

#### 特点

- ✅ **直接、透明**：你能看到每一个字节，适合学习原理、排查问题。
- ✅ 不依赖 Spring 生态，任何 Java 项目都能用。
- ❌ **解锁必须自己写 Lua**，忘了写或者写错就是线上事故。
- ❌ 没有可重入、没有自动续租、没有等待重试，要什么自己实现。
- ❌ 连接管理要自己搞（生产环境应该用 `JedisPool`，不要每次 new 一个 Jedis）。

---

### 方式 2：RedisTemplate（Spring 项目里最常用）

#### 加锁

```java
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import java.util.Collections;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Service
public class OrderService {

    private static final String INSTANCE_ID = UUID.randomUUID().toString();

    private static final String UNLOCK_LUA =
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "  return redis.call('del', KEYS[1]) " +
            "else return 0 end";

    private static final DefaultRedisScript<Long> UNLOCK_SCRIPT =
            new DefaultRedisScript<>(UNLOCK_LUA, Long.class);

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    public void submitOrder(Long orderId) {
        String lockKey = "oms:oa:submit:order:" + orderId;
        String holderId = INSTANCE_ID + ":" + Thread.currentThread().getId();
        Boolean locked = false;

        try {
            // ① 加锁：等价于 SET key value NX EX 120
            locked = stringRedisTemplate.opsForValue()
                    .setIfAbsent(lockKey, holderId, 120, TimeUnit.SECONDS);

            if (!Boolean.TRUE.equals(locked)) {
                throw new CommonException("订单正在提交OA，请勿重复操作");
            }

            // ② 业务逻辑
            doBusiness(orderId);

        } finally {
            // ③ 解锁：执行 Lua 脚本
            if (Boolean.TRUE.equals(locked)) {
                stringRedisTemplate.execute(
                        UNLOCK_SCRIPT,
                        Collections.singletonList(lockKey),  // KEYS
                        holderId);                            // ARGV
            }
        }
    }
}
```

#### 逐行讲解

| 代码 | 说明 |
| --- | --- |
| `setIfAbsent(k, v, 120, SECONDS)` | 名字就是「不存在才设置」，等价于 `SET k v NX EX 120` |
| 返回 `Boolean` | `true` = 抢到，`false` = 没抢到，`null` = 管道/事务场景，所以用 `Boolean.TRUE.equals(...)` 更稳 |
| `DefaultRedisScript<>(lua, Long.class)` | 把 Lua 包成一个可复用的脚本对象；`Long.class` 是**返回类型**（Lua 的整数映射为 Long） |
| `redisTemplate.execute(script, keys, args)` | 注意签名：第二个参数是 `List<K> keys`，后面可变参数是 ARGV |
| `StringRedisTemplate` | **重点！** 见下面的坑 |

#### ⚠️ 坑：用 `RedisTemplate` 还是 `StringRedisTemplate`？

这是新手在 Spring 项目里最容易踩的坑之一。

`RedisTemplate`（泛型版）默认使用 **JDK 序列化**（`JdkSerializationRedisSerializer`），也就是说：

- 你 `set` 进去的字符串，在 Redis 里看到的是一堆带二进制前缀的乱码。
- 你 `execute` 脚本时传的 `keys` / `args`，也会被序列化器处理。
- Lua 里的 `redis.call('get', KEYS[1]) == ARGV[1]` 比较的就不是「人类可读的字符串」，而是序列化后的字节——虽然两边序列化方式一致时可能"恰好能用"，但极其脆弱：一旦换了序列化器、换了 Spring 版本，或者用 redis-cli 去查数据，就会对不上。

**正确做法**：

```java
// 方案 A（推荐）：加锁专用的模板，用 String 序列化
@Bean("lockRedisTemplate")
public StringRedisTemplate lockRedisTemplate(RedisConnectionFactory factory) {
    return new StringRedisTemplate(factory);   // key/value/hashKey/hashValue 全是 String 序列化
}

// 方案 B：给现有的 RedisTemplate 显式设置序列化器
redisTemplate.setKeySerializer(new StringRedisSerializer());
redisTemplate.setValueSerializer(new StringRedisSerializer());
```

**结论：涉及锁、计数、Lua 脚本的 Redis 操作，一律用 `StringRedisTemplate`（或显式配置 String 序列化器）。**

#### 坑：老版本 Spring Data Redis 的原子性

你自己贴的那句备注是对的，值得展开说：

> `setIfAbsent(key, value, timeout, unit)` 底层就是 `SET key value NX EX timeout`。

- **Spring Data Redis 2.1+（Spring Boot 2.1+）**：这是一个**原子**操作，一条命令搞定 ✅
- **更老的版本**：底层是 `SETNX` + `EXPIRE` 两条命令，中间有窗口，理论上存在「设了 key 但没设过期时间」的隐患 ⚠️

**怎么确认自己用的是哪种？** 看 Spring Boot 版本：

```
Spring Boot 2.1+  →  Spring Data Redis 2.1+  →  原子 ✅
Spring Boot 2.0 及以前  →  建议手写 Lua 或改用新版本
```

现在（2020 年之后）新起项目基本都是 2.1+，可以放心用。但如果你维护的是老项目，**请务必确认版本**。

#### 特点

- ✅ Spring 生态里最顺手，依赖已经在项目里了，不用额外引入。
- ✅ 单命令加锁天然原子（2.1+）。
- ❌ **解锁还是要自己写 Lua**。
- ❌ **可重入要自己搞**（用 Hash 结构 + `hincrby`，写起来很啰嗦）。
- ❌ **自动续租要自己搞**（起个定时任务，还得处理各种边界）。
- ❌ 序列化器配置是个隐藏陷阱。

> 一句话：RedisTemplate 帮你省了「拼 SET 命令」这一小步，但**解锁、重入、续租这三块硬骨头全得你自己啃**。

---

### 方式 3：Redisson（封装最全，生产首选）

#### 加锁

```java
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import java.util.concurrent.TimeUnit;

@Service
public class OrderService {

    @Autowired
    private RedissonClient redissonClient;

    public void submitOrder(Long orderId) {
        // ① 拿到锁对象（注意：getLock 不会真的加锁，只是拿一个"句柄"）
        RLock lock = redissonClient.getLock("oms:oa:submit:order:" + orderId);

        boolean locked = false;
        try {
            // ② 加锁：waitTime=0 不排队，leaseTime=120 秒后自动释放
            locked = lock.tryLock(0, 120, TimeUnit.SECONDS);

            if (!locked) {
                throw new CommonException("订单正在提交OA，请勿重复操作");
            }

            // ③ 业务逻辑
            doBusiness(orderId);

        } catch (InterruptedException e) {
            // tryLock 会抛 InterruptedException，别吞掉
            Thread.currentThread().interrupt();
            throw new CommonException("加锁被中断");
        } finally {
            // ④ 解锁：只有当前线程持锁才解
            if (locked && lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }
}
```

#### 逐行讲解

| 代码 | 说明 |
| --- | --- |
| `getLock(key)` | 只是**获取一个锁对象**，不产生任何 Redis 操作。同一把 key 每次调用返回的是新对象，但操作的是同一把 Redis 锁 |
| `tryLock(0, 120, SECONDS)` | 参数1 = `waitTime` **等待时间**；参数2 = `leaseTime` **租约时间**；参数3 = 单位 |
| `waitTime = 0` | **不排队**：尝试一次，拿不到立刻返回 `false`（适合「重复提交直接拒绝」） |
| `leaseTime = 120` | 锁最多活 120 秒，**到点强制释放，且不会自动续租**（详见第八章） |
| `isHeldByCurrentThread()` | **关键**：判断「当前线程是否还持有这把锁」。不过这个检查，一旦锁已经超时释放、又被别人拿走，`unlock()` 会抛 `IllegalMonitorStateException` |
| `lock.unlock()` | 里面有内置 Lua：校验身份 → `hincrby -1` 减重入计数 → 减到 0 才 `del` |

> 注意 `unlock()` 必须在 **finally** 里，并且要配合 `locked` 判断——没抢到锁的人不能去解锁。

#### Redisson 内置帮你搞定了什么

| 能力 | 实现方式 |
| --- | --- |
| **加锁** | 内置 Lua 脚本，一条命令完成判断 + 写入 + 设置过期 |
| **解锁** | 内置 Lua：`hexists` 校验身份 → `hincrby -1` → 减到 0 才 `del` |
| **防误删** | 解锁脚本里校验 `uuid:threadId`，不是自己的锁直接抛异常/不删 |
| **可重入** | 用 **Hash 结构**存锁，field = `uuid:threadId`，value = 重入次数。同一线程再进一次就 `hincrby +1` |
| **自动续租** | 「看门狗」后台定时任务，默认每 10 秒把 30 秒的租约刷回 30 秒（**仅在不传 leaseTime 时启用**） |
| **等待重试** | `waitTime` 参数，内部通过订阅 Redis 的发布订阅频道来感知锁释放，比轮询高效 |
| **公平锁** | `redissonClient.getFairLock(key)`，按请求顺序排队 |
| **读写锁** | `redissonClient.getReadWriteLock(key)`，读读不互斥 |
| **联锁** | `redissonClient.getMultiLock(l1, l2, ...)`，多把锁同时加 |

#### Redisson 加锁脚本长什么样

了解底层有助于理解为什么它"看起来什么都能干"。加锁脚本大致是（简化版）：

```lua
-- KEYS[1] = 锁名；ARGV[1] = 过期时间毫秒；ARGV[2] = uuid:threadId
if (redis.call('exists', KEYS[1]) == 0) then
    -- 锁不存在 → 用 Hash 结构创建，重入次数 = 1
    redis.call('hincrby', KEYS[1], ARGV[2], 1);
    redis.call('pexpire', KEYS[1], ARGV[1]);
    return nil;                          -- 返回 nil 表示加锁成功
end;

if (redis.call('hexists', KEYS[1], ARGV[2]) == 1) then
    -- 锁存在，但持有者就是我 → 重入，次数 +1
    redis.call('hincrby', KEYS[1], ARGV[2], 1);
    redis.call('pexpire', KEYS[1], ARGV[1]);
    return nil;
end;

-- 锁被别人占着 → 返回剩余存活时间（毫秒），客户端据此决定等多久
return redis.call('pttl', KEYS[1]);
```

解锁脚本（简化版）：

```lua
-- KEYS[1] = 锁名；KEYS[2] = 发布订阅频道；ARGV[1] = 解锁消息；ARGV[2] = uuid:threadId；ARGV[3] = 过期时间
if (redis.call('hexists', KEYS[1], ARGV[2]) == 0) then
    return nil;                          -- 锁不是我的 → 什么都不做（客户端会抛异常）
end;

local counter = redis.call('hincrby', KEYS[1], ARGV[2], -1);  -- 重入次数 -1
if (counter > 0) then
    redis.call('pexpire', KEYS[1], ARGV[3]);   -- 还有外层调用没退出，续一下期，不删
    return 0;
else
    redis.call('del', KEYS[1]);                -- 重入次数归零 → 真正释放锁
    redis.call('publish', KEYS[2], ARGV[1]);   -- 通知正在排队等待的客户端
    return 1;
end;
```

看明白这两段，你就理解了**「Redisson 帮你省了多少事」**，也理解了**「自己手写为什么累」**。

#### 特点

- ✅ 加锁/解锁全内置，不用担心写错 Lua。
- ✅ 解锁自动校验身份，不会误删别人的锁。
- ✅ 支持可重入、自动续租、等待重试、公平锁、读写锁。
- ✅ 生产环境事实标准，社区活跃。
- ❌ 多一个依赖（`redisson-spring-boot-starter`）。
- ❌ 封装太深，出问题时排查需要看源码（但比你自己写错强）。
- ❌ 注意 `tryLock` 的 `InterruptedException` 处理，注意 `unlock` 的 `IllegalMonitorStateException`。

---

## 第七章 三者对照表与本质对应关系

### 7.1 对照表

| 维度 | Jedis | RedisTemplate | Redisson |
| --- | --- | --- | --- |
| **加锁一行代码** | `set(k, v, "NX", "EX", 120)` | `setIfAbsent(k, v, 120, SECONDS)` | `lock.tryLock(0, 120, SECONDS)` |
| **返回值** | `"OK"` / `null` | `true` / `false` / `null` | `true` / `false`（抛 `InterruptedException`） |
| **加锁原子性** | ✅ 单命令 | ✅ 单命令（2.1+） | ✅ Lua 脚本 |
| **解锁** | 自己写 Lua | 自己写 Lua | `lock.unlock()` |
| **防误删** | 靠自己写 Lua | 靠自己写 Lua | ✅ 内置（校验 uuid:threadId） |
| **可重入** | ❌ | ❌ | ✅ `hincrby` |
| **自动续租** | ❌ | ❌ | ✅ 看门狗（不传 leaseTime 时） |
| **等待重试** | ❌ | ❌ | ✅ `waitTime` + 发布订阅 |
| **公平锁** | ❌ | ❌ | ✅ `getFairLock` |
| **读写锁** | ❌ | ❌ | ✅ `getReadWriteLock` |
| **依赖** | `jedis` | `spring-data-redis` | `redisson`（或 `redisson-spring-boot-starter`） |
| **学习价值** | 高（看得到原理） | 中 | 低（但用得最多） |
| **生产推荐度** | 了解原理用 | 简单场景可用 | ⭐ 首选 |

### 7.2 本质对应关系：`SET NX EX` 与 Redisson 的 Lua 是同一件事

把两者并排看，你会发现**Redisson 只是把「加锁」这一件事做了加法**：

```
基础版（SET NX EX）做的事：
┌──────────────────────────────────────────────┐
│  key 不存在？                                 │
│    ├─ 是 → 写入 key=value，设置过期时间 → 成功 │
│    └─ 否 → 失败                               │
└──────────────────────────────────────────────┘

Redisson 做的事（在基础版之上加了两个分支）：
┌──────────────────────────────────────────────┐
│  key 不存在？                                 │
│    ├─ 是 → hset key uuid:threadId 1，pexpire  │
│    │      → 成功，并启动看门狗续租             │
│    └─ 否 → 持有者是我吗？                     │
│            ├─ 是 → hincrby +1（重入），续期     │
│            │      → 成功                       │
│            └─ 否 → 失败，返回剩余存活时间       │
│                   （客户端据此决定等多久）      │
└──────────────────────────────────────────────┘
```

解锁同理：

```
基础版（需要自己写）：               Redisson 内置：
┌────────────────────────┐         ┌────────────────────────────────┐
│ get key                │         │ hexists 校验身份                │
│   == holderId ?        │         │   ↓                            │
│   ├─ 是 → del key      │         │ hincrby -1（重入次数减一）      │
│   └─ 否 → 不动         │         │   ↓                            │
└────────────────────────┘         │ 减到 0 → del key + 通知等待者   │
                                   │ 还有值 → pexpire 续期，不删      │
                                   └────────────────────────────────┘
```

**结论**：

- `SETNX + EX` 只覆盖了「最基础的加锁」——占坑 + 别人进不来 + 自动过期。
- Redisson 的 Lua 覆盖了「加锁 + 重入 + 身份校验 + 续租启动 + 失败时告知剩余时间」——一整套。

所以**不是两套不同的东西，而是同一个思路的「基础版」和「完整版」**。

---

## 第八章 Redisson 到底会不会自动续租

**结论先说：取决于你调用加锁方法时有没有传 `leaseTime`。传了就一定不会续租，不传才会启用看门狗。**

### 8.1 什么情况下会自动续租

只有一种情况：**你没有指定租约时间**，也就是让 Redisson 用默认值。

```java
// ✅ 会自动续租（看门狗启动）
lock.lock();

// ✅ 会自动续租（leaseTime 传 -1，表示用默认值）
lock.tryLock(10, TimeUnit.SECONDS);              // 只有 waitTime
lock.tryLock(10, -1, TimeUnit.SECONDS);          // 显式传 -1
```

### 8.2 看门狗的工作方式

```
加锁成功
   │
   ├─ 锁的初始过期时间 = 30 秒（默认值，可配置）
   │
   ├─ 启动一个后台定时任务，每隔 10 秒（= 30 / 3）跑一次
   │      │
   │      ├─ 当前线程还持有这把锁吗？
   │      │     ├─ 是 → 把过期时间重新刷回 30 秒
   │      │     └─ 否 → 停止续租
   │      │
   │      └─ 循环，直到锁被主动释放 / 线程终止 / 客户端下线
   │
   └─ 客户端宕机 → 定时任务消失 → 30 秒后锁自动过期 → 不会死锁 ✅
```

关键数字：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `lockWatchdogTimeout` | `30000` 毫秒（30 秒） | 锁的默认租约时间，也是每次续租刷新的目标值 |
| 续租间隔 | `lockWatchdogTimeout / 3` = 10 秒 | 每 10 秒检查并续一次 |
| 配置方式 | `config.setLockWatchdogTimeout(ms)` | 可以在 `RedissonClient` 初始化时改 |

**看门狗的意义**：只要你业务还在跑并且没崩，锁就一直不过期。业务跑 5 分钟，锁就续到 5 分钟。既解决了「业务超时锁提前释放」，又保留了「进程死亡后锁自动释放」。

### 8.3 什么情况下不会续租（你贴的代码就是这种）

```java
lock.tryLock(0, 120, TimeUnit.SECONDS);
//                ↑
//          leaseTime = 120，明确指定了
```

**一旦显式指定了 `leaseTime`，看门狗机制被禁用。**

- 锁的过期时间被硬编码为 120 秒。
- 120 秒倒计时开始，**不会有任何续租**。
- 120 秒一到，无论业务有没有执行完，锁都会被释放。

```
数值上区分：

leaseTime = -1  或  不传  →  看门狗生效，自动续租 ✅
leaseTime >= 0（比如 120）  →  看门狗关闭，到点强制释放 ⚠️
```

> 注意 `lock.lock(10, TimeUnit.SECONDS)` 也是显式指定 leaseTime，同样不续租。

### 8.4 两种选择的取舍

| | 用看门狗（不传 leaseTime） | 用固定租约（传 leaseTime） |
| --- | --- | --- |
| **优点** | 业务多久都不怕锁提前释放 | 行为可控、可预测，不会无限续租 |
| **优点** | 进程死了会自动释放 | Redis 上不会长期挂着一把锁 |
| **缺点** | 如果业务卡死（比如死循环），锁会被无限续租，别人永远拿不到  | 业务超过租约时间 → 锁提前释放 → 并发问题 |
| **适合** | 业务耗时不确定、有明确退出的场景 | 业务耗时可预估，或者想强制「超时就失败」 |

**实践建议**：

1. **优先「固定租约 + 业务幂等」**：明确知道业务最长跑多久，就设一个略大于它的租约（比如业务最长 30 秒，租约给 120 秒），同时在业务层做幂等兜底。
2. **实在估不准就用看门狗**，但要给业务加上**超时熔断**（比如给内部调用设置超时时间），否则业务卡死会变成「永久占锁」。
3. **无论选哪种，业务都必须幂等**。分布式锁只是「降低并发概率」，不是「绝对互斥」——主从切换、网络分区都可能导致锁失效。**数据库唯一索引 / 状态机校验才是最后一道防线。**

### 8.5 一个需要注意的边界问题

Redisson 社区曾报告过一个**看门狗的竞态缺陷**，大致场景是：

```
1. 线程 A 加锁成功，看门狗准备启动续租任务
2. 线程 A 被中断（interrupt）或解锁
3. unlock() 的「取消续租」操作先执行了
4. 然后加锁流程的「启动续租」才执行
   → 取消"落空"，续租任务被启动了却没人取消
5. 结果：锁已经被释放，但看门狗还在一直续租 
```

这属于**极其罕见的边界情况**（需要精确的时序巧合），但如果你的系统高度依赖看门狗的可靠性，需要知道这个理论风险。

**规避思路**：要么用固定租约（不依赖看门狗），要么升级到包含修复的 Redisson 版本，要么让业务本身幂等（即使锁失效也不会出数据问题）。

### 8.6 一句话总结本章

> **不传 `leaseTime` → 看门狗自动续租（默认 30 秒租约，每 10 秒续一次）；传了 `leaseTime` → 不续租，到点强制释放。**
> `tryLock(0, 120, SECONDS)` 传了 120，所以**不会续租**。

---

## 第九章 实战：一个能直接抄的完整例子

### 9.1 场景

订单提交到 OA 系统。要求：

- 同一个订单不能重复提交
- 多实例部署下依然有效
- 失败要给出友好提示

### 9.2 Redisson 版（推荐）

```java
@Slf4j
@Service
public class OaSubmitService {

    /** 锁的 key 前缀，统一管理方便排查 */
    private static final String LOCK_KEY_PREFIX = "oms:oa:submit:order:";

    /** 租约时间（秒）：业务最长执行时间的 3~4 倍，且不会自动续租 */
    private static final long LEASE_SECONDS = 120;

    @Autowired
    private RedissonClient redissonClient;

    @Autowired
    private OrderMapper orderMapper;

    @Autowired
    private OaClient oaClient;

    public void submitToOa(Long orderId) {
        String lockKey = LOCK_KEY_PREFIX + orderId;
        RLock lock = redissonClient.getLock(lockKey);

        boolean locked = false;
        try {
            // waitTime=0：不排队，拿不到立刻失败（重复提交就该被拒绝）
            locked = lock.tryLock(0, LEASE_SECONDS, TimeUnit.SECONDS);

            if (!locked) {
                log.warn("订单 {} 正在提交OA，本次请求被拒绝", orderId);
                throw new BizException("订单正在提交OA，请勿重复操作");
            }

            // ---------- 锁内业务 ----------
            // 1) 先做一次幂等校验（双保险）
            Order order = orderMapper.selectById(orderId);
            if (order == null) {
                throw new BizException("订单不存在");
            }
            if (OrderStatus.OA_SUBMITTED == order.getStatus()) {
                log.info("订单 {} 已经提交过OA，直接返回", orderId);
                return;
            }

            // 2) 调 OA
            oaClient.submit(order);

            // 3) 更新状态
            orderMapper.updateStatus(orderId, OrderStatus.OA_SUBMITTED);

        } catch (InterruptedException e) {
            // tryLock 会抛这个异常，必须处理：恢复中断标记 + 不要吞掉
            Thread.currentThread().interrupt();
            throw new BizException("提交被中断，请稍后重试");
        } finally {
            // 只有「确实抢到了锁」并且「锁还在自己手上」才解锁
            if (locked && lock.isHeldByCurrentThread()) {
                try {
                    lock.unlock();
                } catch (Exception e) {
                    // 解锁失败不应该影响业务结果，但要打日志
                    log.error("解锁失败 lockKey={}", lockKey, e);
                }
            }
        }
    }
}
```

### 9.3 自定义注解 + AOP 版（想更进一步可以看）

如果这种加锁逻辑在项目里到处都是，可以抽成注解：

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface RedisLock {

    /** 锁的 key，支持 SpEL，例如 "#orderId" */
    String key();

    /** 锁的 key 前缀 */
    String prefix() default "";

    /** 租约时间（秒） */
    long leaseSeconds() default 120;

    /** 拿不到锁时的提示 */
    String message() default "操作正在进行中，请勿重复操作";
}
```

```java
@Aspect
@Component
public class RedisLockAspect {

    @Autowired
    private RedissonClient redissonClient;

    @Around("@annotation(redisLock)")
    public Object around(ProceedingJoinPoint pjp, RedisLock redisLock) throws Throwable {
        String key = redisLock.prefix() + parseKey(pjp, redisLock.key());
        RLock lock = redissonClient.getLock(key);

        boolean locked = false;
        try {
            locked = lock.tryLock(0, redisLock.leaseSeconds(), TimeUnit.SECONDS);
            if (!locked) {
                throw new BizException(redisLock.message());
            }
            return pjp.proceed();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new BizException("获取锁被中断");
        } finally {
            if (locked && lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }

    private String parseKey(ProceedingJoinPoint pjp, String spEl) {
        // 用 SpEL 解析方法参数，得到真正的 key（比如 orderId 的值）
        // 具体实现略，可参考 Spring 的 MethodBasedEvaluationContext
        return spEl;
    }
}
```

使用：

```java
@RedisLock(prefix = "oms:oa:submit:order:", key = "#orderId",
           leaseSeconds = 120, message = "订单正在提交OA，请勿重复操作")
public void submitToOa(Long orderId) {
    // 业务逻辑里完全不用关心锁了
}
```

> ⚠️ 注意：AOP 只能拦截 Spring Bean 的**外部调用**，同一个类内部 `this.method()` 调用不会走代理，注解会失效。这是 Spring AOP 的通用坑，不是锁的问题。

### 9.4 如果坚持用 RedisTemplate 手写

```java
@Slf4j
@Service
public class OaSubmitService {

    private static final String INSTANCE_ID = UUID.randomUUID().toString();
    private static final String UNLOCK_LUA =
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "  return redis.call('del', KEYS[1]) " +
            "else return 0 end";
    private static final DefaultRedisScript<Long> UNLOCK_SCRIPT =
            new DefaultRedisScript<>(UNLOCK_LUA, Long.class);

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    public void submitToOa(Long orderId) {
        String lockKey = "oms:oa:submit:order:" + orderId;
        String holderId = INSTANCE_ID + ":" + Thread.currentThread().getId();
        boolean locked = false;

        try {
            locked = Boolean.TRUE.equals(
                    stringRedisTemplate.opsForValue()
                            .setIfAbsent(lockKey, holderId, 120, TimeUnit.SECONDS));

            if (!locked) {
                throw new BizException("订单正在提交OA，请勿重复操作");
            }

            // 业务逻辑……

        } finally {
            if (locked) {
                try {
                    stringRedisTemplate.execute(
                            UNLOCK_SCRIPT,
                            Collections.singletonList(lockKey),
                            holderId);
                } catch (Exception e) {
                    log.error("解锁失败 lockKey={}", lockKey, e);
                }
            }
        }
    }
}
```

**注意这个版本的局限**：没有可重入、没有自动续租、业务超过 120 秒锁会提前释放。如果这些对你重要，请用 Redisson。

---

## 第十章 常见坑与 FAQ

### Q1：为什么不能 `SETNX` + `EXPIRE` 分两条命令写？

因为两条命令之间有窗口：`SETNX` 成功后进程崩了，`EXPIRE` 没执行，就产生了一把**永不过期的锁**——死锁。

**一条命令 `SET k v NX EX 120` 是原子的，没有这个窗口。**

### Q2：锁过期了但业务还没跑完，怎么办？

这是分布式锁最本质的难题。可选方案：

| 方案 | 说明 | 代价 |
| --- | --- | --- |
| **估算好时间** | 租约设成业务最长耗时的 3~4 倍 | 业务偶发超时还是会出问题 |
| **自动续租** | 用 Redisson 看门狗 | 业务卡死会变成永久占锁 |
| **业务幂等** | 数据库唯一索引、状态机校验 | ⭐ **必须做，这是最后的防线** |
| **把长任务拆短** | 加锁只保护「状态判断 + 打标记」，耗时操作放到锁外 | 需要重新设计流程 |

**关键认知**：任何分布式锁都无法 100% 保证互斥（Redis 主从切换时锁可能丢失）。**锁是「优化」，幂等才是「正确性保证」。**

### Q3：加了 Redis 锁就一定不会重复提交了吗？

**不是。** 至少这几种情况会失效：

- Redis 主从切换：主节点加了锁但还没同步到从节点，主挂了，从节点升主，锁丢了。
- 看门狗竞态（见 8.5）。
- 业务超过租约时间（见 Q2）。

所以：**Redis 锁做「减少并发」，数据库唯一索引 / 状态机做「兜底正确性」。** 两者都要有。

### Q4：锁的粒度怎么定？

**越细越好，但不要细到失去意义。**

```
❌ "order:lock"                        → 所有订单互相阻塞，性能灾难
❌ "order:submit"                     → 同上
✅ "oms:oa:submit:order:1001"         → 只锁 1001 这一单，正确
✅ "oms:push:shop:8888"               → 只锁 8888 这个店铺的推送，正确
```

**命名建议**：`业务域:子模块:动作:资源类型:资源ID`

```
oms : oa : submit : order : 1001
 ↑     ↑     ↑        ↑       ↑
订单   OA   提交     订单     订单ID
```

### Q5：解锁为什么要放在 `finally`？

不加 `finally`，业务代码一抛异常，`unlock()` 就永远执行不到，锁只能等过期。**期间别人全都进不来**，等于把「短暂的互斥」变成了「120 秒的阻塞」。

```java
// ✅ 正确
try {
    // 业务
} finally {
    unlock();
}
```

### Q6：`if (locked)` 判断没抢到锁的人还要不要解锁？

**不要。** 没抢到锁的人去 `unlock()` 会：

- Redisson：抛 `IllegalMonitorStateException`（因为它会校验身份）。
- 手写 Lua：Lua 校验不通过返回 0，锁不会被删（但如果搞错了 holderId 就可能删错）。

所以标准写法是：

```java
finally {
    if (locked && lock.isHeldByCurrentThread()) {
        lock.unlock();
    }
}
```

### Q7：`lock.isLocked()` 和 `lock.isHeldByCurrentThread()` 有什么区别？

| 方法 | 含义 | 用途 |
| --- | --- | --- |
| `isLocked()` | 这把锁**是否被任何客户端**持有 | 监控、判断 |
| `isHeldByCurrentThread()` | 这把锁**是否被当前线程**持有 | ⭐ **解锁前判断用这个** |

**解锁前一定要用 `isHeldByCurrentThread()`**，因为在「业务超时 → 锁被释放 → 别人拿走」的场景下，`isLocked()` 会返回 `true`（锁确实被锁着，只是不是你的），但它不能告诉你「锁还是不是你的」。

### Q8：`tryLock(0, ...)` 和 `tryLock()` 有什么区别？

```java
lock.tryLock()                              // 不等待，leaseTime 用默认（看门狗生效）
lock.tryLock(0, 120, TimeUnit.SECONDS)      // 不等待，leaseTime = 120（无看门狗）
lock.tryLock(10, 120, TimeUnit.SECONDS)     // 最多等 10 秒，leaseTime = 120（无看门狗）
lock.tryLock(10, TimeUnit.SECONDS)          // 最多等 10 秒，leaseTime 用默认（看门狗生效）
```

> ⚠️ `tryLock()` 会抛 `InterruptedException`（因为等待过程中可能被中断），必须处理。

### Q9：`lock()` 和 `tryLock()` 有什么区别？

```java
lock.lock(120, TimeUnit.SECONDS);   // 一直阻塞直到拿到锁（不推荐在生产用，可能永远阻塞）
lock.tryLock(...);                  // 有 waitTime 上限，拿不到就返回 false
```

**生产环境建议用 `tryLock`**，因为 `lock()` 会无限等待，一旦某个线程持锁不释放，其他线程会全部堆积，最终线程池被占满。

### Q10：可以用 Redis 锁做「秒杀扣库存」吗？

可以，但要小心：

- 锁粒度要细到 `sku:1001`，不能是全局。
- 高并发下 Redis 本身会成为瓶颈（虽然命令是 O(1)，但所有请求都去 SET 同一个 key，QPS 上限在几万级别）。
- 更好的方案是 `DECR` 原子扣减 + Lua 脚本，或者用 Redis 的 `INCRBY` 做预扣。

**锁适合「互斥」，不适合「高性能计数」。**

### Q11：Redisson 的锁对象是线程安全的吗？可以缓存起来复用吗？

- `RLock` 对象**不能被多个线程共享使用**（它内部记了当前线程），每次要用的时候 `getLock(key)` 拿一个新的。
- `getLock()` 本身很轻量，只是创建一个对象，**不产生 Redis 请求**，可以放心频繁调用。
- 但要注意：`RLock` 内部有 `ConcurrentHashMap` 缓存续租任务（`EXPIRATION_RENEWAL_MAP`），同一时刻同一个 `uuid:threadId` 只能有一个续租任务。

### Q12：Redis 集群模式下 Redisson 是怎么工作的？

- 普通的 `RLock` 只会锁在**一个节点**上（根据 key 的 hash slot 路由）。
- 如果这个节点宕机，锁可能丢失——这就是「主从切换丢锁」问题的来源。
- Redisson 也提供了 `RedissonRedLock`（红锁）和 `getMultiLock`，但需要注意的是，**红锁方案在分布式系统理论界存在争议**（Martin Kleppmann 与 Redis 作者 antirez 有过著名论战），实际使用时收益和成本需要权衡。
- 对绝大多数业务来说：**普通锁 + 幂等兜底**比「纠结红锁」务实得多。

### Q13：为什么锁的代码里要用 `"OK".equals(result)` 而不是 `result.equals("OK")`？

因为 `result` 可能是 `null`（没抢到锁时 Jedis 返回 `null`）。`null.equals(...)` 会抛 `NullPointerException`。

把常量写在前面（`"OK".equals(result)`）就永远不会 NPE。这是 Java 的通用技巧，叫「Yoda 条件」。

同理，RedisTemplate 的 `setIfAbsent` 返回 `Boolean`，也要用 `Boolean.TRUE.equals(locked)` 而不是 `locked`（自动拆箱可能 NPE）。

### Q14：`StringRedisTemplate` 能不能用 `RedisTemplate<String, Object>` 替代？

涉及锁和 Lua 的场景**强烈不建议**。原因见第六章「⚠️ 坑：用 `RedisTemplate` 还是 `StringRedisTemplate`？」那一节。

简单说：`RedisTemplate<String, Object>` 默认用 JDK 序列化，存进 Redis 的是二进制乱码，Lua 脚本里的字符串比较会变得不可控。

### Q15：业务里已经用了 `@Transactional`，加锁应该放事务里面还是外面？

**加锁要在事务外面，且在锁内提交事务。**

```java
// ✅ 正确
public void doSomething(Long id) {
    lock.lock();                     // 锁在事务外
    try {
        transactionTemplate.execute(status -> {   // 事务在锁内提交
            // 业务
            return null;
        });
    } finally {
        lock.unlock();
    }
}
```

```java
// ❌ 错误：@Transactional 在方法上，锁在方法内
@Transactional
public void doSomething(Long id) {
    lock.lock();
    try {
        // 业务
    } finally {
        lock.unlock();               // ⚠️ 这里事务还没提交！
    }
}
// unlock 之后、事务提交之前，别的请求可以拿到锁
// 但读到的还是"未提交的数据" → 脏读 → 重复处理
```

**原因**：`@Transactional` 的提交发生在方法返回时，而 `unlock()` 在方法内部。解锁那一刻事务还没提交，别的线程拿到锁后读到的还是旧数据。

### Q16：日志里要不要打锁的信息？

**要，而且很有用。**

```java
log.info("加锁成功 lockKey={} holderId={}", lockKey, holderId);
log.warn("加锁失败 lockKey={} holderId={}", lockKey, holderId);
log.error("解锁失败 lockKey={} holderId={}", lockKey, holderId, e);
```

排查「锁没释放」「误删了别人的锁」这类问题时，`holderId` 是关键线索——你能一眼看出是哪个 JVM、哪个线程干的。

### Q17：有没有更简单的替代方案？

看场景：

| 场景 | 更简单的方案 |
| --- | --- |
| 防重复提交（同一个用户短时间点两次） | 前端按钮置灰 + 后端令牌（Token）机制 + 数据库唯一索引 |
| 定时任务多实例只跑一个 | 分布式锁，或者用调度框架（XXL-JOB 自带分片/单机执行） |
| 数据一致性 | 数据库唯一索引 / `SELECT ... FOR UPDATE` / 乐观锁版本号 |
| 强一致的互斥 | ZooKeeper / etcd（CP 系统，比 Redis 更适合做「绝对互斥」） |

**Redis 锁是「简单、快、够用」，不是「绝对正确」。** 如果你的场景真的需要强一致，选 ZooKeeper 或 etcd。

---

## 附录 A 术语小词典

| 术语 | 白话解释 |
| --- | --- |
| **NX** | Not eXists，Redis 的「不存在才写入」条件 |
| **EX / PX** | 过期时间单位，EX = 秒（expire），PX = 毫秒（pexpire） |
| **原子性** | 一个操作要么全部完成、要么完全不做，中间不会被别人插队 |
| **Lua 脚本** | Redis 内置的脚本语言，脚本执行期间 Redis 不执行其他命令 → 天然原子 |
| **KEYS / ARGV** | Lua 脚本的两个参数数组，KEYS 装 key 名，ARGV 装普通参数（下标都从 1 开始） |
| **holderId** | 持有者标识，用来回答「这把锁是谁加的」 |
| **租约（lease）** | 锁的有效期，到点自动释放 |
| **续租** | 在租约到期前把有效期往后延 |
| **看门狗（Watchdog）** | Redisson 的后台定时任务，自动给锁续租 |
| **可重入** | 同一个线程可以重复加同一把锁，计数方式记录重入层数 |
| **死锁** | 锁永远不被释放，谁都拿不到 |
| **误删** | 解除了别人的锁（因为自己的锁已经超时易主） |
| **TTL** | Time To Live，剩余存活时间 |
| **PTTL** | 剩余存活时间，单位毫秒 |

---

## 附录 B 记忆速查卡

### 加锁一句话

```
SET lockKey holderId NX EX 120
     ↑        ↑      ↑  ↑   ↑
   锁的是谁  谁锁的  不存在 秒  120秒
```

### 解锁一句话

```
Lua：value 是我的 → 删；不是我的 → 不动。（必须原子，所以用 Lua）
```

### holderId 一句话

```
实例UUID + ":" + 线程ID
（只写线程ID，多实例会撞车）
```

### 三者一句话

```
Jedis：          set(k, v, "NX", "EX", 120)，解锁自己写 Lua
RedisTemplate：  setIfAbsent(k, v, 120, SECONDS)，解锁自己写 Lua
Redisson：       tryLock(0, 120, SECONDS) 一脚踢开，加解锁全内置
```

### 续租一句话

```
不传 leaseTime  →  看门狗生效，默认 30 秒租约，每 10 秒续一次
传了 leaseTime  →  不续租，到点强制释放
```

### 最重要的三句话

1. **加锁必须一条命令**（`SET NX EX`），不能 `SETNX` + `EXPIRE` 两条。
2. **解锁必须 Lua**（校验 value 后删除），不能无脑 `del`。
3. **锁是优化，幂等才是保证。** 数据库唯一索引/状态机兜底永远不能省。
