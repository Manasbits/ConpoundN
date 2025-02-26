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

def parse_shareholding(markdown_text):
    """Parses the shareholding pattern markdown text into a JSON object.
       Returns JSON object if parsing is successful, otherwise returns None.
    """
    try:
        lines = [line for line in markdown_text.strip().split('\n') if line.strip()]
        if len(lines) < 5:  # Minimum lines for shareholding table
            return None

        quarterly_data = {}
        yearly_data = {}
        current_section = None  # To track if parsing "Quarterly" or "Yearly"

        for i, line in enumerate(lines):
            line = line.strip()

            if "Quarterly" in line:
                current_section = "Quarterly"
                quarterly_data["Quarters"] = [] # Initialize Quarters header
                continue
            elif "Yearly" in line:
                current_section = "Yearly"
                yearly_data["Years"] = [] # Initialize Years header
                continue
            elif "---" in line:
                continue # Skip separator lines
            elif i > 2 and current_section == "Quarterly": # Start parsing quarterly data after headers
                if not quarterly_data.get("Quarters"): # Extract quarterly headers only once
                    quarterly_headers = [h.strip() for h in lines[i-1].split('|') if h.strip()]
                    quarterly_data["Quarters"] = quarterly_headers
                else:
                    parts = [part.strip() for part in line.split('|')]
                    if parts and parts[0]:
                        metric_name = parts[0]
                        values = parts[1:] if len(parts) > 1 else []
                        quarterly_data[metric_name] = values

            elif i > 7 and current_section == "Yearly": # Start parsing yearly data after headers and quarterly table
                 if not yearly_data.get("Years"): # Extract yearly headers only once
                    yearly_headers = [h.strip() for h in lines[i-1].split('|') if h.strip()]
                    yearly_data["Years"] = yearly_headers
                 else:
                    parts = [part.strip() for part in line.split('|')]
                    if parts and parts[0]:
                        metric_name = parts[0]
                        values = parts[1:] if len(parts) > 1 else []
                        yearly_data[metric_name] = values

        shareholding_data = {}
        if quarterly_data:
            shareholding_data["Quarterly Shareholding"] = quarterly_data
        if yearly_data:
            shareholding_data["Yearly Shareholding"] = yearly_data

        return shareholding_data

    except Exception as e:
        print(f"Parsing error: {e}")
        return None


async def main():
    async with AsyncWebCrawler() as crawler:
        # Configure CrawlerRunConfig with css_selector
        config = CrawlerRunConfig(
            css_selector="#shareholding",
            cache_mode=CacheMode.BYPASS
        )

        result = await crawler.arun(
            url=f"https://www.screener.in/company/ENGINERSIN/",
            config=config
        )

        if result.markdown:
            parsed_json = parse_shareholding(result.markdown)
            if parsed_json:
                print(json.dumps(parsed_json, indent=2))
            else:
                print("Unable to parse shareholding data into JSON. Returning plain text:")
                print(result.markdown)
        else:
            print("No shareholding data found.")


if __name__ == "__main__":
    asyncio.run(main())