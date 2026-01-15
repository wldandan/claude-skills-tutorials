# 特性 01: CPU 异常检测与分析

## 功能概述

提供智能化的 CPU 使用率异常检测和深度分析功能，能够自动识别 CPU 瓶颈、单核过载、进程级 CPU 异常等问题，并通过机器学习算法区分正常业务高峰和异常负载。

## 用户场景

**场景 1: 突发 CPU 高负载告警**
- 运维人员收到 CPU 使用率超过 90% 的告警
- 需要快速判断是业务正常增长还是异常进程导致
- 使用 `aiops detect cpu --threshold 90` 快速定位问题

**场景 2: 周期性性能问题排查**
- 系统每天固定时间出现 CPU 飙升
- 需要分析历史数据找出规律和根因
- 使用 `aiops analyze cpu --history 7d --pattern-detection` 识别周期性模式

**场景 3: 进程级 CPU 异常定位**
- 某个服务进程 CPU 占用异常
- 需要分析进程内部线程分布和调用栈
- 使用 `aiops inspect cpu --pid <pid> --thread-analysis` 深入分析

## 技术方案概要

### 数据采集层
- 读取 `/proc/stat`、`/proc/cpuinfo` 获取系统级 CPU 指标
- 读取 `/proc/<pid>/stat`、`/proc/<pid>/task` 获取进程级指标
- 使用 perf、eBPF 采集 CPU 性能事件和调用栈
- 采样频率: 1秒（系统级）、5秒（进程级）

### 异常检测算法
- **静态阈值检测**: 基于配置的绝对阈值（如 CPU > 80%）
- **动态基线检测**: 使用历史 7/14/30 天数据计算动态阈值
- **时间序列异常检测**: 使用 ARIMA、Prophet 或 LSTM 检测突变点
- **多维度关联分析**: 结合 CPU、负载均衡、上下文切换等指标

### 根因分析
- **Top 进程识别**: 列出 CPU 占用最高的 Top N 进程
- **线程级别分析**: 识别进程内的热点线程
- **调用栈采样**: 使用 perf flamegraph 生成热点函数调用链
- **进程树分析**: 识别父子进程关系和资源继承
- **历史对比**: 与正常时段的进程列表对比，识别新增/异常进程

## 核心功能点

### 1. 实时 CPU 监控
```bash
# 实时显示 CPU 使用率，类似 top 但更智能
aiops monitor cpu --interval 1
```
- 输出: 整体 CPU、各核使用率、用户/系统/空闲/等待时间
- 异常高亮: 自动标记异常指标（红色/黄色）
- 进程 Top 列表: 实时更新 Top 10 进程

### 2. 异常事件检测
```bash
# 检测过去 1 小时的 CPU 异常事件
aiops detect cpu --time-range 1h --algorithm auto
```
- 自动选择最佳检测算法（静态/动态/ML）
- 输出异常时间段、严重程度、置信度
- 关联进程列表和资源快照

### 3. 进程深度分析
```bash
# 分析指定进程的 CPU 使用情况
aiops analyze cpu --pid 1234 --threads --call-graph
```
- 线程级别的 CPU 分布
- 热点调用栈和函数
- 与历史基线对比
- 进程启动时间、运行时长、累计 CPU 时间

### 4. 历史趋势分析
```bash
# 分析 CPU 使用趋势
aiops trend cpu --period 7d --forecast 24h
```
- 绘制 CPU 使用率时间序列曲线
- 识别周期性模式（小时级、天级、周级）
- 预测未来 24 小时负载（使用 Prophet 或 LSTM）
- 标注历史异常事件点

### 5. 智能告警
```bash
# 配置智能告警规则
aiops alert cpu --threshold dynamic --window 5m --consecutive 3
```
- 支持静态阈值和动态基线
- 持续时间窗口（避免瞬时抖动）
- 告警抑制（相同根因的重复告警）
- 多级告警（Warning/Critical/Emergency）

## 验收标准 (Acceptance Criteria)

### AC 1: 数据采集准确性
- **Given**: Linux 系统运行正常
- **When**: 执行 `aiops collect cpu --duration 60s`
- **Then**:
  - 采集的 CPU 使用率与 `/proc/stat` 计算结果一致（误差 < 1%）
  - 每个逻辑核心的数据准确采集
  - User/System/Idle/IO Wait 时间占比总和为 100%

### AC 2: 异常检测准确性
- **Given**: 系统存在 CPU 异常（使用率 > 90% 持续 5 分钟）
- **When**: 执行 `aiops detect cpu --time-range 1h`
- **Then**:
  - 检测到异常事件，准确率 >= 95%（基于标注测试集）
  - 误报率 <= 5%（正常时段误报）
  - 检测延迟 <= 30 秒（从异常发生到检测出）

### AC 3: 进程分析完整性
- **Given**: 指定进程正在运行
- **When**: 执行 `aiops analyze cpu --pid <pid> --threads`
- **Then**:
  - 正确列出进程的所有线程
  - 每个线程的 CPU 使用率准确（误差 < 2%）
  - 显示线程的 CPU 亲和性（CPU 核绑定）

### AC 4: 性能与资源占用
- **Given**: 系统正常运行
- **When**: 启动 `aiops monitor cpu --daemon` 后台运行
- **Then**:
  - 工具自身 CPU 占用 < 2%（单核）
  - 内存占用 < 100MB
  - 磁盘写入 < 10MB/hour（数据持久化）

### AC 5: 命令行输出格式
- **Given**: 执行任意 CPU 分析命令
- **When**: 查看输出
- **Then**:
  - 支持 `--output json`、`--output yaml`、`--output table` 三种格式
  - JSON 输出符合预定义的 Schema
  - 表格输出对齐美观，异常行自动高亮

### AC 6: 历史数据查询
- **Given**: 已采集 30 天的 CPU 数据
- **When**: 执行 `aiops query cpu --start "2024-01-01" --end "2024-01-07"`
- **Then**:
  - 返回指定时间段的所有数据点
  - 查询响应时间 < 3 秒（7 天数据）
  - 支持聚合（avg/max/min/stddev）

### AC 7: eBPF 集成
- **Given**: 系统支持 eBPF（内核 >= 4.1）
- **When**: 执行 `aiops profile cpu --pid <pid> --duration 30s`
- **Then**:
  - 使用 eBPF 采集 on-CPU 火焰图数据
  - 生成 flamegraph SVG 文件
  - 采集开销 < 5% CPU

### AC 8: 交叉引用
- **Given**: CPU 异常检测到问题
- **When**: 查看检测报告
- **Then**:
  - 自动关联同时间段的内存、磁盘、网络指标
  - 提供相关日志事件的链接
  - 标注相关告警和事件

## 依赖项

### 系统依赖
- **操作系统**: Linux (内核 >= 3.10)，推荐 CentOS 7+/Ubuntu 18.04+
- **Python**: Python 3.8+
- **权限**: 需要普通用户权限（读取 /proc），部分功能需要 root（eBPF、perf）

### Python 库依赖
```
psutil>=5.9.0          # 进程和系统信息采集
pandas>=2.0.0          # 数据处理和分析
numpy>=1.24.0          # 数值计算
scikit-learn>=1.3.0    # 机器学习算法（Isolation Forest）
scipy>=1.10.0          # 统计分析
click>=8.1.0           # 命令行框架
rich>=13.0.0           # 终端美化和进度条
pyyaml>=6.0            # 配置文件解析
```

### 可选依赖
```
protobuf>=4.0.0        # 如果使用 Prometheus 数据源
bpfcc>=0.20.0          # eBPF 工具（需要内核支持）
plotly>=5.14.0         # 交互式图表（HTML 输出）
```

### 数据存储
- **本地存储**: SQLite（默认）或 CSV 文件
- **时序数据库**: InfluxDB 2.x（可选，用于大规模部署）
- **远程存储**: 支持 Prometheus 兼容 API（可选）

## 优先级

**P0 (必须实现)**
- AC 1: 数据采集准确性
- AC 2: 异常检测准确性（基础算法）
- AC 5: 命令行输出格式

**P1 (首版本必备)**
- AC 3: 进程分析完整性
- AC 4: 性能与资源占用
- AC 6: 历史数据查询
- 核心功能点 1-3

**P2 (后续版本优化)**
- AC 7: eBPF 集成
- AC 8: 交叉引用
- 核心功能点 4-5
- ML 预测和高级分析

## 输出示例

### 表格输出示例
```bash
$ aiops detect cpu --time-range 1h

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ CPU 异常检测报告                                     2024-01-15 14:30:25 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 检测时间范围: 2024-01-15 13:30:00 - 14:30:00                      │
│ 检测算法: Dynamic Baseline (Isolation Forest)                    │
├──────────────────────────────────────────────────────────────────┤
│ ⚠️  检测到 2 个异常事件                                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 🚨 事件 #1: Critical                                              │
│    时间: 2024-01-15 14:15:23 - 14:20:45 (持续 5分22秒)            │
│    平均 CPU: 94.2% (基线: 45.3%)                                 │
│    置信度: 98.5%                                                 │
│    Top 进程:                                                      │
│      1. java (PID 15234) - 67.8%                                 │
│      2. python (PID 22891) - 12.3%                               │
│    根因提示: Java 进程异常高 CPU，建议使用 'aiops inspect cpu    │
│             --pid 15234' 深入分析                                 │
│                                                                  │
│ ⚠️  事件 #2: Warning                                               │
│    时间: 2024-01-15 13:45:10 - 13:47:30 (持续 2分20秒)            │
│    平均 CPU: 78.5% (基线: 42.1%)                                 │
│    置信度: 85.2%                                                 │
│    Top 进程:                                                      │
│      1. systemd (PID 1) - 8.2%                                   │
│      2. cron (PID 892) - 6.7%                                    │
│    根因提示: 可能是定时任务导致                                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

💡 提示: 使用 'aiops analyze cpu --time-range 1h --detail' 查看详细分析
```

### JSON 输出示例
```json
{
  "detection_results": {
    "time_range": {
      "start": "2024-01-15T13:30:00Z",
      "end": "2024-01-15T14:30:00Z"
    },
    "algorithm": "dynamic_baseline",
    "anomalies": [
      {
        "id": "anomaly_001",
        "severity": "critical",
        "start_time": "2024-01-15T14:15:23Z",
        "end_time": "2024-01-15T14:20:45Z",
        "duration_seconds": 322,
        "metrics": {
          "avg_cpu_percent": 94.2,
          "max_cpu_percent": 98.7,
          "baseline_cpu_percent": 45.3,
          "deviation_score": 2.08
        },
        "confidence": 0.985,
        "top_processes": [
          {
            "pid": 15234,
            "name": "java",
            "cpu_percent": 67.8,
            "user": "appuser"
          },
          {
            "pid": 22891,
            "name": "python",
            "cpu_percent": 12.3,
            "user": "root"
          }
        ],
        "root_cause_hypothesis": "Java process (PID 15234) consuming abnormal CPU",
        "recommended_actions": [
          "aiops inspect cpu --pid 15234 --threads",
          "aiops logs --pid 15234 --tail 100"
        ]
      }
    ]
  }
}
```

## 后续演进方向

1. **容器环境支持**: 增加 Kubernetes/Docker 容器 CPU 限制和份额分析
2. **自动调优**: 基于 CPU 使用模式自动调整进程优先级和 CPU 亲和性
3. **预测性告警**: 提前预测 CPU 资源不足，提前扩容或优化
4. **多云环境对比**: 对比不同云实例的 CPU 性能和成本
