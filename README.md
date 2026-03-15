# Workflow Automation API

Configure automated workflows via API. Define triggers and action chains — when a webhook fires, the system executes all actions in sequence: send Telegram messages, make HTTP requests, log events.

## What it does

- Create workflows with webhook triggers and multiple actions
- Supports action chaining — execute in order on each trigger
- Template system — inject webhook data into messages using `{{data.field}}`
- Stores execution history per workflow
- Clean REST API with auto-generated docs

## Tech stack

- **FastAPI** — REST API framework
- **SQLite** — storage for workflows and execution history
- **Telegram Bot API** — notification action
- **Docker** — containerization

## Quick start

### With Docker

```bash
git clone https://github.com/Dr-Jusper/workflow-automation.git
cd workflow-automation

# Create .env file
cat > .env << 'ENV'
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ENV

docker build -t workflow-automation .
docker run -d -p 8000:8000 --env-file .env --name workflow-automation workflow-automation
```

### Local development

```bash
cd app
pip install -r ../requirements.txt
uvicorn main:app --reload
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/workflows` | Create a new workflow |
| GET | `/workflows` | List all workflows |
| GET | `/workflows/{id}` | Get workflow by ID |
| GET | `/workflows/{id}/executions` | Get execution history |
| POST | `/webhooks/{token}` | Trigger a workflow |

Interactive docs available at `http://localhost:8000/docs`

## Example

Create a workflow:

```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Order notification",
    "actions": [
      {
        "type": "telegram",
        "config": {
          "message": "New order {{data.order_id}} from {{data.customer}}"
        }
      },
      {
        "type": "log",
        "config": {
          "message": "Order logged: {{data.order_id}}"
        }
      }
    ]
  }'
```

Response includes a webhook URL:

```json
{
  "id": 1,
  "name": "Order notification",
  "webhook_url": "/webhooks/abc123XYZ",
  "actions": [...]
}
```

Trigger the workflow:

```bash
curl -X POST http://localhost:8000/webhooks/abc123XYZ \
  -H "Content-Type: application/json" \
  -d '{"order_id": "42", "customer": "John Smith"}'
```

Telegram receives: `New order 42 from John Smith`

## Supported actions

| Type | Description | Config fields |
|------|-------------|---------------|
| `telegram` | Send Telegram message | `message` |
| `http` | Make HTTP request | `url`, `method`, `body` |
| `log` | Print to console | `message` |

## Template syntax

Use `{{data.field}}` in action configs to inject incoming webhook data:

```json
{"message": "Hello {{data.name}}, your order {{data.order_id}} is confirmed"}
```

## Project structure

```
workflow-automation/
├── app/
│   ├── main.py        # FastAPI app and endpoints
│   ├── executor.py    # Action execution and template rendering
│   └── database.py    # SQLite models and queries
├── Dockerfile
├── requirements.txt
└── README.md
```
