# 规划与推理：Agent如何分解复杂任务

> **本系列简介**：这是一套系统性的AI Agent技术教程，覆盖从基础概念到生产级应用的完整知识体系。本文是系列的第8篇。

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



> 本文是《AI Agent系列教程》的第8篇，将深入探讨Agent的规划与推理能力，这是让Agent能够处理复杂多步骤任务的核心技术。

## 上一篇回顾

在之前的文章中，我们学习了：
- 第1篇：Agent的基本概念
- 第2篇：ReAct、ReWOO等架构模式
- 第3篇：工具调用机制
- 第4篇：Workflow架构
- 第5篇：Skills系统
- 第6篇：MCP协议
- 第7篇：记忆系统

这些组件让Agent具备了"感知"、"行动"和"记忆"能力。但要处理复杂任务，Agent还需要**规划和推理能力**——能够将大目标分解为小步骤，并根据执行结果动态调整策略。

## 引言：为什么需要规划能力？

让我们从一个场景开始：

**用户任务**："帮我规划一次从北京到上海的旅行"

**没有规划能力的Agent**：
- 可能会立即搜索机票
- 或者立即搜索酒店
- 但缺乏整体思考，步骤混乱，可能遗漏重要事项

**有规划能力的Agent**：
```
思考分解：
1. 明确需求：出行时间、预算、偏好
2. 交通方案：对比飞机、高铁、自驾
3. 住宿安排：选择位置和价格合适的酒店
4. 行程规划：景点、美食、时间安排
5. 预算计算：各项费用汇总
6. 方案推荐：提供多个可选方案
```

这就是**规划（Planning）**与**推理（Reasoning）**的力量。

## 一、规划与推理的基本概念

### 1.1 什么是规划？

**规划**是指在给定初始状态和目标状态的情况下，找到一系列行动步骤，将初始状态转换为目标状态的过程。

**核心要素**：
- **初始状态**：当前情况
- **目标状态**：期望达成的结果
- **行动空间**：可执行的操作集合
- **约束条件**：时间、成本、资源等限制

### 1.2 什么是推理？

**推理**是从已知信息出发，通过逻辑推导得出新结论的过程。

**在Agent中的推理类型**：
1. **演绎推理**：从一般规则推导具体结论
2. **归纳推理**：从具体案例总结一般规律
3. **溯因推理**：从观察结果推断可能原因
4. **类比推理**：通过相似性进行推理

### 1.3 规划与推理的关系

```
┌─────────────────────────────────────┐
│         用户复杂任务                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         推理阶段                      │
│   - 理解任务意图                      │
│   - 分析任务结构                      │
│   - 识别关键约束                      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         规划阶段                      │
│   - 分解任务为子任务                  │
│   - 确定执行顺序                      │
│   - 分配资源                          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         执行阶段                      │
│   - 按计划执行                        │
│   - 监控进度                          │
│   - 处理异常                          │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         调整阶段                      │
│   - 评估结果                          │
│   - 必要时重新规划                    │
│   - 学习经验                          │
└─────────────────────────────────────┘
```

## 二、任务分解策略

### 2.1 层次化任务分解

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    parent_id: Optional[str] = None
    dependencies: List[str] = None
    subtasks: List['Task'] = None
    result: Optional[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.subtasks is None:
            self.subtasks = []
        if self.metadata is None:
            self.metadata = {}

class HierarchicalPlanner:
    """层次化任务规划器"""

    def __init__(self, llm_model="gpt-4"):
        self.model = llm_model
        self.tasks = {}  # id -> Task
        self.task_counter = 0

    def decompose_task(self, goal: str, max_depth: int = 3) -> Task:
        """分解任务"""
        root_task = Task(
            id=self._generate_id(),
            description=goal
        )
        self.tasks[root_task.id] = root_task

        # 递归分解
        self._decompose_recursive(root_task, max_depth)

        return root_task

    def _decompose_recursive(self, task: Task, remaining_depth: int):
        """递归分解任务"""
        if remaining_depth <= 0:
            return

        # 使用LLM生成子任务
        subtask_descriptions = self._generate_subtasks(
            task.description,
            remaining_depth
        )

        # 创建子任务
        for desc in subtask_descriptions:
            subtask = Task(
                id=self._generate_id(),
                description=desc,
                parent_id=task.id
            )
            self.tasks[subtask.id] = subtask
            task.subtasks.append(subtask)

            # 递归分解
            self._decompose_recursive(subtask, remaining_depth - 1)

    def _generate_subtasks(self, task_description: str, depth: int) -> List[str]:
        """生成子任务"""
        prompt = f"""
        将以下任务分解为3-5个子任务：

        任务：{task_description}
        当前深度：{depth}

        要求：
        1. 子任务应该具体可执行
        2. 子任务之间逻辑清晰
        3. 每行一个子任务
        4. 不要编号，直接描述
        """

        import openai
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        content = response.choices[0].message.content.strip()
        subtasks = [line.strip() for line in content.split('\n') if line.strip()]

        return subtasks[:5]  # 限制子任务数量

    def _generate_id(self) -> str:
        """生成任务ID"""
        self.task_counter += 1
        return f"task_{self.task_counter}"

    def get_execution_plan(self, root_task_id: str) -> List[Task]:
        """获取执行计划（拓扑排序）"""
        plan = []
        visited = set()

        def dfs(task_id):
            if task_id in visited:
                return
            visited.add(task_id)

            task = self.tasks[task_id]

            # 先处理依赖
            for dep_id in task.dependencies:
                dfs(dep_id)

            # 再处理子任务
            for subtask in task.subtasks:
                dfs(subtask.id)

            # 添加到计划
            plan.append(task)

        dfs(root_task_id)
        return plan

    def visualize_task_tree(self, root_task_id: str):
        """可视化任务树"""
        def print_tree(task, indent=0):
            prefix = "  " * indent + ("├─ " if indent > 0 else "")
            status_icon = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.BLOCKED: "🚫"
            }
            print(f"{prefix}{status_icon[task.status]} {task.description}")

            for subtask in task.subtasks:
                print_tree(subtask, indent + 1)

        root_task = self.tasks[root_task_id]
        print_tree(root_task)

# 使用示例
planner = HierarchicalPlanner()

# 分解复杂任务
root_task = planner.decompose_task(
    "构建一个企业级AI助手系统",
    max_depth=3
)

# 可视化任务树
print("任务分解树：")
planner.visualize_task_tree(root_task.id)

# 获取执行计划
print("\n执行计划：")
plan = planner.get_execution_plan(root_task.id)
for i, task in enumerate(plan, 1):
    print(f"{i}. {task.description}")
```

### 2.2 依赖感知规划

```python
class DependencyAwarePlanner(HierarchicalPlanner):
    """依赖感知的规划器"""

    def add_dependency(self, task_id: str, depends_on: str):
        """添加任务依赖"""
        if task_id in self.tasks and depends_on in self.tasks:
            self.tasks[task_id].dependencies.append(depends_on)

    def detect_cycles(self) -> List[str]:
        """检测循环依赖"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {task_id: WHITE for task_id in self.tasks}
        cycles = []

        def dfs(task_id, path):
            color[task_id] = GRAY
            path.append(task_id)

            task = self.tasks[task_id]

            for dep_id in task.dependencies:
                if color[dep_id] == GRAY:
                    # 发现环
                    cycle_start = path.index(dep_id)
                    cycle = path[cycle_start:]
                    cycles.append(" -> ".join(cycle))
                elif color[dep_id] == WHITE:
                    dfs(dep_id, path)

            color[task_id] = BLACK
            path.pop()

        for task_id in self.tasks:
            if color[task_id] == WHITE:
                dfs(task_id, [])

        return cycles

    def find_executable_tasks(self) -> List[Task]:
        """找到可以立即执行的任务"""
        executable = []

        for task_id, task in self.tasks.items():
            if task.status != TaskStatus.PENDING:
                continue

            # 检查所有依赖是否完成
            dependencies_met = all(
                self.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )

            # 检查父任务是否在进行中
            if task.parent_id:
                parent = self.tasks[task.parent_id]
                if parent.status != TaskStatus.IN_PROGRESS:
                    continue

            if dependencies_met:
                executable.append(task)

        return executable

    def update_task_status(self, task_id: str, new_status: TaskStatus):
        """更新任务状态"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            old_status = task.status
            task.status = new_status

            # 级联更新
            if new_status == TaskStatus.IN_PROGRESS:
                # 父任务也标记为进行中
                if task.parent_id:
                    self.update_task_status(
                        task.parent_id,
                        TaskStatus.IN_PROGRESS
                    )

            elif new_status == TaskStatus.COMPLETED:
                # 检查父任务的所有子任务是否都完成
                if task.parent_id:
                    parent = self.tasks[task.parent_id]
                    all_completed = all(
                        st.status == TaskStatus.COMPLETED
                        for st in parent.subtasks
                    )
                    if all_completed:
                        self.update_task_status(
                            task.parent_id,
                            TaskStatus.COMPLETED
                        )

            elif new_status == TaskStatus.FAILED:
                # 子任务失败，父任务也失败
                if task.parent_id:
                    self.update_task_status(
                        task.parent_id,
                        TaskStatus.FAILED
                    )
```

### 2.3 动态重规划

```python
class DynamicPlanner(DependencyAwarePlanner):
    """动态规划器：能够根据执行情况调整计划"""

    def __init__(self, llm_model="gpt-4"):
        super().__init__(llm_model)
        self.execution_history = []

    def execute_with_monitoring(self, root_task_id: str):
        """执行计划并监控，必要时重规划"""
        max_iterations = 100

        for iteration in range(max_iterations):
            # 1. 找到可执行的任务
            executable_tasks = self.find_executable_tasks()

            if not executable_tasks:
                # 没有可执行任务，检查是否完成
                root_task = self.tasks[root_task_id]
                if root_task.status == TaskStatus.COMPLETED:
                    print("✅ 所有任务完成！")
                    return True
                else:
                    print("⚠️ 没有可执行任务，但根任务未完成")
                    return False

            # 2. 执行任务
            for task in executable_tasks[:3]:  # 并行执行3个
                self._execute_task(task)

            # 3. 检查是否需要重规划
            if self._should_replan():
                print("🔄 检测到异常，重新规划...")
                self._replan(root_task_id)

            # 4. 可视化进度
            self.visualize_task_tree(root_task_id)
            print("\n")

        return False

    def _execute_task(self, task: Task):
        """执行单个任务"""
        print(f"执行任务：{task.description}")
        task.status = TaskStatus.IN_PROGRESS

        # 模拟执行
        try:
            # 这里应该调用实际的执行逻辑
            # 或者使用Agent执行
            result = f"完成：{task.description}"

            task.result = result
            task.status = TaskStatus.COMPLETED

            # 记录历史
            self.execution_history.append({
                "task_id": task.id,
                "description": task.description,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.result = str(e)

            self.execution_history.append({
                "task_id": task.id,
                "description": task.description,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    def _should_replan(self) -> bool:
        """判断是否需要重规划"""
        # 简单策略：如果失败率超过30%，重规划
        if not self.execution_history:
            return False

        recent = self.execution_history[-10:]
        failed_count = sum(1 for h in recent if h["status"] == "failed")

        return failed_count / len(recent) > 0.3

    def _replan(self, root_task_id: str):
        """重新规划"""
        # 分析失败原因
        failed_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.FAILED
        ]

        if not failed_tasks:
            return

        # 使用LLM分析并重新规划
        failure_context = "\n".join([
            f"- {task.description}: {task.result}"
            for task in failed_tasks
        ])

        replan_prompt = f"""
        以下任务执行失败，请分析原因并提出改进方案：

        失败任务：
        {failure_context}

        请提供：
        1. 失败原因分析
        2. 改进建议（重新分解任务或改变策略）
        """

        import openai
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": replan_prompt}],
            temperature=0.7
        )

        print("重规划建议：")
        print(response.choices[0].message.content)

        # 实际应用中应该根据建议调整计划
        # 这里简化处理：重置失败任务
        for task in failed_tasks:
            task.status = TaskStatus.PENDING
            task.result = None
```

## 三、思维链推理

### 3.1 思维链基础

```python
class ChainOfThought:
    """思维链推理"""

    def __init__(self, model="gpt-4"):
        self.model = model
        self.thoughts = []

    def reason(self, question: str) -> str:
        """使用思维链推理"""
        prompt = f"""
        问题：{question}

        让我们一步步思考，逐步分析问题。

        思考步骤：
        """

        import openai
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        reasoning = response.choices[0].message.content

        # 保存思维链
        self.thoughts.append({
            "question": question,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        })

        return reasoning

    def reason_with_validation(self, question: str) -> tuple[str, bool]:
        """带验证的思维链"""
        # 第一步：生成推理
        reasoning = self.reason(question)

        # 第二步：验证推理
        validation_prompt = f"""
        评估以下推理是否合理：

        问题：{question}

        推理过程：
        {reasoning}

        评估标准：
        1. 逻辑是否连贯
        2. 结论是否合理
        3. 是否有遗漏

        只回答"合理"或"不合理"。
        """

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": validation_prompt}],
            temperature=0
        )

        is_valid = "合理" in response.choices[0].message.content

        return reasoning, is_valid
```

### 3.2 自我一致性推理

```python
class SelfConsistencyReasoner(ChainOfThought):
    """自我一致性推理：生成多个思维链，选择最一致的答案"""

    def reason_with_consensus(self, question: str, n_samples: int = 5) -> str:
        """通过多个推理路径达成共识"""
        reasonings = []

        # 生成多个推理路径
        for i in range(n_samples):
            reasoning = self.reason(question)
            reasonings.append(reasoning)

        # 提取每个推理的结论
        conclusions = []
        for reasoning in reasonings:
            conclusion = self._extract_conclusion(reasoning)
            conclusions.append(conclusion)

        # 找到最一致的结论
        from collections import Counter
        consensus = Counter(conclusions).most_common(1)[0][0]

        # 生成最终解释
        final_prompt = f"""
        问题：{question}

        多个推理路径的结论：{', '.join(conclusions)}

        最一致的结论：{consensus}

        基于以上信息，给出最终答案和解释：
        """

        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0
        )

        return response.choices[0].message.content

    def _extract_conclusion(self, reasoning: str) -> str:
        """从推理中提取结论"""
        # 简化处理：取最后一句话
        sentences = reasoning.split('。')
        return sentences[-1].strip()
```

### 3.3 树状思维（Tree of Thoughts）

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ThoughtNode:
    content: str
    parent: Optional['ThoughtNode'] = None
    children: List['ThoughtNode'] = None
    score: float = 0.0
    visits: int = 0

    def __post_init__(self):
        if self.children is None:
            self.children = []

class TreeOfThoughts:
    """树状思维推理"""

    def __init__(self, model="gpt-4", max_depth: int = 3, branching_factor: int = 3):
        self.model = model
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.root = None

    def solve(self, problem: str) -> str:
        """使用树状思维解决问题"""
        # 1. 初始化根节点
        self.root = ThoughtNode(content=problem)

        # 2. 构建思维树
        self._build_tree(self.root, depth=0)

        # 3. 选择最佳路径
        best_path = self._select_best_path()

        return best_path

    def _build_tree(self, node: ThoughtNode, depth: int):
        """递归构建思维树"""
        if depth >= self.max_depth:
            return

        # 生成多个思考方向
        thoughts = self._generate_thoughts(node.content, depth)

        # 创建子节点
        for thought in thoughts:
            child = ThoughtNode(content=thought, parent=node)
            node.children.append(child)

            # 递归构建
            self._build_tree(child, depth + 1)

    def _generate_thoughts(self, current_state: str, depth: int) -> List[str]:
        """生成下一个思考步骤"""
        if depth == 0:
            prompt = f"""
            问题：{current_state}

            生成{self.branching_factor}个可能的解决思路。
            每行一个思路。
            """
        else:
            prompt = f"""
            当前思考：{current_state}

            基于{self.branching_factor}个可能的下一步思考或行动。
            每行一个思路。
            """

        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8  # 更高的温度以增加多样性
        )

        content = response.choices[0].message.content.strip()
        thoughts = [line.strip() for line in content.split('\n') if line.strip()]

        return thoughts[:self.branching_factor]

    def _select_best_path(self) -> str:
        """选择最佳路径（使用简单的启发式评估）"""
        # 评估所有叶子节点
        leaf_nodes = self._get_leaf_nodes(self.root)

        scored_paths = []
        for leaf in leaf_nodes:
            path = self._get_path(leaf)
            score = self._evaluate_path(path)
            scored_paths.append((path, score))

        # 返回得分最高的路径
        scored_paths.sort(key=lambda x: x[1], reverse=True)
        best_path = scored_paths[0][0]

        return " -> ".join(best_path)

    def _get_leaf_nodes(self, node: ThoughtNode) -> List[ThoughtNode]:
        """获取所有叶子节点"""
        if not node.children:
            return [node]

        leaves = []
        for child in node.children:
            leaves.extend(self._get_leaf_nodes(child))

        return leaves

    def _get_path(self, node: ThoughtNode) -> List[str]:
        """获取从根到节点的路径"""
        path = []
        current = node
        while current:
            path.insert(0, current.content)
            current = current.parent
        return path

    def _evaluate_path(self, path: List[str]) -> float:
        """评估路径的质量"""
        # 使用LLM评估
        evaluation_prompt = f"""
        评估以下解决路径的质量（0-1分）：

        问题：{self.root.content}

        解决路径：
        {' -> '.join(path)}

        评估标准：
        1. 逻辑连贯性
        2. 可行性
        3. 完整性

        只返回0-1之间的分数。
        """

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0
        )

        try:
            return float(response.choices[0].message.content.strip())
        except:
            return 0.5
```

## 四、ReAct推理循环

```python
class ReActPlanner:
    """结合推理和行动的规划器"""

    def __init__(self, model="gpt-4"):
        self.model = model
        self.tools = self._init_tools()

    def _init_tools(self):
        """初始化工具"""
        return {
            "search": lambda q: f"搜索结果：{q}",
            "calculate": lambda e: str(eval(e)),
            "database_query": lambda q: f"数据库查询结果：{q}"
        }

    def plan_and_act(self, goal: str, max_iterations: int = 10) -> str:
        """ReAct循环：规划 -> 行动 -> 观察 -> 重新规划"""
        context = [{
            "role": "system",
            "content": f"""你是一个智能规划助手。目标：{goal}

可用工具：
- search(query): 搜索信息
- calculate(expression): 数学计算
- database_query(query): 查询数据库

请按照以下格式回答：
Thought: [你的思考过程]
Action: [工具名称]
Action Input: [工具参数]

或者如果已有答案：
Thought: [你的思考过程]
Final Answer: [最终答案]
"""
        }]

        for iteration in range(max_iterations):
            # 调用LLM
            response = openai.chat.completions.create(
                model=self.model,
                messages=context,
                temperature=0
            )

            message = response.choices[0].message
            context.append(message)

            content = message.content

            # 检查是否是最终答案
            if "Final Answer:" in content:
                return content.split("Final Answer:")[1].strip()

            # 解析并执行行动
            if "Action:" in content:
                action, action_input = self._parse_action(content)

                if action in self.tools:
                    # 执行工具
                    result = self.tools[action](action_input)

                    # 添加观察
                    context.append({
                        "role": "user",
                        "content": f"Observation: {result}"
                    })

        return "未能在规定迭代次数内完成"

    def _parse_action(self, content: str) -> tuple[str, str]:
        """解析行动"""
        lines = content.split('\n')
        action = action_input = ""

        for line in lines:
            if line.startswith("Action:"):
                action = line.split("Action:")[1].strip()
            elif line.startswith("Action Input:"):
                action_input = line.split("Action Input:")[1].strip()

        return action, action_input
```

## 五、实战案例：智能旅行规划Agent

```python
class TravelPlanningAgent:
    """智能旅行规划Agent"""

    def __init__(self):
        self.planner = DynamicPlanner()
        self.react = ReActPlanner()
        self.model = "gpt-4"

    def plan_trip(self, user_request: str) -> str:
        """规划旅行"""
        # 第一步：理解需求
        requirements = self._understand_requirements(user_request)

        # 第二步：分解任务
        root_task = self.planner.decompose_task(
            f"规划{requirements['destination']}旅行",
            max_depth=3
        )

        # 第三步：执行计划
        print("📋 旅行规划任务分解：")
        self.planner.visualize_task_tree(root_task.id)

        # 第四步：使用ReAct收集信息
        info = self._gather_information(requirements)

        # 第五步：生成方案
        proposal = self._generate_proposal(requirements, info)

        return proposal

    def _understand_requirements(self, request: str) -> Dict:
        """理解用户需求"""
        prompt = f"""
        从以下请求中提取旅行需求：

        请求：{request}

        提取字段（JSON格式）：
        - destination: 目的地
        - duration: 天数
        - budget: 预算
        - dates: 出行日期
        - travelers: 人数
        - preferences: 偏好列表
        - constraints: 限制条件
        """

        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        import json
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return {
                "destination": "上海",
                "duration": 3,
                "budget": 5000,
                "dates": "2024-03-01至2024-03-03",
                "travelers": 2,
                "preferences": ["美食", "文化"],
                "constraints": []
            }

    def _gather_information(self, requirements: Dict) -> Dict:
        """收集旅行信息"""
        info = {}

        # 使用ReAct收集信息
        queries = [
            f"{requirements['destination']}旅游景点推荐",
            f"{requirements['destination']}酒店价格",
            f"{requirements['destination']}交通方式"
        ]

        for query in queries:
            result = self.react.plan_and_act(query, max_iterations=5)
            info[query] = result

        return info

    def _generate_proposal(self, requirements: Dict, info: Dict) -> str:
        """生成旅行方案"""
        proposal_prompt = f"""
        基于以下信息生成详细的旅行方案：

        需求：
        {json.dumps(requirements, ensure_ascii=False, indent=2)}

        收集的信息：
        {json.dumps(info, ensure_ascii=False, indent=2)}

        方案应包括：
        1. 行程概览
        2. 每日详细安排
        3. 交通方案
        4. 住宿推荐
        5. 预算明细
        6. 注意事项
        """

        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": proposal_prompt}],
            temperature=0.7
        )

        return response.choices[0].message.content

# 使用示例
agent = TravelPlanningAgent()

proposal = agent.plan_trip(
    "我想和女朋友一起去上海玩3天，预算5000元，"
    "3月初出发，我们喜欢美食和文化，住舒适一点的酒店"
)

print("\n📝 旅行方案：")
print(proposal)
```

## 六、总结

### 核心要点

1. **任务分解**：层次化分解复杂任务为可执行的子任务
2. **依赖管理**：识别任务间的依赖关系，优化执行顺序
3. **思维链**：显式的推理步骤，提升复杂任务表现
4. **动态调整**：根据执行情况重新规划
5. **多种推理方式**：ReAct、ToT、自我一致性等

### 最佳实践

- ✅ **分层规划**：先高层规划，再细化执行
- ✅ **显式推理**：记录思考过程，便于调试
- ✅ **动态调整**：不要固守初始计划
- ✅ **并行执行**：独立任务并行处理
- ✅ **验证结果**：检查每个步骤的正确性

### 常见陷阱

- ❌ **过度分解**：任务粒度过小，增加复杂度
- ❌ **忽视依赖**：导致任务执行失败
- ❌ **缺乏灵活性**：无法应对变化
- ❌ **推理循环**：思维链陷入死循环

---

## 推荐阅读

- [Tree of Thoughts: Deliberate Problem Solving with Large Language Models](https://arxiv.org/abs/2305.10601)
- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [Self-Consistency Improves Chain of Thought Reasoning](https://arxiv.org/abs/2203.11171)

## 关于本系列

这是《AI Agent系列教程》的第8篇，共14篇。

**上一篇回顾**：《记忆系统：让Agent拥有上下文感知能力》

**下一篇预告**：《多模态Agent：视觉、语音与文本的融合》

---

*如果这篇文章对你有帮助，欢迎点赞、收藏和分享！有任何问题欢迎在评论区讨论。*

---

**上一篇**：[记忆系统：让Agent拥有上下文感知能力](./article-06-memory-system.md)
**下一篇**：[多模态Agent：视觉、语音与文本的融合](./article-09-multimodal-agent.md)

---

**系列说明**：
- 本系列文章正在持续更新中，欢迎关注！
- 所有代码示例将在GitHub仓库开源：`ai-agent-tutorial-series`
- 有问题欢迎在评论区讨论，我会及时回复
