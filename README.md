# E-commerce Customer Service Agent

基于 LangChain ReAct + DeepEval 的电商客服 Agent，用于练习对 agent 做轨迹断言与自动化评测。

[![CI](https://github.com/xiaozi2400/deepeval_shop_agent/actions/workflows/ci.yml/badge.svg)](https://github.com/xiaozi2400/deepeval_shop_agent/actions/workflows/ci.yml)

## 项目结构

```
.
├── src/
│   ├── agent/
│   │   ├── react_agent.py             # ReAct Agent（create_agent + checkpointer）
│   │   ├── intent.py                  # 五分类意图表与意图回读
│   │   └── state.py                   # 状态结构与订单状态枚举
│   ├── tools/
│   │   ├── product_tools.py           # 商品查询
│   │   ├── order_tools.py             # 订单查询
│   │   ├── logistics_tools.py         # 物流查询
│   │   ├── policy_tools.py            # 政策查询
│   │   └── handoff_tools.py           # 转人工兜底
│   ├── database/
│   │   ├── connection.py              # SQLite 连接与建表
│   │   ├── models.py                  # ORM 模型
│   │   ├── seed.py                    # 种子数据
│   │   └── repositories/              # 各实体的仓储
│   ├── data/
│   │   └── knowledge_data.py          # 统一知识库（政策 + FAQ）
│   ├── prompts/
│   │   └── system_prompts.py          # 系统提示词
│   ├── schemas.py                     # 工具返回的结构化结果模型
│   └── identifiers.py                 # 订单号归一
├── tests/
│   ├── conftest.py                    # 测试隔离（临时库 + 假模型 fixture）
│   ├── fake_llm.py                    # 可编程的假模型，驱动真实 ReAct 循环
│   ├── unit/
│   │   ├── test_tools.py              # 工具单元测试
│   │   └── test_intent.py             # 意图表与意图回读
│   └── integration/
│       ├── test_agent_flow.py         # 五类意图的轨迹断言
│       └── test_deepeval.py           # DeepEval 指标
├── app/
│   └── web_chat.py                    # Streamlit 聊天界面
├── scripts/
│   └── verify_agent.py                # 五类意图端到端验证
├── docs/
│   └── architecture.md                # 架构说明与已知取舍
├── data/                              # 运行时 SQLite 库，不进版本库
├── .env.example                       # 环境变量模板
├── pyproject.toml                     # 依赖与工具配置的单一事实来源
└── uv.lock                            # 钉住依赖版本，保证可复现安装
```

## 五分类意图

每次 function call 就是一次意图判定。工具集严格收敛为五个，`TOOL_ROUTES` 是唯一事实来源。

| 意图 | 典型问法 | 工具 | 参数 |
|---|---|---|---|
| 商品查询 | "这个多少钱""还有货吗" | `query_product` | `sku_id` |
| 订单查询 | "我的订单到哪了" | `query_order` | `order_id` |
| 物流查询 | "快递到哪了" | `query_logistics` | `order_id` |
| 政策查询 | "能七天无理由吗" | `search_policy` | `query` |
| 兜底 | 意图不明 / 投诉 / 操作类请求 | `handoff_to_human` | `reason` |

兜底涵盖取消订单、办理退货换货、改地址、赔偿、转人工等一切需要执行动作的请求。用户明确要转人工时同样走 `handoff_to_human`。

## 架构说明

### ReAct 循环 + 意图回读

```
用户消息
   │
   ▼
┌──────────────────────────────┐
│ model 节点                    │  ← 决定调哪个工具，参数填什么
│  ├─ 工具调用 ────────────────►│
│  └─ 最终答复                  │
└──────────────────────────────┘
   │            ▲
   ▼            │
tools 节点      │
（执行工具）────┘
   │
   ▼
extract_intent：遍历本轮 tool call，
用 TOOL_ROUTES 反查 intent
   │
   ▼
CustomerServiceState
（intent / tool_calls / retrieved_content / context）
```

意图不做二次 LLM 分类。function call 本身就是 LLM 的结构化输出，从实际调用的工具名反查意图，保证"记录的意图"和"执行的工具"永远不会分叉。

`create_agent` 挂了 `InMemorySaver`，`user_id` 直接作为 `thread_id`，所以"这个多少钱""还有货吗"这类依赖上一轮的表述能真正跨轮使用。

### 工具返回值

五个工具统一返回 Pydantic 模型（`src/schemas.py`），同一份数据既回灌给 LLM，也直接作为 DeepEval 的 context。

- `found`：是否查到实体
- `needs_input`：没查到是因为参数缺失（需要追问），而不是实体不存在
- `message`：没查到或缺参时给 LLM 的说明与话术
- `to_text()`：命中时渲染成一行事实，既是 LLM 看到的 observation，也是 DeepEval 的 context

缺参数时仍然调用工具、参数留空，工具返回 `needs_input=True`，Agent 据此向用户追问。这样每一轮都有确定的意图与工具调用，意图准确率才有意义。

### 状态结构

`CustomerServiceState` 包含：

- `messages`：完整对话历史
- `intent`：本轮意图，五个枚举值之一
- `tool_calls`：工具调用记录（工具名、参数、结果摘要）
- `retrieved_content`：本轮所有工具返回的文本拼接
- `context`：`tool` / `params` / `extra_tools` / `fallback_reason`
- `user_id`：会话标识

## 快速开始

### 1. 安装依赖

```bash
pip install -e ".[dev]"
```

依赖清单的唯一事实来源是 `pyproject.toml`。运行时依赖在 `[project.dependencies]`，测试与 lint 依赖在 `[project.optional-dependencies].dev`，所以只跑应用的人不必装整套评测框架。

用 [uv](https://docs.astral.sh/uv/) 的话更省事，锁文件保证依赖版本可复现：

```bash
uv sync --all-extras
```

`uv.lock` 已提交到仓库，CI 与本地装出的是同一套依赖版本。改完 `pyproject.toml` 的依赖后用 `uv lock` 更新它。

### 2. 配置环境变量

```bash
cp .env.example .env
```

在 `.env` 里填入真实值：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.example.com/v1
MODEL_NAME=your_model_name
```

`MODEL_NAME` 同时被 Agent 和 DeepEval 使用（`DEEPEVAL_MODEL` 可单独覆盖评估用的模型）。

### 3. 运行测试

```bash
# 单元测试，不碰 LLM
pytest tests/unit -v

# 集成测试与 DeepEval，需要 OPENAI_API_KEY
pytest tests/integration -v

# 全部
pytest tests -v
```

集成测试带 `llm` 标记，缺少 `OPENAI_API_KEY` 时自动跳过。没装 `deepeval` 时 `test_deepeval.py` 整个模块跳过，不会影响其他测试的收集。

测试用 `tests/conftest.py` 把 `DATABASE_URL` 指向 `tests/.tmp/test.db`，不会碰开发库 `data/orders.db`。

### 4. 五类意图端到端验证

```bash
python scripts/verify_agent.py
```

逐条断言 intent 与主工具名。

### 5. Web 界面

```bash
streamlit run app/web_chat.py
```

会话以 Streamlit session 为单位，session id 即 `thread_id`，多轮上下文可用。

## 测试覆盖

### 单元测试（34 个，不依赖 LLM）

- `test_tools.py`：五个工具的命中与未命中、缺参数、乱序订单号抽取、商品名从整句问法里识别、订单状态回归（曾因跨枚举查表恒为"待发货"）
- `test_intent.py`：`TOOL_ROUTES` 映射、`extract_intent` 对单工具 / 多工具 / 零工具的判定、假模型驱动真实 ReAct 循环

### 集成测试（14 个，需要真实 LLM）

- `test_agent_flow.py`：五类意图各一条典型问法，断言 `intent` 与 `context["tool"]`；缺参数仍产生工具调用；多轮上下文延续
- `test_deepeval.py`：`AnswerRelevancy` / `Faithfulness` / `Hallucination` / `Toxicity`，context 一律取自 `retrieved_content`

## 测试数据

| 订单号 | 状态 | 商品 | 物流 |
|---|---|---|---|
| ORD2024001 | 已发货 | iPhone 15 Pro Max、AirPods Pro 2 | 顺丰速运，在途 |
| ORD2024002 | 已签收 | MacBook Pro 14寸、Magic Mouse | 中通快递，已签收 |
| ORD2024003 | 待发货 | iPad Air 5、Apple Pencil | 无物流记录 |
| ORD2024004 | 已取消 | Sony WH-1000XM5 | 无物流记录 |

ORD2024003 与 ORD2024004 刻意不配物流，"该订单暂无物流信息"是一个真实的可测场景。`SKU-SONY-WH1000XM5` 库存为 0，用于"还有货吗"的用例。

## 使用示例

```python
from src.agent.react_agent import ReactCustomerServiceAgent

agent = ReactCustomerServiceAgent()

result = agent.invoke("iPhone 15 Pro Max 256GB 多少钱")
print(result["intent"])             # Intent.PRODUCT_QUERY
print(result["context"]["tool"])     # query_product
print(result["retrieved_content"])   # 工具返回的事实
print(result["messages"][-1].content)

# 多轮：user_id 即会话 thread_id
agent.invoke("iPhone 15 Pro Max 256GB 多少钱", user_id="u1")
result = agent.invoke("这个还有货吗", user_id="u1")
```

## License

[MIT](LICENSE)
