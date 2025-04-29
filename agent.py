from llama_index.core.agent.workflow import FunctionAgent, AgentWorkflow
from linkup import LinkupClient
from pydantic import BaseModel, Field
from data import vector_index, llm, embed_model, Settings
from llama_index.core.indices.query.query_transform.base import HyDEQueryTransform
from llama_index.core.query_engine import TransformQueryEngine
from llama_index.core.evaluation import CorrectnessEvaluator, FaithfulnessEvaluator, RelevancyEvaluator

with open("/run/secrets/linkup_key") as f:
    linkup_api_key = f.read()
f.close()

Settings.llm = llm
Settings.embed_model = embed_model

class CodeSolution(BaseModel):
    code_solution: str | None = Field(description="Code snippet that solves the problem of the user. Set to None if the code snippet is not necessary")
    explanation: str = Field(description="Explanation to solve the coding problem")

class EvaluationOutput(BaseModel):
    correctness: float | None
    relevancy: float | None
    faithfulness: float | None

linkup_client = LinkupClient(api_key=linkup_api_key)
qe = vector_index.as_query_engine()
qt = HyDEQueryTransform()
tqe = TransformQueryEngine(query_engine=qe,query_transform=qt)

evaluator_c = CorrectnessEvaluator()
evaluator_f = FaithfulnessEvaluator()
evaluator_r = RelevancyEvaluator()

async def evaluate_response(original_query: str = Field(description="User's original query"), retrieved_context: str = Field(description="Retrieved context, either from the web or from the vector database"), response: str = Field(description="Response to be evaluated")):
    f = await evaluator_f.aevaluate(query = original_query, contexts = [retrieved_context], response = response)
    c = await evaluator_c.aevaluate(query = original_query, contexts = [retrieved_context], response = response)
    r = await evaluator_r.aevaluate(query = original_query, contexts = [retrieved_context], response = response)
    return EvaluationOutput(correctness=c.score, faithfulness=f.score, relevancy=r.score).model_dump_json(indent=4)
    
async def web_search_tool(query: str = Field(description="The query, related to the user code problem, with which to search the web for a solution")):
    """
    Useful for performing web searches related to user code problems.

    This tool queries the web for solutions to coding issues using the provided query string.
    Performs a deep, structured search and returns either a formatted code solution with an explanation or just the explanation if no code solution is found.

    Args:
        query (str): The search query describing the user's code problem.
    """
    search_results = await linkup_client.async_search(query=query, depth="deep", output_type="structured", structured_output_schema=CodeSolution)
    c = f"Code Solution:\n\n{search_results.code_solution}\n\nExplanation:\n\n{search_results.explanation}" if search_results.code_solution is not None else search_results.explanation
    return c

async def vector_search_tool(query: str = Field(description="The query with which to search a vector database that contains an entire codebase of programming exercises")):
    """
    Useful to search for information within a vector database that contains an entire codebase of programming exercises.

    This tools searches a vector database containing a codebase of programming exercises using the provided query.

    Args:
        query (str): The query string used to search the vector database.
    """
    res = await tqe.aquery(query)
    return res.response

agent = FunctionAgent(
    name = "CodeAssistAgent",
    description="Useful for resolving programming questions with access to the web, a vector database of programming exercises, and evaluation tools.",
    system_prompt=(
        "You are CodeAssistAgent, an expert programming assistant. "
        "You have access to three tools:\n"
        "1. vector_search_tool: Use this to search a vector database containing a large codebase of programming exercises. "
        "It is best for finding code examples, explanations, or solutions from the codebase.\n"
        "2. web_search_tool: Use this to search the web for solutions to coding problems. "
        "It is best for finding up-to-date information, external code snippets, or explanations not found in the codebase.\n"
        "3. evaluate_response: Use this to evaluate the correctness, faithfulness, and relevancy of a response given the original query and retrieved context. You should always use this tool.\n"
        "Choose the most appropriate tool based on the user's query. "
        "Always provide clear, concise, and accurate answers. "
        "If code is required, include a code snippet and an explanation."
        "You should always use the evaluate_response tool."
    ),
    tools = [vector_search_tool, web_search_tool, evaluate_response],
)

workflow = AgentWorkflow(
    agents = [agent],
    root_agent = agent.name
)

