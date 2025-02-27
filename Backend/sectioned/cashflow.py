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

def parse_cash_flow(markdown_text):
    """Parses the cash flow markdown text into a JSON object.
       Returns JSON object if parsing is successful, otherwise returns None.
    """
    try:
        lines = [line for line in markdown_text.strip().split('\n') if line.strip()]
        if len(lines) < 3:
            return None

        header_line_index = -1
        for i, line in enumerate(lines):
            if "Mar 2013" in line:  # Assuming "Mar 2013" is always in the header
                header_line_index = i
                break

        if header_line_index == -1:
            return None

        headers = [h.strip() for h in lines[header_line_index].split('|') if h.strip()]

        cash_flow_data = {}
        start_parsing = False

        for i in range(header_line_index + 1, len(lines)):
            line = lines[i].strip()
            if line == '---|---|---|---|---|---|---|---|---|---|---|---':
                start_parsing = True
                continue
            if start_parsing and line and "Net Cash Flow" not in line:
                parts = [part.strip() for part in line.split('|')]
                if parts and parts[0]: # Check if metric name exists
                    metric_name = parts[0]
                    values = parts[1:] if len(parts) > 1 else []
                    cash_flow_data[metric_name] = values


        return cash_flow_data

    except Exception:
        return None

async def main():
    async with AsyncWebCrawler() as crawler:
        # Configure CrawlerRunConfig with css_selector
        config = CrawlerRunConfig(
            css_selector="#cash-flow",
            cache_mode=CacheMode.BYPASS
        )

        result = await crawler.arun(
            url=f"https://www.screener.in/company/ENGINERSIN/",
            config=config
        )

        if result.markdown:
            parsed_json = parse_cash_flow(result.markdown)
            if parsed_json:
                print(json.dumps(parsed_json, indent=2))
            else:
                print("Unable to parse cash flow data into JSON. Returning plain text:")
                print(result.markdown)
        else:
            print("No cash flow data found.")


if __name__ == "__main__":
    asyncio.run(main())