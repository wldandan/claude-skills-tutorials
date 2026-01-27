# 工具调用（Function Calling）：Agent的手和脚

> **本系列简介**：这是一套系统性的AI Agent技术教程，覆盖从基础概念到生产级应用的完整知识体系。本文是系列的第3篇。

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



> 本文是《AI Agent系列教程》的第3篇，将深入解析工具调用（Function Calling）的原理与实践，这是Agent与世界交互的核心机制。

## 上一篇回顾

在上一篇文章《Agent架构设计：ReAct、ReWOO与思维链》中，我们学习了Agent的架构模式。你可能注意到，无论是ReAct还是ReWOO，都依赖一个关键能力：**工具调用（Function Calling）**。

如果说LLM是Agent的"大脑"，那么工具调用就是Agent的"手和脚"，让它能够真正地与世界交互。

## 引言：为什么需要工具调用？

想象一下，即使是最聪明的大脑，如果被禁锢在一个没有输入输出的房间里，也无法发挥任何作用。同样，LLM再强大，如果只能输出文本，其应用场景也会受到极大限制。

**工具调用的出现，改变了这一切**：

- **LLM只能**：回答训练数据中的知识（2021年之前的）
- **LLM + 工具**：查询实时信息、执行代码、调用API、操作数据库

**一个典型的场景**：

```
用户：今天的天气怎么样？

没有工具调用：
LLM："我无法获取实时天气信息，因为我的训练数据截止到..."

有工具调用：
LLM：调用weather_api工具 → 获取实时天气 → "今天北京晴天，温度20°C"
```

## 一、工具调用的本质

### 1.1 什么是工具调用？

**工具调用（Function Calling）**是指LLM能够根据任务需求，自主选择并执行预定义的函数（工具），然后将结果融入后续推理的过程。

**关键特点**：
1. **自主性**：LLM自己决定何时调用哪个工具
2. **结构化**：工具调用遵循严格的输入输出格式
3. **可组合**：多个工具可以串联或并联使用
4. **可扩展**：可以轻松添加新的工具

### 1.2 工具调用的工作流程

```
┌─────────────┐
│  User Query │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│         LLM Reasoning           │
│  (分析需求，决定是否需要工具)      │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│    Function Selection           │
│  (选择合适的工具及参数)            │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│      Tool Execution             │
│   (执行函数，获取结果)             │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│    Result Integration           │
│  (将结果反馈给LLM继续处理)        │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────┐
│  Final Answer│
└─────────────┘
```

### 1.3 主流模型的工具调用支持

| 模型 | 工具调用API | 特点 |
|------|------------|------|
| **OpenAI (GPT-4/3.5)** | Function Calling | 最早推出，生态成熟 |
| **Anthropic (Claude)** | Tool Use | 支持多模态工具调用 |
| **Google (Gemini)** | Function Calling | 原生支持代码执行 |
| **开源模型 (Llama, Mistral)** | 各自实现 | 需要自己训练或使用微调 |

## 二、OpenAI Function Calling详解

### 2.1 基础用法

```python
import openai
import json

# 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：北京、上海"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# 模拟工具实现
def get_weather(city, unit="celsius"):
    """实际应用中这里会调用真实的天气API"""
    weather_data = {
        "北京": {"temp": 20, "condition": "晴天"},
        "上海": {"temp": 25, "condition": "多云"},
        "深圳": {"temp": 30, "condition": "阴天"}
    }
    data = weather_data.get(city, {"temp": 15, "condition": "未知"})
    return json.dumps({
        "city": city,
        "temperature": data["temp"],
        "unit": unit,
        "condition": data["condition"]
    })

# 主函数
def run_agent(user_message):
    # 调用LLM
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}],
        tools=tools,
        tool_choice="auto"  # 让模型自动决定是否调用工具
    )

    message = response.choices[0].message

    # 检查是否需要调用工具
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        # 执行工具
        if function_name == "get_weather":
            result = get_weather(**function_args)

            # 将结果反馈给LLM
            second_response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": user_message},
                    message,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    }
                ]
            )
            return second_response.choices[0].message.content

    return message.content

# 使用示例
result = run_agent("今天北京的天气怎么样？")
print(result)
# 输出：今天北京晴天，温度20°C，适合外出活动。
```

### 2.2 多工具调用

```python
class MultiToolAgent:
    def __init__(self):
        self.tools = self._init_tools()
        self.model = "gpt-4"

    def _init_tools(self):
        """初始化所有工具"""
        return {
            "get_weather": {
                "func": self._get_weather,
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "获取天气信息",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string"},
                                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                            },
                            "required": ["city"]
                        }
                    }
                }
            },
            "calculate": {
                "func": self._calculate,
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "calculate",
                        "description": "执行数学计算",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "expression": {"type": "string", "description": "数学表达式"}
                            },
                            "required": ["expression"]
                        }
                    }
                }
            },
            "search": {
                "func": self._search,
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "search",
                        "description": "搜索互联网信息",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"}
                            },
                            "required": ["query"]
                        }
                    }
                }
            }
        }

    def _get_weather(self, city, unit="celsius"):
        # 实际应用中调用真实API
        return json.dumps({"city": city, "temp": 20, "condition": "晴天"})

    def _calculate(self, expression):
        try:
            result = eval(expression)
            return json.dumps({"expression": expression, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _search(self, query):
        # 实际应用中调用搜索API
        return json.dumps({"query": query, "results": f"关于{query}的搜索结果..."})

    def run(self, user_message, max_iterations=5):
        """运行Agent"""
        messages = [{"role": "user", "content": user_message}]

        for iteration in range(max_iterations):
            # 调用LLM
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[tool["schema"] for tool in self.tools.values()],
                tool_choice="auto"
            )

            message = response.choices[0].message
            messages.append(message)

            # 如果没有工具调用，返回最终答案
            if not message.tool_calls:
                return message.content

            # 执行所有工具调用
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                if function_name in self.tools:
                    # 执行工具
                    result = self.tools[function_name]["func"](**function_args)

                    # 添加工具结果到消息列表
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

        return "达到最大迭代次数"

# 使用示例
agent = MultiToolAgent()
result = agent.run("北京今天天气如何？如果温度超过25度，帮我计算25的平方")
print(result)
# 输出：北京今天晴天，温度20°C，未超过25度，因此无需计算。
```

### 2.3 并行工具调用

```python
def parallel_tool_calls():
    """演示并行工具调用"""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_stock_price",
                "description": "获取股票价格",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"}
                    },
                    "required": ["symbol"]
                }
            }
        }
    ]

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": "查询AAPL、GOOGL、MSFT这三只股票的当前价格"
        }],
        tools=tools
    )

    message = response.choices[0].message

    # GPT-4会同时调用3次get_stock_price
    if message.tool_calls:
        print(f"并行调用次数: {len(message.tool_calls)}")
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            print(f"  - 查询 {args['symbol']}")
```

## 三、Anthropic Claude Tool Use

### 3.1 Claude的Tool Use特点

Claude的工具调用与OpenAI类似，但有几个关键差异：

1. **多模态支持**：Claude可以基于图像内容调用工具
2. **更强的推理**：Claude通常能更好地理解何时使用工具
3. **不同的API格式**

### 3.2 Claude工具调用示例

```python
import anthropic

client = anthropic.Anthropic()

def run_claude_agent(user_message):
    """Claude工具调用示例"""
    tools = [
        {
            "name": "get_weather",
            "description": "获取天气信息",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                },
                "required": ["city"]
            }
        }
    ]

    def get_weather(city):
        return f"{city}今天晴天，20°C"

    # 调用Claude
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=tools,
        messages=[{"role": "user", "content": user_message}]
    )

    # 处理工具使用
    if response.stop_reason == "tool_use":
        # 提取工具调用
        tool_use = next(block for block in response.content if block.type == "tool_use")

        # 执行工具
        result = get_weather(**tool_use.input)

        # 继续对话
        final_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": user_message},
                response,
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": result
                        }
                    ]
                }
            ]
        )

        return final_response.content[0].text

    return response.content[0].text

# 使用
result = run_claude_agent("上海今天天气怎么样？")
print(result)
```

## 四、工具设计的最佳实践

### 4.1 工具定义的原则

#### 原则1：单一职责

```python
# ❌ 不好：一个工具做太多事情
def handle_all_requests(request_type, params):
    if request_type == "weather":
        return get_weather(params)
    elif request_type == "search":
        return search(params)
    # ...

# ✅ 好：每个工具只做一件事
def get_weather(city):
    """获取天气"""
    pass

def search(query):
    """搜索信息"""
    pass
```

#### 原则2：清晰的描述

```python
# ❌ 不好：描述模糊
tools = [{
    "name": "process",
    "description": "处理数据",
    "parameters": {
        "type": "object",
        "properties": {
            "data": {"type": "string"}
        }
    }
}]

# ✅ 好：描述具体
tools = [{
    "name": "analyze_sentiment",
    "description": "分析文本的情感倾向，返回正面、负面或中性以及置信度",
    "parameters": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "需要分析的文本内容，长度限制在1000字以内"
            }
        },
        "required": ["text"]
    }
}]
```

#### 原则3：合理的参数设计

```python
# ❌ 不好：参数过于复杂
{
    "name": "complex_tool",
    "parameters": {
        "type": "object",
        "properties": {
            "option1": {"type": "string"},
            "option2": {"type": "string"},
            # ... 20多个参数
        }
    }
}

# ✅ 好：使用嵌套对象或简化参数
{
    "name": "search_database",
    "description": "搜索数据库",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "自然语言查询，例如：查找所有价格大于100的产品"
            },
            "filters": {
                "type": "object",
                "description": "高级过滤条件（可选）",
                "properties": {
                    "category": {"type": "string"},
                    "price_range": {
                        "type": "object",
                        "properties": {
                            "min": {"type": "number"},
                            "max": {"type": "number"}
                        }
                    }
                }
            }
        },
        "required": ["query"]
    }
}
```

### 4.2 工具实现的要点

#### 要点1：错误处理

```python
def robust_tool(param):
    """健壮的工具实现"""
    try:
        # 参数验证
        if not param or not isinstance(param, str):
            return json.dumps({
                "error": "invalid_parameter",
                "message": "参数必须是非空字符串"
            })

        # 执行逻辑
        result = do_something(param)

        # 返回结构化结果
        return json.dumps({
            "success": True,
            "data": result
        })

    except ValidationError as e:
        return json.dumps({
            "error": "validation_failed",
            "message": str(e)
        })
    except Exception as e:
        return json.dumps({
            "error": "internal_error",
            "message": "服务暂时不可用，请稍后重试"
        })
```

#### 要点2：超时控制

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError

def timeout_tool(func, timeout_seconds=10):
    """为工具添加超时控制"""
    def wrapper(*args, **kwargs):
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout_seconds)
            except TimeoutError:
                return json.dumps({
                    "error": "timeout",
                    "message": f"工具执行超过{timeout_seconds}秒"
                })
    return wrapper

@timeout_tool
def slow_operation(data):
    # 可能很慢的操作
    pass
```

#### 要点3：结果格式化

```python
def format_result(tool_name, data, error=None):
    """统一的结果格式"""
    if error:
        return {
            "tool": tool_name,
            "status": "error",
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "tool": tool_name,
            "status": "success",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

# 使用
def good_tool(query):
    try:
        results = search_api(query)
        return format_result("good_tool", results)
    except Exception as e:
        return format_result("good_tool", error=str(e))
```

### 4.3 工具组合模式

#### 模式1：顺序调用

```python
class SequentialAgent:
    """工具按顺序执行"""
    def run(self, user_query):
        # 步骤1：搜索
        search_result = self.tools["search"](query=user_query)

        # 步骤2：分析搜索结果
        analysis = self.tools["analyze"](data=search_result)

        # 步骤3：生成报告
        report = self.tools["generate_report"](analysis=analysis)

        return report
```

#### 模式2：并行调用

```python
import asyncio

class ParallelAgent:
    """工具并行执行"""
    async def run(self, user_query):
        # 同时执行多个独立工具
        tasks = [
            self.tools["search"](query=user_query),
            self.tools["get_weather"](city="北京"),
            self.tools["get_time"]()
        ]

        results = await asyncio.gather(*tasks)
        return self._merge_results(results)
```

#### 模式3：条件调用

```python
class ConditionalAgent:
    """根据条件选择工具"""
    def run(self, user_query):
        # 先判断意图
        intent = self.tools["classify_intent"](query=user_query)

        # 根据意图选择工具
        if intent == "weather":
            return self.tools["get_weather"](extract_city(user_query))
        elif intent == "calculation":
            return self.tools["calculate"](extract_expression(user_query))
        else:
            return self.tools["general_chat"](query=user_query)
```

## 五、常见工具类型实现

### 5.1 数据库查询工具

```python
import sqlite3
from typing import List, Dict

class DatabaseTool:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def query(self, sql: str) -> Dict:
        """执行SQL查询"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(sql)
            rows = cursor.fetchall()

            results = [dict(row) for row in rows]

            return {
                "success": True,
                "data": results,
                "row_count": len(results)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            conn.close()

    def natural_language_query(self, question: str) -> str:
        """自然语言查询（使用LLM生成SQL）"""
        # 第一步：生成SQL
        sql_prompt = f"""
        根据以下问题生成SQL查询：

        数据库schema：
        - users(id, name, email, created_at)
        - orders(id, user_id, amount, created_at)
        - products(id, name, price)

        问题：{question}

        只返回SQL语句，不要其他内容。
        """

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": sql_prompt}]
        )

        sql = response.choices[0].message.content.strip()

        # 第二步：执行SQL
        result = self.query(sql)

        return json.dumps(result, ensure_ascii=False)

# 使用
db_tool = DatabaseTool("company.db")
result = db_tool.natural_language_query("找出消费金额最高的前10个用户")
```

### 5.2 文件操作工具

```python
import os
import chardet
from pathlib import Path

class FileTool:
    """文件操作工具集"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def read_file(self, filepath: str) -> str:
        """安全地读取文件"""
        full_path = self._safe_path(filepath)

        if not full_path.exists():
            return json.dumps({"error": "文件不存在"})

        try:
            # 检测编码
            with open(full_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']

            # 读取内容
            content = raw_data.decode(encoding)

            return json.dumps({
                "success": True,
                "content": content,
                "size": len(content),
                "encoding": encoding
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    def write_file(self, filepath: str, content: str) -> str:
        """安全地写入文件"""
        full_path = self._safe_path(filepath)

        try:
            # 创建目录
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return json.dumps({
                "success": True,
                "path": str(full_path)
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    def list_files(self, directory: str, pattern: str = "*") -> str:
        """列出目录文件"""
        full_path = self._safe_path(directory)

        if not full_path.is_dir():
            return json.dumps({"error": "不是有效的目录"})

        try:
            files = [
                {
                    "name": f.name,
                    "path": str(f.relative_to(self.base_path)),
                    "size": f.stat().st_size,
                    "is_file": f.is_file()
                }
                for f in full_path.glob(pattern)
            ]

            return json.dumps({
                "success": True,
                "files": files,
                "count": len(files)
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _safe_path(self, filepath: str) -> Path:
        """防止路径遍历攻击"""
        full_path = (self.base_path / filepath).resolve()
        if not str(full_path).startswith(str(self.base_path)):
            raise ValueError("非法路径访问")
        return full_path

# 工具定义
file_tool_schema = {
    "name": "file_operations",
    "description": "文件操作工具",
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["read", "write", "list"],
                "description": "操作类型"
            },
            "path": {
                "type": "string",
                "description": "文件路径"
            },
            "content": {
                "type": "string",
                "description": "文件内容（write操作需要）"
            }
        },
        "required": ["operation", "path"]
    }
}
```

### 5.3 API调用工具

```python
import requests
from typing import Dict, Any

class APIConnector:
    """通用API调用工具"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AI-Agent/1.0"
        })

    def call_api(
        self,
        url: str,
        method: str = "GET",
        headers: Dict = None,
        params: Dict = None,
        data: Dict = None,
        timeout: int = 10
    ) -> Dict:
        """调用外部API"""
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=timeout
            )

            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }

        except requests.Timeout:
            return {"success": False, "error": "请求超时"}
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"未知错误: {str(e)}"}

    def get(self, url: str, params: Dict = None) -> str:
        """GET请求"""
        result = self.call_api(url, method="GET", params=params)
        return json.dumps(result, ensure_ascii=False)

    def post(self, url: str, data: Dict) -> str:
        """POST请求"""
        result = self.call_api(url, method="POST", data=data)
        return json.dumps(result, ensure_ascii=False)

# 工具定义
api_tool_schema = {
    "name": "http_request",
    "description": "发送HTTP请求",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "请求URL"
            },
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE"],
                "description": "HTTP方法"
            },
            "data": {
                "type": "object",
                "description": "请求体数据（POST/PUT）"
            }
        },
        "required": ["url", "method"]
    }
}
```

### 5.4 代码执行工具

```python
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import traceback

class CodeExecutor:
    """安全的代码执行工具"""

    def execute_python(self, code: str, timeout: int = 5) -> str:
        """执行Python代码"""
        # 捕获输出
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        try:
            # 重定向输出
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # 限制执行环境
                safe_globals = {
                    "__builtins__": {
                        "print": print,
                        "range": range,
                        "len": len,
                        "str": str,
                        "int": int,
                        "float": float,
                        "list": list,
                        "dict": dict,
                        "set": set,
                        "sum": sum,
                        "max": max,
                        "min": min,
                        "abs": abs,
                        "round": round,
                    },
                    "math": __import__("math"),
                }

                # 执行代码
                exec(code, safe_globals)

            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()

            return json.dumps({
                "success": True,
                "output": stdout_output,
                "error": stderr_output
            })

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": "".join(traceback.format_exception(type(e), e, e.__traceback__))
            })

# 工具定义
code_tool_schema = {
    "name": "execute_code",
    "description": "执行Python代码并返回结果",
    "parameters": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "要执行的Python代码"
            }
        },
        "required": ["code"]
    }
}
```

## 六、工具调用的优化策略

### 6.1 减少Token消耗

```python
class OptimizedAgent:
    """优化Token使用的Agent"""

    def __init__(self):
        self.tool_cache = {}  # 工具结果缓存
        self.conversation_summary = ""  # 对话摘要

    def run_with_caching(self, user_message):
        """使用缓存减少重复调用"""
        # 检查缓存
        cache_key = self._get_cache_key(user_message)
        if cache_key in self.tool_cache:
            return self.tool_cache[cache_key]

        # 执行工具调用
        result = self._execute_with_tools(user_message)

        # 缓存结果
        self.tool_cache[cache_key] = result

        return result

    def compress_history(self, messages):
        """压缩历史消息"""
        if len(messages) > 10:
            # 使用LLM生成摘要
            summary_prompt = f"""
            总结以下对话的要点：
            {messages[:-5]}
            """
            summary = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": summary_prompt}]
            )

            # 只保留最近5条消息 + 摘要
            return [
                {"role": "system", "content": f"对话摘要：{summary}"}
            ] + messages[-5:]

        return messages
```

### 6.2 提升响应速度

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncAgent:
    """异步Agent，提升并发性能"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def run_parallel_tools(self, tool_calls):
        """并行执行多个工具"""
        tasks = []
        for tool_call in tool_calls:
            task = asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._execute_tool,
                tool_call
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

    def _execute_tool(self, tool_call):
        """执行单个工具"""
        # 实际的工具执行逻辑
        pass
```

### 6.3 提高工具调用准确率

```python
class SmartAgent:
    """智能Agent，提高工具选择准确率"""

    def run_with_verification(self, user_message):
        """验证工具调用的正确性"""
        # 第一步：让LLM选择工具
        tool_choice = self._select_tool(user_message)

        # 第二步：验证工具选择
        verification = self._verify_tool_choice(
            user_message,
            tool_choice
        )

        if not verification["is_appropriate"]:
            # 工具选择不合适，使用默认策略
            return self._default_response(user_message)

        # 第三步：执行工具
        return self._execute_tool(tool_choice)

    def _select_tool(self, message):
        """选择工具"""
        pass

    def _verify_tool_choice(self, message, tool_choice):
        """验证工具选择是否合适"""
        verification_prompt = f"""
        用户问题：{message}
        选择工具：{tool_choice['name']}
        工具参数：{tool_choice['args']}

        这个工具选择是否合适？只回答"是"或"否"。
        """

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": verification_prompt}],
            temperature=0
        )

        is_appropriate = "是" in response.choices[0].message.content

        return {"is_appropriate": is_appropriate}
```

## 七、实战案例：构建全能助手

```python
class UniversalAssistant:
    """集成了多种工具的通用助手"""

    def __init__(self):
        self.tools = {
            "search": SearchTool(),
            "calculator": CalculatorTool(),
            "weather": WeatherTool(),
            "database": DatabaseTool("data.db"),
            "file_ops": FileTool("./workspace"),
            "api_client": APIConnector(),
            "code_executor": CodeExecutor()
        }

        self.model = "gpt-4"

    def get_tool_schemas(self):
        """获取所有工具的schema"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "搜索互联网信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "执行数学计算",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string"}
                        },
                        "required": ["expression"]
                    }
                }
            },
            # ... 其他工具定义
        ]

    def run(self, user_message, max_iterations=10):
        """运行助手"""
        messages = [{"role": "user", "content": user_message}]

        for iteration in range(max_iterations):
            # 调用LLM
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.get_tool_schemas(),
                tool_choice="auto"
            )

            message = response.choices[0].message
            messages.append(message)

            # 检查是否需要调用工具
            if not message.tool_calls:
                return message.content

            # 执行所有工具调用
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                if function_name in self.tools:
                    # 执行工具
                    tool_instance = self.tools[function_name]
                    result = getattr(tool_instance, 'run', tool_instance)(**function_args)

                    # 添加结果
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

        return "任务执行超时或失败"

# 使用示例
assistant = UniversalAssistant()

# 案例1：查询天气
result1 = assistant.run("今天北京和上海的天气怎么样？")
print(result1)

# 案例2：数据分析
result2 = assistant.run("""
从数据库中查询销售数据，计算每个产品的销售额，
然后找出销售额最高的5个产品
""")
print(result2)

# 案例3：文件处理
result3 = assistant.run("""
读取data.csv文件，计算每行的平均值，
然后将结果保存到output.txt
""")
print(result3)
```

## 八、总结

### 核心要点

1. **工具调用是Agent的能力延伸**：让LLM突破文本限制，与真实世界交互
2. **OpenAI vs Claude**：两者API类似，但Claude支持多模态工具调用
3. **工具设计原则**：单一职责、清晰描述、合理参数
4. **实现要点**：错误处理、超时控制、结果格式化
5. **优化策略**：缓存、异步执行、智能验证

### 最佳实践

- ✅ **从简单工具开始**：先实现基础功能，再逐步优化
- ✅ **做好错误处理**：工具调用可能失败，要优雅降级
- ✅ **记录工具使用日志**：便于调试和优化
- ✅ **设置合理的超时**：避免工具调用卡住整个流程
- ✅ **使用缓存**：减少重复调用，降低成本

### 常见陷阱

- ❌ **过度依赖工具**：不是所有问题都需要工具调用
- ❌ **工具定义不清晰**：导致LLM选择错误的工具
- ❌ **忽略安全性**：文件操作、代码执行等需要严格限制
- ❌ **没有错误处理**：工具调用失败会导致整个Agent崩溃

---

## 推荐阅读

- [OpenAI Function Calling Documentation](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic Tool Use Documentation](https://docs.anthropic.com/claude/docs/tool-use)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)

## 关于本系列

这是《AI Agent系列教程》的第3篇，共12篇。

**上一篇回顾**：《Agent架构设计：ReAct、ReWOO与思维链》

**下一篇预告**：《MCP协议深度解析：连接AI与数据源的标准化桥梁》

---

*如果这篇文章对你有帮助，欢迎点赞、收藏和分享！有任何问题欢迎在评论区讨论。*

---

**上一篇**：[Agent架构设计：ReAct、ReWOO与思维链](./article-02-agent-architecture.md)
**下一篇**：[MCP协议深度解析：连接AI与数据源的标准化桥梁](./article-04-mcp-protocol.md)

---

**系列说明**：
- 本系列文章正在持续更新中，欢迎关注！
- 所有代码示例将在GitHub仓库开源：`ai-agent-tutorial-series`
- 有问题欢迎在评论区讨论，我会及时回复
