import asyncio
from typing import override

from semantic_kernel.agents import Agent, ChatCompletionAgent, GroupChatOrchestration
from semantic_kernel.agents.orchestration.group_chat import BooleanResult, RoundRobinGroupChatManager
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent

from semantic_kernel.agents import AzureResponsesAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings

from config import AOAI_API_KEY, AOAI_ENDPOINT, AOAI_CHAT_DEPLOYMENT_NAME, API_VERSION

def get_agents () -> list[Agent]:
    client = AzureResponsesAgent.create_client(
        deployment_name=AOAI_CHAT_DEPLOYMENT_NAME,  
        api_key=AOAI_API_KEY,
        endpoint=AOAI_ENDPOINT
    )

    web_search_tool = AzureResponsesAgent.configure_web_search_tool()
    writer = AzureResponsesAgent(
        ai_model_id=AOAI_CHAT_DEPLOYMENT_NAME,
        client=client,
        instructions="You are a writer agent. Generate text based on the provided prompts.",
        description="You are a writer agent that generates text based on the provided prompts.",
        name="Writer",
        tools=[web_search_tool],
    )
    
    reviewer = ChatCompletionAgent(
        name="Reviewer",
        description="You are a content reviewer",
        instructions="You are an excellent content reviewer. You review the content and provide feedback to the writer",
        service=AzureChatCompletion(
            deployment_name=AOAI_CHAT_DEPLOYMENT_NAME,  
            api_key=AOAI_API_KEY,
            endpoint=AOAI_ENDPOINT
        ),
    )

    return [writer, reviewer]

class CustomRoundRobinGroupChatManager(RoundRobinGroupChatManager):
    """Custom round robin group chat manager to enable user input."""

    @override
    async def should_request_user_input(self, chat_history: ChatHistory) -> BooleanResult:
        """Override the default behavior to request user input after the reviewer's message.

        The manager will check if input from human is needed after each agent message.
        """
        if len(chat_history.messages) == 0:
            return BooleanResult(
                result=False,
                reason="No agents have spoken yet.",
            )
        last_message = chat_history.messages[-1]
        if last_message.name == "Reviewer":
            return BooleanResult(
                result=True,
                reason="User input is needed after the reviewer's message.",
            )

        return BooleanResult(
            result=False,
            reason="User input is not needed if the last message is not from the reviewer.",
        )



def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents."""
    print(f"**{message.name}**\n{message.content}")


async def human_response_function(chat_histoy: ChatHistory) -> ChatMessageContent:
    """Function to get user input."""
    user_input = input("User: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)

async def main():
    """Main function to run the agents."""
    # 1. Create a group chat orchestration with a round robin manager
    agents = get_agents()
    group_chat_orchestration = GroupChatOrchestration(
        members=agents,
        # max_rounds is odd, so that the writer gets the last round
        manager=CustomRoundRobinGroupChatManager(
            max_rounds=5,
            human_response_function=human_response_function,
        ),
        agent_response_callback=agent_response_callback,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await group_chat_orchestration.invoke(
        task="write a report on FY2024 L&T performance",
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get()
    print(f"***** Result *****\n{value}")

    # 5. Stop the runtime after the invocation is complete
    await runtime.stop_when_idle()

if __name__ == "__main__":
    asyncio.run(main())