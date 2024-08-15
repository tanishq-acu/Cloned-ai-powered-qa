from ai_powered_qa.components.agent import Agent
from ai_powered_qa.components.plugin import RandomNumberPlugin
from ai_powered_qa.custom_plugins.playwright_plugin.base import PlaywrightPlugin
from ai_powered_qa.components.agent_store import AgentStore
from ai_powered_qa.ui_common.constants import AGENT_INSTANCE_KEY
from ai_powered_qa.ui_common.load_agent import NAME_TO_PLUGIN_CLASS
import json
def test_agent_playwright_response():
    agent = Agent(agent_name="test_agent_with_playwright")
    plugin = PlaywrightPlugin()
    agent.add_plugin(plugin)
    assert len(agent.plugins) == 1
    completion = agent.generate_interaction("Can you open google.com?")
    assert completion.agent_response.tool_calls[0].function.name == "navigate"
    agent.commit_interaction(interaction=completion)
    assert agent.plugins["PlaywrightPlugin"]._pages._page.url == "https://www.google.com/"
    completion = agent.generate_interaction()  # Agent reacts to the tool call
    plugin.close()


def test_agent_with_rng():
    agent = Agent(agent_name="test_agent_with_rng")
    agent.add_plugin(RandomNumberPlugin())
    assert len(agent.plugins) == 1
    interaction = agent.generate_interaction(
        "Please generate a random number between 1 and 10"
    )
    agent_response = interaction.agent_response
    assert agent_response.tool_calls[0].function.name == "get_random_number"
    agent.commit_interaction(interaction)
    assert len(agent.history) == 3


# Flaky with gpt-3.5
# def test_agent_parallel_tool_call():
#     agent = Agent(agent_name="test_agent_parallel_tool_call")
#     plugin = PlaywrightPlugin()
#     agent.add_plugin(plugin)
#     completion = agent.generate_interaction(
#         "Navigate to gmail, youtube and google.com")
#     assert len(completion.agent_response.tool_calls) == 3
#     plugin.close()


def test_agent_init():
    agent = Agent(agent_name="test_agent_init")
    assert agent.agent_name == "test_agent_init"


def test_agent_version_number():
    # Initialize agent
    agent = Agent(agent_name="test_agent_get_completion")
    assert agent.version == 0

    # Changing system_message increments the version
    agent.system_message = "You are a super helpful assistant"
    assert agent.version == 1

    # Adding a plugin increments the version
    agent.add_plugin(RandomNumberPlugin())
    assert agent.version == 2

    # Commiting an interaction does not increment the version (and doesn't change the hash)
    hash_before = agent.hash
    interaction = agent.generate_interaction(
        "Please generate a random number between 1 and 10"
    )
    agent.commit_interaction(interaction)
    # fake changing the system message to make sure hash computation got triggered
    agent.system_message = "You are a super helpful assistant"
    assert agent.version == 2
    assert agent.hash == hash_before
def test_agent_qa():
    agent_store = AgentStore(
        "agents",
        name_to_plugin_class=NAME_TO_PLUGIN_CLASS,
    )
    agent_name = "acuvity_qa_agent"
    playwright_plugin_name = "PlaywrightPluginOnlyVisible"
    _agent = agent_store.load_agent(
        agent_name,
        default_kwargs={
            "model": "gpt-4o",
            "plugins": {
                playwright_plugin_name: NAME_TO_PLUGIN_CLASS[playwright_plugin_name](),
            },
        },
    )
    agent = _agent
    inFilePath = "./tests/tests.txt"

    infile = open(inFilePath, "r")
    lines = infile.readlines()
    for line in lines:
        prompt = f"Reminder: Make sure you wait() as many times as needed until the page loads, and be persistent with trying to pass the test case. Now, Please go to {line.strip()} and verify that when you send a message, you receive a response."
        interaction = agent.generate_interaction(prompt)
        ### Start output
        if interaction.agent_response.content:
            print("Assistant:" + interaction.agent_response.content + "\n")
            if interaction.agent_response.tool_calls:
                for tool_call in interaction.agent_response.tool_calls:
                    print("Function arguments:" + json.loads(tool_call.function.arguments) + "\n")
        ### end output
        max_iter = 25
        while(max_iter > 0 and interaction.agent_response.tool_calls and not any(
            tool_call.function.name == "finish" for tool_call in interaction.agent_response.tool_calls
            )
        ):
            max_iter -=1 
            agent_store.save_interaction(agent, agent.commit_interaction(interaction=interaction))
            agent_store.save_history(agent)
            interaction = agent.generate_interaction()
            ### Start output:
            if interaction.tool_responses is not None:
                for tool_call in interaction.tool_responses:
                    print(f"Tool call: {tool_call["content"]}\n")
            if interaction.agent_response.content:
                print(f"Assistant: {interaction.agent_response.content}\n")
            if interaction.agent_response.tool_calls:
                 for tool_call in interaction.agent_response.tool_calls:
                    print(f"Function arguments: {json.loads(tool_call.function.arguments)}\n")
            ### End output
        if(interaction.agent_response.tool_calls):
            assert(any(tool_call.function.name == "finish" for tool_call in interaction.agent_response.tool_calls))
                
            


