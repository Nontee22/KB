# 配置是怎么从 Nacos 跑到代码里的

## 一条链路

```
JVM 启动
  ↓
读 bootstrap.yml          ← 里面写着"Nacos 在哪"和"要拉哪份配置"
  ↓
拿这些信息去问 Nacos       ← 一次网络请求，Nacos 把配置文件的文本返回
  ↓
文本变成一堆 key-value     ← 这一堆东西统一叫 Environment（环境）
  ↓
绑定到 Java 对象           ← @ConfigurationProperties 把 integration.* 塞进 IntegrationConfig
  ↓
代码里读对象字段           ← integrationConfig.getSap().getEsb().getOrderCreateUrl()
```

**为什么要配置中心**：同一个程序要部署到多个环境（开发连 `192.168.61.221` 的库，生产连别的），而且改一个值不想重新打包发版。Nacos 就是把这些会变的值从代码和安装包里拿出去、集中存放的服务（本项目默认 `192.168.61.221:8848`）。本文只讲配置（`spring.cloud.nacos.config`），不讲服务注册。

---

## 定位一份配置靠三个坐标

一台 Nacos 上存着几十上百份配置，凭什么知道要哪一份？靠三个东西（一份配置的三维坐标）：

| 名字 | 作用 | 类比 |
|---|---|---|
| **namespace**（命名空间） | 最外层的隔离，通常是"环境"级别 | 楼盘 |
| **group**（分组） | 中间层，一般按用途分 | 楼栋 |
| **dataId** | 具体那一份配置的文件名 | 门牌号 |

坐标系定死了，拿到的就是唯一一份。**本项目要的是"public 命名空间下、`DEFAULT_GROUP` 里的 `winkey-lowcode-data.yml`"**（`dataId` 里的 `winkey-lowcode-data` 来自 `spring.application.name`，约定就是"服务名.yml"）：

| | 取值 | 从哪看出来 |
|---|---|---|
| namespace | **没设置**（用默认的 public） | `bootstrap.yml` 里 `#namespace:` 被注释掉了 |
| group | `DEFAULT_GROUP` | `bootstrap.yml` 里 `group: DEFAULT_GROUP` |
| dataId | `winkey-lowcode-data.yml` | 由 `prefix: winkey-lowcode-data` + `file-extension: yml` 拼出来，也在 `spring.config.import` 里显式写了一遍 |

> `bootstrap.yml` 里 `spring.cloud.nacos` 下面也有一个 `namespace`，那是 Nacos 的。代码里的常量 `PlatformChannel.NAMESPACE = "HZERO"`（在 `constant/PlatformChannel.java`）是 **H0 接口平台的命名空间**，跟 Nacos 无关。两者重名，注意区分。

---

## 启动六步

### 第 1 步：为什么先读 bootstrap.yml

**配置的地址本身也是配置。** 「Nacos 在 `192.168.61.221:8848`」这句话如果写在 `application.yml` 里，那读 `application.yml` 的时候还不知道要去 Nacos 拿配置——先有鸡还是先有蛋。

Spring 的解法是**引导上下文**（bootstrap context）：主程序创建之前，先跑一个临时的、很小的上下文，专门读 `bootstrap.yml`、把远程配置拉下来。这个机制默认**关闭**，要开必须引 `spring-cloud-starter-bootstrap`。本项目依赖链里有它，来自框架的父工程 `hzero-parent`：

```xml
<!--启动引导类，加载bootstrap.yml配置文件-->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-bootstrap</artifactId>
</dependency>
```

不引这个依赖，`bootstrap.yml` 会被 Spring Boot **完全忽略**，配置一整个拿不到，而且往往不报错，非常难查。

### 第 2 步：bootstrap.yml 里有什么

文件在 `src/main/resources/bootstrap.yml`，和 `application.yml` 放在一起。去掉注释后的关键部分：

```yaml
spring:
  config:
    import:
      - optional:nacos:winkey-lowcode-data.yml     # ① 要导入的远程配置
  cloud:
    nacos:
      config:
        server-addr: ${NACOS_CONFIG_SERVER_ADDR:192.168.61.221:8848}   # ② Nacos 在哪
        username: ${NACOS_CONFIG_USERNAME:nacos}
        password: ${NACOS_CONFIG_PASSWORD:nacos}
        file-extension: yml                        # ③ 文件格式
        group: DEFAULT_GROUP                       # ④ 分组
        enabled: true
        prefix: winkey-lowcode-data                # ⑤ 文件名前缀
```

**`${环境变量名:默认值}` 要讲透。** 意思是"优先用环境变量 `NACOS_CONFIG_SERVER_ADDR`；这个环境变量不存在，就用冒号后面的 `192.168.61.221:8848`"。同一个 key 有两层来源：开发同学本地跑不用配任何环境变量，默认值就够；正式部署时运维通过环境变量注入生产地址，**代码一行都不用改**。`application.yml` 里满屏都是这个写法。

**③④⑤ 拼出 dataId**：`prefix` + `file-extension` = `winkey-lowcode-data.yml`，就是上面那个门牌号。**① `spring.config.import` 是 Spring Boot 2.4 以后的新写法**，声明"除了本地文件，还要额外从某个地方导入配置"，`nacos:` 前缀由 Spring Cloud Alibaba 的解析器识别；前面的 `optional:` 意思是**"这份配置拿不到也不要让程序启动失败"**。

### 第 3 步：向 Nacos 发一次请求

输入是上面那三个坐标，输出是一段 yml **纯文本**（通信细节由 `nacos-client` 负责）。

### 第 4 步：文本变成 key-value，进 Environment

`integration.tms.direct.carrier-query-url: http://tms.example.com/api` 这样的一行文本，解析成同名的键值对，放进 **Environment（环境）**。它不只是个大 Map，还记录了每个 key **是从哪个来源拿到的**：Java 字段初始值、`application.yml`、`bootstrap.yml`、Nacos 下载的配置、操作系统环境变量、命令行参数。同一个 key 可以在多个来源里都有值，使用哪个见"一个值可能来自四个地方"。

### 第 5 步：绑定到 Java 对象

干这件事的类是 `src/main/java/org/hzero/lowcodedata/config/IntegrationConfig.java`。关键就是 `@ConfigurationProperties(prefix = "integration")` 这一行：把 Environment 里所有以 `integration.` 开头的 key，按名字塞进这个对象的字段。`@Configuration` 让 Spring 创建它，`@RefreshScope` 让它支持不重启就更新。

```java
@RefreshScope
@ConfigurationProperties(prefix = "integration")
@Configuration
public class IntegrationConfig {
    private SapConfig sap = new SapConfig();
    private OaConfig oa = new OaConfig();
    private MesConfig mes = new MesConfig();
    private TmsConfig tms = new TmsConfig();
    private OldOmsConfig oldOms = new OldOmsConfig();
    private MqConfig mq = new MqConfig();
    ...
}
```

**嵌套结构一一对应**，Java 的字段名和 Nacos 上的 key 名称严格对应：

```
Java 类的结构                   Nacos 上的 key
IntegrationConfig               integration
├── sap  (SapConfig)            ├── sap
│   ├── esb  (EsbConfig)        │   ├── esb
│   │   ├── orderCreateUrl  ←── │   │   ├── order-create-url
│   │   └── sapClient  ←─────── │   │   └── sap-client
│   └── direct  (DirectConfig)  │   └── direct
├── oa  (OaConfig)              ├── oa
│   └── workflowId              │   └── workflow-id
├── mes / tms / oldOms / mq     └── mes / tms / old-oms / mq
```

`orderCreateUrl` 和 `order-create-url` 写法不一样（Java 驼峰、配置短横线），但**自动对应**，这叫**宽松绑定**：

| 环境里 | Java 字段 | 能对应上吗 |
|---|---|---|
| `order-create-url` | `orderCreateUrl` | ✅ 自动 |
| `orderCreateUrl` | `orderCreateUrl` | ✅ 自动 |
| `ORDER_CREATE_URL` | `orderCreateUrl` | ✅ 自动（环境变量的习惯写法） |

**想知道一个配置项的准确 key，直接在 `IntegrationConfig` 里搜字段名**，注释里都写着，例如 `订单创建推送接口地址（integration.sap.esb.order-create-url，SD010），仅在 nacos 配置`。

### 第 6 步：运行期改配置会怎样

**这条界限要记牢：本项目只有 `IntegrationConfig` 一个类标了 `@RefreshScope`（全项目搜索只有这一处）。** 改 Nacos 上的 `integration.*` → **不重启生效**（`nacos-client` 一直用长轮询盯着 `winkey-lowcode-data.yml`，收到变更后，下次访问 `IntegrationConfig` 时会重建这个对象，用最新值重新绑定）；改其他配置（比如 `application.yml` 里的 `hzero.lock.*`）→ **要重启**。

---

## 一个值可能来自四个地方

| # | 来源 | 在哪看到 | 本项目举例 |
|---|---|---|---|
| 1 | Java 字段初始值 | `IntegrationConfig.java` 里字段后面 `= "xxx"` | `private int port = 5672;`（MQ 端口） |
| 2 | 本地 `application.yml` | 项目里就有，能直接看到 | `SPRING_DATASOURCE_URL` 的默认值 |
| 3 | **Nacos** | **看不到，要登录 Nacos 控制台** | 所有 `integration.*` |
| 4 | 操作系统环境变量 | 看不到，要问运维或看部署配置 | `NACOS_CONFIG_SERVER_ADDR` |

优先级从低到高（记忆方式：**越靠外的、越"临时"的，优先级越高**）：

```
低  1. Java 字段初始值     2. 本地 application.yml     3. Nacos 导入的配置
    4. 操作系统环境变量    5. 命令行参数（-Dxxx=yyy）
高
```

（第 1 条严格说不是"属性源"；所有来源都没有这个 key 时，字段保持初始值。）**结论：你在代码里看到的 `integration.*` 的值，很可能不是它实际跑起来的值**——比如 MQ 的 broker 地址字段默认是 `192.168.61.196`，生产环境上它一定不是这个值。想知道真实值，只有两条路：登录 Nacos 控制台，或者问运行中的程序。

> 顺带一句：数据库密码、Nacos 账号密码这类凭证，目前是以"默认值"的形式写在仓库里的，这属于可以改进的地方——默认值应该放一个明显无效的占位值（比如 `CHANGE_ME`），真实凭证只从环境变量或 Nacos 来。看代码时不用被这些值干扰，但心里要知道这不是好做法。

---

## 改完不生效怎么查

**一、Nacos 控制台。** 打开 `http://192.168.61.221:8848/nacos`，进"配置管理"，确认命名空间是 public、Group 是 `DEFAULT_GROUP`、Data ID 是 `winkey-lowcode-data.yml`——坐标选错了，后面全白搭。

**二、启动日志。** 启动时 Nacos 客户端会打日志，能看到它去拉了什么、有没有成功。配置没生效，第一步就是翻日志确认"到底拉到了没有"。

**三、actuator 接口。** 管理端口 **28086**，业务端口 28085，别找错：`/actuator/env` 看每个 key 最终生效的值来自哪个来源；`/actuator/configprops` 看 `IntegrationConfig` **绑定完之后**长什么样；`POST /actuator/refresh` 手动触发一次刷新。

---

## 五个坑速查

**坑一：改 Nacos 配置不生效。** 先看改的是不是 `integration.*`——只有 `IntegrationConfig` 标了 `@RefreshScope`，其他配置改完要重启。再去 `/actuator/env` 确认程序真拿到了新值。
**坑二：把 Nacos 的 namespace 和 H0 接口平台的 NAMESPACE 搞混。** `PlatformChannel.NAMESPACE = "HZERO"` 是接口平台的，跟 Nacos 没关系。
**坑三：dataId 名字对不上。** 它是 `prefix` + `file-extension` 拼的，`prefix` 又跟 `spring.application.name` 有关。服务名改了而 Nacos 上的文件名没跟着改，就会拉到一份空配置。
**坑四：环境变量把 Nacos 的值覆盖了。** 机器上设了 `NACOS_CONFIG_SERVER_ADDR` 之类的环境变量，它会压过 `bootstrap.yml` 里的默认值，**指向另一台 Nacos**。
**坑五：以为 `bootstrap.yml` 一定生效。** 它生效是因为依赖里有 `spring-cloud-starter-bootstrap`。这个依赖被排除掉，`bootstrap.yml` 会被**静默忽略**，不报错、配置全空。

---

## Nacos 拿不到配置会怎样

**情况一：有兜底值 —— 程序照常启动。** `optional:` 前缀、`application.yml` 里的 `${环境变量:默认值}`、`IntegrationConfig` 里部分字段的初始值，三层兜底叠起来，配置中心不可用时程序仍然能起来，用的是本地那套值——牺牲"用上最新配置"，换"服务不停"。**但后果是它用的是旧值或开发环境的默认值——发现"推 SAP 推到开发环境去了"，先怀疑这个。**
**情况二：没有兜底值 —— 启动成功，用到才报。** 这类 key 就是注释里写的"仅在 nacos 配置，代码中不设默认值"，比如所有 `integration.sap.esb.*`：Nacos 上没有它，字段就是 `null`，**程序照样启动成功，不报任何错**，直到真的去推订单才走到 `if (StringUtils.isBlank(sapConfig.getOrderCreateUrl())) return "请配置sap的url信息";` 这一句。

**这是排查的关键认知：配置缺失的表现不是"启动失败"，而是"跑到某个功能时才报一句提示"。** 遇到"某功能用了没反应/提示配置问题"，第一条线索就往 Nacos 上那个 key 存不存在去查，别先怀疑代码逻辑。对策：拿 `IntegrationConfig` 的字段列表和 Nacos 上的实际配置对一遍，看有没有漏配。

---

