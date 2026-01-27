# Agent架构设计：ReAct、ReWOO与思维链

> **本系列简介**：这是一套系统性的AI Agent技术教程，覆盖从基础概念到生产级应用的完整知识体系。本文是系列的第2篇。

**系列目录**：
1. [AI Agent的本质：从自动化到自主智能](./article-01-agent-essence.md)
2. [Agent架构设计：ReAct、ReWOO与思维链](./article-02-agent-architecture.md)
3. [工具调用（Function Calling）：Agent的手和脚](./article-03-function-calling.md)
4. [MCP协议深度解析：连接AI与数据源的标准化桥梁](./article-04-mcp-protocol.md)
5. [Workflow架构：可视化Agent编排平台](./article-05-workflow.md)
6. [Skills系统：Claude Code的模块化能力封装](./article-06-skills-system.md)
7. [记忆系统：让Agent拥有上下文感知能力](./article-07-memory-system.md)
8. [规划与推理：Agent如何分解复杂任务](./article-08-planning-reasoning.md)
9. [多模态Agent：视觉、语音与文本的融合](./article-09-multimodal-agent.md)
10. [Agent评估与优化：如何衡量Agent性能](./article-10-agent-evaluation.md)
11. [Multi-Agent系统：协作、竞争与涌现](./article-11-multi-agent-systems.md)
12. [生产级Agent架构：可靠性、安全性与可观测性](./article-12-production-agent.md)
13. [实战案例：构建企业级AI助手（完整项目）](./article-13-enterprise-ai-assistant.md)
14. [AI Agent的未来：AGI之路上的关键一步](./article-14-future-of-agents.md)


---



> 本文是《AI Agent系列教程》的第2篇，将带你深入理解AI Agent的核心架构模式，掌握ReAct、ReWOO、CoT等主流设计思想。

## 引言：为什么需要专门的Agent架构？

在上一篇文章中，我们了解了AI Agent的基本概念和最小可行实现。但在实际生产环境中，简单的"推理-行动"循环远远不够。一个生产级的Agent需要解决：

- **如何分解复杂任务？**
- **如何平衡推理成本与效果？**
- **如何处理工具调用的依赖关系？**
- **如何避免无限循环？**

这些问题都指向一个核心话题：**Agent架构设计**。

## 一、Agent架构的核心要素

### 1.1 什么是Agent架构？

**Agent架构**是指Agent系统内部各组件的组织方式、交互流程和控制策略。它决定了Agent如何：

1. **理解任务**：将用户输入转化为可执行的计划
2. **分解问题**：将复杂任务拆解为子任务
3. **选择工具**：决定何时调用哪个工具
4. **处理结果**：将工具输出融入后续推理
5. **终止判断**：知道何时完成目标

### 1.2 架构设计的关键维度

| 维度 | 说明 | 典型选择 |
|------|------|----------|
| **推理模式** | LLM如何思考和规划 | ReAct、CoT、ReWOO |
| **执行策略** | 工具调用的时机和方式 | 单次调用、迭代调用、并行调用 |
| **记忆机制** | 如何存储和检索上下文 | 短期记忆、长期记忆、向量检索 |
| **控制流程** | 如何管理执行分支 | 顺序、并行、条件分支 |
| **错误处理** | 如何应对失败 | 重试、回退、人工介入 |

## 二、ReAct架构：推理与行动的协同

### 2.1 ReAct的核心思想

**ReAct**（**Re**asoning + **Act**ing）是2022年普林斯顿大学提出的架构模式，其核心思想是：

> **让LLM在执行行动的同时，生成推理轨迹（Reasoning Traces）**

这种方式让Agent能够：
- **解释自己的决策**：为什么选择这个工具？
- **纠正错误**：根据工具结果调整策略
- **保持上下文**：推理轨迹成为记忆的一部分

### 2.2 ReAct工作流程

```
User: "帮我查一下今天的天气，如果是晴天就推荐户外活动"

Thought 1: 用户需要查询天气信息
Action 1: search(query="今天北京天气")
Observation 1: 今天北京晴，温度15-25°C

Thought 2: 天气是晴天，用户希望推荐户外活动
Action 2: search(query="适合晴天的户外活动")
Observation 2: 徒步、骑行、野餐、摄影等

Thought 3: 结合温度和季节，给出具体建议
Final Answer: 今天北京晴天，温度15-25°C，非常适合户外活动。推荐：...
```

**关键特征**：
- **Thought**：显式的推理步骤
- **Action**：具体的工具调用
- **Observation**：工具返回的结果
- **迭代循环**：直到生成Final Answer

### 2.3 ReAct代码实现

```python
import openai
import json

class ReActAgent:
    def __init__(self, model="gpt-4"):
        self.model = model
        self.tools = self._init_tools()
        self.history = []

    def _init_tools(self):
        return {
            "search": {
                "func": self._search,
                "description": "搜索互联网信息",
                "params": {"query": {"type": "string", "description": "搜索关键词"}}
            },
            "calculate": {
                "func": self._calculate,
                "description": "执行数学计算",
                "params": {"expression": {"type": "string", "description": "数学表达式"}}
            }
        }

    def _search(self, query):
        # 模拟搜索
        return f"搜索结果：关于'{query}'的信息..."

    def _calculate(self, expression):
        try:
            return str(eval(expression))
        except:
            return "计算错误"

    def _build_prompt(self, user_input):
        """构建ReAct格式的提示词"""
        tool_desc = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])

        return f"""你是一个智能助手，可以使用以下工具：

{tool_desc}

请按照以下格式回答：

Thought: 你的思考过程
Action: 工具名称
Action Input: 工具参数（JSON格式）

或者如果已经有答案：

Thought: 你的思考过程
Final Answer: 最终答案

用户问题：{user_input}

Thought:"""

    def _parse_response(self, response):
        """解析LLM响应"""
        lines = response.strip().split('\n')
        thought = action = action_input = final_answer = None

        for line in lines:
            if line.startswith("Thought:"):
                thought = line[8:].strip()
            elif line.startswith("Action:"):
                action = line[7:].strip()
            elif line.startswith("Action Input:"):
                action_input = line[13:].strip()
            elif line.startswith("Final Answer:"):
                final_answer = line[13:].strip()

        return {
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "final_answer": final_answer
        }

    def run(self, user_input, max_iterations=10):
        """ReAct主循环"""
        prompt = self._build_prompt(user_input)
        full_response = ""

        for i in range(max_iterations):
            # 调用LLM
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            llm_output = response.choices[0].message.content

            # 解析响应
            parsed = self._parse_response(llm_output)

            # 记录推理轨迹
            full_response += f"\n{llm_output}"
            prompt += f"\n{llm_output}\n"

            # 判断是否终止
            if parsed["final_answer"]:
                return {
                    "answer": parsed["final_answer"],
                    "trace": full_response
                }

            # 执行工具调用
            if parsed["action"] and parsed["action"] in self.tools:
                tool = self.tools[parsed["action"]]
                try:
                    args = json.loads(parsed["action_input"])
                    result = tool["func"](**args)
                    observation = f"Observation: {result}"
                    prompt += f"\n{observation}\nThought:"
                except Exception as e:
                    prompt += f"\nError: {str(e)}\nThought:"

        return {"error": "达到最大迭代次数", "trace": full_response}

# 使用示例
agent = ReActAgent()
result = agent.run("计算25乘以36，然后搜索这个数字相关的历史事件")
print(result["answer"])
print("\n推理轨迹：")
print(result["trace"])
```

### 2.4 ReAct的优势与局限

**优势**：
- ✅ **透明性高**：每个决策都有推理说明
- ✅ **可调试**：可以追踪完整的思考路径
- ✅ **自适应**：根据工具结果动态调整策略

**局限**：
- ❌ **成本较高**：每次迭代都需要调用LLM
- ❌ **可能陷入循环**：没有明确的终止保证
- ❌ **推理冗余**：Thought可能包含重复信息

## 三、ReWOO架构：解耦推理与执行

### 3.1 ReWOO的核心思想

**ReWOO**（**Re**asoning **W**ith**O**ut **O**bservation）是2023年提出的架构，旨在解决ReAct的效率问题：

> **将推理过程分为两个阶段：规划阶段和执行阶段**

**核心创新**：
- **规划阶段**：一次性生成完整的执行计划
- **执行阶段**：按计划调用工具，不再调用LLM
- **汇总阶段**：将所有结果汇总，生成最终答案

### 3.2 ReWOO vs ReAct

| 维度 | ReAct | ReWOO |
|------|-------|-------|
| **LLM调用次数** | N次（N=工具调用次数） | 2次（规划+汇总） |
| **推理方式** | 迭代式 | 一次性规划 |
| **适应性** | 高（可动态调整） | 中（依赖初始规划） |
| **成本** | 高 | 低 |
| **适用场景** | 未知任务、探索性任务 | 结构化任务、可预测任务 |

### 3.3 ReWOO代码实现

```python
import openai
import json
import re

class ReWOOAgent:
    def __init__(self, model="gpt-4"):
        self.model = model
        self.tools = self._init_tools()

    def _init_tools(self):
        return {
            "search": lambda q: f"搜索结果：{q}",
            "calculate": lambda e: str(eval(e)),
            "get_weather": lambda c: f"{c}今天晴天，20°C"
        }

    def _extract_plan(self, response):
        """提取执行计划"""
        # 响应格式：
        # Plan: E1 = search(...)
        #       E2 = calculate(...)
        #       E3 = search(...)
        plan = []
        lines = response.split('\n')
        for line in lines:
            match = re.search(r'E(\d+)\s*=\s*(\w+)\(([^)]*)\)', line)
            if match:
                plan.append({
                    "step": match.group(1),
                    "tool": match.group(2),
                    "args": match.group(3)
                })
        return plan

    def _generate_plan(self, user_input):
        """阶段1：生成执行计划"""
        plan_prompt = f"""你是一个任务规划专家。对于用户的问题，生成一个执行计划。

可用工具：
- search(query): 搜索信息
- calculate(expression): 数学计算
- get_weather(city): 查询天气

规划格式示例：
Plan: E1 = search("AI Agent最新进展")
      E2 = calculate("100 * 1.5")
      E3 = get_weather("北京")

用户问题：{user_input}

Plan:"""

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": plan_prompt}],
            temperature=0
        )

        plan_text = response.choices[0].message.content
        return self._extract_plan(plan_text), plan_text

    def _execute_plan(self, plan):
        """阶段2：执行计划（不调用LLM）"""
        results = {}
        for step in plan:
            tool_name = step["tool"]
            args = step["args"]

            if tool_name in self.tools:
                # 解析参数
                if tool_name == "search":
                    result = self.tools["search"](args.strip('"'))
                elif tool_name == "calculate":
                    result = self.tools["calculate"](args)
                elif tool_name == "get_weather":
                    result = self.tools["get_weather"](args.strip('"'))

                results[f"E{step['step']}"] = result

        return results

    def _generate_final_answer(self, user_input, plan_text, results):
        """阶段3：生成最终答案"""
        # 构建结果摘要
        results_summary = "\n".join([
            f"{k} = {v}" for k, v in results.items()
        ])

        answer_prompt = f"""根据以下执行计划和结果，回答用户问题。

用户问题：{user_input}

执行计划：
{plan_text}

执行结果：
{results_summary}

请基于以上信息给出最终答案："""

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": answer_prompt}],
            temperature=0
        )

        return response.choices[0].message.content

    def run(self, user_input):
        """ReWOO主流程"""
        # 阶段1：规划
        plan, plan_text = self._generate_plan(user_input)
        print(f"执行计划：\n{plan_text}\n")

        # 阶段2：执行
        results = self._execute_plan(plan)
        print(f"执行结果：\n{json.dumps(results, ensure_ascii=False, indent=2)}\n")

        # 阶段3：汇总
        final_answer = self._generate_final_answer(user_input, plan_text, results)
        return final_answer

# 使用示例
agent = ReWOOAgent()
result = agent.run("计算20乘以35，然后查询北京的天气，最后基于这两个信息给我建议")
print(f"\n最终答案：\n{result}")
```

**输出示例**：
```
执行计划：
Plan: E1 = calculate("20 * 35")
      E2 = get_weather("北京")
      E3 = search("适合晴天20度的活动")

执行结果：
{
  "E1": "700",
  "E2": "北京今天晴天，20°C",
  "E3": "搜索结果：适合晴天20度的活动"
}

最终答案：
根据计算结果，20 × 35 = 700。北京今天天气晴朗，温度20°C，非常适合户外活动。推荐您可以考虑：...
```

### 3.4 ReWOO的优势与局限

**优势**：
- ✅ **成本更低**：只需2次LLM调用
- ✅ **执行更快**：工具调用可并行化
- ✅ **结构清晰**：计划、执行、结果分离

**局限**：
- ❌ **适应性弱**：无法根据中间结果调整
- ❌ **错误传播**：规划错误影响后续执行
- ❌ **复杂度限制**：难以处理高度动态的任务

## 四、思维链（Chain of Thought）

### 4.1 什么是思维链？

**思维链（CoT）**是一种提示技术，通过引导LLM生成中间推理步骤来提升复杂问题的解决能力。

**核心思想**：
> 让模型"慢下来"，逐步思考而非直接给出答案

### 4.2 CoT的三种实现方式

#### 方式1：零样本CoT（Zero-shot CoT）

```python
def zero_shot_cot(model, question):
    prompt = f"""{question}

让我们一步步思考。"""

    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

#### 方式2：少样本CoT（Few-shot CoT）

```python
def few_shot_cot(model, question):
    prompt = f"""Q: 罗杰有5个网球，他又买了2罐网球，每罐3个。现在他有多少个网球？
A: 罗杰开始有5个网球。2罐网球，每罐3个，就是2×3=6个。5+6=11。答案是11。

Q: 餐厅有23个苹果，如果他们用20个做午餐，买了6个，现在有多少个？
A: 餐厅开始有23个苹果。用了20个，剩下23-20=3个。买了6个，所以3+6=9。答案是9。

Q: {question}
A:"""

    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

#### 方式3：自动CoT（Auto-CoT）

```python
def auto_cot(model, question):
    # 阶段1：生成推理链
    generate_prompt = f"""Q: {question}
A:"""

    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": generate_prompt + " 让我们一步步思考。"}]
    )

    reasoning = response.choices[0].message.content

    # 阶段2：提取答案
    answer_prompt = f"""基于以下推理，给出最终答案。

推理过程：
{reasoning}

最终答案："""

    final_response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": answer_prompt}]
    )

    return final_response.choices[0].message.content
```

### 4.3 CoT在Agent中的应用

```python
class COTAgent:
    def __init__(self, model="gpt-4"):
        self.model = model
        self.tools = self._init_tools()

    def _init_tools(self):
        return {
            "search": lambda q: f"搜索结果：{q}",
            "calculate": lambda e: str(eval(e))
        }

    def think(self, question):
        """生成思维链"""
        cot_prompt = f"""问题：{question}

请按以下格式思考：

思考步骤1：[分析问题]
思考步骤2：[确定需要的工具]
思考步骤3：[规划执行顺序]
思考步骤4：[预测结果]

执行计划："""

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": cot_prompt}],
            temperature=0
        )

        reasoning = response.choices[0].message.content
        return reasoning

    def execute(self, reasoning):
        """基于思维链执行"""
        # 提取工具调用指令
        # ... (解析逻辑)

        # 执行工具
        results = {}
        # ... (执行逻辑)

        return results

    def synthesize(self, question, reasoning, results):
        """综合推理和结果生成答案"""
        synthesis_prompt = f"""问题：{question}

思考过程：
{reasoning}

执行结果：
{json.dumps(results, ensure_ascii=False, indent=2)}

基于以上思考和结果，给出最终答案："""

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0
        )

        return response.choices[0].message.content

    def run(self, question):
        """完整的CoT Agent流程"""
        # 1. 生成思维链
        reasoning = self.think(question)
        print(f"思维链：\n{reasoning}\n")

        # 2. 执行
        results = self.execute(reasoning)
        print(f"执行结果：\n{results}\n")

        # 3. 综合
        answer = self.synthesize(question, reasoning, results)
        return answer
```

## 六、架构选择指南

### 6.1 决策树

```
开始
  |
  ├─ 需要重用已有能力模块？
  |   ├─ 是 → Skills（模块化复用）
  |   └─ 否 → 继续判断
  |
  ├─ 任务是否高度不确定？
  |   ├─ 是 → ReAct（需要动态调整）
  |   └─ 否 → 继续判断
  |
  ├─ 工具调用是否可预先规划？
  |   ├─ 是 → ReWOO（降低成本）
  |   └─ 否 → 继续判断
  |
  ├─ 是否需要透明推理过程？
  |   ├─ 是 → ReAct + CoT
  |   └─ 否 → 继续判断
  |
  └─ 成本是否为主要约束？
      ├─ 是 → ReWOO
      └─ 否 → ReAct
```

### 6.2 架构对比总结

| 场景 | 推荐架构 | 理由 |
|------|----------|------|
| **可重用能力库** | 组件库 | 模块化、团队协作 |
| **探索性任务** | ReAct | 需要根据中间结果动态调整策略 |
| **结构化任务** | ReWOO | 可预先规划，降低成本 |
| **多步推理** | ReAct + CoT | 需要显式的推理链 |
| **简单查询** | 直接Function Calling | 无需复杂架构 |
| **成本敏感** | ReWOO | 最小化LLM调用次数 |
| **透明性要求高** | ReAct | 完整的推理轨迹 |

### 6.3 混合架构

实际应用中，可以结合多种架构：

```python
class HybridAgent:
    def __init__(self):
        self.react_agent = ReActAgent()
        self.rewoo_agent = ReWOOAgent()

    def run(self, user_input):
        # 先判断任务类型
        task_type = self._classify_task(user_input)

        if task_type == "structured":
            # 结构化任务用ReWOO
            return self.rewoo_agent.run(user_input)
        elif task_type == "exploratory":
            # 探索性任务用ReAct
            return self.react_agent.run(user_input)
        else:
            # 未知任务，先用ReAct尝试
            return self.react_agent.run(user_input)

    def _classify_task(self, user_input):
        """简单的任务分类"""
        # 可以用小模型快速分类
        # 或者基于规则判断
        pass
```

## 七、实战案例

### 案例：多架构混合Agent

```python
# article-02-hybrid-agent.py
class HybridArchitectureAgent:
    """混合架构Agent"""

    def __init__(self):
        self.react_agent = ReActAgent()
        self.rewoo_agent = ReWOOAgent()

    def route(self, user_input: str):
        """智能路由到合适的架构"""

        # 判断任务类型
        task_type = self._classify_task(user_input)

        if task_type == "exploratory":
            # 探索性任务用ReAct
            return self.react_agent.run(user_input)
        elif task_type == "structured":
            # 结构化任务用ReWOO
            return self.rewoo_agent.run(user_input)
        else:
            # 默认使用ReAct
            return self.react_agent.run(user_input)

    def _classify_task(self, user_input: str) -> str:
        """任务分类"""
        # 简化的分类逻辑
        if "如何" in user_input or "为什么" in user_input:
            return "exploratory"
        elif "计算" in user_input or "查询" in user_input:
            return "structured"
        else:
            return "unknown"
```

## 八、总结

### 8.1 关键要点

本文深入探讨了三大核心Agent架构模式：

1. **ReAct**：推理-行动迭代，适合动态、不确定的任务
2. **ReWOO**：规划-执行分离，适合结构化、成本敏感的场景
3. **CoT（思维链）**：显式推理链，提升复杂任务的表现

### 8.2 最佳实践

- ✅ **从简单开始**：先用ReAct，再考虑优化
- ✅ **记录推理轨迹**：便于调试和优化
- ✅ **设置合理的终止条件**：避免无限循环
- ✅ **监控成本**：跟踪LLM调用次数和Token消耗
- ✅ **A/B测试**：对比不同架构的效果
- ✅ **构建组件库**：将常用能力封装为可复用组件
- ✅ **混合架构**：根据任务特性灵活选择

### 8.3 未来趋势

1. **自适应架构**：根据任务自动选择最优架构
2. **模块化生态系统**：繁荣的组件市场和社区
3. **多模态融合**：视觉、语音与文本的统一架构
4. **分布式Agent**：跨多个模型和服务的协作架构
5. **可观测性增强**：更完善的监控和调试工具

### 8.4 架构选择速查表

| 你的需求 | 推荐架构 |
|---------|---------|
| 处理未知、复杂任务 | ReAct |
| 降低LLM调用成本 | ReWOO |
| 需要透明推理 | ReAct + CoT |
| 简单工具调用 | Function Calling |
| 混合多种场景 | Hybrid Agent |

---

## 推荐阅读

**学术论文**：
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [ReWOO: Decoupling Reasoning and Observing for Efficient Language Model Agents](https://arxiv.org/abs/2305.18323)
- [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903)

**官方文档**：
- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic Tool Use Documentation](https://docs.anthropic.com/claude/docs/tool-use)
- [Claude Code Documentation](https://code.claude.com/docs/en/intro)

## 关于本系列

这是《AI Agent系列教程》的第2篇，共12篇。关注我，不错过后续精彩内容！

**上一篇回顾**：《AI Agent的本质：从自动化到自主智能》

**下一篇预告**：《工具调用（Function Calling）：Agent的手和脚》

---

*如果这篇文章对你有帮助，欢迎点赞、收藏和分享！有任何问题欢迎在评论区讨论。*

---

**上一篇**：[AI Agent的本质：从自动化到自主智能](./article-01-agent-essence.md)
**下一篇**：[工具调用（Function Calling）：Agent的手和脚](./article-03-function-calling.md)

---

**系列说明**：
- 本系列文章正在持续更新中，欢迎关注！
- 所有代码示例将在GitHub仓库开源：`ai-agent-tutorial-series`
- 有问题欢迎在评论区讨论，我会及时回复
