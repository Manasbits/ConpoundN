import os
import asyncio
from pydantic_ai import Agent
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from dotenv import load_dotenv

import json

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key as an environment variable
openai_api_key = os.environ.get("OPENAI_API_KEY")

def parse_basic_data(markdown_text):
    """Parses the basic data markdown text into a JSON object.
       Returns JSON object if parsing is successful, otherwise returns None.
    """
    basic_data_json = {}
    try:
        lines = markdown_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("* "):
                parts = line[2:].split('  ', 1)  # Split after the first "  "
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    basic_data_json[key] = value
        return basic_data_json
    except Exception:
        return None  # Return None if parsing fails


async def main():
    async with AsyncWebCrawler() as crawler:
        # Configure CrawlerRunConfig with css_selector
        config = CrawlerRunConfig(
            css_selector="#top-ratios",
            cache_mode=CacheMode.BYPASS
        )

        result = await crawler.arun(
            url=f"https://www.screener.in/company/{symbol}/",
            config=config
        )

        if result.markdown:
            parsed_json = parse_basic_data(result.markdown)
            if parsed_json: # Check if parsing was successful (not None)
                print(json.dumps(parsed_json, indent=2))
            else:
                print("Unable to parse basic data into JSON. Returning plain text:")
                print(result.markdown) # Print plain text if parsing failed
        else:
            print("No basic data found.")


if __name__ == "__main__":
    asyncio.run(main())