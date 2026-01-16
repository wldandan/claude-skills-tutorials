# 特性 14: 节点资源调度与配额优化分析

## 功能概述

提供 Kubernetes 集群资源调度策略分析和优化建议能力,分析 Pod 调度决策、节点亲和性、资源配额(ResourceQuota/LimitRange)配置合理性,识别调度瓶颈和资源浪费,实现集群资源的最优分配和利用。

## 用户场景

**场景 1: Pod 无法调度,需要分析原因**
- Pod 处于 Pending 状态,无法调度
- 不清楚是资源不足还是亲和性配置问题
- 使用 `aiops analyze-scheduling --pod <pod-name>` 诊断调度失败原因

**场景 2: 节点资源利用率不均衡**
- 部分节点高负载,部分节点空闲
- 需要分析调度策略和优化配置
- 使用 `aiops analyze-balance --cluster superpod-1` 分析负载均衡

**场景 3: 资源配额配置不合理**
- Namespace 资源配额过紧,导致 Pod 无法创建
- 需要分析配额使用情况和优化建议
- 使用 `aiops analyze-quota --namespace production` 分析配额

## 技术方案概要

### 调度分析
- **调度事件分析**: 分析 Kubernetes scheduler 事件日志
- **调度约束分析**: 分析 nodeSelector、nodeAffinity、podAntiAffinity 等约束
- **资源需求分析**: 分析 Pod 资源 requests/limits 与节点资源的匹配
- ** predicates/priority 分析**: 分析调度器的过滤和打分策略

### 优化算法
- **装箱算法(Bin Packing)**: 分析节点资源利用率,优化 Pod 排布
- **负载均衡算法**: 分析节点负载差异,提供重调度建议
- **容量规划**: 基于历史数据和趋势,预测资源需求
- **成本优化**: 分析资源成本,提供成本优化建议

## 核心功能点

### 1. 调度失败诊断
```bash
# 分析调度失败原因
aiops diagnose-scheduling --pod <pod-name>
```
- 识别调度失败的具体原因
- 分析资源不足、亲和性、污点(Taint)等因素
- 提供修复建议

### 2. 节点负载均衡分析
```bash
# 分析节点负载均衡
aiops analyze-balance --cluster <cluster-name>
```
- 计算节点负载差异(标准差、变异系数)
- 识别负载不均的节点
- 提供重调度建议

### 3. 资源配额分析
```bash
# 分析 Namespace 资源配额
aiops analyze-quota --namespace <namespace>
```
- 分析配额使用情况
- 识别配额瓶颈
- 提供配额优化建议

### 4. 调度策略模拟
```bash
# 模拟调度策略
aiops simulate-scheduling --pod <pod-spec> --dry-run
```
- 模拟 Pod 调度到不同节点的结果
- 评估调度策略影响
- 提供优化建议

## 验收标准 (Acceptance Criteria)

### AC 1: 调度失败诊断准确性
- **Given**: Pod 因资源不足调度失败
- **When**: 执行 `aiops diagnose-scheduling --pod <pod-name>`
- **Then**:
  - 正确识别失败原因(准确率 >= 90%)
  - 提供详细的原因分析
  - 提供可执行的修复建议

### AC 2: 负载均衡分析准确性
- **Given**: 集群中有 50 个节点,负载不均
- **When**: 执行 `aiops analyze-balance --cluster <cluster>`
- **Then**:
  - 识别负载不均的节点(准确率 >= 85%)
  - 提供合理的重调度建议
  - 估算优化后的负载均衡度

### AC 3: 性能与资源占用
- **Given**: 100 节点集群,1000 个 Pod
- **When**: 执行 `aiops analyze-balance --cluster <cluster>`
- **Then**:
  - 分析时间 < 60 秒
  - 内存占用 < 1GB

## 依赖项

```
kubernetes>=24.0.0
pandas>=2.0.0
numpy>=1.24.0
click>=8.1.0
rich>=13.0.0
pyyaml>=6.0
```

## 优先级

**P0**: AC 1, 核心功能点 1
**P1**: AC 2, AC 3, 核心功能点 2, 3
**P2**: 核心功能点 4

## 输出示例

### 调度失败诊断输出
```bash
$ aiops diagnose-scheduling --pod payment-api-5d7f9

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Pod 调度失败诊断                                      2024-01-15 14:30:25 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Pod: payment-api-5d7f9                                       │
│ Namespace: production                                         │
│ Phase: Pending ⚠️                                             │
│ 等待时间: 15 分钟                                             │
├──────────────────────────────────────────────────────────────────┤
│ 🚨 调度失败原因:                                                │
│   Error: 0/3 nodes are available:                             │
│     1 Insufficient cpu, 1 Insufficient memory,                │
│     1 node(s) had taint {node-role.kubernetes.io/master:      │
│     NoSchedule}, that the pod didn't tolerate                 │
├──────────────────────────────────────────────────────────────────┤
│ 📊 详细原因分析:                                                  │
│                                                                  │
│   原因 #1: CPU 不足 (2 个节点)                                  │
│     Pod CPU request: 4 cores                                   │
│     节点可用 CPU:                                               │
│       • node-1: 1.5 cores available (需要 4, 缺少 2.5)         │
│       • node-2: 2 cores available (需要 4, 缺少 2)             │
│     解决方案:                                                   │
│       • 增加 2 个节点(每个至少 4 cores)                         │
│       • 或降低 Pod CPU request: 4 cores → 2 cores              │
│                                                                  │
│   原因 #2: 内存不足 (1 个节点)                                  │
│     Pod Memory request: 8 GB                                   │
│     节点可用内存:                                                │
│       • node-3: 5 GB available (需要 8, 缺少 3)                │
│     解决方案:                                                   │
│       • 增加 1 个节点(至少 16 GB 内存)                          │
│       • 或驱逐低优先级 Pod                                      │
│                                                                  │
│   原因 #3: Master 节点污点 (1 个节点)                           │
│     Pod 无法容忍 master 节点污点                                │
│     节点: node-master (tainted: NoSchedule)                   │
│     解决方案:                                                   │
│       • 增加工作节点                                            │
│       • 或添加 tolerations(不推荐)                              │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 💡 修复建议:                                                      │
│                                                                  │
│   立即:                                                          │
│     1. 增加工作节点:                                             │
│        kubectl scale nodepool --replicas=5                     │
│     2. 调整资源 requests:                                       │
│        kubectl set resources pod payment-api-5d7f9             │
│          --requests=cpu=2,memory=4Gi                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 节点负载均衡分析输出
```bash
$ aiops analyze-balance --cluster superpod-1

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 节点负载均衡分析                                      2024-01-15 14:30:25 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 集群: superpod-1                                               │
│ 节点数: 50                                                     │
│ Pod 数: 850                                                    │
├──────────────────────────────────────────────────────────────────┤
│ 📊 负载均衡度评估:                                                │
│   CPU 负载均衡度: ⚠️ 中等 (变异系数 CV = 0.35)                  │
│   内存负载均衡度: ✅ 良好 (变异系数 CV = 0.18)                 │
│   Pod 数量均衡度: ✅ 良好 (变异系数 CV = 0.15)                │
│                                                                  │
│   总体评分: 72/100 (中等)                                       │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 🚨 负载不均节点 (Top 5):                                          │
│                                                                  │
│   node-5 (CPU 过载) 🚨                                         │
│     CPU 使用率: 92% (集群平均: 65%)                            │
│     Pod 数: 22 (集群平均: 17)                                  │
│     建议: 驱逐部分 Pod 到其他节点                               │
│                                                                  │
│   node-12 (CPU 过载) 🚨                                       │
│     CPU 使用率: 88% (集群平均: 65%)                            │
│     建议: 驱逐部分 Pod                                         │
│                                                                  │
│   node-23 (内存空闲) ⚠️                                       │
│     内存使用率: 35% (集群平均: 68%)                            │
│     Pod 数: 8 (集群平均: 17)                                   │
│     建议: 调度更多 Pod 到此节点                                 │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 💡 优化建议:                                                      │
│   1. 重调度高负载节点 Pod:                                       │
│      kubectl drain node-5 --ignore-daemonsets --delete-emptydir-pod
│   2. 调整调度器权重:                                             │
│      优化 CPU 资源打分权重                                      │
│   3. 使用 descheduler:                                          │
│      定期重调度不均衡的 Pod                                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 后续演进方向

1. **自动重调度**: 自动识别并重调度不均衡的 Pod
2. **智能扩缩容**: 基于负载预测的自动扩缩容
3. **多集群调度**: 支持跨集群的统一调度策略
4. **成本优化**: 基于成本最优的调度建议
