from typing import Sequence, TypedDict, List, Union, Annotated
from dotenv import load_dotenv  
from langchain_core.messages import BaseMessage
from langchain_core.messages import ToolMessage
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from datetime import datetime

import asyncio
from kuksa_client.grpc.aio import VSSClient
from kuksa_client.grpc import Datapoint

#import pygame
#from gtts import gTTS
import os
import time

import json

load_dotenv()

try:
    with open('define.json') as F:
        configure = json.load(F)
except Exception as e:
    print("Error: " , e)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

vss = VSSClient(configure["ip_address"], configure["port"])


# tool call and funtion to support it
#-----------------------------------#
async def target_value_teller(api: str):
    try:
        async with vss as client:
            display_value = await client.get_target_values([api])
            if api in display_value and display_value[api].value is not None:
                value = display_value[api].value
                if isinstance(value, bool):
                    return "On" if value else "Off"
                elif isinstance(value, int):
                    return value
                else:
                    return str(value)
            else:
                return f"Current state of {api} is not available"
    except Exception as e:
        return f"Failed to tell {api} value: {e}"


async def target_value_setter(type: str, new_state: Union[bool, int, str]):
    try:
        async with vss as client:
            success = await client.set_target_values({
                f"{type}": Datapoint(new_state)
            })
            return success
    except:
        return f"Failed to set {type} value to {new_state}"

@tool
def setter(api: str, value: Union[bool, int, str]):
    """
        Tool to set the vehicle lights.
        Tool to check what kind of vehicle value the user want to change. there are multiple types of api for you to choose.
        Choose the api based on the user demand
        Args:
            api (str): the api acording to user demand.
            value (bool/int/str): The state of it depend on what user said, it can be boolean, int or string.
    """
    result = asyncio.run(target_value_setter(api, value))
    
    return result

@tool
def teller(api: str):
    """ Tool to check what kind of vehicle value the user want to check. there are multiple types of api for you to choose.
        Choose the api based on the user demand.
        Args:
            api (str): the api according to user demand.
    """
    state = asyncio.run(target_value_teller(api))
    return state

@tool
def time_teller():
    """Returns the current time."""
    return datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

tools = [time_teller, teller, setter]


# defining model for tool calling
#--------------------------------#
try:
    model = ChatOllama(model = configure['tool_model']).bind_tools(tools)
    llm = ChatOllama(model = configure['com_model'])
    model1 = ChatOllama(model = configure['api_detect_model'])
    print("✅ AI model is ready")
except:
    print("There is something wrong with AI model")


# importing model to call API
#----------------------------#
from langchain_core.prompts import ChatPromptTemplate
from fine_vector import retriever

template = """
    You are an exeprt in answering questions about a vehicle.

    Always find the correct API path from the vehicle API CSV that matches the user's request.  
    - Use the 'prefer_name' column to identify the API path first, as it provides the most human-friendly description.  
    - If multiple APIs match, choose the most relevant one based on the user's request. 
    
    If they ask for api then prioritize giving the whole api and you should you "." in api not "/", however answer as straight to the point as posible.
    
    If they want to change the state of the vehicle or status of vehicle attachment tool then answer arcoding to the example.

    Here are some relevant infor: {information}

    Here is the question to answer: {question}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model1


def model_call(state: AgentState) -> AgentState:

    last_user_input = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_input = msg.content.lower()
            break

    allowed_keywords = ["time", "date", "set", "change", "turn", "status"]

    is_tool_needed = any(keyword in last_user_input for keyword in allowed_keywords)

    if is_tool_needed:
        last_message = state['messages'][-1].content
        information = retriever.invoke(last_message)
            
        # Assign result to response
        response = chain.invoke({
            "information": information,
            "question": last_message,
        })
        system_prompt = SystemMessage(content= f"""
            The api which user mention will be determine by another ai, and the api and the type are {response}. and there for you don't need to detect api yourself.
            If the user demand you to change or to alter vehicle value, then call tool 'setter'. However, enable to make the tool work, you need to detect the vehicle api and the value user want to change into.
            
            If the user want you to tell them the specific state of vehicle value then you should call 'teller'. This tool only demand you to detect the vehicle api to make it work.
            
            If the user ask you to set or to change vehicle value to 100 then make sure to pass 100 as int to 'setter' tool. However, if user ask you to 'turn on' vehicle value which is suppose to be int like 'passenger fan speed' or 'driver fan speed' then pass value as 100
            
            If the user asking anything about the 'time' including 'month', 'day', 'minnute', 'hour',... then call tool 'time_teller'.

            After calling tool, the tool will give the result back to confirm that the tool calling work or not. Therefore, answer base on that but answer as straight forward as possible.
        """)

        response = model.invoke([configure["name"]] + [configure["definition"]] + [system_prompt] + state["messages"])
        print("Thinking...")

        if hasattr(response, "tool_calls") and response.tool_calls:
            print("\nAI is making a tool call")
            for call in response.tool_calls:
                print(f"→ Tool: {call['name']}, Arguments: {call['args']}")
        else:
            #speech(response.content)
            print("\nAI: ", response.content)

        state["messages"].append(response)
        return state
    else:
        response = llm.stream([configure["name"]] + [configure["definition"]] + state["messages"])
        full_response = ""
        print("Thinking... ")
        frist_res = False

        if response:
            for res in response:
                if not frist_res:
                    frist_res = True
                    print("\nAI: ", end="" , flush= True)
                print(res.content, end="", flush=True)
                full_response += res.content
            try:
                #check_json = json.loads(full_response)
                state["messages"].append(AIMessage(content= "Failed"))
            except (ValueError, TypeError):
                #speech(full_response)
                state["messages"].append(AIMessage(content= full_response))
        else:
            print("\nAI: [No meaningful response generated]")

        return state


def should_continue(state: AgentState): 
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls: 
        return "tools"
    else:
        return "end"
    
graph = StateGraph(AgentState)
graph.add_edge("tools", "our_agent")
graph.add_node("our_agent", model_call)

tool_node = ToolNode(tools=tools)
graph.add_node("tools", tool_node)

graph.set_entry_point("our_agent")

graph.add_conditional_edges(
    "our_agent",
    should_continue,
    {
        "tools": "tools",
        "end": END,
    },
)

graph.add_edge(START, "our_agent")
graph.add_edge("our_agent", END)

agent = graph.compile()

history = []

agent.invoke({"messages": [HumanMessage(content= "Hello")]})

while True:
    user_input = input("\nEnter: ")

    if user_input in ["end", "exit", "clode", "goodbye"]:
        print("Turning model off...")
        break
    history.append(HumanMessage(content= user_input))
    result = agent.invoke({"messages" : history})
    history = result["messages"]

print(f"\n✅ Successfull turn model {configure['tool_model']}, {configure['com_model']} and {configure['api_detect_model']}")
