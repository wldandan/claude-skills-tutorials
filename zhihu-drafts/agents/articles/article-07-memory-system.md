# 记忆系统：让Agent拥有上下文感知能力

> **本系列简介**：这是一套系统性的AI Agent技术教程，覆盖从基础概念到生产级应用的完整知识体系。本文是系列的第7篇。

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



> 本文是《AI Agent系列教程》的第5篇，将深入解析Agent记忆系统的设计原理与实现方法，这是让Agent具备持续对话和长期学习能力的核心。

## 上一篇回顾

在上一篇文章《MCP协议深度解析：连接AI与数据源的标准化桥梁》中，我们学习了如何使用MCP协议标准化Agent与外部数据源的连接。有了MCP，Agent可以方便地访问各种工具和数据。

但如果你与Agent对话时间稍长，就会发现一个问题：

**Agent会"遗忘"之前的对话内容！**

这是因为LLM本身是无状态的，每次调用都是独立的。要实现真正的智能助手，我们需要构建**记忆系统**，让Agent能够：

- 记住对话历史
- 提取关键信息
- 跨会话保持一致性
- 从过去经验中学习

## 引言：为什么需要记忆系统？

想象这样一个场景：

```
第一轮对话：
用户：我的名字是张三
Agent：你好张三，很高兴认识你！

第二轮对话（5分钟后）：
用户：我叫什么名字？
Agent：抱歉，我不知道您的名字。
```

这就是没有记忆系统的Agent。而有了记忆系统：

```
第一轮对话：
用户：我的名字是张三
Agent：[记忆：用户姓名=张三]
     你好张三，很高兴认识你！

第二轮对话（5分钟后）：
Agent：[从记忆中检索：用户姓名=张三]
     你叫张三！我们之前聊过。
```

**记忆系统的价值**：
1. **上下文连贯性**：保持对话的连续性
2. **个性化服务**：记住用户偏好和历史
3. **学习与进化**：从经验中优化行为
4. **长期关系**：建立持久的用户-Agent关系

## 一、记忆系统的分类

### 1.1 记忆的三个层次

借鉴认知心理学，我们将Agent的记忆分为三类：

| 记忆类型 | 存储时长 | 容量 | 用途 | 类比 |
|---------|---------|------|------|------|
| **感官记忆** | 极短（秒级） | 极小 | 暂存输入信息 | 电脑的寄存器 |
| **短期记忆（工作记忆）** | 短（分钟-小时） | 有限（几KB-几十KB） | 当前对话上下文 | 电脑的RAM |
| **长期记忆** | 长（天-年） | 近似无限 | 知识、经验、用户信息 | 电脑的硬盘 |

### 1.2 记忆架构图

```
┌─────────────────────────────────────────┐
│         User Input                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Sensory Memory                      │
│   (暂存当前输入)                          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    Working Memory (短期记忆)              │
│   - 对话历史                              │
│   - 当前任务状态                          │
│   - 临时变量                              │
└──────┬──────────────────┬────────────────┘
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│ Attention   │    │  Encoding   │
│  (关注机制)  │    │  (编码存储)  │
└──────┬──────┘    └──────┬───────┘
       │                  │
       └────────┬─────────┘
                ▼
┌─────────────────────────────────────────┐
│     Long-term Memory (长期记忆)           │
│   - 语义记忆（知识）                       │
│   - 情景记忆（事件）                       │
│   - 程序记忆（技能）                       │
└─────────────────────────────────────────┘
```

## 二、短期记忆实现

### 2.1 基础对话历史管理

最简单的记忆系统就是保存对话历史：

```python
from typing import List, Dict
import json
from datetime import datetime

class ConversationMemory:
    """对话记忆管理"""

    def __init__(self, max_turns: int = 10):
        self.messages: List[Dict] = []
        self.max_turns = max_turns
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "message_count": 0
        }

    def add_message(self, role: str, content: str, **kwargs):
        """添加消息"""
        message = {
            "role": role,  # "user", "assistant", "system"
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.messages.append(message)
        self.metadata["message_count"] += 1

    def get_messages(self, last_n: int = None) -> List[Dict]:
        """获取最近的消息"""
        if last_n:
            return self.messages[-last_n:]
        return self.messages

    def get_context_window(self, max_tokens: int = 4000) -> List[Dict]:
        """获取适合上下文窗口的消息"""
        # 估算token数（简化版，实际需要更精确的tokenizer）
        total_tokens = 0
        context_messages = []

        for msg in reversed(self.messages):
            msg_tokens = len(msg["content"]) // 4  # 粗略估算
            if total_tokens + msg_tokens > max_tokens:
                break
            context_messages.insert(0, msg)
            total_tokens += msg_tokens

        return context_messages

    def summarize_old_messages(self):
        """压缩旧消息"""
        if len(self.messages) <= self.max_turns:
            return

        # 保留最近的消息
        recent_messages = self.messages[-self.max_turns:]

        # 总结旧消息
        old_messages = self.messages[:-self.max_turns]
        summary_prompt = f"""
        总结以下对话的要点：

        {json.dumps(old_messages, ensure_ascii=False, indent=2)}

        只保留关键信息，如用户偏好、重要事实、已完成任务等。
        """

        # 这里简化处理，实际应该调用LLM生成摘要
        summary = f"之前对话的摘要：包含{len(old_messages)}条消息"

        # 重建消息列表
        self.messages = [
            {
                "role": "system",
                "content": summary,
                "type": "summary"
            }
        ] + recent_messages

    def clear(self):
        """清空记忆"""
        self.messages = []
        self.metadata["message_count"] = 0

    def save(self, filepath: str):
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "messages": self.messages,
                "metadata": self.metadata
            }, f, ensure_ascii=False, indent=2)

    def load(self, filepath: str):
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.messages = data["messages"]
            self.metadata = data["metadata"]

# 使用示例
memory = ConversationMemory(max_turns=5)

memory.add_message("user", "你好，我叫张三")
memory.add_message("assistant", "你好张三，很高兴认识你！")
memory.add_message("user", "我喜欢吃苹果")
memory.add_message("assistant", "记住了，你喜欢苹果")

print("所有消息：")
for msg in memory.get_messages():
    print(f"{msg['role']}: {msg['content']}")

print("\n最近2条消息：")
for msg in memory.get_messages(last_n=2):
    print(f"{msg['role']}: {msg['content']}")
```

### 2.2 滑动窗口与摘要结合

```python
class SmartConversationMemory:
    """智能对话记忆：滑动窗口 + 摘要"""

    def __init__(self, max_recent_turns=5, max_total_tokens=8000):
        self.max_recent_turns = max_recent_turns
        self.max_total_tokens = max_total_tokens
        self.messages = []
        self.summaries = []  # 存储多个摘要

    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # 检查是否需要压缩
        if self._should_compress():
            self._compress()

    def _should_compress(self) -> bool:
        """判断是否需要压缩"""
        total_tokens = sum(len(msg["content"]) for msg in self.messages)
        return total_tokens > self.max_total_tokens

    def _compress(self):
        """压缩旧消息"""
        if len(self.messages) <= self.max_recent_turns:
            return

        # 分离旧消息和最近消息
        old_messages = self.messages[:-self.max_recent_turns]
        recent_messages = self.messages[-self.max_recent_turns:]

        # 生成摘要
        summary = self._generate_summary(old_messages)
        self.summaries.append(summary)

        # 只保留最近消息
        self.messages = recent_messages

    def _generate_summary(self, messages: List[Dict]) -> str:
        """生成摘要（调用LLM）"""
        summary_prompt = f"""
        总结以下对话，提取关键信息：

        {json.dumps(messages, ensure_ascii=False, indent=2)}

        请提取：
        1. 用户的基本信息（姓名、偏好等）
        2. 已讨论的主要话题
        3. 达成的重要结论
        4. 待完成的任务

        用简洁的语言总结。
        """

        # 实际应用中调用LLM
        # 这里简化处理
        return f"摘要：{len(messages)}条对话的总结"

    def get_full_context(self) -> List[Dict]:
        """获取完整上下文（摘要+最近消息）"""
        context = []

        # 添加所有摘要
        for summary in self.summaries:
            context.append({
                "role": "system",
                "content": summary,
                "type": "summary"
            })

        # 添加最近消息
        context.extend(self.messages)

        return context
```

### 2.3 Token计数优化

```python
import tiktoken

class TokenAwareMemory:
    """精确Token计数的记忆管理"""

    def __init__(self, model="gpt-4", max_tokens=8000):
        self.model = model
        self.max_tokens = max_tokens
        self.encoding = tiktoken.encoding_for_model(model)
        self.messages = []

    def count_tokens(self, messages: List[Dict]) -> int:
        """精确计算Token数"""
        num_tokens = 0
        for message in messages:
            # 每条消息的固定开销
            num_tokens += 4
            num_tokens += len(self.encoding.encode(message["content"]))
        num_tokens += 2  # 回复的固定开销
        return num_tokens

    def trim_to_fit(self, messages: List[Dict]) -> List[Dict]:
        """裁剪消息以适应Token限制"""
        if self.count_tokens(messages) <= self.max_tokens:
            return messages

        # 从最旧的消息开始删除
        trimmed = messages.copy()
        while self.count_tokens(trimmed) > self.max_tokens and len(trimmed) > 1:
            trimmed.pop(0)

        return trimmed

    def get_context(self) -> List[Dict]:
        """获取适合上下文的消息"""
        return self.trim_to_fit(self.messages)
```

## 三、长期记忆实现

### 3.1 向量存储与检索

长期记忆的核心是**向量数据库**，通过语义相似度检索相关信息：

```python
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import json
from datetime import datetime

class VectorMemory:
    """基于向量的长期记忆"""

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        # 加载嵌入模型
        self.encoder = SentenceTransformer(model_name)
        self.dimension = self.encoder.get_sentence_embedding_dimension()

        # FAISS索引（用于快速相似度搜索）
        self.index = faiss.IndexFlatL2(self.dimension)

        # 存储元数据
        self.memories = []  # List[Dict]
        self.id_map = {}    # id -> index

    def add_memory(
        self,
        content: str,
        memory_type: str = "general",
        metadata: Dict = None
    ) -> str:
        """添加记忆"""
        # 生成嵌入
        embedding = self.encoder.encode([content])[0]

        # 存储到FAISS
        memory_id = f"mem_{len(self.memories)}"
        self.index.add(np.array([embedding]))

        # 存储元数据
        memory_data = {
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.memories.append(memory_data)
        self.id_map[memory_id] = len(self.memories) - 1

        return memory_id

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str = None
    ) -> List[Dict]:
        """检索相关记忆"""
        # 生成查询嵌入
        query_embedding = self.encoder.encode([query])[0]

        # 搜索最相似的向量
        distances, indices = self.index.search(
            np.array([query_embedding]),
            top_k
        )

        # 返回结果
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.memories):
                memory = self.memories[idx].copy()

                # 添加相似度分数
                memory["similarity"] = 1 / (1 + dist)

                # 类型过滤
                if memory_type is None or memory["type"] == memory_type:
                    results.append(memory)

        return results

    def update_memory(self, memory_id: str, new_content: str):
        """更新记忆"""
        if memory_id not in self.id_map:
            raise ValueError(f"Memory {memory_id} not found")

        idx = self.id_map[memory_id]

        # 更新内容
        self.memories[idx]["content"] = new_content
        self.memories[idx]["updated_at"] = datetime.now().isoformat()

        # 重新生成嵌入
        new_embedding = self.encoder.encode([new_content])[0]
        self.index.remove_ids(np.array([idx]))
        self.index.add(np.array([new_embedding]))

    def delete_memory(self, memory_id: str):
        """删除记忆"""
        if memory_id not in self.id_map:
            return

        # 标记为删除（实际应用中需要重建索引）
        idx = self.id_map[memory_id]
        self.memories[idx]["deleted"] = True
        del self.id_map[memory_id]

    def search_by_metadata(
        self,
        key: str,
        value: any
    ) -> List[Dict]:
        """按元数据搜索"""
        results = []
        for memory in self.memories:
            if memory.get("deleted"):
                continue
            if memory.get("metadata", {}).get(key) == value:
                results.append(memory)
        return results

    def get_all_memories(self, memory_type: str = None) -> List[Dict]:
        """获取所有记忆"""
        memories = [
            m for m in self.memories
            if not m.get("deleted")
        ]

        if memory_type:
            memories = [m for m in memories if m["type"] == memory_type]

        return memories

    def save(self, filepath: str):
        """保存到文件"""
        data = {
            "memories": self.memories,
            "id_map": self.id_map
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, filepath: str):
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.memories = data["memories"]
            self.id_map = data["id_map"]

        # 重建FAISS索引
        embeddings = []
        for memory in self.memories:
            if not memory.get("deleted"):
                emb = self.encoder.encode([memory["content"]])[0]
                embeddings.append(emb)

        if embeddings:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(np.array(embeddings))

# 使用示例
memory = VectorMemory()

# 添加不同类型的记忆
memory.add_memory(
    "用户姓名是张三，喜欢苹果",
    memory_type="user_profile",
    metadata={"user_id": "123"}
)

memory.add_memory(
    "用户询问了如何学习Python，建议先学基础语法",
    memory_type="conversation",
    metadata={"topic": "programming"}
)

memory.add_memory(
    "用户完成了Python基础课程",
    memory_type="milestone",
    metadata={"topic": "programming", "level": "beginner"}
)

# 检索相关记忆
query = "用户对编程感兴趣吗？"
results = memory.retrieve(query, top_k=3)

print(f"查询：{query}\n")
for result in results:
    print(f"[{result['type']}] {result['content']}")
    print(f"  相似度：{result['similarity']:.3f}\n")
```

### 3.2 分层记忆系统

结合短期和长期记忆：

```python
class HierarchicalMemory:
    """分层记忆系统"""

    def __init__(self):
        # 短期记忆
        self.short_term = ConversationMemory(max_turns=10)

        # 长期记忆
        self.long_term = VectorMemory()

        # 重要信息缓存（快速访问）
        self.key_value_store = {}

    def add_message(self, role: str, content: str):
        """添加消息到短期记忆"""
        self.short_term.add_message(role, content)

        # 提取并保存重要信息到长期记忆
        if role == "user":
            self._extract_and_store(content)

    def _extract_and_store(self, content: str):
        """提取重要信息并存储"""
        # 使用LLM提取关键信息
        extraction_prompt = f"""
        从以下文本中提取关键信息，格式为JSON：

        文本：{content}

        提取字段：
        - user_name: 用户姓名
        - preferences: 用户偏好（列表）
        - important_facts: 重要事实（列表）

        如果某个字段没有信息，设为null。
        """

        # 实际应用中调用LLM
        # 这里简化处理
        extracted = {"user_name": None, "preferences": [], "important_facts": []}

        # 存储到长期记忆
        if extracted["user_name"]:
            memory_id = self.long_term.add_memory(
                f"用户姓名：{extracted['user_name']}",
                memory_type="user_profile"
            )
            # 同时存入KV缓存
            self.key_value_store["user_name"] = extracted["user_name"]

    def get_context(self, query: str = None) -> List[Dict]:
        """获取完整上下文"""
        context = []

        # 1. 从长期记忆检索相关信息
        if query:
            relevant_memories = self.long_term.retrieve(query, top_k=3)
            if relevant_memories:
                context.append({
                    "role": "system",
                    "content": f"相关记忆：\n" + "\n".join([
                        f"- {m['content']}" for m in relevant_memories
                    ])
                })

        # 2. 添加短期记忆（对话历史）
        context.extend(self.short_term.get_messages())

        return context

    def consolidate(self):
        """将短期记忆合并到长期记忆"""
        # 生成对话摘要
        messages = self.short_term.get_messages()
        summary = self._generate_conversation_summary(messages)

        # 存储到长期记忆
        self.long_term.add_memory(
            summary,
            memory_type="conversation_summary",
            metadata={"timestamp": datetime.now().isoformat()}
        )

        # 清空短期记忆
        self.short_term.clear()

    def _generate_conversation_summary(self, messages: List[Dict]) -> str:
        """生成对话摘要"""
        summary_prompt = f"""
        总结以下对话的要点：

        {json.dumps(messages, ensure_ascii=False, indent=2)}

        提取：
        1. 用户的新信息
        2. 讨论的主要话题
        3. 达成的结论
        4. 待办事项
        """

        # 实际应用中调用LLM
        return f"对话摘要：{len(messages)}条消息"

    def get_user_profile(self) -> Dict:
        """获取用户画像"""
        # 从KV缓存获取基本信息
        profile = self.key_value_store.copy()

        # 从长期记忆检索详细信息
        profile_memories = self.long_term.retrieve(
            "用户的基本信息和偏好",
            top_k=10,
            memory_type="user_profile"
        )

        profile["detailed_info"] = profile_memories

        return profile
```

## 四、记忆增强的Agent

### 4.1 完整的记忆Agent

```python
import openai

class MemoryEnhancedAgent:
    """具备记忆能力的Agent"""

    def __init__(self):
        self.memory = HierarchicalMemory()
        self.model = "gpt-4"

    def chat(self, user_message: str) -> str:
        """与用户对话"""
        # 1. 添加用户消息到记忆
        self.memory.add_message("user", user_message)

        # 2. 获取上下文
        context = self.memory.get_context(query=user_message)

        # 3. 调用LLM
        response = openai.chat.completions.create(
            model=self.model,
            messages=context,
            temperature=0.7
        )

        assistant_message = response.choices[0].message.content

        # 4. 添加助手回复到记忆
        self.memory.add_message("assistant", assistant_message)

        return assistant_message

    def recall(self, query: str) -> List[Dict]:
        """回忆相关信息"""
        return self.memory.long_term.retrieve(query, top_k=5)

    def reflect(self):
        """反思并整合记忆"""
        # 定期将短期记忆合并到长期记忆
        if len(self.memory.short_term.messages) > 20:
            self.memory.consolidate()

    def remember_user_preference(self, preference: str):
        """记住用户偏好"""
        self.memory.long_term.add_memory(
            f"用户偏好：{preference}",
            memory_type="user_preference"
        )

    def get_user_profile(self) -> Dict:
        """获取用户画像"""
        return self.memory.get_user_profile()

# 使用示例
agent = MemoryEnhancedAgent()

# 模拟对话
print(agent.chat("你好，我叫张三"))
# 输出：你好张三，很高兴认识你！

print(agent.chat("我喜欢学习编程，特别是Python"))
# 输出：Python是一门很棒的编程语言！...

print(agent.chat("我之前说过我喜欢什么吗？"))
# 输出：您提到过喜欢学习编程，特别是Python。

# 查看用户画像
profile = agent.get_user_profile()
print("\n用户画像：")
print(json.dumps(profile, ensure_ascii=False, indent=2))
```

### 4.2 记忆触发机制

```python
class MemoryTriggerAgent:
    """带记忆触发的Agent"""

    def __init__(self):
        self.memory = HierarchicalMemory()
        self.model = "gpt-4"

    def should_access_memory(self, user_message: str) -> bool:
        """判断是否需要访问长期记忆"""
        # 使用小模型快速判断
        classification_prompt = f"""
        判断以下问题是否需要访问历史记忆：

        问题：{user_message}

        只回答"是"或"否"。

        需要记忆的情况：
        - 提到之前的信息
        - 问"还记得吗"、"之前说过"
        - 询问个人信息、偏好
        - 引用过去的对话
        """

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": classification_prompt}],
            temperature=0
        )

        return "是" in response.choices[0].message.content

    def chat(self, user_message: str) -> str:
        """智能对话"""
        # 添加到短期记忆
        self.memory.add_message("user", user_message)

        # 构建上下文
        context = []

        # 根据需要检索长期记忆
        if self.should_access_memory(user_message):
            relevant_memories = self.memory.recall(user_message)
            if relevant_memories:
                context.append({
                    "role": "system",
                    "content": "相关记忆：\n" + "\n".join([
                        f"- {m['content']}" for m in relevant_memories[:3]
                    ])
                })

        # 添加对话历史
        context.extend(self.memory.short_term.get_context_window())

        # 生成回复
        response = openai.chat.completions.create(
            model=self.model,
            messages=context
        )

        assistant_message = response.choices[0].message.content
        self.memory.add_message("assistant", assistant_message)

        return assistant_message
```

## 五、记忆管理最佳实践

### 5.1 记忆更新策略

```python
class MemoryUpdateStrategy:
    """记忆更新策略"""

    def __init__(self, memory: VectorMemory):
        self.memory = memory

    def update_if_changed(self, memory_id: str, new_info: str):
        """只有信息变化时才更新"""
        old_memory = self.memory.memories[
            self.memory.id_map[memory_id]
        ]

        # 判断是否真的变化了
        if self._is_significant_change(
            old_memory["content"],
            new_info
        ):
            self.memory.update_memory(memory_id, new_info)

    def _is_significant_change(self, old: str, new: str) -> bool:
        """判断是否有显著变化"""
        # 使用LLM判断
        comparison_prompt = f"""
        比较两个信息是否有显著变化：

        旧信息：{old}
        新信息：{new}

        只回答"是"或"否"。
        """

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": comparison_prompt}],
            temperature=0
        )

        return "是" in response.choices[0].message.content

    def merge_similar_memories(self, threshold=0.9):
        """合并相似的记忆"""
        all_memories = self.memory.get_all_memories()
        to_merge = []

        for i, mem1 in enumerate(all_memories):
            for j, mem2 in enumerate(all_memories[i+1:], i+1):
                # 计算相似度
                similarity = self._compute_similarity(
                    mem1["content"],
                    mem2["content"]
                )

                if similarity > threshold:
                    to_merge.append((mem1, mem2))

        # 执行合并
        for mem1, mem2 in to_merge:
            merged_content = self._merge_contents(
                mem1["content"],
                mem2["content"]
            )

            # 更新mem1，删除mem2
            self.memory.update_memory(mem1["id"], merged_content)
            self.memory.delete_memory(mem2["id"])

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        emb1 = self.memory.encoder.encode([text1])[0]
        emb2 = self.memory.encoder.encode([text2])[0]

        # 余弦相似度
        return np.dot(emb1, emb2) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )

    def _merge_contents(self, content1: str, content2: str) -> str:
        """合并两个内容"""
        merge_prompt = f"""
        合并以下两个信息，保留所有重要细节：

        信息1：{content1}
        信息2：{content2}

        合并后的信息：
        """

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": merge_prompt}],
            temperature=0
        )

        return response.choices[0].message.content
```

### 5.2 记忆重要性评估

```python
class MemoryScorer:
    """记忆重要性评分"""

    def __init__(self, memory: VectorMemory):
        self.memory = memory

    def score_memory(self, memory_id: str) -> float:
        """评估记忆的重要性（0-1）"""
        memory = self.memory.memories[
            self.memory.id_map[memory_id]
        ]

        score = 0.0

        # 因素1：访问频率
        score += self._access_frequency_score(memory_id) * 0.3

        # 因素2：时间衰减
        score += self._recency_score(memory) * 0.2

        # 因素3：内容重要性
        score += self._content_importance_score(memory["content"]) * 0.3

        # 因素4：用户标记
        if memory.get("metadata", {}).get("important"):
            score += 0.2

        return min(score, 1.0)

    def _access_frequency_score(self, memory_id: str) -> float:
        """访问频率评分"""
        # 简化处理，实际需要记录访问次数
        return 0.5

    def _recency_score(self, memory: Dict) -> float:
        """时间衰减评分"""
        created_at = datetime.fromisoformat(memory["created_at"])
        days_ago = (datetime.now() - created_at).days

        # 指数衰减
        return math.exp(-days_ago / 30)  # 30天半衰期

    def _content_importance_score(self, content: str) -> float:
        """内容重要性评分（使用LLM）"""
        prompt = f"""
        评估以下信息的重要性（0-1之间的分数）：

        {content}

        只返回数字分数，不要其他内容。
        """

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        try:
            return float(response.choices[0].message.content.strip())
        except:
            return 0.5

    def cleanup_low_score_memories(self, threshold=0.3):
        """清理低分记忆"""
        all_memories = self.memory.get_all_memories()

        for memory in all_memories:
            score = self.score_memory(memory["id"])
            if score < threshold:
                print(f"删除低分记忆 [{score:.2f}]: {memory['content'][:50]}...")
                self.memory.delete_memory(memory["id"])
```

### 5.3 记忆遗忘机制

```python
class ForgettingMechanism:
    """记忆遗忘机制"""

    def __init__(self, memory: VectorMemory):
        self.memory = memory

    def adaptive_forgetting(self):
        """自适应遗忘"""
        all_memories = self.memory.get_all_memories()

        scorer = MemoryScorer(self.memory)

        for memory in all_memories:
            importance = scorer.score_memory(memory["id"])

            # 根据重要性和时间决定是否遗忘
            if importance < 0.2:
                # 低重要性：快速遗忘
                if self._days_old(memory) > 7:
                    self.memory.delete_memory(memory["id"])

            elif importance < 0.5:
                # 中等重要性：慢速遗忘
                if self._days_old(memory) > 90:
                    self.memory.delete_memory(memory["id"])

            # 高重要性：不主动遗忘

    def _days_old(self, memory: Dict) -> int:
        """计算记忆的天数"""
        created_at = datetime.fromisoformat(memory["created_at"])
        return (datetime.now() - created_at).days

    def compress_old_memories(self):
        """压缩旧记忆"""
        all_memories = self.memory.get_all_memories()
        old_memories = [
            m for m in all_memories
            if self._days_old(m) > 30
        ]

        if len(old_memories) < 5:
            return

        # 按类型分组
        grouped = {}
        for memory in old_memories:
            memory_type = memory["type"]
            if memory_type not in grouped:
                grouped[memory_type] = []
            grouped[memory_type].append(memory)

        # 对每类记忆进行压缩
        for memory_type, memories in grouped.items():
            self._compress_memory_group(memories)

    def _compress_memory_group(self, memories: List[Dict]):
        """压缩一组记忆"""
        contents = [m["content"] for m in memories]

        compress_prompt = f"""
        将以下多个记忆压缩成简洁的摘要，保留所有关键信息：

        {json.dumps(contents, ensure_ascii=False, indent=2)}

        摘要：
        """

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": compress_prompt}],
            temperature=0
        )

        summary = response.choices[0].message.content

        # 删除旧记忆，添加压缩后的记忆
        for memory in memories:
            self.memory.delete_memory(memory["id"])

        self.memory.add_memory(
            summary,
            memory_type=memories[0]["type"],
            metadata={"compressed": True, "original_count": len(memories)}
        )
```

## 六、实战案例：个性化学习助手

```python
class PersonalizedLearningAssistant:
    """个性化学习助手"""

    def __init__(self):
        self.memory = HierarchicalMemory()
        self.model = "gpt-4"
        self.scoring = MemoryScorer(self.memory.long_term)

    def learn(self, user_input: str):
        """学习过程"""
        # 添加到记忆
        self.memory.add_message("user", user_input)

        # 提取学习信息
        self._extract_learning_info(user_input)

        # 获取上下文
        context = self._get_learning_context(user_input)

        # 生成个性化回复
        response = openai.chat.completions.create(
            model=self.model,
            messages=context
        )

        assistant_message = response.choices[0].message.content

        # 保存交互
        self.memory.add_message("assistant", assistant_message)

        return assistant_message

    def _extract_learning_info(self, user_input: str):
        """提取学习信息"""
        extraction_prompt = f"""
        从以下输入中提取学习相关信息：

        {user_input}

        提取字段（JSON格式）：
        - topic: 学习主题
        - level: 掌握程度（beginner/intermediate/advanced）
        - progress: 进度描述
        - difficulties: 遇到的困难
        - goals: 学习目标
        """

        # 实际应用中调用LLM
        # 这里简化处理

        # 保存到长期记忆
        self.memory.long_term.add_memory(
            f"学习信息：{user_input}",
            memory_type="learning",
            metadata={"topic": "编程", "level": "beginner"}
        )

    def _get_learning_context(self, query: str) -> List[Dict]:
        """获取学习上下文"""
        context = []

        # 检索相关学习记忆
        learning_memories = self.memory.long_term.retrieve(
            query,
            top_k=5,
            memory_type="learning"
        )

        if learning_memories:
            # 构建学习者画像
            profile = self._build_learning_profile(learning_memories)

            context.append({
                "role": "system",
                "content": f"""你是专业的学习助手。学习者画像：

{profile}

根据学习者的水平和进度，提供个性化的指导。"""
            })

        # 添加对话历史
        context.extend(self.memory.short_term.get_context_window())

        # 添加当前问题
        context.append({"role": "user", "content": query})

        return context

    def _build_learning_profile(self, memories: List[Dict]) -> str:
        """构建学习者画像"""
        profile_prompt = f"""
        基于以下学习记录，生成学习者画像：

        {json.dumps([m['content'] for m in memories], ensure_ascii=False, indent=2)}

        画像应包括：
        1. 当前学习主题
        2. 掌握水平
        3. 学习进度
        4. 需要帮助的方面
        """

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": profile_prompt}],
            temperature=0
        )

        return response.choices[0].message.content

    def get_learning_path(self, topic: str) -> str:
        """生成学习路径"""
        # 检索相关学习记忆
        relevant_memories = self.memory.long_term.retrieve(
            topic,
            top_k=10,
            memory_type="learning"
        )

        # 生成个性化学习路径
        path_prompt = f"""
        为学习者制定个性化的学习路径：

        学习主题：{topic}

        学习者历史：
        {json.dumps([m['content'] for m in relevant_memories], ensure_ascii=False, indent=2)}

        请提供：
        1. 基于当前水平的起点
        2. 分阶段的学习目标
        3. 每个阶段的具体任务
        4. 预估时间
        5. 推荐资源
        """

        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": path_prompt}],
            temperature=0.7
        )

        return response.choices[0].message.content

    def review_progress(self) -> str:
        """回顾学习进度"""
        all_learning = self.memory.long_term.get_all_memories(
            memory_type="learning"
        )

        review_prompt = f"""
        回顾学习者的整体进度：

        {json.dumps([m['content'] for m in all_learning], ensure_ascii=False, indent=2)}

        提供：
        1. 已完成的里程碑
        2. 当前水平评估
        3. 待改进的地方
        4. 下一步建议
        """

        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": review_prompt}],
            temperature=0.5
        )

        return response.choices[0].message.content

# 使用示例
assistant = PersonalizedLearningAssistant()

# 学习过程
print(assistant.learn("我想学习Python编程，我是完全的初学者"))
print(assistant.learn("我学会了Python的基础语法，现在想学习面向对象"))
print(assistant.learn("在理解类和对象时遇到了困难"))

# 获取学习路径
print("\n个性化学习路径：")
print(assistant.get_learning_path("Python"))

# 回顾进度
print("\n学习进度回顾：")
print(assistant.review_progress())
```

## 七、总结

### 核心要点

1. **记忆分层**：短期记忆（对话历史）+ 长期记忆（向量存储）
2. **向量检索**：使用嵌入模型和FAISS实现语义检索
3. **记忆管理**：定期压缩、重要性评分、自适应遗忘
4. **上下文整合**：根据需要动态检索相关记忆
5. **个性化服务**：基于记忆提供定制化体验

### 最佳实践

- ✅ **分层存储**：短期用列表，长期用向量数据库
- ✅ **定期压缩**：避免记忆无限膨胀
- ✅ **重要性评分**：优先保留高价值记忆
- ✅ **智能检索**：只在需要时访问长期记忆
- ✅ **隐私保护**：允许用户删除敏感记忆

### 常见陷阱

- ❌ **记忆过载**：存储太多无关信息
- ❌ **检索噪音**：返回不相关的记忆
- ❌ **忽视隐私**：未经用户同意存储敏感信息
- ❌ **过度依赖**：不是所有任务都需要复杂记忆系统

---

## 推荐阅读

- [LangChain Memory Documentation](https://python.langchain.com/docs/modules/memory/)
- [Semantic Search with FAISS](https://github.com/facebookresearch/faiss)
- [Sentence-Transformers](https://www.sbert.net/)

## 关于本系列

这是《AI Agent系列教程》的第5篇，共12篇。

**上一篇回顾**：《MCP协议深度解析：连接AI与数据源的标准化桥梁》

**下一篇预告**：《规划与推理：Agent如何分解复杂任务》

---

*如果这篇文章对你有帮助，欢迎点赞、收藏和分享！有任何问题欢迎在评论区讨论。*

---

**上一篇**：[MCP协议深度解析：连接AI与数据源的标准化桥梁](./article-05-mcp-protocol.md)
**下一篇**：[规划与推理：Agent如何分解复杂任务](./article-08-planning-reasoning.md)

---

**系列说明**：
- 本系列文章正在持续更新中，欢迎关注！
- 所有代码示例将在GitHub仓库开源：`ai-agent-tutorial-series`
- 有问题欢迎在评论区讨论，我会及时回复
