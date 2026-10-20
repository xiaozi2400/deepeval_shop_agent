# 电商客服Agent应用实现计划

## Context

用户需要一个电商客服Agent应用来练习agent应用测试。目标是构建一个基于 LangGraph + Claude 的客服系统，使用 DeepEval 进行测试评估。

---

## 项目结构

```
ecommerce_customer_service/
├── src/
│   ├── agent/
│   │   ├── customer_service_agent.py   # 核心Agent (LangGraph流程编排)
│   │   ├── state.py                    # 状态管理
│   │   └── nodes.py                    # 节点定义(FAQ/订单/退换货/政策)
│   ├── tools/
│   │   ├── order_tools.py              # 订单查询工具
│   │   ├── faq_tools.py                # FAQ检索工具
│   │   ├── return_tools.py             # 退换货工具
│   │   └── policy_tools.py             # 政策查询工具
│   ├── data/
│   │   ├── faq_data.py                # FAQ模拟数据
│   │   ├── policy_data.py              # 政策模拟数据
│   │   └── mock_orders.py              # 模拟订单数据
│   └── prompts/
│       └── system_prompts.py           # 系统提示词
├── tests/
│   ├── unit/
│   │   └── test_tools.py              # 工具单元测试
│   └── integration/
│       ├── test_agent_flow.py          # Agent流程集成测试
│       └── test_deepeval.py           # DeepEval评估测试
├── pyproject.toml
├── .env.example
└── requirements.txt
```

---

## 实现步骤

### Phase 1: 项目基础
- 创建目录结构
- 配置 `requirements.txt` 和 `pyproject.toml`
- 配置 `.env.example`

### Phase 2: 数据层 + 工具层
- 实现模拟数据 (`src/data/`)
- 实现工具层 (`src/tools/order_tools.py`, `faq_tools.py`, `return_tools.py`, `policy_tools.py`)
- 单元测试验证

### Phase 3: Agent核心
- 实现状态管理 (`src/agent/state.py`)
- 实现节点定义 (`src/agent/nodes.py`)
- 实现Agent主类 (`src/agent/customer_service_agent.py`)
- 集成测试验证

### Phase 4: 测试与评估
- 配置DeepEval
- 编写测试用例 (FAQ查询、订单查询、退换货、政策咨询、问候告别)
- 运行评估

---

## 核心模块设计

### 状态管理 (state.py)
- `CustomerServiceState`: LangGraph共享状态
- `Intent`枚举: greeting, order_query, return_exchange, policy_query, faq, fallback, goodbye
- `OrderInfo`, `ReturnRequest` 数据类

### 节点定义 (nodes.py)
- `routing_node`: 意图分类路由
- `faq_node`, `order_query_node`, `return_exchange_node`, `policy_query_node`, `greeting_node`, `goodbye_node`

### 工具设计
| 工具 | 功能 |
|------|------|
| order_tools | query_order, cancel_order |
| faq_tools | search_faq (关键词匹配) |
| return_tools | process_return_request, check_return_status |
| policy_tools | query_policy (配送/退换货/支付/会员政策) |

---

## 测试用例设计

### 集成测试
- `TestOrderQuery`: 订单号查询、发货状态、签收状态
- `TestReturnExchange`: 退货申请、换货申请、政策查询
- `TestFAQ`: 运费、支付方式、联系客服
- `TestPolicyQuery`: 配送政策、会员政策
- `TestGreetingGoodbye`: 问候与告别

### DeepEval评估指标
- `AnswerRelevancyMetric`: 答案相关性 (threshold=0.7)
- `FaithfulnessMetric`: 答案忠实度 (threshold=0.8)
- `HallucinationMetric`: 幻觉检测 (threshold=0.1)
- `ToxicityMetric`: 毒性检测 (threshold=0.1)

---

## 关键文件

| 文件 | 作用 |
|------|------|
| `src/agent/customer_service_agent.py` | 核心Agent，LangGraph流程编排 |
| `src/agent/state.py` | 状态管理 |
| `src/agent/nodes.py` | 节点定义 |
| `tests/integration/test_deepeval.py` | DeepEval测试评估 |

---

## 验证方式

1. 运行单元测试: `pytest tests/unit/ -v`
2. 运行集成测试: `pytest tests/integration/ -v`
3. 运行DeepEval评估: `pytest tests/integration/test_deepeval.py -v`
4. 手动测试对话流程，验证各功能节点正常工作

---

## 依赖

```
langgraph>=0.0.20
langchain-anthropic>=0.1.0
anthropic>=0.18.0
deepeval>=0.21.0
pytest>=8.0.0
python-dotenv>=1.0.0
```
