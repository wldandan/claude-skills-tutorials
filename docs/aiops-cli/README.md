# AIOps CLI 工具 - 首版本特性总览

## 产品定位

**AIOps CLI** 是一款聚焦于操作系统（OS）层面的智能运维命令行工具，面向运维工程师和 SRE，通过 AI 技术实现运维问题的自动检测、定界和根因分析。

### 核心价值

- **快速定界**: 自动识别问题发生的层面（硬件、内核、资源、进程、应用）
- **智能根因分析**: 基于因果推断和关联分析，自动找出根本原因
- **降低运维门槛**: 通过 CLI 界面和智能分析，降低复杂问题的排查难度
- **提升效率**: 减少 MTTR（平均恢复时间），提高运维效率

### 目标用户

- **运维工程师**: 日常系统监控、故障排查
- **SRE**: 系统稳定性保障、容量规划、性能优化
- **DevOps 工程师**: CI/CD 流水线集成、自动化运维
- **应用开发者**: 应用性能分析、问题定位

---

## 首版本 10 大核心特性

### 1. CPU 异常检测与分析
**文件**: [01-cpu-anomaly-detection.md](./features/01-cpu-anomaly-detection.md)

- 实时 CPU 监控（整体、各核、进程级）
- 异常检测（静态阈值、动态基线、ML 算法）
- 进程深度分析（线程级、调用栈）
- 历史趋势分析与预测
- 智能告警

**关键命令**:
```bash
aiops detect cpu --time-range 1h
aiops analyze cpu --pid <pid> --threads --call-graph
aiops trend cpu --period 7d --forecast 24h
```

---

### 2. 内存异常检测与分析
**文件**: [02-memory-anomaly-detection.md](./features/02-memory-anomaly-detection.md)

- 内存健康评分
- 内存泄漏检测与预测
- OOM 事件分析
- Swap 分析与优化建议
- 进程内存详情（heap/stack/maps）
- 缓存效率分析

**关键命令**:
```bash
aiops detect memory-leak --pid <pid> --history 24h
aiops analyze oom --last
aiops analyze swap --processes
```

---

### 3. 磁盘 IO 异常检测与分析
**文件**: [03-disk-io-anomaly-detection.md](./features/03-disk-io-anomaly-detection.md)

- IO 性能实时监控（吞吐量、IOPS、延迟、队列）
- IO 异常检测（延迟突增、吞吐量突降）
- 进程 IO 分析
- 磁盘使用分析（大文件、目录占用）
- IO 等待分析
- 磁盘性能基准测试

**关键命令**:
```bash
aiops monitor io --interval 1
aiops detect io-anomaly --device sda
aiops analyze disk-usage --mountpoint / --top-dirs 20
```

---

### 4. 网络异常检测与分析
**文件**: [04-network-anomaly-detection.md](./features/04-network-anomaly-detection.md)

- 网络连通性诊断（多层次 L1-L7）
- 带宽分析（网卡、进程、连接）
- 连接分析（状态分布、连接泄露）
- TCP 协议栈分析（重传、丢包、拥塞）
- 端口监听分析
- 网络异常检测（DDoS、连接风暴）

**关键命令**:
```bash
aiops diagnose connectivity --host example.com --port 443
aiops analyze bandwidth --interface eth0 --processes
aiops analyze connections --state
```

---

### 5. 进程与服务异常检测与分析
**文件**: [05-process-service-anomaly-detection.md](./features/05-process-service-anomaly-detection.md)

- 进程健康监控
- 服务状态分析（systemd、SysV init）
- 进程崩溃分析（core dump、信号）
- 重启历史分析（原因、模式）
- 启动失败诊断
- 进程树分析
- 进程行为分析（系统调用、文件访问）

**关键命令**:
```bash
aiops monitor processes --critical PIDs
aiops analyze service --name nginx --detail
aiops analyze restarts --service mysql --period 7d
aiops diagnose start-failure --name <service>
```

---

### 6. 智能日志分析与异常检测
**文件**: [06-log-analysis.md](./features/06-log-analysis.md)

- 日志查询与过滤（多条件、实时追踪）
- 日志模式识别（自动提取日志模板）
- 异常日志检测（罕见模式、日志风暴）
- 错误日志聚合与统计
- 日志关联分析（与系统指标关联）
- 日志统计与报告

**关键命令**:
```bash
aiops logs --path /var/log/app.log --level error --tail 100
aiops logs --pattern-detect --period 1h
aiops logs --correlate --anomaly-time 2024-01-15T14:15:00
```

---

### 7. 多维度关联分析与问题定界
**文件**: [07-correlation-analysis.md](./features/07-correlation-analysis.md)

- 全局关联分析（CPU、内存、IO、网络、日志）
- 问题定界（逐层排除，定位问题层次）
- 事件时间线（构建完整事件链）
- 指标相关性分析（皮尔逊、滞后相关）
- 异常传播分析
- 对比分析（正常 vs 异常）
- 根因假设生成

**关键命令**:
```bash
aiops correlate --all --time-range 1h
aiops diagnose --symptom "应用响应慢" --time-range 30m
aiops timeline --event 2024-01-15T14:15:00 --window 10m
```

---

### 8. 智能根因分析 (RCA)
**文件**: [08-root-cause-analysis.md](./features/08-root-cause-analysis.md)

- 自动根因分析（因果推断、异常传播）
- 对比根因分析（正常 vs 异常时段）
- 因果关系图（可视化因果路径）
- 根因假设管理（生成、验证、反馈）
- 历史案例匹配
- 5 Why 分析
- 鱼骨图分析
- 根因报告生成

**关键命令**:
```bash
aiops rca --auto --event 2024-01-15T14:15:00
aiops rca --five-why --symptom "服务不可用"
aiops rca --fishbone --symptom "性能下降"
aiops rca --report --event <timestamp> --output rca_report.md
```

---

### 9. 指标采集与存储引擎
**文件**: [09-metrics-collection-storage.md](./features/09-metrics-collection-storage.md)

- 采集服务管理（启动、停止、状态查询）
- 采集配置（频率、保留策略、存储后端）
- 实时采集和批量采集
- 数据查询（时间范围、聚合、多指标）
- 数据导出（Prometheus、JSON、CSV）
- 存储管理（压缩、归档、清理）
- 数据源管理（本地、远程）

**关键命令**:
```bash
aiops collector start --config /etc/aiops/collector.yaml
aiops query --metric cpu.percent --period 1h
aiops export --format prometheus
aiops storage status
```

---

### 10. 智能告警与通知系统
**文件**: [10-alerting-notification.md](./features/10-alerting-notification.md)

- 告警规则管理（创建、删除、启用、禁用）
- 智能告警（ML 异常检测、趋势告警、复合条件）
- 多通道通知（邮件、短信、Webhook、Slack、钉钉、企业微信）
- 告警聚合与抑制（时间聚合、空间聚合、依赖抑制）
- 告警路由与升级（基于标签、严重性、On-call）
- 告警历史与统计
- 静默与维护模式

**关键命令**:
```bash
aiops alert create --name "high_cpu" --condition "cpu.percent > 90"
aiops notification add --type dingtalk --webhook <url>
aiops alert history --time-range 24h
aiops alert silence --name high_cpu --duration 1h
```

---

## 技术架构

### 系统分层

```
┌─────────────────────────────────────────────────────────┐
│                   CLI 交互层                            │
│         (Click、Rich、命令补全、进度条)                   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  分析引擎层                              │
│   异常检测 | 关联分析 | 根因分析 | 预测 | 日志分析         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  数据采集层                              │
│   系统指标 | 进程 | 日志 | 网络状态 | 内核事件             │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  数据存储层                              │
│   SQLite | InfluxDB | Prometheus | 文件系统               │
└─────────────────────────────────────────────────────────┘
```

### 数据流

```
数据源 (系统/进程/日志)
    ↓
采集器 (周期性采集)
    ↓
存储引擎 (持久化)
    ↓
分析引擎 (异常检测、关联分析)
    ↓
告警引擎 (规则评估、通知发送)
    ↓
CLI 用户界面 (查询、可视化)
```

---

## 优先级规划

### P0 (必须实现 - MVP)
- **特性 9**: 指标采集与存储引擎（基础设施）
- **特性 1**: CPU 异常检测与分析（最常见问题）
- **特性 6**: 智能日志分析（问题排查基础）
- **特性 10**: 智能告警与通知（及时发现问题）

### P1 (首版本必备)
- **特性 2**: 内存异常检测（第二大问题）
- **特性 3**: 磁盘 IO 异常（性能瓶颈）
- **特性 5**: 进程与服务分析（服务稳定性）
- **特性 7**: 多维度关联分析（问题定界）

### P2 (后续版本优化)
- **特性 4**: 网络异常检测（专业场景）
- **特性 8**: 智能根因分析（高级功能）

---

## 依赖环境

### 系统要求
- **操作系统**: Linux (内核 >= 3.10)
  - 推荐: CentOS 7+, Ubuntu 18.04+, Debian 10+
- **Python**: Python 3.8+
- **权限**: 普通用户权限（部分功能需要 root）
- **磁盘空间**: 至少 10GB（用于数据存储）

### 核心依赖库
```
psutil>=5.9.0          # 系统信息采集
pandas>=2.0.0          # 数据处理
numpy>=1.24.0          # 数值计算
scipy>=1.10.0          # 统计分析
scikit-learn>=1.3.0    # 机器学习
click>=8.1.0           # CLI 框架
rich>=13.0.0           # 终端美化
pyyaml>=6.0            # 配置文件
```

### 可选依赖
```
influxdb-client       # InfluxDB 存储
prometheus-client     # Prometheus 兼容
bpfcc                 # eBPF 工具（进程/网络深度分析）
```

---

## 快速开始

### 1. 安装
```bash
pip install aiops-cli
```

### 2. 初始化
```bash
aiops init
aiops collector start
```

### 3. 查看系统状态
```bash
aiops status
```

### 4. 检测异常
```bash
aiops detect --all --time-range 1h
```

### 5. 根因分析
```bash
aiops rca --auto --event <timestamp>
```

---

## 路线图

### v1.0 (首版本 - 3 个月)
- ✅ 特性 1-10 的 P0 和 P1 功能
- ✅ 基础 CLI 框架
- ✅ SQLite 存储支持
- ✅ 基础告警和通知

### v1.5 (增强版 - 6 个月)
- ⏳ InfluxDB/Prometheus 存储
- ⏳ Web Dashboard
- ⏳ eBPF 深度分析
- ⏳ 分布式追踪集成

### v2.0 (企业版 - 12 个月)
- ⏳ 多主机集中管理
- ⏳ 自动化修复
- ⏳ 知识图谱
- ⏳ 预测性运维

---

## 贡献指南

欢迎贡献代码、报告 Bug、提出新特性建议！

- **文档**: [每个特性的详细文档](./features/)
- **Issue**: [GitHub Issues](https://github.com/your-org/aiops-cli/issues)
- **Pull Request**: [GitHub PRs](https://github.com/your-org/aiops-cli/pulls)

---

## 许可证

MIT License

---

## 联系方式

- **项目主页**: https://github.com/your-org/aiops-cli
- **文档**: https://docs.aiops-cli.com
- **邮件**: support@aiops-cli.com
- **社区**: Slack #aiops-cli

---

**最后更新**: 2024-01-15
**版本**: v1.0.0-alpha
