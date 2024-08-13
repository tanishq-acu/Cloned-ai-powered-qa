from ai_powered_qa.components.agent import Agent
from ai_powered_qa.components.plugin import RandomNumberPlugin
from ai_powered_qa.custom_plugins.playwright_plugin.base import PlaywrightPlugin
from ai_powered_qa.components.agent_store import AgentStore
from ai_powered_qa.ui_common.load_agent import NAME_TO_PLUGIN_CLASS
import json
def run_agent_on_url(url: str, prompt: str):
    agent_store = AgentStore(
        "agents",
        name_to_plugin_class=NAME_TO_PLUGIN_CLASS,
    )
    agent_name = "acuvity_qa_agent"
    playwright_plugin_name = "PlaywrightPluginOnlyVisible"
    agent = agent_store.load_agent(
        agent_name,
        default_kwargs={
            "model": "gpt-4o",
            "plugins": {
                playwright_plugin_name: NAME_TO_PLUGIN_CLASS[playwright_plugin_name](),
            },
        },
    )
    full_prompt = f"Reminder: Make sure you wait() as many times as needed until the page loads, and be persistent with trying to pass the test case, ensuring your assertion selectors are broad. Now, Please go to {url.strip()} and do the following: {prompt.strip()}"
    interaction = agent.generate_interaction(full_prompt)
    max_iter = 40
    while(max_iter > 0 and interaction.agent_response.tool_calls and not any(
        tool_call.function.name == "finish" for tool_call in interaction.agent_response.tool_calls
        )
    ):
        max_iter -=1 
        agent_store.save_interaction(agent, agent.commit_interaction(interaction=interaction))
        agent_store.save_history(agent)
        interaction = agent.generate_interaction()
    if(interaction.agent_response.tool_calls):
        if (any(tool_call.function.name == "finish" for tool_call in interaction.agent_response.tool_calls)):
            return agent.history_name
        else:
            raise RuntimeError("Agent failed to complete task.")
    return agent.history_name