import os
import asyncio
from pydantic_ai import Agent
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from dotenv import load_dotenv

import json
import re

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key as an environment variable
openai_api_key = os.environ.get("OPENAI_API_KEY")

async def main():
    async with AsyncWebCrawler() as crawler:
        # Configure CrawlerRunConfig with css_selector
        config = CrawlerRunConfig(
            css_selector=".concalls",
            cache_mode=CacheMode.BYPASS
        )

        result = await crawler.arun(
            url=f"https://www.screener.in/company/ENGINERSIN/",
            config=config
        )
    
        print(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())