## sample custom tool (function)
import asyncio
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
from typing import Annotated
from pydantic import Field, BaseModel

class WeatherTools:
    def __init__(self):
        self.last_location = None

    def get_weather(
        self,
        location: Annotated[str, Field(description="The location to get the weather for.")],
    ) -> str:
        """Get the weather for a given location."""
        return f"The weather in {location} is cloudy with a high of 15°C."

    def get_weather_details(self) -> int:
        """Get the detailed weather for the last requested location."""
        if self.last_location is None:
            return "No location specified yet."
        return f"The detailed weather in {self.last_location} is cloudy with a high of 15°C, low of 7°C, and 60% humidity."

tools = WeatherTools()
agent = AzureOpenAIChatClient(credential=AzureCliCredential()).create_agent(
    instructions="You are a helpful assistant",
    tools=[tools.get_weather, tools.get_weather_details]
)


# Agent with structured response
class WeatherResponse(BaseModel):
    """Information about the weather."""
    location: str | None = None
    temperature: float | None = None

async def main():
    async for update in agent.run("What is the weather like in Amsterdam", response_type=WeatherResponse):
        if update.text:
            print(update.text, end="", flush=True)
    print() 

asyncio.run(main())

# # We can use an agent as a tool as well from another agent just similar to foundry connected agents
# from agent_framework.azure import AzureOpenAIChatClient
# from azure.identity import AzureCliCredential

# weather_agent = AzureOpenAIChatClient(credential=AzureCliCredential()).create_agent(
#     name="WeatherAgent",
#     description="An agent that answers questions about the weather.",
#     instructions="You answer questions about the weather.",
#     tools=get_weather
# )

# main_agent = AzureOpenAIChatClient(credential=AzureCliCredential()).create_agent(
#     instructions="You are a helpful assistant who responds in French.",
#     tools=weather_agent.as_tool()
# )