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


def parse_quarterly_results(text):
    lines = text.strip().split('\n')
    metric_names = []
    quarters = []
    data_values = {}
    upcoming_result_date = ""

    try: # Added try-except block
        for i, line in enumerate(lines):
            line = line.strip()
            if i == 2:  # Header row (metric names) - skip "Close Segments Product Segments"
                continue
            if i == 3:  # Quarters row
                quarters = [q.strip() for q in line.split('|') if q.strip()]
            elif i > 4 and "Upcoming result date:" not in line and line and "---" not in line :  # Data rows and ignore "Upcoming result date" and separator lines
                parts = [part.strip() for part in line.split('|')]
                if len(parts) > 1:
                    metric_name = parts[0]
                    values = parts[1:]
                    data_values[metric_name] = values
            elif "Upcoming result date:" in line:
                upcoming_result_date = line.split(": **")[1][:-2]  # Extract date

        quarterly_json = {}
        for metric, values in data_values.items():
            quarterly_json[metric] = values
        quarterly_json["Quarters"] = quarters
        if upcoming_result_date:
            quarterly_json["Upcoming result date"] = upcoming_result_date

        return quarterly_json

    except Exception: # Catch any parsing error
        return None # Return None if parsing fails


async def main():
    async with AsyncWebCrawler() as crawler:
        # Configure CrawlerRunConfig with css_selector
        config = CrawlerRunConfig(
            css_selector="#quarters",
            cache_mode=CacheMode.BYPASS
        )

        result = await crawler.arun(
            url=f"https://www.screener.in/company/ENGINERSIN/",
            config=config
        )

        # Parse the markdown text into JSON
        if result.markdown:
            parsed_json = parse_quarterly_results(result.markdown)
            if parsed_json: # Check if parsing was successful
                print(json.dumps(parsed_json, indent=2))
            else:
                print("Unable to parse quarterly results into JSON. Returning plain text:")
                print(result.markdown) # Print plain text if parsing failed
        else:
            print("No quarterly results data found.")


if __name__ == "__main__":
    asyncio.run(main())