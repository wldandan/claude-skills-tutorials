# aiops-cli 测试套件

本目录包含 aiops-cli CPU 异常检测功能的完整测试套件。

## 目录结构

```
tests/
├── README.md                      # 本文档
├── conftest.py                    # pytest 配置和共享 fixtures
├── pytest.ini                     # pytest 配置文件
├── unit/                          # 单元测试
│   └── test_*.py
├── integration/                   # 集成测试
│   └── test_*.py
├── performance/                   # 性能测试
│   └── test_*.py
├── fixtures/                      # 测试数据和 fixtures
│   └── test_data/
├── mocks/                         # Mock 数据生成器
│   └── generate_test_data.py
└── reports/                       # 测试报告目录
    ├── htmlcov/                   # 覆盖率 HTML 报告
    ├── test-report.html          # pytest HTML 报告
    └── coverage.xml              # 覆盖率 XML 报告
```

## 快速开始

### 安装测试依赖

```bash
cd /path/to/claude-skills-tutorials

# 安装 Python 依赖
pip install pytest pytest-cov pytest-html pytest-benchmark pytest-mock
pip install psutil pandas numpy scikit-learn

# 或使用 requirements.txt
pip install -r requirements-test.txt
```

### 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ -v --cov=aiops-cli --cov-report=html --html=tests/reports/test-report.html

# 运行特定类型的测试
pytest tests/ -v -m unit          # 仅单元测试
pytest tests/ -v -m integration   # 仅集成测试
pytest tests/ -v -m performance   # 仅性能测试
```

### 运行特定测试文件

```bash
# 运行单元测试
pytest tests/unit/test_cpu_collectors.py -v

# 运行集成测试
pytest tests/integration/test_e2e.py -v

# 运行性能测试
pytest tests/performance/test_performance.py -v
```

### 运行验收测试

```bash
# 运行所有验收测试
pytest tests/ -v -m "acceptance"

# 运行 P0 验收测试
pytest tests/ -v -k "P0 or AC1 or AC2 or AC5"

# 运行特定 AC 的测试
pytest tests/ -v -k "AC1"  # 数据采集准确性
pytest tests/ -v -k "AC2"  # 异常检测准确性
```

## 测试分类

### 单元测试 (Unit Tests)

测试单个模块、类或函数的正确性。

**位置**: `tests/unit/`

**示例**:
```bash
pytest tests/unit/test_cpu_collectors.py -v
pytest tests/unit/test_detectors.py -v
```

**标记**: `@pytest.mark.unit`

### 集成测试 (Integration Tests)

测试多个模块协作和端到端流程。

**位置**: `tests/integration/`

**示例**:
```bash
pytest tests/integration/test_e2e.py -v
```

**标记**: `@pytest.mark.integration`

### 性能测试 (Performance Tests)

验证系统性能指标，包括响应时间、资源占用等。

**位置**: `tests/performance/`

**示例**:
```bash
pytest tests/performance/test_performance.py -v
```

**标记**: `@pytest.mark.performance`

### 边界测试 (Boundary Tests)

测试边界条件和异常情况处理。

**位置**: `tests/performance/test_performance.py`

**标记**: `@pytest.mark.boundary`

### 压力测试 (Stress Tests)

测试系统在极端条件下的表现。

**标记**: `@pytest.mark.stress`

## 测试标记 (Markers)

### 按测试类型
- `unit`: 单元测试
- `integration`: 集成测试
- `performance`: 性能测试
- `boundary`: 边界测试
- `stress`: 压力测试
- `accuracy`: 准确性测试

### 按优先级
- `P0`: P0 用例（必须通过）
- `P1`: P1 用例（高优先级）
- `P2`: P2 用例（低优先级）

### 按特殊要求
- `slow`: 慢速测试（> 10秒）
- `linux_only`: 仅在 Linux 上运行
- `requires_root`: 需要 root 权限
- `requires_proc`: 需要 /proc 文件系统

## 测试数据

### 生成测试数据

使用 Mock 数据生成器创建测试数据：

```bash
# 生成正常负载数据（1小时）
python tests/mocks/generate_test_data.py --type normal --duration 60 \
    --output tests/fixtures/test_data/normal_data.json

# 生成包含异常的数据（24小时）
python tests/mocks/generate_test_data.py --type mixed --duration 1440 \
    --anomalies 5 --output tests/fixtures/test_data/mixed_data.json

# 生成 CSV 格式数据
python tests/mocks/generate_test_data.py --type normal --duration 60 \
    --output tests/fixtures/test_data/data.csv --format csv
```

### 使用测试数据

在测试中使用 fixtures 加载数据：

```python
def test_with_dataset(accuracy_dataset_path):
    with open(accuracy_dataset_path, 'r') as f:
        data = json.load(f)
    # 使用数据进行测试
```

## 混沌测试

使用混沌工程工具进行故障注入测试：

```bash
# 生成 CPU 高负载（95% 持续 5 分钟）
python chaos/cpu/stress_generator.py --load 95 --duration 300

# 在另一个终端运行检测
aiops detect cpu --threshold 90 --time-range 10m

# 模拟单核过载
python chaos/cpu/stress_generator.py --load 100 --duration 300 --core 0

# 模拟进程争用
python chaos/cpu/stress_generator.py --contention --num-processes 10 \
    --load-per-process 20 --duration 300

# 注入数据采集故障
python chaos/cpu/fault_injector.py --proc-failure --file /proc/stat --rate 0.5
```

详见: `/chaos/README.md`

## 测试报告

### 生成 HTML 测试报告

```bash
pytest tests/ -v --html=tests/reports/test-report.html --self-contained-html
```

报告位置: `tests/reports/test-report.html`

### 生成覆盖率报告

```bash
pytest tests/ -v --cov=aiops-cli --cov-report=html --cov-report=xml
```

- HTML 报告: `tests/reports/htmlcov/index.html`
- XML 报告: `tests/reports/coverage.xml`

### 查看覆盖率

```bash
# 在浏览器中打开覆盖率报告
open tests/reports/htmlcov/index.html
```

## 持续集成

### GitHub Actions

测试会自动在以下情况运行：
- Pull Request 创建或更新
- 代码推送到 main 分支
- 手动触发

### CI 环境变量

- `TEST_ENV`: 测试环境（dev/staging/prod）
- `SKIP_SLOW`: 设置为 1 跳过慢速测试
- `SKIP_LINUX`: 设置为 1 跳过 Linux 专用测试

## 常见问题

### Q: 测试失败怎么办？

1. 查看测试日志:
   ```bash
   pytest tests/ -v --tb=long
   ```

2. 运行单个失败的测试:
   ```bash
   pytest tests/unit/test_cpu_collectors.py::TestSystemCPUCollector::test_collect_cpu_metrics -v
   ```

3. 查看详细输出:
   ```bash
   pytest tests/ -v -s
   ```

### Q: 如何跳过某些测试？

```bash
# 跳过慢速测试
pytest tests/ -v -m "not slow"

# 跳过需要 Linux 的测试
pytest tests/ -v -m "not linux_only"

# 跳过需要 root 的测试
pytest tests/ -v -m "not requires_root"
```

### Q: 测试需要 root 权限吗？

大部分测试不需要 root 权限。只有以下测试需要 root：
- eBPF 相关测试
- 权限不足模拟测试
- 某些混沌测试

使用 `-m "not requires_root"` 跳过这些测试。

### Q: 如何在非 Linux 系统上运行测试？

```bash
# 跳过所有需要 Linux 的测试
pytest tests/ -v -m "not linux_only"

# 或使用 Mock 数据运行单元测试
pytest tests/unit/ -v
```

## 贡献指南

### 添加新测试

1. 在对应目录创建测试文件
2. 使用合适的标记
3. 添加 docstring 说明测试目的
4. 确保测试独立且可重复

示例:

```python
import pytest
from aiops.cpu.models.cpu_metric import CPUMetric

@pytest.mark.unit
def test_cpu_metric_creation():
    """测试 CPU 指标对象创建"""
    metric = CPUMetric(
        timestamp=datetime.now(),
        cpu_percent=50.0,
        cpu_user=30.0,
        cpu_system=15.0,
        cpu_idle=50.0,
        cpu_iowait=5.0,
        cpu_steal=0.0
    )
    assert metric.cpu_percent == 50.0
```

### 编写测试的最佳实践

1. **遵循 AAA 模式**: Arrange（准备）- Act（执行）- Assert（断言）
2. **使用 fixtures**: 复用测试数据和设置
3. **测试独立性**: 每个测试应该独立运行
4. **清晰的断言**: 使用明确的断言消息
5. **测试边界**: 包含正常和异常情况

## 性能基准

测试建立了以下性能基准：

| 指标 | 基准值 |
|------|--------|
| 采集速度 | > 100 次/秒 |
| 单次采集耗时 | < 10ms |
| 静态阈值检测（100k 点） | < 5秒 |
| 动态基线检测（100k 点） | < 5秒 |
| 内存占用（守护进程） | < 100MB |
| CPU 占用（守护进程） | < 2% |

如果性能测试失败，检查：
- 系统负载
- 后台进程
- Python 版本

## 联系方式

- **测试负责人**: aiops-cli-tester
- **问题反馈**: 在项目中创建 Issue
- **文档更新**: 提交 Pull Request

## 许可证

本测试套件遵循项目主许可证。
