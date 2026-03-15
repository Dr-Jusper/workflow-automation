import secrets
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from database import (
    init_db, create_workflow, create_trigger, create_action,
    get_workflow, get_workflow_by_token, get_all_workflows,
    log_execution, get_executions
)
from executor import execute_workflow


app = FastAPI(
    title="Workflow Automation API",
    description="Configure and automate workflows with webhooks and actions",
    version="1.0.0"
)


class ActionConfig(BaseModel):
    type: str
    config: dict


class WorkflowCreate(BaseModel):
    name: str
    actions: list[ActionConfig]


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok", "message": "Workflow Automation API is running"}


@app.post("/workflows")
def create(workflow: WorkflowCreate):
    """Create a new workflow with trigger and actions."""

    # Создаём workflow
    workflow_id = create_workflow(workflow.name)

    # Генерируем уникальный токен для webhook
    token = secrets.token_urlsafe(16)
    create_trigger(workflow_id, "webhook", token)

    # Создаём actions по порядку
    for i, action in enumerate(workflow.actions):
        create_action(workflow_id, i + 1, action.type, action.config)

    return {
        **get_workflow(workflow_id),
        "webhook_url": f"/webhooks/{token}"
    }


@app.get("/workflows")
def list_workflows():
    """List all workflows."""
    return get_all_workflows()


@app.get("/workflows/{workflow_id}")
def get(workflow_id: int):
    """Get workflow by ID."""
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@app.get("/workflows/{workflow_id}/executions")
def executions(workflow_id: int):
    """Get execution history for a workflow."""
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return get_executions(workflow_id)


@app.post("/webhooks/{token}")
async def webhook(token: str, body: dict = {}):
    input_data = body
    
    workflow = get_workflow_by_token(token)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        execute_workflow(workflow, {"data": input_data})
        log_execution(workflow["id"], "success", input_data)
    except Exception as e:
        log_execution(workflow["id"], "failed", input_data)
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {e}")

    return {"status": "ok", "workflow": workflow["name"]}