#!/usr/bin/env python
"""
M01 demo -- one grounded Foundry agent that makes ALL FOUR Lesson 1 decisions.

AI-103 Lesson 1 is about four choices. Rather than four toy scripts, this builds the
ONE artifact those choices produce -- a small support agent -- the way AI-103 actually
ships: with the Microsoft Agent Framework on Microsoft Foundry. (This is the current,
GA path. The classic create_agent / thread / run agent API is deprecated and retires
in 2027, so we deliberately do not use it.)

Each decision is one ingredient, and they map straight onto the lesson's own slides
("an agent is memory + tools + knowledge, with guardrails"):

  LO1  choose a MODEL ............ the agent reasons with FOUNDRY_MODEL, a capable LLM.
                                   (A small model like Phi-4 would be the call for an
                                   edge or low-latency job; here we want real reasoning.)
  LO2  choose a SERVICE .......... the Agents service via FoundryChatClient -- because
                                   the work needs tools and state, not stateless chat.
  LO3  choose RETRIEVAL .......... ground the agent on a knowledge file with the
                                   file-search tool (a managed vector store).
  LO4  MEMORY + TOOLS + KNOWLEDGE  a conversation thread (memory), a custom @tool
                                   (tool), the file-search knowledge source, and an
                                   approval gate on the tool (the guardrail).

Setup:  pip install -r requirements.txt  ;  az login  ;  copy .env.example to .env
Run:    python m01_agent_demo.py

Author: Tim Warner (TechTrainerTim.com) | Microsoft Press AI-103 video course
"""

import asyncio
import contextlib
import os
import sys
from typing import Annotated

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from pydantic import Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# A tiny knowledge base the agent will ground on. In production this is your real
# corpus (policies, manuals, tickets); one line keeps the demo self-contained.
KB_FILENAME = "globomantics_policy.txt"
KB_CONTENT = (
    b"Globomantics support policy: customers on the Premium plan are entitled to a full "
    b"refund within 30 days of purchase. Standard plan refunds are issued as store credit only."
)


# ---- LO4: a custom TOOL, with an approval gate (the guardrail from the slides) ----
# approval_mode="never_require" keeps the demo flowing; use "always_require" in
# production so a human approves any sensitive action before it runs.
@tool(approval_mode="never_require")
def open_refund_ticket(
    customer: Annotated[str, Field(description="Customer name.")],
    amount_usd: Annotated[float, Field(description="Refund amount in US dollars.")],
) -> str:
    """Open a refund ticket for a customer and return the ticket id."""
    # A real tool would call your ticketing API here.
    return f"Ticket RF-{abs(hash(customer)) % 10000:04d} opened for {customer}: ${amount_usd:.2f} refund queued."


def required_env(name: str, hint: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"ERROR: environment variable {name} is not set.\n  -> {hint}\n  See .env.example.")
    return value


async def main() -> None:
    # LO1 -- the MODEL. The agent reasons with the deployment named in FOUNDRY_MODEL.
    model = required_env("FOUNDRY_MODEL", "your chat model deployment name, e.g. gpt-5.1")
    # FoundryChatClient reads FOUNDRY_PROJECT_ENDPOINT from the environment; validate it early.
    required_env("FOUNDRY_PROJECT_ENDPOINT", "https://<resource>.services.ai.azure.com/api/projects/<project>")
    print(f"LO1  model       : {model}  (capable LLM for agent reasoning)")

    # LO2 -- the SERVICE. FoundryChatClient is the Foundry Agents service via the Microsoft
    # Agent Framework, with keyless Entra ID auth (az login). Stateless chat completions
    # could not do the grounding + tool-calling below; that is exactly why we pick agents.
    client = FoundryChatClient(credential=AzureCliCredential())
    print("LO2  service     : Microsoft Foundry Agents (Agent Framework), keyless auth")

    # LO3 -- RETRIEVAL. Upload a knowledge file, index it into a managed vector store,
    # and expose it as a file-search tool the agent grounds its answers on.
    file = await client.client.files.create(file=(KB_FILENAME, KB_CONTENT), purpose="assistants")
    vstore = await client.client.vector_stores.create(
        name="m01-kb", expires_after={"anchor": "last_active_at", "days": 1}
    )
    await client.client.vector_stores.files.create_and_poll(vector_store_id=vstore.id, file_id=file.id)
    file_search = client.get_file_search_tool(vector_store_ids=[vstore.id])
    print("LO3  retrieval   : file-search grounding over a managed vector store")

    # LO4 -- assemble the agent from MEMORY + TOOLS + KNOWLEDGE (+ the guardrail).
    agent = Agent(
        client=client,
        instructions=(
            "You are Globomantics' support agent. Ground every policy answer in the refund "
            "policy via file search, and open a refund ticket with your tool when a refund applies."
        ),
        tools=[file_search, open_refund_ticket],
    )
    thread = None
    with contextlib.suppress(Exception):
        thread = agent.get_new_thread()  # memory: the thread carries conversation state
    print("LO4  integration : thread (memory) + custom tool + knowledge source + approval gate")
    print("=" * 72)

    # Turn 1 forces RETRIEVAL (read the policy) and the TOOL (open the ticket).
    q1 = ("I'm Dana Lee, a Premium customer. I bought 22 days ago for $80 and want a "
          "refund. Do I qualify, and if so please process it.")
    print(f"\nUser: {q1}")
    print(f"Agent: {await agent.run(q1, thread=thread)}")

    # Turn 2 forces MEMORY: the name and amount are not repeated, so the agent must
    # recall them from the thread.
    q2 = "Remind me which plan I'm on and what refund you just queued for me."
    print(f"\nUser: {q2}")
    print(f"Agent: {await agent.run(q2, thread=thread)}")

    print("\n" + "=" * 72)
    print("One agent, four decisions: model (LO1), Agents service (LO2), grounded")
    print("retrieval (LO3), and memory + tool + knowledge integration (LO4).")

    # Tidy up the managed vector store and file.
    with contextlib.suppress(Exception):
        await client.client.vector_stores.delete(vector_store_id=vstore.id)
        await client.client.files.delete(file_id=file.id)


if __name__ == "__main__":
    asyncio.run(main())
