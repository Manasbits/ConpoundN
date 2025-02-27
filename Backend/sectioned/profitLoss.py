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

def parse_profit_loss(markdown_text):
    """Parses the profit & loss markdown text into a JSON object, including growth ratios.
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

        profit_loss_data = {}
        profit_loss_data["Years"] = year_headers
        start_parsing_metrics = False
        growth_ratios = {} # Dictionary to store growth ratios

        current_growth_section = None # Track current growth section

        for i in range(header_line_index + 1, len(lines)):
            line = lines[i].strip()
            if line == '---|---|---|---|---|---|---|---|---|---|---|---|---':
                start_parsing_metrics = True
                continue

            if start_parsing_metrics:
                if line and "Compounded Sales Growth" in line:
                    current_growth_section = "Compounded Sales Growth"
                    growth_ratios[current_growth_section] = {} # Initialize section
                    continue
                elif line and "Compounded Profit Growth" in line:
                    current_growth_section = "Compounded Profit Growth"
                    growth_ratios[current_growth_section] = {}
                    continue
                elif line and "Stock Price CAGR" in line:
                    current_growth_section = "Stock Price CAGR"
                    growth_ratios[current_growth_section] = {}
                    continue
                elif line and "Return on Equity" in line:
                    current_growth_section = "Return on Equity"
                    growth_ratios[current_growth_section] = {}
                    continue
                elif current_growth_section: # Inside a growth section
                    if ":" in line:
                        ratio_parts = [part.strip() for part in line.split(':')]
                        if len(ratio_parts) == 2:
                            time_period = ratio_parts[0]
                            value = ratio_parts[1]
                            growth_ratios[current_growth_section][time_period] = value
                    elif not line: # Empty line indicates end of growth section
                        current_growth_section = None # Reset section


                elif line and "Compounded Sales Growth" not in line and "Compounded Profit Growth" not in line and "Stock Price CAGR" not in line and "Return on Equity" not in line:
                    parts = [part.strip() for part in line.split('|')]
                    if parts and parts[0]:
                        metric_name = parts[0]
                        values = parts[1:] if len(parts) > 1 else []
                        profit_loss_data[metric_name] = values

        profit_loss_data["Growth Ratios"] = growth_ratios # Add growth ratios to main data
        return profit_loss_data

    except Exception as e:
        print(f"Parsing error: {e}") # Print exception for debugging
        return None

async def main():
    async with AsyncWebCrawler() as crawler:
        # Configure CrawlerRunConfig with css_selector
        config = CrawlerRunConfig(
            css_selector="#profit-loss",
            cache_mode=CacheMode.BYPASS
        )

        result = await crawler.arun(
            url=f"https://www.screener.in/company/ENGINERSIN/",
            config=config
        )

        if result.markdown:
            parsed_json = parse_profit_loss(result.markdown)
            if parsed_json:
                print(json.dumps(parsed_json, indent=2))
            else:
                print("Unable to parse profit & loss data into JSON. Returning plain text:")
                print(result.markdown)
        else:
            print("No profit & loss data found.")


if __name__ == "__main__":
    asyncio.run(main())