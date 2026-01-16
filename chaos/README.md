# 混沌工程工具集

本目录包含用于 aiops-cli CPU 异常检测功能测试的混沌工程和故障注入工具。

## 目录结构

```
chaos/
├── README.md                      # 本文档
├── cpu/
│   ├── stress_generator.py       # CPU 压力生成器
│   ├── fault_injector.py         # 数据采集故障注入器
│   └── scenarios/                # 测试场景脚本
│       ├── high_load_scenario.sh
│       ├── single_core_overload.sh
│       └── multi_fault_scenario.sh
└── tests/
    └── test_chaos_tools.py       # 混沌工具测试
```

## 工具说明

### 1. CPU 压力生成器 (`stress_generator.py`)

用于模拟各种 CPU 负载场景，验证异常检测功能。

#### 功能特性

- **精确的 CPU 使用率控制**: 可以生成指定百分比的 CPU 负载
- **单核过载模拟**: 绑定特定 CPU 核心进行压力测试
- **多核过载模拟**: 同时过载多个 CPU 核心
- **进程争用模拟**: 启动多个进程争夺 CPU 资源
- **间歇性尖峰模拟**: 生成周期性的 CPU 尖峰

#### 使用示例

**基础用法 - 生成 95% CPU 负载**:
```bash
python chaos/cpu/stress_generator.py --load 95 --duration 300
```

**单核过载测试**:
```bash
# 在 CPU 核心 0 上生成 100% 负载
python chaos/cpu/stress_generator.py --load 100 --duration 300 --core 0
```

**多核过载测试**:
```bash
# 在核心 0 和 1 上生成 90% 负载
python chaos/cpu/stress_generator.py --load 90 --duration 300 --multi-core 0 1
```

**进程争用模拟**:
```bash
# 启动 10 个进程，每个占用 20% CPU
python chaos/cpu/stress_generator.py --contention --num-processes 10 \
    --load-per-process 20 --duration 300
```

**间歇性尖峰模拟**:
```bash
# 模拟尖峰 95%，基线 20%，尖峰持续 30 秒，基线 60 秒
python chaos/cpu/stress_generator.py --intermittent --peak-load 95 \
    --baseline-load 20 --peak-duration 30 --baseline-duration 60 \
    --total-duration 300
```

#### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--load` | 目标 CPU 使用率 (0-100) | 95 |
| `--duration` | 持续时间（秒） | 300 |
| `--core` | 绑定的 CPU 核心编号 | None |
| `--multi-core` | 多个核心编号 | - |
| `--contention` | 启用进程争用模式 | False |
| `--num-processes` | 争用进程数量 | 10 |
| `--load-per-process` | 每进程 CPU 使用率 | 20 |
| `--intermittent` | 启用间歇性尖峰模式 | False |
| `--peak-load` | 尖峰时 CPU 使用率 | 95 |
| `--baseline-load` | 基线 CPU 使用率 | 20 |
| `--peak-duration` | 尖峰持续时间（秒） | 30 |
| `--baseline-duration` | 基线持续时间（秒） | 60 |
| `--total-duration` | 总持续时间（秒） | 300 |

---

### 2. 故障注入器 (`fault_injector.py`)

用于模拟各种数据采集异常场景，验证系统的容错能力。

#### 功能特性

- **/proc 文件读取失败**: 模拟 proc 文件系统读取错误
- **数据格式损坏**: 模拟各种数据格式异常
- **权限不足**: 模拟文件访问权限问题
- **网络超时**: 模拟远程数据源超时
- **磁盘 I/O 失败**: 模拟磁盘空间不足

#### 使用示例

**模拟 /proc/stat 读取失败**:
```bash
# 100% 读取失败率
python chaos/cpu/fault_injector.py --proc-failure --file /proc/stat --rate 1.0

# 50% 读取失败率（间歇性失败）
python chaos/cpu/fault_injector.py --proc-failure --file /proc/stat --rate 0.5
```

**模拟数据格式损坏**:
```bash
# 无效格式
python chaos/cpu/fault_injector.py --corruption --type invalid_format

# 缺少字段
python chaos/cpu/fault_injector.py --corruption --type missing_fields

# 错误的数据类型
python chaos/cpu/fault_injector.py --corruption --type wrong_types
```

**模拟权限不足**:
```bash
python chaos/cpu/fault_injector.py --permission --file /proc/cpuinfo
```

**模拟网络超时**:
```bash
# 响应延迟 30 秒
python chaos/cpu/fault_injector.py --network-timeout --delay 30
```

**使用配置文件注入多个故障**:
```bash
python chaos/cpu/fault_injector.py --config fault_config.json
```

配置文件示例 (`fault_config.json`):
```json
{
  "proc_file_failure": {
    "enabled": true,
    "rate": 0.5
  },
  "data_corruption": {
    "enabled": true,
    "types": ["invalid_format", "missing_fields"]
  },
  "network_timeout": {
    "enabled": true,
    "delay": 30.0
  }
}
```

#### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--proc-failure` | 模拟 /proc 文件读取失败 | False |
| `--file` | 目标文件路径 | /proc/stat |
| `--rate` | 读取失败率 (0.0-1.0) | 1.0 |
| `--corruption` | 模拟数据格式损坏 | False |
| `--type` | 损坏类型 | invalid_format |
| `--permission` | 模拟权限不足 | False |
| `--network-timeout` | 模拟网络超时 | False |
| `--delay` | 响应延迟（秒） | 30 |
| `--disk-failure` | 模拟磁盘空间不足 | False |
| `--data-dir` | 数据目录 | /tmp/aiops_data |
| `--config` | 故障配置 JSON 文件 | - |
| `--duration` | 故障持续时间（秒） | 60 |

---

## 测试场景

### 场景 1: 高 CPU 负载检测测试

**目标**: 验证系统能准确检测持续的高 CPU 负载

**步骤**:
1. 启动 CPU 压力生成器（95% 负载，5 分钟）
2. 同时运行 aiops-cli 检测
3. 验证检测结果的准确性和延迟

```bash
#!/bin/bash
# scenarios/high_load_scenario.sh

# 启动 CPU 压力（后台运行）
python chaos/cpu/stress_generator.py --load 95 --duration 300 &
STRESS_PID=$!

# 等待 10 秒让负载稳定
sleep 10

# 运行检测
aiops detect cpu --time-range 10m --threshold 90

# 清理
kill $STRESS_PID
```

### 场景 2: 单核过载测试

**目标**: 验证单核过载检测功能

**步骤**:
1. 在 CPU 核心 0 上生成 100% 负载
2. 验证系统能识别单核异常
3. 检查进程 CPU 亲和性报告

```bash
#!/bin/bash
# scenarios/single_core_overload.sh

# 在核心 0 上生成负载
python chaos/cpu/stress_generator.py --load 100 --duration 300 --core 0 &
STRESS_PID=$!

sleep 10

# 检测单核过载
aiops detect cpu --per-core --threshold 90

# 分析进程
aiops analyze cpu --top 10 --affinity

# 清理
kill $STRESS_PID
```

### 场景 3: 复杂故障场景

**目标**: 验证系统在多种故障同时发生时的表现

**步骤**:
1. 注入数据采集故障
2. 同时生成 CPU 高负载
3. 验证系统的容错和错误处理

```bash
#!/bin/bash
# scenarios/multi_fault_scenario.sh

# 启动故障注入
python chaos/cpu/fault_injector.py --proc-failure --rate 0.3 &
FAULT_PID=$!

# 生成 CPU 负载
python chaos/cpu/stress_generator.py --load 90 --duration 300 &
STRESS_PID=$!

sleep 10

# 运行检测（应能处理部分失败）
aiops detect cpu --time-range 10m --retry 3

# 清理
kill $STRESS_PID $FAULT_PID
```

---

## 注意事项

### 安全警告

1. **权限要求**: 部分故障注入（如权限模拟、磁盘填充）需要 root 权限
2. **生产环境禁用**: 混沌工具仅用于测试环境，禁止在生产环境使用
3. **资源限制**: CPU 压力生成会占用系统资源，建议在隔离的测试环境运行
4. **数据备份**: 故障注入可能影响系统文件，建议在虚拟机或容器中运行

### 最佳实践

1. **使用容器**: 推荐在 Docker 容器中运行混沌测试
2. **监控资源**: 运行混沌工具时监控系统资源
3. **快速清理**: 始终使用 Ctrl+C 或 kill 命令停止工具
4. **测试隔离**: 每次测试后重启测试环境
5. **日志记录**: 保存测试日志以便分析

### 依赖要求

```bash
# Python 依赖
pip install psutil multiprocessing

# 系统工具（部分功能需要）
sudo apt-get install stress taskset  # Ubuntu/Debian
sudo yum install stress util-linux   # CentOS/RHEL
```

---

## 开发指南

### 添加新的故障类型

1. 在 `fault_injector.py` 中创建新的故障类
2. 继承 `FaultInjector` 基类
3. 实现 `inject()` 和 `cleanup()` 方法
4. 在 `main()` 函数中添加命令行参数

示例:
```python
class MyCustomFault(FaultInjector):
    def __init__(self, param):
        super().__init__('my_custom_fault')
        self.param = param

    def inject(self):
        # 实现故障注入逻辑
        pass

    def cleanup(self):
        # 实现清理逻辑
        pass
```

### 添加新的压力场景

1. 在 `scenarios/` 目录创建新脚本
2. 添加详细注释说明
3. 包含启动、测试、清理三个阶段
4. 确保脚本可独立执行

---

## 常见问题

**Q: 为什么 CPU 压力生成器无法达到精确的使用率？**

A: 由于系统调度和其他进程的影响，实际 CPU 使用率可能有偏差。工具通过工作/休眠周期尽量接近目标值。

**Q: 故障注入会影响系统稳定性吗？**

A: 部分故障（如磁盘填充）可能导致系统不稳定。建议在虚拟机中运行，并准备快照以便快速恢复。

**Q: 如何验证故障注入是否成功？**

A: 查看工具输出的日志信息，或使用系统监控工具（top、iostat 等）验证效果。

**Q: 混沌工具可以组合使用吗？**

A: 可以。建议在不同终端或后台运行多个工具，模拟复杂的故障场景。

---

## 贡献指南

欢迎贡献新的混沌工具和测试场景！

1. Fork 本项目
2. 创建特性分支
3. 添加新工具或场景
4. 编写测试和文档
5. 提交 Pull Request

---

## 许可证

本工具集遵循项目主许可证。
