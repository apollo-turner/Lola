from langchain.agents import initialize_agent
from langchain_community.tools import QuerySQLDataBaseTool
from database.db import db
from models.llm import llm

tools = [QuerySQLDataBaseTool(db=db)]

agent = initialize_agent(
    tools, llm, agent="zero-shot-react-description", verbose=True
)

def run_lola(query):
    return agent.run(query)
