# Redis 分布式锁

## 一、为什么单机锁不管用

`synchronized` 和 `ReentrantLock` 这类锁，本质是**在当前 JVM 的内存里记一个标记**：谁拿到了，别人就得排队。这个标记只存在于这一个 JVM 里。

真实项目为了扛流量和容错，同一个服务会部署多份：

```text
        用户点两次「提交 OA」
                │
  Nginx 负载均衡（可能把两次请求分到不同机器）
                │
   ┌────────────┴────────────┐
┌──▼────────┐          ┌────▼──────┐
│  实例 A   │          │  实例 B   │   ← 各记各的，互相看不见
│ lock=已占 │          │ lock=空闲 │
└───────────┘          └───────────┘
```

- 请求 1 落到实例 A，拿到 A 内存里的锁开始干活；请求 2 落到实例 B，看到 B 内存里的锁是空闲的，**也拿到锁了**。
- 结果：两个实例同时在处理同一个订单，`synchronized` 形同虚设。

错误方案：把 `synchronized` 换成 `ReentrantLock` 加个 `static`，或者把锁对象换成 `static final` —— `static` 也是「每个 JVM 一份」，还是只在一个 JVM 内有效。

正确思路：把锁标记放到一个**所有实例都能访问的外部系统**里。这个系统要满足四点：所有实例都能访问、读写足够快、支持「只有一个人能成功占位」的原子操作、能自动释放（超时），否则持锁的机器宕机就锁一辈子。Redis 恰好全中，这就是 Redis 分布式锁。

## 二、Redis 锁就一条命令

```java
String result = jedis.set(lockKey, holderId, "NX", "EX", 120);
boolean locked = "OK".equals(result);
```

| 位置 | 值 | 含义 | 最容易搞错的点 |
| --- | --- | --- | --- |
| 参数1 `lockKey` | `"oms:oa:submit:order:1001"` | **锁名**：锁的是哪一份资源 | 要细到「资源 ID」，写成固定的 `"order:lock"` 会让所有订单互相阻塞 |
| 参数2 `holderId` | `"3f2a-...-98b:14"` | **持有者标识**：谁锁的 | 不是随便填的常量，见第四节 |
| 参数3 `"NX"` | | **不存在才设置**（Not eXists）：坑里没人我才占 | 只要有人占着，就写不进去 |
| 参数4 `"EX"` | | 过期时间**单位是秒** | 换成 `"PX"` 就是毫秒，别混用 |
| 参数5 `120` | | **过期时间 = 120 秒** | 必须大于你的业务最长执行时间 |
| 返回值 | `"OK"` / `null` | `"OK"` = 抢到锁；`null` = 没抢到 | **不是布尔值！**写成 `if (result)` 编译都过不去 |

为什么一条命令就够？Redis 执行命令是串行的（Redis 6 之后网络 IO 用了多线程，真正执行命令还是串行），任何一条命令在执行过程中不可能被别的命令插队，所以「检查 key 在不在」和「写入 key」合在一条命令里，不可能两个人同时占位成功。

过期时间（EX）的大白话是这把锁的自动失效时间：实例 A 拿到锁之后机器被重启、进程被 kill -9、网络断了，没人会去删这把锁，到期自动释放，不会锁一辈子。所以加锁永远只用 `SET ... NX EX ...` 这一条，不能拆成 `SETNX` + `EXPIRE` 两条（第一条成功、第二条还没执行时进程挂了，就留下一把永不过期的锁，死锁）。

## 三、解锁必须用 Lua，而且必须校验 value

这是最容易写错、后果最严重的一环。

```java
// 错误写法
jedis.del(lockKey);
// 或
redisTemplate.delete(lockKey);
```

看起来没毛病：我加的锁我删掉。但看这条时间线：

```text
T0   请求1 加锁成功，租约 120 秒
T1   请求1 开始执行业务（慢 SQL / 第三方接口超时，跑了 150 秒）
T120 锁自动过期，key 被 Redis 删除                ← 分水岭
T121 请求2 加锁成功（key 已经不存在了），开始干自己的活
T150 请求1 跑完了，执行 jedis.del(lockKey)，删掉的是请求2 刚加的锁
T151 请求3 来加锁，又成功了 → 请求2 和请求3 同时在处理同一个订单
```

**`del` 是无差别的：它不看锁是谁的，只要 key 在就删。**

改成「先看 value 是不是我写的，再删」也不行：`get` 和 `del` 是两条独立命令，中间有缝隙——就在「查完确认是我的」和「执行删除」之间，锁可能过期并被请求2 抢走，这一 `del` 删的还是别人的锁。只要用了多条命令，这个窗口就永远存在。

唯一可靠的解法是把「判断 + 删除」合成一个不可分割的操作，也就是 Lua 脚本：

```lua
if redis.call('get', KEYS[1]) == ARGV[1] then   -- 锁里的 value 是我的吗？
    return redis.call('del', KEYS[1])            -- 是 → 删掉，返回 1
else
    return 0                                      -- 不是 → 什么都不做，返回 0
end
```

**Lua 脚本在 Redis 里是原子执行的**：脚本执行期间 Redis 不会去执行别的命令，「判断」和「删除」之间插不进任何操作，那个时间窗口被彻底堵死。

参数对应：`EVAL "脚本" 1 key1 arg1`，脚本里 `KEYS[1]` 是锁名，`ARGV[1]` 是持有者标识（注意 Lua 下标从 **1** 开始）。解锁时传的 holderId 必须和加锁时写进 value 的一模一样，只有这样才说明这把锁从头到尾都是我的。所以 value **不能是固定常量**：如果所有请求都写 `"lock"`，任何人解锁都能校验通过，防误删机制直接失效。

## 四、holderId 是什么

```java
// 应用启动时生成一次，代表「这个 JVM 进程 / 这个客户端实例」
private static final String INSTANCE_ID = UUID.randomUUID().toString();

// 每次加锁时拼上当前线程 ID
String holderId = INSTANCE_ID + ":" + Thread.currentThread().getId();
```

- 只写线程 ID 不行：线程 ID 只在单个 JVM 内唯一。实例 A 的线程 14 和实例 B 的线程 14 算出来都是 `"14"`，A 的锁超时易主之后，A 来解锁照样校验通过，删掉的是 B 的锁。
- 写固定常量等于没写：所有人都能校验通过，防误删失效。
- UUID 段保证跨实例唯一，线程 ID 段保证同实例内跨线程唯一，拼起来就是全局唯一。Redisson 内部用的就是这个格式。

## 五、三种写法怎么选

三种写法**本质完全一样**：都是往 Redis 里占一个带过期时间的坑，区别只在封装程度。

| 维度 | Jedis | RedisTemplate | Redisson |
| --- | --- | --- | --- |
| **加锁一行** | `set(k, v, "NX", "EX", 120)` | `setIfAbsent(k, v, 120, SECONDS)` | `lock.tryLock(0, 120, SECONDS)` |
| **返回值** | `"OK"` / `null` | `true` / `false` / `null` | `true` / `false`（会抛 `InterruptedException`） |
| **解锁** | 自己写 Lua | 自己写 Lua | `lock.unlock()` |
| **防误删** | 靠自己写 Lua | 靠自己写 Lua | 内置（校验 `uuid:threadId`） |
| **可重入** | 无 | 无 | 有（Hash 存 `uuid:threadId`，`hincrby` 计数） |
| **自动续租** | 无 | 无 | 有（看门狗，不传 `leaseTime` 时生效） |
| **生产推荐度** | 了解原理用 | 简单场景可用 | 首选 |

Redisson 完整可抄版：

```java
@Service
public class OrderService {

    @Autowired
    private RedissonClient redissonClient;

    public void submitOrder(Long orderId) {
        // getLock 不会真的加锁，只是拿一个「句柄」
        RLock lock = redissonClient.getLock("oms:oa:submit:order:" + orderId);
        boolean locked = false;
        try {
            // waitTime=0 不排队；leaseTime=120 到点强制释放，不会自动续租
            locked = lock.tryLock(0, 120, TimeUnit.SECONDS);
            if (!locked) {
                throw new CommonException("订单正在提交OA，请勿重复操作");
            }
            doBusiness(orderId);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();      // tryLock 会抛这个，别吞掉
            throw new CommonException("加锁被中断");
        } finally {
            // 只有当前线程还持锁才解锁
            if (locked && lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }
}
```

Jedis / RedisTemplate 的加锁也是两行，但解锁没有捷径，自己写上面那段 Lua：

```java
// Jedis：返回 "OK" 或 null，不是布尔值
boolean locked = "OK".equals(jedis.set(lockKey, holderId, "NX", "EX", 120));
// StringRedisTemplate（Spring Boot 2.1+ 底层就是 SET k v NX EX 120，单命令原子）
boolean locked = Boolean.TRUE.equals(stringRedisTemplate.opsForValue()
        .setIfAbsent(lockKey, holderId, 120, TimeUnit.SECONDS));
```

**坑：一定要用 `StringRedisTemplate`。** `RedisTemplate`（泛型版）默认用 JDK 序列化：你 `set` 进去的字符串在 Redis 里是一堆带二进制前缀的乱码，执行脚本时传的 keys / args 也会被序列化器处理。Lua 里的 `redis.call('get', KEYS[1]) == ARGV[1]` 比较的就不是人类可读的字符串，虽然两边序列化方式一致时可能「恰好能用」，但极其脆弱：一旦换了序列化器、换了 Spring 版本，或者用 redis-cli 去查数据，就会对不上。涉及锁、计数、Lua 脚本的 Redis 操作，一律用 `StringRedisTemplate`。

## 六、Redisson 的租约与看门狗

**租约（lease）** 就是锁的有效期，到点自动释放。要不要自动续租，只看你有没有传 `leaseTime`：

```java
// 不传 leaseTime → 看门狗自动续租
lock.lock();
lock.tryLock(10, TimeUnit.SECONDS);
// 传了 leaseTime → 不续租，到点强制释放
lock.tryLock(0, 120, TimeUnit.SECONDS);
lock.lock(10, TimeUnit.SECONDS);
```

**看门狗（Watchdog）** 是 Redisson 的后台定时任务，只在不传 `leaseTime` 时启用：锁的初始租约是 30 秒（默认值 `lockWatchdogTimeout`，可用 `config.setLockWatchdogTimeout(ms)` 改），后台任务每 10 秒（= 30 / 3）检查一次「当前线程是否还持有这把锁」，还持有就把过期时间刷回 30 秒，直到锁被主动释放、线程终止或客户端下线。客户端宕机则定时任务消失，30 秒后锁自动过期，不会死锁。一旦显式传了 `leaseTime`（比如 120，或 `lock.lock(10, TimeUnit.SECONDS)`），看门狗就被禁用：过期时间被定死，没有任何续租，到点无论业务有没有跑完，锁都会被释放。

两者取舍：看门狗不怕业务跑得久、进程死了也会自动释放，但业务卡死（比如死循环）会无限续租，别人永远拿不到；固定租约行为可控、不会无限续租，但业务超过租约时间锁就提前释放，会有并发问题。

一句话结论：**能估准业务耗时就用固定租约（设成业务最长耗时的 3~4 倍），估不准就用看门狗，并给业务加超时熔断。**

不管选哪种，业务都必须幂等。分布式锁只是「降低并发概率」，不是「绝对互斥」——主从切换、网络分区都可能让锁失效，**数据库唯一索引 / 状态机校验才是最后一道防线**。

## 七、五个坑速查

**1. `SETNX` + `EXPIRE` 分两条命令。** 中间进程崩了就留下一把永不过期的锁，直接死锁。加锁永远只用一条 `SET k v NX EX 120`。

**2. 业务超时，锁提前释放。** 锁没了第二个请求就进来了。租约设成业务最长耗时的 3~4 倍，或者交给看门狗续租；同时业务必须幂等兜底。

**3. 解锁必须放 `finally`。** 否则业务一抛异常，`unlock()` 永远执行不到，锁只能等过期，**期间别人全都进不来**，短暂的互斥变成了 120 秒的阻塞。

**4. 没抢到锁的人不要去 `unlock()`。** Redisson 会抛 `IllegalMonitorStateException`。标准写法是先判断 `if (locked && lock.isHeldByCurrentThread())`；别用 `isLocked()`，它只说明这把锁被任何客户端持有着，不能说明锁还是你的。

**5. 锁的粒度与命名。** 越细越好，但不要细到失去意义：`oms:oa:submit:order:1001` 只锁 1001 这一单，正确；`order:lock`、`order:submit` 让所有订单互相阻塞，是性能灾难。命名用 `业务域:子模块:动作:资源类型:资源ID`。

## 记忆速查卡

```text
加锁：SET lockKey holderId NX EX 120
           ↑        ↑      ↑  ↑   ↑
         锁的是谁  谁锁的  不存在 秒  120秒

解锁：Lua 里 value 是我的 → 删；不是我的 → 不动。（必须原子，所以用 Lua）

holderId：实例UUID + ":" + 线程ID（只写线程ID，多实例会撞车）

三者：Jedis：         set(k, v, "NX", "EX", 120)，解锁自己写 Lua
      RedisTemplate： setIfAbsent(k, v, 120, SECONDS)，解锁自己写 Lua
      Redisson：      tryLock(0, 120, SECONDS) 一脚踢开，加解锁全内置

续租：不传 leaseTime → 看门狗生效，默认 30 秒租约，每 10 秒续一次
      传了 leaseTime → 不续租，到点强制释放
```

最重要的三句话：

1. **加锁必须一条命令**（`SET NX EX`），不能 `SETNX` + `EXPIRE` 两条。
2. **解锁必须 Lua**（校验 value 后删除），不能无脑 `del`。
3. **锁是优化，幂等才是保证。** 数据库唯一索引 / 状态机兜底永远不能省。
