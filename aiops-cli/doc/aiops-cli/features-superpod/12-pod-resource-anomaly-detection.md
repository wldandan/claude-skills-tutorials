# 特性 12: 容器/Pod 级别资源异常检测

## 功能概述

提供 Kubernetes 容器和 Pod 级别的精细化资源异常检测能力,能够监控 Pod 的 CPU、内存、磁盘、网络资源使用情况,检测资源异常(如超限、泄漏、竞争),并提供容器级别的根因分析和优化建议。与节点级监控相比,容器级监控能更精准地定位应用资源问题。

## 用户场景

**场景 1: Pod 被频繁 OOM Kill,需要分析原因**
- 某个 Pod 频繁被 OOM Kill,服务不稳定
- 不清楚是内存配置不足还是应用内存泄漏
- 使用 `aiops detect pod-oom --pod payment-api-5d7f9` 分析 OOM 根因

**场景 2: Pod 性能下降,怀疑资源受限**
- Pod 响应时间变长,怀疑 CPU 限流(throttling)
- 需要分析 CPU request/limit 配置是否合理
- 使用 `aiops analyze pod-throttling --pod frontend-abc123` 诊断 CPU 限流

**场景 3: 容器资源使用异常,需要与基线对比**
- 容器资源使用突然增加,但不确定是否异常
- 需要与历史基线对比,识别异常模式
- 使用 `aiops detect pod-anomaly --namespace production --baseline 7d` 检测异常

## 技术方案概要

### 数据采集层
- **Kubernetes API**: 获取 Pod、Container、ResourceQuota、LimitRange 信息
- **Metrics Server**: 采集 Pod/Container 级别的 CPU/内存指标
- **CAdvisor**: 采集容器细粒度资源使用(从 kubelet)
- ** kube-state-metrics**: 采集 Pod 状态、重启次数等

### 异常检测算法
- **资源超限检测**: 检测 Pod 资源使用超过 limits
- **限流检测**: 检测 CPU throttling(CFS 调度器限流)
- **异常增长检测**: 检测资源使用率异常增长(内存泄漏)
- **基线偏离检测**: 与历史基线对比,检测异常偏离
- **同类对比检测**: 与同类 Pod 对比,识别异常个体

### 根因分析
- **配置分析**: 分析 resource requests/limits 配置合理性
- **竞争分析**: 分析同节点 Pod 间的资源竞争
- **调度分析**: 分析 Pod 调度策略和节点亲和性
- **历史模式分析**: 识别周期性模式和异常模式

## 核心功能点

### 1. Pod 资源使用监控
```bash
# 实时监控 Pod 资源使用
aiops monitor pod --name payment-api-5d7f9 --namespace production
```
- 实时显示 Pod 的 CPU、内存、网络、磁盘使用
- 按 Container 分解资源使用
- 显示 resource requests/limits 和实际使用对比
- 标注资源超限和限流

### 2. OOM 事件分析
```bash
# 分析 Pod OOM Kill 事件
aiops analyze pod-oom --pod payment-api-5d7f9 --history 7d
```
- 分析 OOM Kill 历史和频率
- 对比内存使用和内存 limit
- 识别内存泄漏模式(持续增长)
- 分析容器内存详情(heap、stack、cache)
- 提供内存配置优化建议

### 3. CPU 限流分析
```bash
# 分析 CPU throttling
aiops analyze pod-throttling --pod frontend-abc123
```
- 检测 CPU throttling 频率和时长
- 分析 CPU request/limit 配置合理性
- 计算 CPU 使用率 vs CPU 限流率
- 提供优化建议(调整 limit、消除限流)

### 4. Pod 资源异常检测
```bash
# 检测 Pod 资源异常
aiops detect pod-anomaly --namespace production --algorithm auto
```
- 检测资源使用异常增长(内存泄漏)
- 检测资源使用突降(服务异常)
- 检测频繁重启(CrashLoopBackOff)
- 检测资源限流和超限
- 基于基线和同类 Pod 对比

### 5. 容器资源深度分析
```bash
# 深度分析容器资源使用
aiops inspect container --pod payment-api-5d7f9 --container app
```
- 容器进程级资源分析
- 容器内线程级 CPU 分析
- 容器内存详细分析(heap/stack/cache)
- 容器网络连接分析
- 容器文件系统使用分析

### 6. Pod 资源配置分析
```bash
# 分析 Pod 资源配置合理性
aiops analyze pod-resource-config --pod payment-api-5d7f9
```
- 分析 CPU/内存 requests/limits 配置
- 评估配置合理性(基于历史使用)
- 识别 over-provisioning 和 under-provisioning
- 提供优化建议和推荐配置
- 估算成本节省

### 7. 同节点 Pod 资源竞争分析
```bash
# 分析同节点 Pod 资源竞争
aiops analyze pod-contention --node node-1
```
- 识别同节点所有 Pod
- 分析资源竞争(CPU、内存、磁盘、网络)
- 识别"吵闹邻居"(Noisy Neighbor)
- 分析资源超卖情况
- 提供调度优化建议

### 8. Pod 资源趋势预测
```bash
# 预测 Pod 资源使用趋势
aiops forecast pod-resources --pod payment-api-5d7f9 --period 7d --ahead 24h
```
- 预测未来资源使用趋势
- 识别资源耗尽风险(OOM、限流)
- 提供扩容建议
- 支持自动扩容配置(HPA)

## 验收标准 (Acceptance Criteria)

### AC 1: Pod 资源监控准确性
- **Given**: Pod 运行正常
- **When**: 执行 `aiops monitor pod --name <pod-name>`
- **Then**:
  - 准确显示 CPU/内存使用率(误差 < 5%)
  - 正确获取 resource requests/limits 配置
  - 按 Container 正确分解资源使用
  - 数据更新延迟 < 10 秒

### AC 2: OOM 检测准确性
- **Given**: Pod 发生 OOM Kill 事件
- **When**: 执行 `aiops detect pod-oom --pod <pod-name> --time-range 1h`
- **Then**:
  - 检测到 OOM 事件(准确率 >= 95%)
  - 正确识别被 kill 的容器
  - OOM 时间准确(误差 < 10 秒)
  - 提供内存使用和 limit 对比

### AC 3: CPU Throttling 检测准确性
- **Given**: Pod 存在 CPU throttling
- **When**: 执行 `aiops analyze pod-throttling --pod <pod-name>`
- **Then**:
  - 检测到 throttling 事件(准确率 >= 90%)
  - throttling 时长估算准确(误差 < 20%)
  - 提供优化建议(调整 limit)
  - 关联 CPU 使用率和 throttling 率

### AC 4: 异常检测准确性
- **Given**: Pod 内存使用异常增长(内存泄漏)
- **When**: 执行 `aiops detect pod-anomaly --algorithm ml`
- **Then**:
  - 检测到异常增长(准确率 >= 85%)
  - 误报率 <= 15%(正常增长误判为异常)
  - 检测延迟 < 5 分钟(从异常开始到检测出)
  - 提供异常严重程度评分

### AC 5: 资源竞争检测准确性
- **Given**: 节点上存在多个 Pod,一个 Pod 高负载影响其他 Pod
- **When**: 执行 `aiops analyze pod-contention --node <node-name>`
- **Then**:
  - 识别"吵闹邻居"Pod(准确率 >= 80%)
  - 分析资源竞争程度(CPU、内存、磁盘 IO)
  - 识别受影响的 Pod
  - 提供调度优化建议

### AC 6: 性能与资源占用
- **Given**: 集群中有 1000 个 Pod
- **When**: 执行 `aiops detect pod-anomaly --all`
- **Then**:
  - 扫描时间 < 60 秒
  - 内存占用 < 500MB
  - CPU 占用 < 20%
  - 网络开销 < 5MB(查询 Kubernetes API)

### AC 7: 配置推荐合理性
- **Given**: Pod CPU/内存 requests/limits 配置不合理
- **When**: 执行 `aiops analyze pod-resource-config --pod <pod-name>`
- **Then**:
  - 识别 over-provisioning(配置远高于实际使用)
  - 识别 under-provisioning(配置低于实际使用)
  - 推荐配置基于历史数据(P50、P95、P99)
  - 估算成本节省(如果有)

### AC 8: 趋势预测准确性
- **Given**: Pod 有 7 天历史数据
- **When**: 执行 `aiops forecast pod-resources --pod <pod-name> --ahead 24h`
- **Then**:
  - 预测未来 24 小时资源使用趋势
  - 预测误差(MAPE) < 30%
  - 识别资源耗尽风险(准确率 >= 75%)
  - 提供扩容建议

## 依赖项

### 系统依赖
- **Kubernetes**: Kubernetes 1.19+
- **Metrics Server**: 集群已部署 Metrics Server
- **kube-state-metrics**: 可选,用于采集 Pod 状态
- **Prometheus**: 可选,用于历史指标查询

### Python 库依赖
```
kubernetes>=24.0.0      # Kubernetes API 客户端
pandas>=2.0.0           # 数据处理和分析
numpy>=1.24.0           # 数值计算
scipy>=1.10.0           # 统计分析
scikit-learn>=1.3.0     # 机器学习算法(异常检测)
click>=8.1.0            # CLI 框架
rich>=13.0.0            # 终端美化
pyyaml>=6.0             # 配置文件解析
```

### 可选依赖
```
prometheus-client       # Prometheus 集成
plotly>=5.14.0          # 交互式图表
```

### 数据源
- **Kubernetes API**: Pod、Container、Node 信息
- **Metrics Server**: 实时资源使用指标
- **Prometheus**: 历史指标数据(如果部署)

## 优先级

**P0 (必须实现)**
- AC 1: Pod 资源监控准确性
- AC 2: OOM 检测准确性
- 核心功能点 1, 2

**P1 (首版本必备)**
- AC 6: 性能与资源占用
- AC 3: CPU Throttling 检测准确性
- AC 4: 异常检测准确性
- 核心功能点 3, 4, 6

**P2 (后续版本优化)**
- AC 5: 资源竞争检测准确性
- AC 7: 配置推荐合理性
- AC 8: 趋势预测准确性
- 核心功能点 5, 7, 8

## 输出示例

### Pod 资源监控输出
```bash
$ aiops monitor pod --name payment-api-5d7f9 --namespace production

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Pod 资源监控                                         2024-01-15 14:30:25 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Pod: payment-api-5d7f9                                       │
│ Namespace: production                                         │
│ Node: node-3                                                  │
│ Phase: Running ✅                                             │
│ Age: 7 days 3 hours                                          │
│ Restart Count: 2                                              │
├──────────────────────────────────────────────────────────────────┤
│ 📊 资源使用概览 (最近 5 分钟):                                   │
│                                                                  │
│   CPU:                                                          │
│     当前使用: 1.25 cores / 2 cores (62.5%) ✅                  │
│     Request: 1 core (50% of limit)                            │
│     Limit: 2 cores                                            │
│     Throttling: 0% (无限流)                                   │
│     峰值: 1.8 cores (90%)                                     │
│                                                                  │
│   内存:                                                         │
│     当前使用: 1.8 GB / 2 GB (90%) ⚠️                          │
│     Request: 1 GB (50% of limit)                              │
│     Limit: 2 GB                                               │
│     Cache: 300 MB (16.7%)                                     │
│     峰值: 1.95 GB (97.5%) 🚨 (接近 limit)                    │
│                                                                  │
│   网络:                                                         │
│     接收: 15 MB/s                                              │
│     发送: 8 MB/s                                               │
│     连接数: 245                                                │
│                                                                  │
│   磁盘:                                                         │
│     rootfs: 2.3 GB / 10 GB (23%)                              │
│     写入: 5 MB/s                                               │
│     读取: 2 MB/s                                               │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 📦 容器资源分解:                                                 │
│                                                                  │
│   Container: app (主容器)                                       │
│     CPU: 1.15 cores / 2 cores (57.5%)                         │
│     内存: 1.65 GB / 2 GB (82.5%)                              │
│     状态: Running ✅                                           │
│                                                                  │
│   Container: sidecar-proxy                                     │
│     CPU: 0.1 cores / 2 cores (5%)                             │
│     内存: 150 MB / 2 GB (7.5%)                                │
│     状态: Running ✅                                           │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ ⚠️  警告和异常:                                                   │
│                                                                  │
│   🚨 内存接近 limit:                                            │
│     当前: 1.8 GB (90%)                                        │
│     Limit: 2 GB                                               │
│     峰值: 1.95 GB (97.5%)                                     │
│     风险: 可能发生 OOM Kill                                    │
│     建议: 考虑增加 memory limit 到 3 GB                         │
│                                                                  │
│   🔄 Pod 重启历史:                                              │
│     2 天前: OOM Kill (内存超限)                                │
│     5 天前: OOM Kill (内存超限)                                │
│     模式: 频繁 OOM Kill, 可能存在内存泄漏                       │
│     建议: 使用 'aiops analyze pod-oom --pod payment-api-5d7f9' │
│           分析内存泄漏                                           │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 💡 优化建议:                                                      │
│                                                                  │
│   1. 内存配置优化:                                               │
│      当前: Request 1 GB, Limit 2 GB                            │
│      建议: Request 1.5 GB, Limit 3 GB                          │
│      原因: 内存使用接近 limit,有 OOM 风险                        │
│                                                                  │
│   2. 内存泄漏检测:                                               │
│      命令: aiops analyze pod-oom --pod payment-api-5d7f9       │
│      原因: 频繁 OOM Kill,疑似内存泄漏                           │
│                                                                  │
│   3. CPU 配置合理:                                              │
│      当前配置: Request 1 core, Limit 2 cores                   │
│      使用率: 62.5%,无 throttling                                │
│      结论: 配置合理,无需调整                                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### OOM 事件分析输出
```bash
$ aiops analyze pod-oom --pod payment-api-5d7f9 --history 7d

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Pod OOM 事件分析                                     2024-01-15 14:30:25 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Pod: payment-api-5d7f9                                       │
│ Namespace: production                                         │
│ 分析时间范围: 2024-01-08 - 2024-01-15 (7 天)                 │
├──────────────────────────────────────────────────────────────────┤
│ 📊 OOM 事件统计:                                                │
│   OOM Kill 次数: 5 次                                          │
│   受影响容器: app                                               │
│   OOM 频率: 0.71 次/天                                         │
│   最近一次: 2024-01-15 13:45:23 (1 小时前)                    │
│   MTTR: 2 分钟(从 OOM 到重启)                                 │
├──────────────────────────────────────────────────────────────────┤
│ 🕘 OOM 事件时间线:                                               │
│                                                                  │
│   #1 2024-01-15 13:45:23 (最近一次)                            │
│      内存使用: 2.05 GB / 2 GB (102.5%) 🚨                     │
│      Pod 重启: 13:47:25 (2 分钟后)                            │
│      影响: 服务不可用 2 分钟                                    │
│      原因: 内存使用持续增长,超过 limit                         │
│                                                                  │
│   #2 2024-01-14 09:12:45                                       │
│      内存使用: 2.01 GB / 2 GB (100.5%) 🚨                     │
│      Pod 重启: 09:14:30 (1 分 45 秒后)                        │
│      原因: 内存使用持续增长                                    │
│                                                                  │
│   #3 2024-01-13 16:30:12                                       │
│      内存使用: 1.98 GB / 2 GB (99%) 🚨                        │
│      Pod 重启: 16:32:00 (1 分 48 秒后)                        │
│      原因: 内存使用持续增长                                    │
│                                                                  │
│   #4 2024-01-11 11:20:08                                       │
│      内存使用: 2.03 GB / 2 GB (101.5%) 🚨                     │
│      原因: 内存使用持续增长                                    │
│                                                                  │
│   #5 2024-01-09 14:55:33                                       │
│      内存使用: 1.97 GB / 2 GB (98.5%) 🚨                      │
│      原因: 内存使用持续增长                                    │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 📈 内存使用模式分析:                                              │
│                                                                  │
│   启动后内存增长曲线:                                            │
│     启动时(0h):    800 MB                                       │
│     1 小时后:     1.2 GB                                        │
│     6 小时后:     1.6 GB                                        │
│     12 小时后:    1.9 GB                                        │
│     24 小时后:    2.0 GB → OOM                                 │
│                                                                  │
│   增长速度: 约 50 MB/小时                                       │
│   增长模式: 线性持续增长 ⚠️                                    │
│   推测: 可能存在内存泄漏                                        │
│                                                                  │
│   对比同 Pod 其他实例:                                          │
│     payment-api-abc123: 内存稳定在 1.2 GB                      │
│     payment-api-xyz789: 内存稳定在 1.3 GB                      │
│     结论: 该 Pod 实例内存使用异常                               │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 🔍 根因分析:                                                      │
│                                                                  │
│   假设 #1: 应用内存泄漏 (置信度: 92%)                           │
│                                                                  │
│     证据:                                                        │
│       ✅ 内存线性持续增长                                       │
│       ✅ 24 小时后必然 OOM                                     │
│       ✅ 同 Pod 其他实例内存稳定                                │
│       ✅ 无明显流量或负载变化                                   │
│                                                                  │
│     可能原因:                                                    │
│       • Java 堆内存泄漏                                        │
│       • Go goroutine 泄漏                                      │
│       • 缓存无限增长                                           │
│       • 连接对象未释放                                         │
│                                                                  │
│     验证步骤:                                                    │
│       1. 分析 Java 堆内存(如果是 Java):                         │
│          kubectl exec payment-api-5d7f9 -- jmap -histo 1      │
│       2. 分析 Go goroutine(如果是 Go):                          │
│          kubectl exec payment-api-5d7f9 -- curl localhost:6060/debug/pprof/goroutine
│       3. 检查缓存大小:                                           │
│          kubectl exec payment-api-5d7f9 -- curl localhost:metrics/metrics/cache
│                                                                  │
│   ────────────────────────────────────────────────────────────  │
│                                                                  │
│   假设 #2: 内存 limit 配置不足 (置信度: 45%)                     │
│                                                                  │
│     证据:                                                        │
│       ⚠️  内存确实持续增长,但可能是业务正常增长                 │
│       ❌ 同 Pod 其他实例内存稳定                                │
│                                                                  │
│     建议验证: 检查是否该实例有特殊流量或任务                     │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 💡 修复建议:                                                      │
│                                                                  │
│   立即(避免再次 OOM):                                            │
│     1. 临时增加内存 limit: 2 GB → 4 GB                          │
│        kubectl set resources pod payment-api-5d7f9             │
│           --limits=memory=4Gi                                   │
│     2. 配置内存 dump(捕获 OOM 时堆转储):                        │
│        在 Pod spec 中添加:                                      │
│          - JAVA_OPTS="-XX:+HeapDumpOnOutOfMemoryError ..."      │
│                                                                  │
│   短期(24h):                                                     │
│     3. 分析内存泄漏:                                              │
│        • 使用内存分析工具(jmap、MAT、pprof)                     │
│        • 分析代码,识别泄漏点                                    │
│     4. 配置内存监控告警:                                         │
│        • 内存使用 > 80% 时告警                                  │
│        • 内存增长率 > 30 MB/h 时告警                            │
│                                                                  │
│   长期:                                                          │
│     5. 修复内存泄漏:                                              │
│        • 代码审查和修复                                         │
│        • 增加单元测试和集成测试                                  │
│     6. 配置自动扩容:                                             │
│        • 基于 HPA,根据内存使用自动扩容                          │
│     7. 实施健康检查和自愈:                                       │
│        • 配置 liveness 和 readiness probe                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 资源竞争分析输出
```bash
$ aiops analyze pod-contention --node node-3

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Pod 资源竞争分析                                      2024-01-15 14:30:25 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 节点: node-3                                                   │
│ 节点资源: CPU 32 cores, 内存 128 GB                            │
│ Pod 数量: 12                                                   │
│ 分析时间: 2024-01-15 14:00:00 - 14:30:00                      │
├──────────────────────────────────────────────────────────────────┤
│ 📊 节点资源使用概览:                                              │
│   CPU: 24.5 / 32 cores (76.6%)                                 │
│   内存: 98 GB / 128 GB (76.6%)                                 │
│   资源超卖比: 1.5x (总 requests / 节点容量)                   │
├──────────────────────────────────────────────────────────────────┤
│ 🚨 "吵闹邻居"(Noisy Neighbor) 识别:                               │
│                                                                  │
│   #1 data-pipeline-worker-abc123 (吵闹程度: 高) 🚨             │
│      Namespace: data-processing                                  │
│      资源使用:                                                  │
│        CPU: 4.2 cores / 6 cores (70%)                           │
│        内存: 8.5 GB / 10 GB (85%)                              │
│      问题:                                                      │
│        • CPU throttling 率: 35% (高限流) 🚨                   │
│        • 磁盘 IO: 85 MB/s (远高于其他 Pod) 🚨                 │
│        • 网络带宽: 45 MB/s (高)                                 │
│      影响范围:                                                  │
│        • 同节点其他 5 个 Pod 出现 CPU throttling                │
│        • 磁盘 IO 延迟增加 +150%                                │
│      建议:                                                      │
│        • 调度到专用节点(高 IO 节点)                             │
│        • 使用 nodeSelector 或 nodeAffinity                      │
│        • 考虑使用 Pod Disruption Budget                        │
│                                                                  │
│   #2 ml-training-job-xyz789 (吵闹程度: 中) ⚠️                 │
│      Namespace: ml-workloads                                     │
│      资源使用:                                                  │
│        CPU: 7.8 cores / 8 cores (97.5%)                         │
│        内存: 15 GB / 16 GB (93.75%)                            │
│      问题:                                                      │
│        • CPU 使用率接近 limit,持续高负载                         │
│        • 内存使用率接近 limit                                   │
│      影响:                                                      │
│        • 节点 CPU 使用率 +24%                                  │
│        • 节点内存使用率 +12%                                   │
│      建议:                                                      │
│        • 调度到 GPU 节点或专用 ML 节点                          │
│        • 使用 priorityclass,降低优先级                          │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 📈 资源竞争分析:                                                  │
│                                                                  │
│   CPU 竞争:                                                      │
│     总 requests: 24 cores                                       │
│     节点容量: 32 cores                                         │
│     超卖比: 0.75x (安全范围)                                   │
│     高负载 Pod 数: 3 (CPU > 80%)                                │
│     throttling Pod 数: 6 (50%) ⚠️                             │
│                                                                  │
│   内存竞争:                                                      │
│     总 requests: 96 GB                                          │
│     节点容量: 128 GB                                           │
│     超卖比: 0.75x (安全范围)                                   │
│     高使用 Pod 数: 4 (内存 > 80%)                               │
│     OOM 风险: 低                                               │
│                                                                  │
│   磁盘 IO 竞争: 🚨 高风险                                       │
│     磁盘类型: SSD                                               │
│     总 IO 带宽: 150 MB/s                                        │
│     data-pipeline-worker 单 Pod 占用: 57% (85 MB/s)           │
│     IO 延迟增加: +150% (相比空闲节点)                           │
│     结论: 磁盘 IO 是主要瓶颈                                    │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 💡 调度优化建议:                                                  │
│                                                                  │
│   1. 隔离吵闹 Pod:                                               │
│      • 将 data-pipeline-worker 调度到专用节点                   │
│      • 使用 nodeSelector: node-role=io-intensive               │
│      • 配置 podAntiAffinity,避免与其他 Pod 混合部署            │
│                                                                  │
│   2. 优化资源配置:                                               │
│      • 调整 data-pipeline-worker CPU limit,消除 throttling      │
│      • 为 IO 密集型 Pod 使用本地 SSD (hostPath)                 │
│                                                                  │
│   3. 使用 QoS 和 priorityClass:                                  │
│      • 为关键 Pod 使用 Guaranteed QoS                           │
│      • 为批处理 Pod 使用 Burstable QoS                          │
│      • 使用 priorityClass 控制驱逐优先级                        │
│                                                                  │
│   4. 实施资源配额和 LimitRange:                                  │
│      • 配置 ResourceQuota,限制 namespace 总资源                 │
│      • 配置 LimitRange,强制 Pod 资源 requests/limits           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 后续演进方向

1. **多层资源隔离**: 支持从 Pod 到 Container 到进程的多层资源监控
2. **自动资源调优**: 基于历史数据自动调整 requests/limits
3. **成本优化**: 分析资源成本,提供成本优化建议
4. **多集群资源视图**: 聚合多集群 Pod 资源使用,提供统一视图
