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

def parse_ratios(markdown_text):
    """Parses the ratios markdown text into a JSON object.
       Returns JSON object if parsing is successful, otherwise returns None.
    """
    try:
        lines = [line for line in markdown_text.strip().split('\n') if line.strip()]
        if len(lines) < 3:
            return None

        header_line_index = -1
        for i, line in enumerate(lines):
            if "Mar 2013" in line:
                header_line_index = i
                break

        if header_line_index == -1:
            return None

        headers = [h.strip() for h in lines[header_line_index].split('|') if h.strip()]
        year_headers = headers
        ratios_data = {}
        ratios_data["Years"] = year_headers
        start_parsing = False

        for i in range(header_line_index + 1, len(lines)):
            line = lines[i].strip()
            if line == '---|---|---|---|---|---|---|---|---|---|---|---':
                start_parsing = True
                continue
            if start_parsing and line:
                parts = [part.strip() for part in line.split('|')]
                if parts and parts[0]:
                    metric_name = parts[0]
                    values = parts[1:] if len(parts) > 1 else []
                    ratios_data[metric_name] = values

        return ratios_data

    except Exception as e:
        print(f"Parsing error: {e}")
        return None


async def main():
    async with AsyncWebCrawler() as crawler:
        # Configure CrawlerRunConfig with css_selector
        config = CrawlerRunConfig(
            css_selector="#ratios",
            cache_mode=CacheMode.BYPASS
        )

        result = await crawler.arun(
            url=f"https://www.screener.in/company/ENGINERSIN/",
            config=config
        )

        if result.markdown:
            parsed_json = parse_ratios(result.markdown)
            if parsed_json:
                print(json.dumps(parsed_json, indent=2))
            else:
                print("Unable to parse ratios data into JSON. Returning plain text:")
                print(result.markdown)
        else:
            print("No ratios data found.")


if __name__ == "__main__":
    asyncio.run(main())