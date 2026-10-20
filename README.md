# E-commerce Customer Service Agent

基于 LangGraph + Claude 的电商客服 Agent 应用，用于练习 Agent 应用的测试。

## 项目结构

```
ecommerce_customer_service/
├── src/
│   ├── agent/
│   │   ├── customer_service_agent.py   # 核心Agent
│   │   ├── state.py                  # 状态管理
│   │   └── nodes.py                  # 节点定义
│   ├── tools/
│   │   ├── order_tools.py            # 订单查询工具
│   │   ├── faq_tools.py              # FAQ检索工具
│   │   ├── return_tools.py           # 退换货工具
│   │   └── policy_tools.py          # 政策查询工具
│   └── data/
│       ├── mock_orders.py           # 模拟订单数据
│       ├── faq_data.py              # FAQ数据
│       └── policy_data.py           # 政策数据
├── tests/
│   ├── unit/
│   │   └── test_tools.py            # 工具单元测试
│   └── integration/
│       └── test_agent_flow.py       # Agent流程集成测试
├── pyproject.toml
├── requirements.txt
└── verify_agent.py                  # 快速验证脚本
```

## 功能特性

### 意图识别与路由
| 意图 | 功能 | 路由关键词 |
|------|------|-----------|
| `greeting` | 问候 | 你好、hi、hello、在吗 |
| `order_query` | 订单查询 | 订单、查单、发货、物流 |
| `return_exchange` | 退换货 | 退货、换货、退款、退换 |
| `policy_query` | 政策查询 | 政策、规定、规则、会员 |
| `faq` | 常见问题 | 运费、支付、联系客服 |
| `goodbye` | 告别 | 再见、bye |

### 工具模块
- **order_tools**: 订单查询、取消订单
- **faq_tools**: FAQ关键词匹配检索
- **return_tools**: 退换货申请处理
- **policy_tools**: 配送/退换货/支付/会员政策查询

## 快速开始

### 1. 安装依赖

```bash
pip install langgraph langchain-anthropic anthropic pytest pytest-asyncio python-dotenv
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# 第三方中转配置（OpenAI兼容接口）
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.example.com/v1
MODEL_NAME=claude-3-5-sonnet-20241014

# 如果使用原生OpenAI
# OPENAI_API_KEY=sk-xxx
# MODEL_NAME=gpt-4o

# 如果使用Anthropic直接API
# ANTHROPIC_API_KEY=sk-ant-xxx
# MODEL_NAME=claude-sonnet-4-20250514

# 日志级别
LOG_LEVEL=INFO
```

### 3. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/test_tools.py -v

# 运行集成测试
pytest tests/integration/test_agent_flow.py -v
```

### 4. 验证 Agent

```bash
python verify_agent.py
```

## 测试覆盖

### 单元测试 (11 个)
- `TestOrderTools`: 订单查询、取消订单
- `TestFAQQueries`: FAQ检索
- `TestReturnTools`: 退换货处理
- `TestPolicyTools`: 政策查询

### 集成测试 (14 个)
- 问候/告别流程
- 订单查询流程
- 退换货申请流程
- 政策查询流程
- FAQ问答流程
- 完整对话流程

## 测试数据

### 订单号
| 订单号 | 状态 | 商品 |
|--------|------|------|
| ORD2024001 | 已发货 | iPhone 15 Pro Max、AirPods Pro 2 |
| ORD2024002 | 已签收 | MacBook Pro 14寸、Magic Mouse |
| ORD2024003 | 待发货 | iPad Air 5、Apple Pencil |
| ORD2024004 | 已取消 | Sony WH-1000XM5 |

## 使用示例

```python
from src.agent.customer_service_agent import CustomerServiceAgent

agent = CustomerServiceAgent()pyth

# 问候
result = agent.invoke("你好")
print(result["messages"][-1].content)

# 订单查询
result = agent.invoke("查一下订单ORD2024001")
print(result["messages"][-1].content)

# 退换货
result = agent.invoke("退货订单ORD2024003")
print(result["messages"][-1].content)

# 政策查询
result = agent.invoke("配送政策是什么")
print(result["messages"][-1].content)

# FAQ
result = agent.invoke("运费如何计算")
print(result["messages"][-1].content)

# 使用LLM进行意图识别（需要配置OPENAI_API_KEY）
agent = CustomerServiceAgent(use_llm_routing=True)
result = agent.invoke("我的订单什么时候能到")
print(result["messages"][-1].content)
```

## 架构说明

### LangGraph 流程

```
START
  │
  ▼
routing (意图分类)
  │
  ├── greeting_node ──────────────────────► END
  │
  ├── order_query_node ──────────────────► END
  │
  ├── return_exchange_node ──────────────► END
  │
  ├── policy_query_node ─────────────────► END
  │
  ├── faq_node ─────────────────────────► END
  │
  └── goodbye_node ─────────────────────► END
```

### 状态管理

`CustomerServiceState` 包含：
- `messages`: 对话历史
- `intent`: 当前意图
- `order_info`: 订单信息
- `return_request`: 退换货请求
- `current_node`: 当前节点
- `next_node`: 下一节点
- `context`: 上下文数据
- `user_id`: 用户ID

## License

MIT
