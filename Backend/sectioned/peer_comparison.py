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

def parse_peer_comparison(markdown_text):
    """Parses the peer comparison markdown text into a JSON object.
       Returns JSON object if parsing is successful, otherwise returns None.
    """
    try:
        lines = [line for line in markdown_text.strip().split('\n') if line.strip()] # Split lines and remove empty lines
        if len(lines) < 3:
            return None

        separator_line_index = -1
        for i, line in enumerate(lines):
            if '---' in line:
                separator_line_index = i
                break

        if separator_line_index == -1 or separator_line_index == 0: # Separator not found or at the beginning
            return None

        header_line = lines[separator_line_index - 1]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]

        if not headers: # No headers extracted
            return None

        peer_list = []
        start_parsing = False

        for i in range(separator_line_index + 1, len(lines)): # Start parsing after separator
            line = lines[i].strip()
            if not line or line.startswith("Detailed Comparison with:"): # Skip empty lines and footer
                continue

            parts = [part.strip() for part in line.split('|')]
            if len(parts) == len(headers):
                peer_data = {}
                for j, header in enumerate(headers):
                    peer_data[header] = parts[j]
                peer_list.append(peer_data)
            elif line.startswith("Median:"): # Handle Median row
                median_parts = [part.replace("Median:","").strip() for part in line.split('|')] # Remove "Median:" prefix
                median_parts = [part.strip() for part in median_parts] # Clean up parts again
                if len(median_parts) == len(headers):
                    median_data = {}
                    for j, header in enumerate(headers):
                        median_data[header] = median_parts[j]
                    peer_list.append(median_data)


        return peer_list

    except Exception:
        return None


async def main():
    async with AsyncWebCrawler() as crawler:
        # Configure CrawlerRunConfig with css_selector
        config = CrawlerRunConfig(
            css_selector="#peers",
            cache_mode=CacheMode.BYPASS
        )

        company_symbols = ["RCF", "ENGINERSIN"] # Test with both companies

        for symbol in company_symbols:
            print(f"\nProcessing company: {symbol}")
            result = await crawler.arun(
                url=f"https://www.screener.in/company/{symbol}/",
                config=config
            )

            if result.markdown:
                parsed_json = parse_peer_comparison(result.markdown)
                if parsed_json:
                    print(json.dumps(parsed_json, indent=2))
                else:
                    print(f"Unable to parse peer comparison data into JSON for {symbol}. Returning plain text:")
                    print(result.markdown)
            else:
                print(f"No peer comparison data found for {symbol}.")


if __name__ == "__main__":
    asyncio.run(main())