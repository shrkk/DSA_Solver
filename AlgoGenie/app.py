import streamlit as st
from team.dsa_team import get_dsa_team_and_docker   
from config.docker_utils import start_docker_container, stop_docker_container 
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult
import asyncio


st.title("AlgoGenie -- Your DSA Problem Solver")
st.write("Welcome to AlgoGenie, your go-to solution for all Data Structures and Algorithms problems!")

task = st.text_input("Enter your DSA problem statement here:")

if st.button("Run"):
    st.write("Solving your problem...")
    team, docker = get_dsa_team_and_docker()

    async def collect_messages():
        await start_docker_container(docker)
        code_block = None
        test_cases = []
        chat_history = []
        test_results = []
        try:
            async for message in team.run_stream(task=task):
                if isinstance(message, TextMessage):
                    # Save chat history for display
                    chat_history.append((message.source, message.content))
                    # Extract code block (first python block only)
                    if code_block is None and (
                        message.content.strip().startswith("python") or message.content.strip().startswith("```")
                    ):
                        # Remove leading "python" if present
                        code_block = message.content.replace("python\n", "").strip("`")
                    # Extract test cases (simple heuristic: lines with 'print' or 'Test Case')
                    elif code_block and ("test case" in message.content.lower() or "print" in message.content):
                        test_cases.append(message.content)
                    # Extract test results (from CodeExecutorAgent)
                    elif message.source.lower().startswith("codeexecutoragent"):
                        test_results.append(message.content)
                elif isinstance(message, TaskResult):
                    chat_history.append(("System", f"Stop Reason: {message.stop_reason}"))
        finally:
            await stop_docker_container(docker)
        return chat_history, code_block, test_cases, test_results

    chat_history, code_block, test_cases, test_results = asyncio.run(collect_messages())

    # Display chat history
    st.subheader("Agent Conversation")
    for source, content in chat_history:
        with st.chat_message(source if source != "user" else "User"):
            # Show code blocks as code, rest as markdown
            if content.strip().startswith("python") or content.strip().startswith("```"):
                st.code(content.replace("python\n", ""), language="python")
            else:
                st.markdown(content)

    # Display generated code
    if code_block:
        st.subheader("Generated Code")
        st.code(code_block, language="python")

    # Display test cases separately
    if test_cases:
        st.subheader("Test Cases")
        for tc in test_cases:
            st.markdown(tc)

    # Display test results after code and test cases
    if test_results:
        st.subheader("Test Results")
        for result in test_results:
            st.markdown(result)
