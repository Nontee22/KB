# try-with-resources

## 先给答案

```java
try (LockHandle ignored = submissionGuard.acquireOrder(id)) {
    干活();
    return "成功";
}
```

退出 `try` 块的那一刻，`close()` 一定会被调用。解锁就发生在那里，只是源码里看不到它。

这是 **javac 编译期**干的事：编译器把 `close()` 调用写进了你的方法体。不是 Spring，不是 Redisson，不是 JVM 的垃圾回收，也不是什么"框架的魔法"。

调用链只有三步：编译器插入的 `close()` → `RedissonLockHandle.close()` → `lock.unlock()`，Redis 里的锁键被删除。

## 三条执行路径

| 路径 | `close()` 会被调用吗 | 锁怎么释放 |
| --- | --- | --- |
| 正常 `return submitWithPreRegistration(...)` | 会 | 立刻 `unlock()`；若有活动事务，则移交给事务结束时执行 |
| `try` 块内抛出异常 | 会 | 同上（业务异常原样抛出交给 `catch`，释放动作不受影响） |
| 进程被 `kill -9` / 断电 / OOM Killer 干掉 | **不会** | 无人释放，等租约到期后 Redis 自动删除锁键 |

第三条是唯一逃得掉的情况：JVM 整个进程都没了，没有任何代码有机会运行。所以加锁时**必须显式传租约时间**（比如 120 秒），它是这种情况下最后一道兜底。

如果获取锁时不传租约，Redisson 会启用看门狗（watchdog）定时续期，锁一直活着——一旦进程被杀，这把锁就再也不会有谁来释放。

## `LockHandle` 是干嘛的

```java
@FunctionalInterface
public interface LockHandle extends AutoCloseable {
    @Override
    void close();
}
```

`AutoCloseable.close()` 声明的是 `void close() throws Exception`。这是个受检异常，意味着每个直接拿 `AutoCloseable` 当资源类型的地方，编译器都逼你 `catch` 或 `throws`：

```text
错误: 未报告的异常错误Exception; 必须对其进行捕获或声明以便抛出
对资源变量 'ignored' 隐式调用 close() 时抛出了异常错误
```

Java 有一条现成规则：子类型重写方法时，可以声明比父类型**更少**的受检异常。`LockHandle` 就是按这条规则把 `close()` 的异常收窄掉，于是调用方只需要处理自己的业务异常：

```java
try (LockHandle ignored = submissionGuard.acquireOrder(id)) {
    return submitWithPreRegistration(...);
} catch (Exception exception) {
    return OaUtils.buildErrorResponse(exception);
}
```

`LockHandle` 本身不含任何锁逻辑，它只是让"能放进 `try` 括号里"和"调用方不用被 `catch` 污染"这两件事同时成立。

`@FunctionalInterface` 的作用是让这个接口能用 lambda 实现，所以一个什么都不做的锁可以写成 `() -> { }`。

## 真锁与空锁

`acquireOrder(id)` 可能返回两种东西，调用方完全感觉不到差别：

| | 正常情况 | Redis 不可用时 |
| --- | --- | --- |
| `acquireOrder(id)` 返回 | `RedissonLockHandle` | `NO_OP_LOCK` |
| `close()` 的行为 | 注册事务回调，或立刻 `unlock()` | 什么都不做 |
| 互斥保护 | 有 | **没有** |

`RedissonLockHandle.close()` 里有两个分支，都只看它自己：

- 有活动事务：不立刻解锁，注册一个"事务结束后执行"的回调。否则事务还没提交，下一个线程进来查库看到的是旧数据，照样重复提交一次。
- 没有事务：直接 `unlock()`。解锁前先 `isHeldByCurrentThread()` 判断，防的是"锁已经过期"和"线程对不上"这两种尴尬。

Redis 挂了就返回 `NO_OP_LOCK`，业务代码继续往下跑，一行都不用改——这叫空对象模式。

**但代价要看清**：返回空锁等于互斥保护消失，两个线程可以同时进临界区。所以这是个业务降级决策：

- 锁只是"防用户手抖重复点提交"，降级通常可以接受，数据库唯一索引还能兜一道；
- 锁保护的是"资金扣减必须串行"这类硬约束，那"Redis 挂了就当没锁"必须重新评估。

## 三条最要命的坑

**一、把资源写在 `try` 的花括号里，而不是圆括号里。**

```java
// 错的：这不是 try-with-resources
try {
    LockHandle ignored = submissionGuard.acquireOrder(id);   // 只是个普通局部变量
    干活();
}
// 没有 finally，锁永远不会被主动释放
```

两个写法长得几乎一样，但资源只有在 `try` 后面的圆括号里才算"注册为资源"。后果很具体：锁不释放，只能等租约（比如 120 秒）过期，用户提交一次之后两分钟内提交不了第二次，还以为系统卡死了。

**二、别手动再调一次 `close()`。**

编译器已经调过一次，你再写一次就是释放两次。`RedissonLockHandle` 因为在 `unlock()` 里 catch 掉了 `RuntimeException`，重复调用相对安全，但那是它自己加的防护，不是 try-with-resources 的承诺。

**三、`close()` 抛异常，会让 `try` 里的 `return "成功"` 白写。**

`close()` 是在 `finally` 里执行的，它抛出的异常会让整个方法以异常结束，你算好的返回值被丢弃。这正是 `RedissonLockHandle` 要把 `unlock()` 包在 `catch (RuntimeException)` 里只打一行日志的原因：

```java
log.error("OA Redis锁释放失败，将等待租约过期，lockKey={}", lockKey, e);
```

取舍是：宁可让锁多活一会儿（等租约过期），也不让一个业务数据已经落库的请求因为解锁失败给用户报错。