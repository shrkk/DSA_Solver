import asyncio
from autogen_agentchat.agents import CodeExecutorAgent, AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

model_client = OpenAIChatCompletionClient(
    model="gpt-3.5-turbo",
    api_key=api_key
)

async def main():
    docker = DockerCommandLineCodeExecutor(
        work_dir='/tmp',
        timeout=120
    )

    code_executor_agent = CodeExecutorAgent(
        name="CodeExecutorAgent",
        code_executor=docker
    )

    problem_solver_agent = AssistantAgent(
        name="DSA_Problem_Solver_Agent",
        description="An agent that solves DSA problems and sends code to executor",
        model_client=model_client,
        system_message="""You are a DSA problem solver working with a code execution agent.

Your job:
1. Read the problem statement.
2. Outline a clear step-by-step plan at the beginning of your response.
3. Provide Python code in a single triple-backticked code block with 'python'.
4. Always include at least 3 test cases in the code.
5. Show the Code Executor Agent output of the test cases.
6. If the code runs successfully and meets requirements, say exactly 'STOP' on a separate line to end the conversation.

Rules:
- Only one code block per response.
- No explanations inside the code block.
- Assume the code will be sent directly to CodeExecutorAgent for execution.
"""
    )

    termination_condition = TextMentionTermination(text="STOP")

    team = RoundRobinGroupChat(
        participants=[problem_solver_agent, code_executor_agent],
        termination_condition=termination_condition,
        max_turns=10
    )

    try:
        await docker.start()
        task = "Write python code to reverse a singly-linked list"

        async for message in team.run_stream(task=task):
            if isinstance(message, TextMessage):
                print(f"{message.source}:\n{message.content}\n")
            elif isinstance(message, TaskResult):
                print("Stop Reason:", message.stop_reason)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await docker.stop()

if __name__ == "__main__":
    asyncio.run(main())
