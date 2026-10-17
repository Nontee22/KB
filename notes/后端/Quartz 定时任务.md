## 1. 先搞清楚：定时任务有几种选择？

| 方案 | 一句话说明 | 适用场景 |
|---|---|---|
| `@Scheduled` | Spring 自带，方法上加注解就行 | 单机、任务简单、丢了也无所谓 |
| **Quartz** | 功能强大的定时任务「库」，嵌在你的应用里 | 需要持久化（重启不丢）、集群（多机不重复） |
| XXL-JOB | 独立的调度「平台」，带 Web 管理界面 | 任务多、多机部署、想要可视化管理和监控 |

`@Scheduled` 的两个致命短板：

- 任务信息只在**内存**里，应用一重启就没了；
- 多台机器部署时，**每台机器都会执行一遍**，同一批订单被处理两次。

Quartz 正是为解决这两个问题而生的。

---

## 2. Quartz 的四个核心概念

Quartz 的设计思想就一句话：**把「做什么」和「什么时候做」分开**。

```
Job（做什么的代码）
   │
   ▼
JobDetail（任务的定义：执行哪个类、叫什么名字）
   │
   ├── 关联 ───▶ Trigger（什么时候做：Cron 表达式）
   │
   ▼
Scheduler（调度器：大管家，把两者撮合起来，到点就执行）
```

| 概念 | 类比 | 作用 |
|---|---|---|
| **Job** | 员工 | 写业务逻辑的类，实现 `Job` 接口，逻辑放在 `execute()` 方法里 |
| **JobDetail** | 岗位说明书 | 任务的定义：绑定哪个 Job 类、唯一标识（名字+组）、可传参数 |
| **Trigger** | 闹钟 | 定义执行时间规则：CronTrigger（日历式规则）、SimpleTrigger（固定间隔） |
| **Scheduler** | 领导 | 拿到 JobDetail 和 Trigger，到点就调用 Job 的 `execute()` |

**为什么拆成 JobDetail 和 Trigger 两个概念？** 为了灵活：

- 一个 JobDetail 可以绑定多个 Trigger（比如一个任务既每天早上跑，又每周一额外跑一次）；
- 换执行时间时只换 Trigger，Job 代码一行不用改。

---

## 3. 完整代码示例（Spring Boot + Quartz）

场景：**每 5 分钟扫描一次超时未支付订单并关闭**。

### 3.1 引入依赖（pom.xml）

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-quartz</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-jdbc</artifactId>
</dependency>
<!-- 数据库驱动，比如 mysql-connector-j -->
```

### 3.2 配置文件（application.yml）

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/yourdb?useUnicode=true&characterEncoding=utf8
    username: root
    password: root
  quartz:
    job-store-type: jdbc          # 持久化到数据库
    jdbc:
      initialize-schema: always   # 首次启动自动建 QRTZ_ 表；生产环境建议改为 never
    properties:
      org:
        quartz:
          scheduler:
            instanceName: MyScheduler
            instanceId: AUTO      # 集群时每个节点自动分配唯一 ID
          jobStore:
            class: org.quartz.impl.jdbcjobstore.JobStoreTX
            driverDelegateClass: org.quartz.impl.jdbcjobstore.StdJDBCDelegate
            tablePrefix: QRTZ_
            isClustered: true     # 开启集群，多机不重复执行
            clusterCheckinInterval: 10000
          threadPool:
            class: org.quartz.simpl.SimpleThreadPool
            threadCount: 10
```

### 3.3 Job 类：写业务逻辑的地方

```java
@DisallowConcurrentExecution   // 防止上一轮没跑完，下一轮又进来
public class UnpaidOrderJob implements Job {

    private static final Logger log = LoggerFactory.getLogger(UnpaidOrderJob.class);

    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        // Job 是 Quartz 用反射创建的，不归 Spring 管，不能直接 @Autowired
        // 只能手动从 Spring 容器里"捞" Bean
        OrderMapper orderMapper = SpringContextUtil.getBean(OrderMapper.class);

        try {
            List<Long> orderIds = orderMapper.selectTimeoutUnpaidOrderIds();
            log.info("本次扫描到超时未支付订单 {} 条", orderIds.size());
            for (Long orderId : orderIds) {
                orderMapper.closeOrder(orderId);
            }
        } catch (Exception e) {
            throw new JobExecutionException(e, false); // false = 不立即重试
        }
    }
}
```

### 3.4 Spring 容器工具类

```java
@Component
public class SpringContextUtil implements ApplicationContextAware {
    private static ApplicationContext context;

    @Override
    public void setApplicationContext(ApplicationContext applicationContext) {
        SpringContextUtil.context = applicationContext;
    }

    public static <T> T getBean(Class<T> clazz) {
        return context.getBean(clazz);
    }
}
```

### 3.5 Mapper 接口

```java
@Mapper
public interface OrderMapper {

    @Select("SELECT id FROM t_order WHERE status = 0 AND create_time < DATE_SUB(NOW(), INTERVAL 30 MINUTE)")
    List<Long> selectTimeoutUnpaidOrderIds();

    @Update("UPDATE t_order SET status = 2 WHERE id = #{id} AND status = 0")
    int closeOrder(Long id);
}
```

### 3.6 配置类：定义 JobDetail 和 Trigger

```java
@Configuration
public class QuartzConfig {

    /** 定义任务：做什么 */
    @Bean
    public JobDetail unpaidOrderJobDetail() {
        return JobBuilder.newJob(UnpaidOrderJob.class)
                .withIdentity("unpaidOrderJob", "orderGroup") // 唯一标识：名字+组
                .withDescription("扫描并关闭超时未支付订单")      // 描述，纯辅助信息
                .storeDurably()   // 没有 Trigger 时也保留 Job（默认会被删除）
                .build();
    }

    /** 定义触发器：什么时候做（每 5 分钟） */
    @Bean
    public Trigger unpaidOrderJobTrigger(JobDetail unpaidOrderJobDetail) {
        return TriggerBuilder.newTrigger()
                .forJob(unpaidOrderJobDetail)          // 绑定到上面的 JobDetail
                .withIdentity("unpaidOrderJobTrigger", "orderGroup")
                .withSchedule(CronScheduleBuilder.cronSchedule("0 */5 * * * ?")
                        .withMisfireHandlingInstructionDoNothing()) // 错过不补跑
                .build();
    }
}
```

### 3.7 运行流程

1. 启动应用，Spring Boot 自动配置调度器，Quartz 连接数据库（`QRTZ_` 表）；
2. `QuartzConfig` 里的 JobDetail 和 Trigger 被注册进调度器；
3. 每 5 分钟，Quartz 调用一次 `UnpaidOrderJob.execute()`；
4. 任务信息持久化在数据库，**重启后自动恢复**；多机部署时**集群锁保证同一任务只被一个节点执行**。

---

## 4. 新手最容易踩的坑

| 坑 | 说明 |
|---|---|
| Job 类必须有无参构造函数 | Quartz 通过反射实例化 Job，没有无参构造会在恢复任务时报错 |
| Job 里 `@Autowired` 默认失效 | Job 由 Quartz 创建，不是 Spring Bean，要用 `SpringContextUtil` 或自定义 JobFactory（见第 5 节） |
| 忘记 `storeDurably()` | 没绑定 Trigger 的 JobDetail 会被自动删除 |
| 忘记 `@DisallowConcurrentExecution` | 任务执行慢于触发间隔时，会并发跑多个实例 |
| misfire 策略选错 | 错过触发（停机、线程池满）后：`DoNothing` 不补跑（适合周期扫描）；`FireNow` 立即补跑（适合不能漏的业务） |
| 生产环境 `initialize-schema` 改为 never | 避免每次启动都尝试建表 |
| 集群 `instanceId` 重复 | 会导致数据库锁失效、任务重复执行，配 `AUTO` 即可 |

---

## 5. Job 里想用 `@Autowired` 怎么办？

三种注入方式对比：

| | SpringContextUtil | @Autowired | final 构造器注入 |
|---|---|---|---|
| 谁在操作 | 你手动调 getBean | Spring 自动注入 | Spring 自动注入 |
| 在 Quartz Job 里能用吗 | ✅ 能 | ❌ 默认失效 | ❌ 默认失效 |
| 代码风格 | 混入容器 API，不够优雅 | 干净 | 最规范（Spring 官方推荐） |

想让 `@Autowired` 在 Job 里生效？自定义一个 JobFactory，让 Spring 参与 Job 的创建：

```java
public class AutowiringSpringBeanJobFactory extends SpringBeanJobFactory {
    private final AutowireCapableBeanFactory beanFactory;

    public AutowiringSpringBeanJobFactory(ApplicationContext context) {
        this.beanFactory = context.getAutowireCapableBeanFactory();
    }

    @Override
    protected Object createJobInstance(TriggerFiredBundle bundle) throws Exception {
        Object job = super.createJobInstance(bundle);
        beanFactory.autowireBean(job); // 关键：让 Spring 给 Job 注入依赖
        return job;
    }
}
```

把它设置给 `SchedulerFactoryBean` 后，Job 里就能直接写 `@Autowired` 了。

**怎么选：**
- 不想改配置、能跑就行 → 用 `SpringContextUtil`；
- 希望代码风格统一 → 加自定义 JobFactory。
- 如果逻辑写在普通 `@Service` 里（`@Scheduled` 方案），直接用构造器注入即可，根本没这些麻烦。

---

## 6. 任务多了怎么办？

每个任务都需要一对 Bean：1 个 JobDetail + 1 个 Trigger。3 个任务就是 6 个 `@Bean`，10 个任务配置类会非常臃肿。

**解法：动态注册**——把任务定义抽成数据，循环注册，新增任务只需加一行：

```java
@Component
public class QuartzJobInitializer implements ApplicationRunner {

    @Autowired
    private Scheduler scheduler;

    private final List<JobConfig> jobConfigs = List.of(
        new JobConfig(UnpaidOrderJob.class, "unpaidOrderJob", "orderGroup", "0 */5 * * * ?"),
        new JobConfig(CleanLogJob.class,    "cleanLogJob",   "logGroup",   "0 0 2 * * ?"),
        new JobConfig(DailyReportJob.class, "dailyReportJob","reportGroup","0 0 8 * * ?")
    );

    @Override
    public void run(ApplicationArguments args) throws Exception {
        for (JobConfig config : jobConfigs) {
            JobKey jobKey = JobKey.jobKey(config.getJobName(), config.getJobGroup());

            // 重要！持久化模式下重启后数据库里已有任务，不判断会重复注册报错
            if (!scheduler.checkExists(jobKey)) {
                JobDetail jobDetail = JobBuilder.newJob(config.getJobClass())
                        .withIdentity(jobKey)
                        .storeDurably()
                        .build();
                Trigger trigger = TriggerBuilder.newTrigger()
                        .forJob(jobDetail)
                        .withIdentity(config.getJobName() + "Trigger", config.getJobGroup())
                        .withSchedule(CronScheduleBuilder.cronSchedule(config.getCron()))
                        .build();
                scheduler.scheduleJob(jobDetail, trigger);
            }
        }
    }
}
```

**怎么选：**
- 任务少（三五个）且固定 → `@Bean` 方式直白、好排查；
- 任务多、频繁增删、想做成配置化（存数据库/yml）→ 动态注册。

---

## 7. Cron 表达式速查

Quartz 的 Cron 是 **6 位起步**（秒 分 时 日 月 周），可加第 7 位「年」。⚠️ 和 Linux crontab（5 位、无秒）不一样，直接抄会错位！

### 字段含义

| 位置 | 字段 | 允许值 | 特殊字符 |
|---|---|---|---|
| 1 | 秒 | 0-59 | `, - * /` |
| 2 | 分 | 0-59 | `, - * /` |
| 3 | 时 | 0-23 | `, - * /` |
| 4 | 日 | 1-31 | `, - * ? / L W` |
| 5 | 月 | 1-12 或 JAN-DEC | `, - * /` |
| 6 | 周 | 1-7（**1=周日**）或 SUN-SAT | `, - * ? / L #` |
| 7 | 年（可选） | 1970-2099 | `, - * /` |

### 特殊字符

| 字符 | 含义 | 例子 |
|---|---|---|
| `*` | 任意值 | 秒位写 `*` = 每秒 |
| `?` | 不指定（日和周**必须有一个是 ?**） | |
| `-` | 范围 | `10-12` = 10、11、12 |
| `,` | 枚举 | `MON,WED,FRI` |
| `/` | 步长 | `*/5` = 每 5 个单位；`10/5` = 从 10 开始每 5 |
| `L` | 最后 | 日位 `L` = 当月最后一天 |
| `W` | 最近工作日 | `15W` = 离 15 号最近的工作日 |
| `#` | 第几个（仅周位） | `6#3` = 当月第 3 个周五 |

### 高频例子

| 表达式 | 含义 |
|---|---|
| `0 */5 * * * ?` | 每 5 分钟（全天 288 次）|
| `0 0/5 14 * * ?` | 只在 14 点这一小时内每 5 分钟（12 次）|
| `0 0 12 * * ?` | 每天中午 12 点 |
| `0 15 10 ? * MON-FRI` | 周一到周五 10:15 |
| `0 15 10 15 * ?` | 每月 15 号 10:15 |
| `0 15 10 L * ?` | 每月最后一天 10:15 |
| `0 15 10 ? * 6#3` | 每月第 3 个周五 10:15 |

**`*/5` vs `0/5`**：分字段里两者等价（起始值都是 0）。区别只在起始值不是最小值时体现，如 `10/5` = 从 10 分开始每 5 分钟。

**易错点：**
- 日和周不能同时写具体值，必须有一个是 `?`；
- 周字段 **1 = 周日**（不是周一），写 `MON-FRI` 更不容易错；
- `1/5` 在日字段是「从 1 号开始每 5 天」，跨月会重置，不支持精确的「每隔 N 天」语义。

---

## 8. 和 XXL-JOB 怎么选？

核心区别：**Quartz 是库（写代码配置），XXL-JOB 是平台（Web 界面管理）**。

| 维度 | Quartz | XXL-JOB |
|---|---|---|
| 架构 | 嵌入式，调度逻辑在你应用里 | 调度中心 + 执行器分离 |
| 任务管理 | 写代码定义 Job/Trigger | Web 界面在线增删改查、启停，即时生效 |
| 集群 | 数据库锁实现，配置复杂 | 原生分布式，支持轮询、故障转移等路由策略 |
| 监控告警 | 基础较弱，需自行扩展 | 内置实时日志、失败重试、邮件告警 |
| Cron | 6-7 位 | 兼容 Quartz 写法，可直接复用 |
| 上手成本 | 较高 | 低（写个注解方法 + 后台配一下） |

XXL-JOB 的代码极其简单——Job 就是一个普通 Spring Bean，`@Autowired` 直接用：

```java
@Component
public class UnpaidOrderJob {

    @Autowired
    private OrderMapper orderMapper;   // 正常注入，无需 SpringContextUtil

    @XxlJob("unpaidOrderHandler")      // 值要与调度中心配置的 JobHandler 一致
    public void checkUnpaidOrders() {
        List<Long> orderIds = orderMapper.selectTimeoutUnpaidOrderIds();
        for (Long orderId : orderIds) {
            orderMapper.closeOrder(orderId);
        }
    }
}
```

配置（application.yml）：

```yaml
xxl:
  job:
    admin:
      addresses: http://127.0.0.1:8080/xxl-job-admin  # 调度中心地址
    executor:
      appname: order-executor                          # 执行器应用名
      port: 9999
```

然后在 Web 后台：新建执行器（AppName = `order-executor`）→ 新建任务（JobHandler = `unpaidOrderHandler`，Cron = `0 */5 * * * ?`）→ 启动。

