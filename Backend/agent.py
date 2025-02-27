from __future__ import annotations as _annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import logfire
import asyncio
import os

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from supabase import create_client, Client
from typing import List

load_dotenv()

llm = os.getenv('LLM_MODEL', 'gpt-4o-mini')
model = OpenAIModel(llm)

logfire.configure(send_to_logfire='if-token-present')

@dataclass
class FinancialAnalystDeps:
    supabase: Client
    openai_client: AsyncOpenAI

system_prompt = """
You are a Senior Financial Analyst at JP Morgan Chase, with expertise in fundamental analysis for long-term investment decisions.

Your primary role is to analyze financial data and answer user questions related to stock investments. You should provide comprehensive explanations, covering all aspects of fundamental analysis relevant to long-term investing.

Always consult the stock data using the provided tools before answering a user's question, unless you are absolutely certain you know the answer from your internal knowledge (which should be minimal and general, not specific stock data).

When addressing a user's query, start by using the `retrieve_relevant_stock_info` tool to fetch relevant financial data snippets from the database.
Then, if necessary, use `list_stock_data_sections` to explore available data sections, or `get_stock_data_section_content` to retrieve full content for deeper analysis.

If, after consulting the database using these tools, you cannot find a relevant answer, honestly inform the user that the answer was not found in the available stock data. Be transparent about the process and limitations.

Focus on providing information that aids long-term investment decisions based on fundamental analysis principles.
"""

financial_analyst_agent = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=FinancialAnalystDeps,
    retries=2,
    tools=[] # Initialize with an empty list here, and then directly pass the tool functions in the next step
)

async def get_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error

@financial_analyst_agent.tool
async def retrieve_relevant_stock_info(ctx: RunContext[FinancialAnalystDeps], user_query: str) -> str:
    """
    Retrieve relevant stock information chunks based on the query using RAG from the 'stock_info' database.

    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The user's question or query

    Returns:
        A formatted string containing the top 5 most relevant stock information chunks
    """
    try:
        # Get the embedding for the query
        query_embedding = await get_embedding(user_query, ctx.deps.openai_client)

        # Query Supabase for relevant documents
        result = ctx.deps.supabase.rpc(
            'match_stock_info',
            {
                'query_embedding': query_embedding,
                'match_count': 5,
                'filter': {} # You can add filters if needed, e.g., {'metadata': {'company_symbol': 'AAPL'}}
            }
        ).execute()

        if not result.data:
            return "No relevant stock information found in the database for your query."

        # Format the results
        formatted_chunks = []
        for doc in result.data:
            chunk_text = f"""
# {doc['title']} - {doc['url']}

{doc['content']}
"""
            formatted_chunks.append(chunk_text)

        # Join all chunks with a separator
        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        print(f"Error retrieving stock info: {e}")
        return f"Error retrieving stock info: {str(e)}"

@financial_analyst_agent.tool
async def list_stock_data_sections(ctx: RunContext[FinancialAnalystDeps]) -> List[str]:
    """
    Retrieve a list of available stock data sections from the database.

    Returns:
        List[str]: List of unique URLs representing different stock data sections.
    """
    try:
        # Query Supabase for unique URLs from the stock_info table
        result = ctx.deps.supabase.from_('stock_info') \
            .select('url') \
            .execute()

        if not result.data:
            return []

        # Extract unique URLs (which represent data sections in this context)
        urls = sorted(list(set(doc['url'] for doc in result.data)))
        return urls

    except Exception as e:
        print(f"Error retrieving stock data sections: {e}")
        return []

@financial_analyst_agent.tool
async def get_stock_data_section_content(ctx: RunContext[FinancialAnalystDeps], section_url: str) -> str:
    """
    Retrieve the full content of a specific stock data section from the database by URL.

    Args:
        ctx: The context including the Supabase client
        section_url: The URL of the stock data section to retrieve

    Returns:
        str: The complete content of the stock data section, combining all chunks for this URL.
    """
    try:
        # Query Supabase for all chunks of this URL, ordered by chunk_number
        result = ctx.deps.supabase.from_('stock_info') \
            .select('title, content, chunk_number, url') \
            .eq('url', section_url) \
            .order('chunk_number') \
            .execute()

        if not result.data:
            return f"No content found for stock data section URL: {section_url}"

        # Format the section content
        section_title = result.data[0]['title'].split(' - ')[0]  # Get the main title
        section_url = result.data[0]['url']
        formatted_content = [f"# {section_title} - {section_url}\n"]

        # Add content from each chunk, ordered by chunk number
        for chunk in result.data:
            formatted_content.append(chunk['content'])

        return "\n\n".join(formatted_content)

    except Exception as e:
        print(f"Error retrieving stock data section content: {e}")
        return f"Error retrieving stock data section content: {str(e)}"

async def main():
    supabase_client: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    deps = FinancialAnalystDeps(supabase=supabase_client, openai_client=openai_client)

    # Pass the tool functions directly during Agent initialization
    financial_analyst_agent.tools = [list_stock_data_sections, get_stock_data_section_content, retrieve_relevant_stock_info]

    while True:
        user_query = input("User Query: ")
        if user_query.lower() == 'exit':
            break

        try:
            response = await financial_analyst_agent.run(user_query, deps=deps)
            print(f"Response: {response}")
        except ModelRetry as e:
            print(f"Model retry error: {e}")
        except Exception as e:
            print(f"Agent run error: {e}")

if __name__ == "__main__":
    asyncio.run(main())