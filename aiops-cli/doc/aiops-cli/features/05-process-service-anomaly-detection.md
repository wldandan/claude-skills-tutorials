# 特性 05: 进程与服务异常检测与分析

## 功能概述

提供进程和服务级别的异常检测与分析能力，涵盖进程崩溃、服务重启、僵尸进程、进程资源异常、进程启动失败等问题。通过监控进程生命周期、资源使用、状态变化，快速定位服务不可用的根本原因（资源耗尽、配置错误、依赖失败等）。

## 用户场景

**场景 1: 服务频繁重启**
- 应用服务频繁重启（OOM kill、segfault、被 systemd 重启）
- 需要分析重启原因和模式
- 使用 `aiops analyze restarts --service nginx` 查看重启历史和原因

**场景 2: 进程僵死或卡死**
- 进程存在但不响应（卡在某个系统调用）
- 需要分析进程状态和堆栈
- 使用 `aiops inspect process --pid <pid> --stack` 分析进程状态

**场景 3: 服务启动失败**
- 服务启动失败，无法确定原因
- 需要分析启动日志和依赖
- 使用 `aiops diagnose start-failure --service <service>` 诊断启动问题

## 技术方案概要

### 数据采集层
- 读取 `/proc/<pid>/*` 获取进程详细信息
- 读取 systemd 日志 (`journalctl`) 获取服务启动/停止/重启事件
- 读取 `/var/log/messages`、dmesg 获取内核日志（OOM kill、segfault）
- 使用 `systemctl`、`service` 获取服务状态
- 使用 `ps`、`pstree` 获取进程树和关系
- 使用 `strace` 追踪系统调用（诊断模式）
- 使用 eBPF 追踪进程生命周期事件

### 异常检测算法
- **进程退出异常**: 检测异常退出码（非 0）、信号 kill（SIGKILL、SIGSEGV）
- **重启异常**: 检测频繁重启（restart rate > 阈值）
- **僵尸进程**: 检测僵尸进程（Z 状态）积累
- **资源异常**: 检测进程资源使用突变（CPU/内存/IO）
- **启动失败**: 检测服务启动失败（systemd failed 状态）

### 根因分析
- **退出码分析**: 解析退出码对应的错误含义
- **信号分析**: 识别导致进程死亡的信号（SIGKILL/SIGSEGV/SIGABRT 等）
- **日志关联**: 关联进程的 stdout/stderr 日志和系统日志
- **资源快照**: 保存进程退出前的资源使用快照
- **依赖检查**: 检查服务的依赖项（端口、文件系统、其他服务）
- **配置检查**: 检查配置文件语法和有效性

## 核心功能点

### 1. 进程健康监控
```bash
# 实时监控进程健康状态
aiops monitor processes --interval 10 --critical PIDs
```
- 监控关键进程的存活状态
- 检测进程意外退出
- 检测进程资源使用异常
- 发送告警通知

### 2. 服务状态分析
```bash
# 分析 systemd 服务状态
aiops analyze service --name nginx --detail
```
- 显示服务状态（running/exited/failed）
- 显示服务启动时间、PID、主进程
- 显示最近的启动/停止/重启事件
- 显示服务日志尾部（journalctl）

### 3. 进程崩溃分析
```bash
# 分析进程崩溃事件
aiops analyze crash --last --detail
```
- 读取 core dump 文件（如果有）
- 解析崩溃信号（SIGSEGV、SIGABRT 等）
- 显示崩溃时的堆栈和寄存器
- 关联崩溃前的日志和资源状态

### 4. 重启历史分析
```bash
# 分析服务重启历史
aiops analyze restarts --service mysql --period 7d
```
- 列出服务重启历史（时间、原因）
- 分析重启模式（频率、时间分布）
- 识别重启原因（OOM kill、手动重启、崩溃）
- 统计重启间隔和 MTTR（平均恢复时间）

### 5. 进程资源分析
```bash
# 分析进程资源使用
aiops analyze process --pid <pid> --resources
```
- 显示 CPU、内存、IO、网络使用
- 对比同类型进程的资源使用
- 检测资源泄漏（持续增长）
- 显示进程限制（ulimit、cgroups）

### 6. 启动失败诊断
```bash
# 诊断服务启动失败
aiops diagnose start-failure --name <service>
```
- 检查配置文件语法
- 检查依赖服务状态
- 检查端口占用
- 检查文件权限
- 分析启动日志错误信息
- 提供修复建议

### 7. 进程树分析
```bash
# 分析进程树和关系
aiops analyze ptree --pid <pid> --recursive
```
- 显示完整的进程树（父进程、子进程）
- 显示每个进程的资源占用
- 检测异常的进程关系（孤儿进程、僵尸进程）
- 显示进程间通信（管道、共享内存）

### 8. 进程行为分析
```bash
# 分析进程行为模式
aiops analyze behavior --pid <pid> --duration 60s
```
- 追踪系统调用（strace 或 eBPF）
- 识别文件访问模式
- 识别网络连接模式
- 检测异常行为（如频繁 fork、异常文件访问）

## 验收标准 (Acceptance Criteria)

### AC 1: 进程数据采集准确性
- **Given**: 系统运行多个进程
- **When**: 执行 `aiops collect processes --duration 60s`
- **Then**:
  - 采集的进程列表与 `ps aux` 一致（误差 < 1%）
  - 进程状态（R/S/D/Z）识别准确
  - 进程资源占用与 `ps` 或 `/proc/<pid>/stat` 一致（误差 < 5%）

### AC 2: 服务状态分析准确性
- **Given**: systemd 服务正在运行
- **When**: 执行 `aiops analyze service --name nginx`
- **Then**:
  - 服务状态与 `systemctl status nginx` 一致
  - PID、启动时间、主进程识别准确
  - 最近的启动/停止事件时间准确（误差 < 1s）

### AC 3: 进程崩溃检测准确性
- **Given**: 进程发生崩溃（如 segfault）
- **When**: 执行 `aiops analyze crash --last`
- **Then**:
  - 检测到崩溃事件，准确率 >= 95%（基于日志）
  - 崩溃信号识别正确（SIGSEGV、SIGKILL 等）
  - 崩溃时间准确（误差 < 1s）

### AC 4: 重启历史分析完整性
- **Given**: 服务过去 7 天有多次重启
- **When**: 执行 `aiops analyze restarts --service nginx --period 7d`
- **Then**:
  - 列出所有重启事件（时间、原因）
  - 重启原因分类准确（手动/OOM/崩溃）
  - MTTR 计算正确

### AC 5: 启动失败诊断
- **Given**: 服务启动失败（systemd failed 状态）
- **When**: 执行 `aiops diagnose start-failure --name <service>`
- **Then**:
  - 识别启动失败的原因（配置/依赖/权限等）
  - 提供的错误信息准确（来自 journalctl）
  - 提供的修复建议可操作

### AC 6: 性能与资源占用
- **Given**: 系统运行正常
- **When**: 启动 `aiops monitor processes --daemon` 后台运行
- **Then**:
  - 工具自身 CPU 占用 < 2%（单核）
  - 内存占用 < 100MB
  - 不影响被监控进程的性能

### AC 7: 僵尸进程检测
- **Given**: 系统存在僵尸进程
- **When**: 执行 `aiops analyze zombies`
- **Then**:
  - 识别所有僵尸进程
  - 显示僵尸进程的父进程
  - 提供清理建议（kill 父进程或重启服务）

### AC 8: 进程树分析
- **Given**: 系统有复杂的进程树
- **When**: 执行 `aiops analyze ptree --pid <init_pid> --recursive`
- **Then**:
  - 正确显示完整的进程树结构
  - 父子关系准确
  - 每个进程的资源占用显示正确

## 依赖项

### 系统依赖
- **操作系统**: Linux (内核 >= 3.10)
- **Python**: Python 3.8+
- **init 系统**: systemd (推荐) 或 SysV init
- **权限**: 普通用户权限，部分功能需要 root

### Python 库依赖
```
psutil>=5.9.0          # 进程信息采集
pandas>=2.0.0          # 数据处理
click>=8.1.0           # CLI 框架
rich>=13.0.0           # 终端美化
```

### 可选依赖
```
systemd-python>=234    # systemd 日志和状态查询
```

## 优先级

**P0 (必须实现)**
- AC 1: 进程数据采集准确性
- AC 2: 服务状态分析
- AC 6: 性能与资源占用
- 核心功能点 1, 2

**P1 (首版本必备)**
- AC 3: 进程崩溃检测
- AC 4: 重启历史分析
- AC 5: 启动失败诊断
- 核心功能点 3, 4, 5, 6

**P2 (后续版本优化)**
- AC 7: 僵尸进程检测
- AC 8: 进程树分析
- 核心功能点 7, 8

## 输出示例

### 服务重启历史分析输出
```bash
$ aiops analyze restarts --service mysql --period 7d

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 服务重启历史分析                                     2024-01-15 14:30:25 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 服务名: mysql.service                                           │
│ 当前状态: running (PID: 2891)                                   │
│ 运行时长: 3d 12h 30m                                           │
│ 分析周期: 2024-01-08 - 2024-01-15 (7 天)                         │
├──────────────────────────────────────────────────────────────────┤
│ 📊 重启统计:                                                      │
│   总重启次数: 8 次                                               │
│   重启率: 1.14 次/天 ⚠️                                          │
│   平均运行时长: 18.5 小时                                        │
│   MTTR (平均恢复时间): 2.3 分钟                                   │
├──────────────────────────────────────────────────────────────────┤
│ 🕐 重启时间线:                                                    │
│                                                                  │
│   1. 2024-01-15 01:00:45 (3d 12h 前) - OOM Kill                 │
│      原因: Memory cgroup OOM                                    │
│      内存占用: 4.2 GB (限制: 4.0 GB)                            │
│      恢复时间: 45 秒                                             │
│                                                                  │
│   2. 2024-01-13 18:23:12 (1d 20h 前) - 手动重启                  │
│      原因: systemctl restart mysql (User: root)                 │
│      恢复时间: 12 秒                                             │
│                                                                  │
│   3. 2024-01-12 10:15:33 (3d 4h 前) - 崩溃 (SIGSEGV)            │
│      原因: Segmentation fault                                    │
│      Core dump: /var/crash/mysql.core.12345                     │
│      恢复时间: 2 分 15 秒                                         │
│      日志尾段:                                                   │
│        mysqld: got signal 11 ;                                  │
│        mysqld: terminating on signal 11                         │
│                                                                  │
│   4. 2024-01-11 02:45:10 (1d 7h 前) - OOM Kill                 │
│      原因: System OOM                                           │
│      内存占用: 3.8 GB (可用: 256 MB)                            │
│      恢复时间: 3 分 30 秒                                         │
│                                                                  │
│   5. 2024-01-10 14:22:55 (12h 前) - 崩溃 (SIGABRT)              │
│      原因: Abort (内部断言失败)                                  │
│      恢复时间: 1 分 45 秒                                         │
│      日志尾段:                                                   │
│        InnoDB: Assertion failure in thread 12345                │
│        InnoDB: We intentionally generate a memory trap          │
│                                                                  │
│   ... (省略 3 次重启)                                            │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 🔍 根因分析:                                                      │
│   主要原因:                                                       │
│     • OOM Kill: 3 次 (37.5%) - 内存不足                          │
│     • 崩溃 (SIGSEGV/SIGABRT): 4 次 (50%) - 软件缺陷              │
│     • 手动重启: 1 次 (12.5%) - 运维操作                           │
│                                                                  │
│   时间模式:                                                       │
│     • 无明显周期性                                               │
│     • 大多发生在凌晨或业务低峰期                                  │
│     • 崩溃主要在高负载后                                         │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 💡 优化建议:                                                      │
│   短期:                                                          │
│     1. 增加 MySQL 内存限制:                                       │
│        systemctl set-property mysql.service MemoryLimit=6G      │
│     2. 升级 MySQL 到最新稳定版（修复崩溃 bug）                    │
│     3. 启用 core dump 进行详细分析:                               │
│        systemctl set-property mysql.service LimitCORE=infinity  │
│                                                                  │
│   长期:                                                          │
│     1. 分析崩溃原因:                                              │
│        gdb /usr/sbin/mysqld /var/crash/mysql.core.12345         │
│     2. 监控和告警:                                                │
│        aiops alert create --service mysql --condition restarts>3/day
│     3. 考虑使用高可用方案 (Galera/MGR)                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 启动失败诊断输出
```bash
$ aiops diagnose start-failure --name nginx

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 服务启动失败诊断                                     2024-01-15 14:30:25 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 服务名: nginx.service                                           │
│ 当前状态: failed                                                │
├──────────────────────────────────────────────────────────────────┤
│ 🔴 失败信息:                                                      │
│   启动时间: 2024-01-15 14:28:15                                │
│   失败原因: Exit code 1                                         │
│   错误详情:                                                      │
│                                                                  │
│   Journalctl 日志:                                               │
│     Jan 15 14:28:15 server systemd[1]: Starting nginx...        │
│     Jan 15 14:28:15 server nginx[15234]:                        │
│     nginx: [emerg] bind() to 0.0.0.0:443 failed (98: Address already in use)
│     Jan 15 14:28:15 server nginx[15234]:                        │
│     nginx: [emerg] bind() to [::]:443 failed (98: Address already in use)
│     Jan 15 14:28:15 server nginx[15234]:                        │
│     nginx: [emerg] still could not bind()                       │
│     Jan 15 14:28:15 server systemd[1]: nginx.service: Control   │
│     process exited, code=exited, status=1/FAILURE               │
│     Jan 15 14:28:15 server systemd[1]: Failed to start nginx.   │
├──────────────────────────────────────────────────────────────────┤
│ 🔍 问题诊断:                                                      │
│   ❌ 端口冲突:                                                    │
│      端口 443 已被占用                                          │
│      占用进程:                                                   │
│        PID: 2891                                                │
│        名称: apache2                                            │
│        命令: /usr/sbin/apache2 -k start                         │
│        启动时间: 2024-01-10 09:15:30                            │
│                                                                  │
│   ✅ 配置文件:                                                    │
│      /etc/nginx/nginx.conf - 语法正确                           │
│      /etc/nginx/sites-enabled/* - 语法正确                      │
│                                                                  │
│   ✅ 依赖服务:                                                    │
│      network.target - 已启动                                    │
│      sysinit.target - 已启动                                    │
│                                                                  │
│   ✅ 文件权限:                                                    │
│      /var/log/nginx - 755 (可写)                                │
│      /var/lib/nginx - 755 (可写)                                │
│      /run/nginx.pid - 父目录可写                                │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ 💡 解决方案:                                                      │
│   方案 1: 停止冲突服务并启动 Nginx (推荐)                          │
│     sudo systemctl stop apache2                                │
│     sudo systemctl start nginx                                 │
│                                                                  │
│   方案 2: 修改 Nginx 监听端口                                     │
│     编辑 /etc/nginx/sites-enabled/default:                      │
│     listen 443 ssl; -> listen 8443 ssl;                         │
│     sudo systemctl start nginx                                 │
│                                                                  │
│   方案 3: 使用 Apache 作为前端，Nginx 作为后端                     │
│     配置反向代理:                                                │
│     ProxyPass / http://localhost:8080/                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

⚡ 快速修复:
sudo systemctl stop apache2 && sudo systemctl start nginx
```

## 后续演进方向

1. **容器进程监控**: 支持 Docker、Kubernetes 容器进程监控
2. **进程性能剖析**: 集成 perf、py-spy 进行进程性能剖析
3. **自动恢复**: 自动重启失败的服务并上报
4. **进程依赖图**: 可视化进程间依赖关系和通信
