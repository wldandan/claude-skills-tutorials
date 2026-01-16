# CPU 异常检测功能测试报告

## 报告概要

| 项目 | 内容 |
|------|------|
| **项目名称** | aiops-cli |
| **测试功能** | Feature 01: CPU 异常检测与分析 |
| **测试版本** | v1.0 |
| **测试周期** | 2026-01-16 至 2026-01-30 |
| **报告日期** | {{REPORT_DATE}} |
| **测试负责人** | aiops-cli-tester |
| **测试环境** | Ubuntu 20.04 LTS / Python 3.8+ |

### 执行摘要

{{EXECUTIVE_SUMMARY}}

- **测试用例总数**: {{TOTAL_TEST_CASES}}
- **执行用例数**: {{EXECUTED_TEST_CASES}}
- **通过用例数**: {{PASSED_TEST_CASES}}
- **失败用例数**: {{FAILED_TEST_CASES}}
- **跳过用例数**: {{SKIPPED_TEST_CASES}}
- **通过率**: {{PASS_RATE}}%

### 结论

{{TEST_CONCLUSION}}

---

## 1. 测试执行统计

### 1.1 整体统计

| 测试类型 | 总数 | 通过 | 失败 | 跳过 | 通过率 |
|---------|------|------|------|------|--------|
| 单元测试 | {{UNIT_TOTAL}} | {{UNIT_PASSED}} | {{UNIT_FAILED}} | {{UNIT_SKIPPED}} | {{UNIT_RATE}}% |
| 集成测试 | {{INTEGRATION_TOTAL}} | {{INTEGRATION_PASSED}} | {{INTEGRATION_FAILED}} | {{INTEGRATION_SKIPPED}} | {{INTEGRATION_RATE}}% |
| 性能测试 | {{PERFORMANCE_TOTAL}} | {{PERFORMANCE_PASSED}} | {{PERFORMANCE_FAILED}} | {{PERFORMANCE_SKIPPED}} | {{PERFORMANCE_RATE}}% |
| 边界测试 | {{BOUNDARY_TOTAL}} | {{BOUNDARY_PASSED}} | {{BOUNDARY_FAILED}} | {{BOUNDARY_SKIPPED}} | {{BOUNDARY_RATE}}% |
| 验收测试 | {{ACCEPTANCE_TOTAL}} | {{ACCEPTANCE_PASSED}} | {{ACCEPTANCE_FAILED}} | {{ACCEPTANCE_SKIPPED}} | {{ACCEPTANCE_RATE}}% |
| **总计** | {{GRAND_TOTAL}} | {{GRAND_PASSED}} | {{GRAND_FAILED}} | {{GRAND_SKIPPED}} | {{GRAND_RATE}}% |

### 1.2 按优先级统计

| 优先级 | 总数 | 通过 | 失败 | 通过率 |
|--------|------|------|------|--------|
| P0 (必须) | {{P0_TOTAL}} | {{P0_PASSED}} | {{P0_FAILED}} | {{P0_RATE}}% |
| P1 (高) | {{P1_TOTAL}} | {{P1_PASSED}} | {{P1_FAILED}} | {{P1_RATE}}% |
| P2 (低) | {{P2_TOTAL}} | {{P2_PASSED}} | {{P2_FAILED}} | {{P2_RATE}}% |

### 1.3 测试执行趋势

{{TEST_TREND_CHART}}

---

## 2. 代码覆盖率

### 2.1 覆盖率概览

| 模块 | 行覆盖率 | 分支覆盖率 | 函数覆盖率 |
|------|---------|-----------|-----------|
| aiops.cpu.collectors | {{COLLECTORS_COV}}% | {{COLLECTORS_BRANCH}}% | {{COLLECTORS_FUNC}}% |
| aiops.cpu.detectors | {{DETECTORS_COV}}% | {{DETECTORS_BRANCH}}% | {{DETECTORS_FUNC}}% |
| aiops.cpu.models | {{MODELS_COV}}% | {{MODELS_BRANCH}}% | {{MODELS_FUNC}}% |
| aiops.core | {{CORE_COV}}% | {{CORE_BRANCH}}% | {{CORE_FUNC}}% |
| **总计** | {{TOTAL_COV}}% | {{TOTAL_BRANCH}}% | {{TOTAL_FUNC}}% |

### 2.2 覆盖率详情

{{COVERAGE_REPORT_LINK}}

---

## 3. 验收标准达成情况

### AC 1: 数据采集准确性

| 验收项 | 状态 | 测试结果 |
|--------|------|---------|
| CPU 使用率准确性 | {{AC1_1_STATUS}} | {{AC1_1_RESULT}} |
| 多核数据采集 | {{AC1_2_STATUS}} | {{AC1_2_RESULT}} |
| 时间分量完整性 | {{AC1_3_STATUS}} | {{AC1_3_RESULT}} |

**结论**: {{AC1_CONCLUSION}}

### AC 2: 异常检测准确性

| 验收项 | 目标 | 实际 | 状态 |
|--------|------|------|------|
| 准确率 | >= 95% | {{AC2_ACCURACY}}% | {{AC2_ACCURACY_STATUS}} |
| 误报率 | <= 5% | {{AC2_FALSE_POSITIVE}}% | {{AC2_FP_STATUS}} |
| 检测延迟 | <= 30秒 | {{AC2_DELAY}}秒 | {{AC2_DELAY_STATUS}} |

**结论**: {{AC2_CONCLUSION}}

### AC 3: 进程分析完整性

| 验收项 | 状态 | 测试结果 |
|--------|------|---------|
| 进程 CPU 准确性 | {{AC3_1_STATUS}} | {{AC3_1_RESULT}} |
| 线程级别分析 | {{AC3_2_STATUS}} | {{AC3_2_RESULT}} |
| CPU 亲和性 | {{AC3_3_STATUS}} | {{AC3_3_RESULT}} |
| Top N 进程 | {{AC3_4_STATUS}} | {{AC3_4_RESULT}} |

**结论**: {{AC3_CONCLUSION}}

### AC 4: 性能与资源占用

| 验收项 | 目标 | 实际 | 状态 |
|--------|------|------|------|
| 工具 CPU 占用 | < 2% | {{AC4_CPU}}% | {{AC4_CPU_STATUS}} |
| 内存占用 | < 100MB | {{AC4_MEMORY}}MB | {{AC4_MEMORY_STATUS}} |
| 磁盘写入 | < 10MB/h | {{AC4_DISK}}MB/h | {{AC4_DISK_STATUS}} |

**结论**: {{AC4_CONCLUSION}}

### AC 5: 命令行输出格式

| 验收项 | 状态 | 测试结果 |
|--------|------|---------|
| JSON 格式 | {{AC5_1_STATUS}} | {{AC5_1_RESULT}} |
| YAML 格式 | {{AC5_2_STATUS}} | {{AC5_2_RESULT}} |
| 表格格式 | {{AC5_3_STATUS}} | {{AC5_3_RESULT}} |
| 格式一致性 | {{AC5_4_STATUS}} | {{AC5_4_RESULT}} |

**结论**: {{AC5_CONCLUSION}}

### AC 6: 历史数据查询

| 验收项 | 状态 | 测试结果 |
|--------|------|---------|
| 时间范围查询 | {{AC6_1_STATUS}} | {{AC6_1_RESULT}} |
| 查询性能 | {{AC6_2_STATUS}} | {{AC6_2_RESULT}} |
| 聚合查询 | {{AC6_3_STATUS}} | {{AC6_3_RESULT}} |
| 分组查询 | {{AC6_4_STATUS}} | {{AC6_4_RESULT}} |

**结论**: {{AC6_CONCLUSION}}

---

## 4. 性能测试结果

### 4.1 采集性能

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 采集速度 | > 100 次/秒 | {{COLLECTION_SPEED}} 次/秒 | {{COLLECTION_SPEED_STATUS}} |
| 单次采集耗时 | < 10ms | {{COLLECTION_TIME}}ms | {{COLLECTION_TIME_STATUS}} |
| 内存占用 | < 100MB | {{COLLECTION_MEMORY}}MB | {{COLLECTION_MEMORY_STATUS}} |

### 4.2 检测性能

| 指标 | 数据规模 | 目标 | 实际 | 状态 |
|------|---------|------|------|------|
| 静态阈值检测 | 100k 点 | < 5秒 | {{STATIC_DETECT_TIME}}秒 | {{STATIC_DETECT_STATUS}} |
| 动态基线检测 | 100k 点 | < 5秒 | {{DYNAMIC_DETECT_TIME}}秒 | {{DYNAMIC_DETECT_STATUS}} |
| 基线计算 | 7 天数据 | < 10秒 | {{BASELINE_CALC_TIME}}秒 | {{BASELINE_CALC_STATUS}} |

### 4.3 资源占用

| 资源 | 场景 | 目标 | 实际 | 状态 |
|------|------|------|------|------|
| CPU | 守护进程 | < 2% | {{DAEMON_CPU}}% | {{DAEMON_CPU_STATUS}} |
| 内存 | 守护进程 | < 100MB | {{DAEMON_MEMORY}}MB | {{DAEMON_MEMORY_STATUS}} |
| 磁盘 I/O | 数据持久化 | < 10MB/h | {{DISK_IO}}MB/h | {{DISK_IO_STATUS}} |

### 4.4 压力测试

| 测试场景 | 数据量 | 结果 | 状态 |
|---------|--------|------|------|
| 高频采集 | 10ms 间隔，60秒 | {{HIGH_FREQ_RESULT}} | {{HIGH_FREQ_STATUS}} |
| 大数据集检测 | 1M 数据点 | {{LARGE_DATASET_RESULT}} | {{LARGE_DATASET_STATUS}} |
| 长时间运行 | 24小时 | {{LONG_RUN_RESULT}} | {{LONG_RUN_STATUS}} |

---

## 5. 缺陷分析

### 5.1 缺陷统计

| 严重程度 | 数量 | 百分比 |
|---------|------|--------|
| Critical | {{CRITICAL_COUNT}} | {{CRITICAL_PERCENT}}% |
| High | {{HIGH_COUNT}} | {{HIGH_PERCENT}}% |
| Medium | {{MEDIUM_COUNT}} | {{MEDIUM_PERCENT}}% |
| Low | {{LOW_COUNT}} | {{LOW_PERCENT}}% |
| **总计** | {{TOTAL_DEFECTS}} | 100% |

### 5.2 缺陷分布

{{DEFECT_DISTRIBUTION_CHART}}

### 5.3 Top 缺陷列表

| ID | 严重程度 | 模块 | 描述 | 状态 |
|----|---------|------|------|------|
| {{DEFECT_1_ID}} | {{DEFECT_1_SEVERITY}} | {{DEFECT_1_MODULE}} | {{DEFECT_1_DESC}} | {{DEFECT_1_STATUS}} |
| {{DEFECT_2_ID}} | {{DEFECT_2_SEVERITY}} | {{DEFECT_2_MODULE}} | {{DEFECT_2_DESC}} | {{DEFECT_2_STATUS}} |
| {{DEFECT_3_ID}} | {{DEFECT_3_SEVERITY}} | {{DEFECT_3_MODULE}} | {{DEFECT_3_DESC}} | {{DEFECT_3_STATUS}} |

### 5.4 缺陷趋势

{{DEFECT_TREND_CHART}}

---

## 6. 失败用例分析

### 6.1 失败用例列表

| 用例编号 | 用例名称 | 失败原因 | 错误日志链接 |
|---------|---------|---------|-------------|
| {{FAILED_1_ID}} | {{FAILED_1_NAME}} | {{FAILED_1_REASON}} | {{FAILED_1_LOG}} |
| {{FAILED_2_ID}} | {{FAILED_2_NAME}} | {{FAILED_2_REASON}} | {{FAILED_2_LOG}} |

### 6.2 失败原因分类

| 原因分类 | 数量 | 占比 |
|---------|------|------|
| 功能缺陷 | {{DEFECT_FAILURES}} | {{DEFECT_FAILURES_PERCENT}}% |
| 环境问题 | {{ENV_FAILURES}} | {{ENV_FAILURES_PERCENT}}% |
| 测试数据问题 | {{DATA_FAILURES}} | {{DATA_FAILURES_PERCENT}}% |
| 其他 | {{OTHER_FAILURES}} | {{OTHER_FAILURES_PERCENT}}% |

---

## 7. 测试环境信息

### 7.1 硬件环境
- **CPU**: {{CPU_INFO}}
- **内存**: {{MEMORY_INFO}}
- **磁盘**: {{DISK_INFO}}

### 7.2 软件环境
- **操作系统**: {{OS_INFO}}
- **Python 版本**: {{PYTHON_VERSION}}
- **依赖库版本**:
  ```
  {{DEPENDENCY_VERSIONS}}
  ```

### 7.3 测试工具版本
- **pytest**: {{PYTEST_VERSION}}
- **pytest-cov**: {{PYCOV_VERSION}}
- **pytest-benchmark**: {{PYBENCHMARK_VERSION}}

---

## 8. 风险与建议

### 8.1 测试风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| {{RISK_1}} | {{RISK_1_IMPACT}} | {{RISK_1_MITIGATION}} |
| {{RISK_2}} | {{RISK_2_IMPACT}} | {{RISK_2_MITIGATION}} |

### 8.2 改进建议

1. {{SUGGESTION_1}}
2. {{SUGGESTION_2}}
3. {{SUGGESTION_3}}

---

## 9. 结论与建议

### 9.1 总体评估

{{OVERALL_ASSESSMENT}}

### 9.2 发布建议

基于测试结果，发布建议为:

- [ ] **通过** - 可以发布
- [ ] **有条件通过** - 修复关键缺陷后可以发布
- [ ] **不通过** - 需要重大修改

**理由**: {{RELEASE_RATIONALE}}

### 9.3 后续工作

- [ ] {{NEXT_TASK_1}}
- [ ] {{NEXT_TASK_2}}
- [ ] {{NEXT_TASK_3}}

---

## 附录

### A. 测试报告文件
- HTML 测试报告: {{HTML_REPORT_LINK}}
- 覆盖率报告: {{COVERAGE_REPORT_LINK}}
- 性能测试报告: {{PERFORMANCE_REPORT_LINK}}

### B. 相关文档
- 测试计划: {{TEST_PLAN_LINK}}
- 验收测试用例: {{ACCEPTANCE_TEST_LINK}}
- 功能规格: {{FEATURE_SPEC_LINK}}

### C. 变更记录

| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|---------|--------|
| v1.0 | {{REPORT_DATE}} | 初始版本 | aiops-cli-tester |

---

**报告生成时间**: {{GENERATION_TIME}}
**报告生成人**: aiops-cli-tester
