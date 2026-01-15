# 特性 02: 内存异常检测与分析

## 功能概述

提供全面的内存异常检测和分析能力，涵盖内存泄漏、OOM (Out of Memory)、缓存异常、进程内存膨胀等问题。通过多维度内存指标分析（物理内存、虚拟内存、Swap、进程内存分布），快速定位内存问题的根本原因。

## 用户场景

**场景 1: 内存泄漏排查**
- 应用程序内存占用持续增长，最终 OOM
- 需要识别泄漏的进程和内存类型（堆/栈/共享内存）
- 使用 `aiops detect memory-leak --pid <pid>` 分析内存增长模式

**场景 2: Swap 频繁交换导致性能下降**
- 系统可用内存充足但 Swap 使用率高
- 需要分析哪些进程导致 Swap
- 使用 `aiops analyze swap --processes` 定位 Swap 罪魁祸首

**场景 3: 缓存命中率低**
- 应用性能差，怀疑是缓存问题
- 需要分析页缓存、slab 缓存使用情况
- 使用 `aiops inspect cache --detail` 查看缓存分布和热点

## 技术方案概要

### 数据采集层
- 读取 `/proc/meminfo` 获取系统级内存指标（MemTotal/MemFree/Cached/Slab/Dirty 等）
- 读取 `/proc/vmstat` 获取内存统计（pswpin/pswpout 页换入换出）
- 读取 `/proc/<pid>/status`、`/proc/<pid>/statm` 获取进程内存指标
- 读取 `/proc/<pid>/smaps` 获取进程内存映射详情（RSS/PSS/Swap/Dirty）
- 读取 `/proc/<pid>/maps` 获取内存映射区域
- 使用 slabtop、pmap 辅助分析

### 异常检测算法
- **内存泄漏检测**: 基于时间序列的趋势分析（线性回归、变化点检测）
- **OOM 风险预测**: 基于内存增长速率预测到达 OOM 的时间
- **异常内存增长**: 使用 STL 分解 + 残差分析检测异常增长点
- **Swap 异常**: 检测 Swap 使用率突增或持续增长

### 根因分析
- **进程内存分布**: 识别内存占用 Top 进程及其内存组成（匿名/文件/共享）
- **内存热区分析**: 识别进程内的内存热点（堆、栈、代码段、动态库）
- **泄漏源定位**: 通过堆栈采样和对象统计定位泄漏代码路径
- **关联分析**: 关联日志中的 OOM 事件、GC 事件、内存分配失败

## 核心功能点

### 1. 内存健康评分
```bash
# 评估系统内存健康度
aiops health memory --score
```
- 综合评估内存使用率、碎片化、Swap、缓存效率
- 输出 0-100 分的健康评分和风险等级
- 列出影响健康的 Top 因素

### 2. 内存泄漏检测
```bash
# 检测进程内存泄漏
aiops detect memory-leak --pid <pid> --history 24h
```
- 分析进程内存增长趋势（RSS/VMS/Heap）
- 计算内存增长率（MB/hour）
- 区分正常业务增长和泄漏模式
- 预测 OOM 时间窗口

### 3. OOM 事件分析
```bash
# 分析历史 OOM 事件
aiops analyze oom --last
```
- 读取 `/var/log/messages` 或 dmesg 中的 OOM 日志
- 解析 OOM killer 的决策过程和被杀进程
- 分析 OOM 时的内存状态快照
- 提供后续预防建议

### 4. Swap 分析
```bash
# 分析 Swap 使用情况
aiops analyze swap --processes --threshold 10%
```
- 列出 Swap 占用最高的进程
- 分析 Swap 换入换出频率（pswpin/pswpout）
- 识别 Swap 热区（哪些内存被换出）
- 提供优化建议（关闭 Swap/调整 swappiness/增加内存）

### 5. 进程内存详情
```bash
# 查看进程内存详细分布
aiops inspect memory --pid <pid> --maps --detail
```
- 按内存映射区域分解（heap/stack/lib/anon/file）
- 显示每个区域的 RSS/PSS/Swap/Dirty
- 识别内存占用最大的库和模块
- 检测异常的内存映射（如超大共享内存）

### 6. 缓存效率分析
```bash
# 分析页缓存和 slab 缓存效率
aiops analyze cache --efficiency
```
- 计算缓存命中率（基于 page reference 统计）
- 识别 slab 缓存中的 Top 对象（dentry/inode 等）
- 分析脏页（Dirty Pages）产生和回写速率
- 提供缓存调优建议

### 7. 内存对比分析
```bash
# 对比两个时间点的内存快照
aiops diff memory --snapshot1 mem_snap1.db --snapshot2 mem_snap2.db
```
- 显示内存增量的进程分布
- 识别新增的大内存进程
- 对比内存热区变化

## 验收标准 (Acceptance Criteria)

### AC 1: 内存数据采集准确性
- **Given**: Linux 系统运行正常
- **When**: 执行 `aiops collect memory --duration 60s`
- **Then**:
  - 采集的内存使用率与 `free -m` 结果一致（误差 < 1%）
  - 进程 RSS 与 `ps aux --sort=-rss` 一致（误差 < 2%）
  - Swap 使用率准确无误

### AC 2: 内存泄漏检测准确性
- **Given**: 存在内存泄漏的进程（内存持续增长 > 24 小时）
- **When**: 执行 `aiops detect memory-leak --pid <pid> --history 24h`
- **Then**:
  - 检测到内存泄漏，准确率 >= 90%（基于标注测试集）
  - 计算的泄漏速率误差 < 20%（与实际对比）
  - 预测的 OOM 时间误差 < 30%

### AC 3: OOM 事件解析完整性
- **Given**: 系统发生过 OOM（有 dmesg 或日志记录）
- **When**: 执行 `aiops analyze oom --last`
- **Then**:
  - 正确解析 OOM killer 日志格式
  - 显示被杀进程及其内存占用
  - 显示系统当时的内存状态（Total/Free/Available）
  - 提供 OOM 发生的精确时间戳

### AC 4: 进程内存映射分析
- **Given**: 指定进程正在运行
- **When**: 执行 `aiops inspect memory --pid <pid> --maps`
- **Then**:
  - 正确读取 `/proc/<pid>/smaps` 的所有映射区域
  - 每个区域的 Size/RSS/PSS/Swap 准确无误
  - 区分匿名映射和文件映射
  - 显示权限（r/w/x）和共享属性

### AC 5: Swap 分析准确性
- **Given**: 系统使用 Swap（Swap 使用率 > 5%）
- **When**: 执行 `aiops analyze swap --processes`
- **Then**:
  - 准确列出每个进程的 Swap 占用（对比 /proc/<pid>/status 的 VmSwap）
  - Swap 总和与系统 Swap 使用一致（误差 < 5%）
  - 显示 Swap in/out 统计（/proc/vmstat）

### AC 6: 性能与资源占用
- **Given**: 系统正常运行
- **When**: 启动 `aiops monitor memory --daemon` 后台运行
- **Then**:
  - 工具自身内存占用 < 150MB
  - CPU 占用 < 2%（单核）
  - 磁盘写入 < 20MB/hour

### AC 7: 历史数据查询
- **Given**: 已采集 30 天的内存数据
- **When**: 执行 `aiops query memory --start "2024-01-01" --end "2024-01-07" --processes`
- **Then**:
  - 返回指定时间段的所有进程内存数据
  - 查询响应时间 < 5 秒（7 天数据）
  - 支持按进程聚合和排序

### AC 8: 多维度关联分析
- **Given**: 发生内存异常事件
- **When**: 查看检测报告
- **Then**:
  - 关联同时间段的 CPU、磁盘 IO、网络指标
  - 显示相关日志（如 OOM、GC、内存分配失败）
  - 提供可能的根因假设（泄漏/缓存/业务增长）

## 依赖项

### 系统依赖
- **操作系统**: Linux (内核 >= 3.10)
- **Python**: Python 3.8+
- **权限**: 普通用户权限（读取 /proc），部分功能需要 root

### Python 库依赖
```
psutil>=5.9.0          # 进程和系统信息
pandas>=2.0.0          # 数据处理
numpy>=1.24.0          # 数值计算
scikit-learn>=1.3.0    # 异常检测（DBSCAN、Isolation Forest）
scipy>=1.10.0          # 统计分析（线性回归）
click>=8.1.0           # CLI 框架
rich>=13.0.0           # 终端美化
```

### 可选依赖
```
matplotlib>=3.7.0      # 内存增长曲线图
plotly>=5.14.0         # 交互式图表
```

## 优先级

**P0 (必须实现)**
- AC 1: 内存数据采集准确性
- AC 4: 进程内存映射分析
- AC 6: 性能与资源占用
- 核心功能点 1, 5

**P1 (首版本必备)**
- AC 2: 内存泄漏检测
- AC 3: OOM 事件解析
- AC 5: Swap 分析
- 核心功能点 2, 3, 4

**P2 (后续版本优化)**
- AC 7: 历史数据查询
- AC 8: 多维度关联分析
- 核心功能点 6, 7

## 输出示例

### 内存泄漏检测输出
```bash
$ aiops detect memory-leak --pid 15234 --history 24h

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 内存泄漏检测报告                                    2024-01-15 14:30:25 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 进程: java (PID: 15234)                                            │
│ 检测时间范围: 2024-01-14 14:30:25 - 2024-01-15 14:30:25          │
│ 检测算法: 线性回归 + 变化点检测                                   │
├──────────────────────────────────────────────────────────────────┤
│ 🔴 检测到内存泄漏 (置信度: 96.3%)                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 📊 内存增长趋势:                                                   │
│   ┌────────────────────────────────────────┐                   │
│   │ RSS: 1.2GB → 3.8GB (+216%)             │                   │
│   │ 增长速率: 108.3 MB/hour                │                   │
│   │ 线性拟合 R² = 0.94                     │                   │
│   └────────────────────────────────────────┘                   │
│                                                                  │
│ ⏱️  OOM 预测:                                                      │
│   系统可用内存: 4.2 GB                                             │
│   按当前增长速率，预计 39 小时后 OOM                                │
│   OOM 时间估算: 2024-01-17 05:30:00                              │
│                                                                  │
│ 🔍 泄漏类型分析:                                                   │
│   - Heap 内存: +2.1 GB (主要贡献)                                  │
│   - Anonymous mmap: +0.3 GB                                        │
│   - Shared memory: +0.2 GB                                         │
│                                                                  │
│ 💡 建议操作:                                                       │
│   1. 生成堆转储: jmap -dump:live,format=b,file=heap.hprof 15234  │
│   2. 分析堆对象: MAT、jhat 等                                      │
│   3. 检查 GC 日志: aiops logs --pid 15234 --grep "GC"            │
│   4. 重启进程（临时缓解）                                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### OOM 分析输出
```bash
$ aiops analyze oom --last

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ OOM 事件分析                                       2024-01-15 14:30:25 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ OOM 发生时间: 2024-01-15 10:23:45                                  │
│ 触发类型: oom-killer                                              │
├──────────────────────────────────────────────────────────────────┤
│ 🚨 被 Kill 进程:                                                   │
│   进程名: mysqld                                                  │
│   PID: 2891                                                       │
│   内存占用: 4.2 GB (RSS)                                          │
│   oom_score: 891                                                 │
├──────────────────────────────────────────────────────────────────┤
│ 📊 系统内存状态 (OOM 时):                                          │
│   Total: 8.0 GB                                                   │
│   Free: 52 MB (0.65%)                                            │
│   Available: 128 MB (1.6%)                                       │
│   Cached: 256 MB                                                  │
│   Swap: 5.1 GB / 8.0 GB (63.75%)                                 │
├──────────────────────────────────────────────────────────────────┤
│ 🔍 根因分析:                                                       │
│   1. MySQL 进程内存持续增长（可能是连接数或查询缓存导致）            │
│   2. Swap 已大量使用，但无法缓解内存压力                            │
│   3. 系统 Available 内存不足 200MB                                 │
│                                                                  │
│ 💡 预防建议:                                                       │
│   1. 增加 MySQL 内存限制 (innodb_buffer_pool_size)                │
│   2. 配置 OOM 保护 (oom_score_adj)                                 │
│   3. 增加物理内存或 Swap 空间                                       │
│   4. 设置内存监控告警 (aiops alert memory)                         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 后续演进方向

1. **Java 堆分析**: 集成 jmap、MAT，自动分析 Java 堆泄漏
2. **C/C++ 堆分析**: 集成 valgrind、AddressSanitizer
3. **容器内存限制**: 分析 Kubernetes/Docker 内存限制和 OOM
4. **NUMA 感知**: 分析 NUMA 架构下的内存分配和跨节点访问
