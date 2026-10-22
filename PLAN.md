# 电商客服 Agent 架构说明

## Context

本项目用于练习用 DeepEval 对 agent 做评测与轨迹断言。架构是 LangChain 1.x 的 ReAct 循环（`create_agent`），五分类意图通过 function call 表达。

系统提示词在 `src/prompts/system_prompts.py`，意图表在 `src/agent/intent.py`。

---

## 项目结构

```
deepeval_test/
├── src/
│   ├── agent/
│   │   ├── react_agent.py             # ReAct Agent 主体
│   │   ├── intent.py                  # 意图表与意图回读
│   │   └── state.py                   # 状态结构
│   ├── tools/                         # 五个工具
│   ├── database/                      # SQLite + ORM + 仓储
│   ├── data/knowledge_data.py         # 统一知识库
│   ├── prompts/system_prompts.py      # 系统提示词
│   ├── schemas.py                     # 工具结果模型
│   └── identifiers.py                 # 订单号归一
├── tests/
│   ├── conftest.py / fake_llm.py
│   ├── unit/test_tools.py / test_intent.py
│   └── integration/test_agent_flow.py / test_deepeval.py
├── verify_agent.py
└── web_chat.py
```

---

## 核心设计

### 1. 意图即工具调用

不做二次 LLM 分类。function call 本身就是 LLM 的结构化输出，`extract_intent` 遍历本轮实际发出的工具调用，用 `TOOL_ROUTES` 反查得到意图。这样"记录的意图"和"执行的工具"永远不会分叉。

| 意图 | 工具 | 参数 |
|---|---|---|
| `product_query` | `query_product` | `sku_id` |
| `order_query` | `query_order` | `order_id` |
| `logistics_query` | `query_logistics` | `order_id` |
| `policy_query` | `search_policy` | `query` |
| `fallback` | `handoff_to_human` | `reason` |

零工具调用也归 `fallback`，用 `context["fallback_reason"]` 区分 `no_tool_call` 与 `handoff`。

### 2. ReAct 循环

```
model 节点 ──tool call──► tools 节点 ──observation──► model 节点（可循环）──► 最终答复
```

`create_agent` 挂 `InMemorySaver`，`user_id` 即 `thread_id`，支持跨轮上下文。

### 3. 缺参数时的统一语义

分类表规定一轮一意图，所以缺参数时不跳过工具，而是照常调用、参数留空。工具返回 `needs_input=True` 与一段可直接转述给用户的话术，LLM 据此追问。

工具结果统一三个字段：`found`（是否命中）、`needs_input`（是否因缺参未命中）、`message`（未命中时给 LLM 的说明）。命中时的事实由各结果类的 `to_text()` 渲染成一行，既是 LLM 看到的 observation，也是 DeepEval 的 context。

### 4. DeepEval 的 context 来源

`retrieved_content` 是本轮所有工具返回文本的拼接，直接作为 `FaithfulnessMetric` 与 `HallucinationMetric` 的 context，不硬编码字符串。忠实度指标衡量的才是"答案有没有超出工具给的信息"。

---

## 已知取舍

- 工具集严格按五分类表收敛。取消订单、退换货受理这类能力归入"操作类请求"，走 `handoff_to_human` 并落一条 `handoffs` 记录，返回工单号。
- 意图判定完全依赖 LLM 的工具选择，提示词是唯一的消歧依据。提示词变更需要重跑集成测试。
- 集成测试需要真实 LLM，缺少 `OPENAI_API_KEY` 时跳过。单元测试用 `FakeToolCallingModel` 驱动真实 ReAct 循环，不烧 token。

---

## 验证方式

```bash
pytest tests/unit -v          # 34 个，不依赖 LLM
pytest tests/integration -v   # 14 个，需要 OPENAI_API_KEY
python verify_agent.py        # 五类意图端到端
streamlit run web_chat.py     # Web 界面
```
