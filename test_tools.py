import os
import json
from dotenv import load_dotenv

from llm_client import LLMClient
from tool_schemas import TOOLS_SCHEMA
from tools import dispatcher

load_dotenv()

llm_client = LLMClient(
    api_key=os.getenv("GROQ_API_KEY"),
    model=os.getenv("GROQ_MODEL")
)

messages = [
    {
        "role": "user",
        "content": "Create a file called hello.py containing print('Hello ForgeAI')"
    }
]

message = llm_client.chat_with_tools(
    messages,
    TOOLS_SCHEMA
)

tool_call = message.tool_calls[0]

tool_name = tool_call.function.name
arguments = json.loads(tool_call.function.arguments)

result = dispatcher(tool_name, arguments)

messages.append(message)

messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": str(result)
})

final_message = llm_client.chat_with_tools(
    messages,
    TOOLS_SCHEMA
)

print(final_message.content)