from agent import workflow, BaseModel
from llama_index.core.agent.workflow import ToolCall, ToolCallResult
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import json

class ApiInput(BaseModel):
    prompt: str

class ApiOutout(BaseModel):
    response: str
    process: str

app = FastAPI(default_response_class=ORJSONResponse)

@app.post("/chat")
async def chat(inpt: ApiInput) -> ApiOutout:
    prompt = inpt.prompt
    handle = workflow.run(user_msg=prompt)
    process = ""
    async for event in handle.stream_events():
        if isinstance(event, ToolCallResult):
            process += f"Tool Call Result for **{event.tool_name}**:\n```json\n{event.tool_output.model_dump_json(indent=4)}\n```\n"
        elif isinstance(event, ToolCall):
            process += f"Called Tool **{event.tool_name}** with arguments:\n```json\n{json.dumps(event.tool_kwargs, indent=4)}\n```\n"
    response = await handle
    response = str(response)
    return ApiOutout(response=response, process=process)