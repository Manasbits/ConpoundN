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

def parse_documents(markdown_text):
    """Parses documents, EXCLUDING concalls.
       Returns JSON object if parsing is successful, otherwise returns None.
    """
    try:
        lines = markdown_text.strip().split('\n')
        documents_data = {}
        current_section = None

        for line in lines:
            line = line.strip()

            if line.startswith("### Announcements"):
                current_section = "Announcements"
                documents_data[current_section] = []
            elif line.startswith("### Annual reports"):
                current_section = "Annual Reports"
                documents_data[current_section] = []
            elif line.startswith("### Credit ratings"):
                current_section = "Credit Ratings"
                documents_data[current_section] = []
            elif line.startswith("### Concalls"):
                current_section = "Concalls"
                # DO NOT PARSE CONCALLS SECTION


            elif line.startswith("*"):
                if current_section == "Credit Ratings": # --- CREDIT RATINGS PARSING --- # No date field
                    parts = line[1:].strip()
                    link_match = parts.rsplit('](', 1)
                    if len(link_match) == 2:
                        text_part = link_match[0].strip()
                        url_part = link_match[1].strip(')>')
                        description = text_part
                        documents_data[current_section].append({
                            "description": description,
                            "url": url_part
                        })


                elif current_section == "Announcements": # --- ANNOUNCEMENTS PARSING --- # No change
                    parts = line[1:].strip()
                    link_match = parts.rsplit('](', 1)
                    if len(link_match) == 2:
                        text_part = link_match[0].strip()
                        url_part = link_match[1].strip(')>')

                        date_match = re.search(r'^(.*?)\s*(\d+\s?\w+\s?\d{4}|\d+\s?\w+|\d+h)\s*-\s*(.*)$', text_part, re.IGNORECASE)
                        if date_match:
                            description_prefix = date_match.group(1).strip('- ').strip()
                            date_info = date_match.group(2).strip()
                            description_suffix = date_match.group(3).strip('- ').strip()
                            description = (description_prefix + " - " + description_suffix).strip('- ').strip() if description_suffix else description_prefix
                        else:
                            description = text_part
                            date_info = None

                        documents_data[current_section].append({
                            "description": description,
                            "date": date_info,
                            "url": url_part
                        })

                elif current_section == "Annual Reports": # --- ANNUAL REPORTS PARSING --- # No change
                    parts = line[1:].strip()
                    link_match = parts.rsplit('](', 1)
                    if len(link_match) == 2:
                        text_part = link_match[0].strip()
                        url_part = link_match[1].strip(')>')
                        description_parts = text_part.rsplit('from', 1)
                        if len(description_parts) == 2:
                            description = description_parts[0].strip()
                            source_info = description_parts[1].strip()
                        else:
                            description = text_part
                            source_info = None

                        documents_data[current_section].append({
                            "description": description,
                            "source": source_info,
                            "url": url_part
                        })


        return documents_data

    except Exception as e:
        print(f"Parsing error: {e}")
        return None


async def main():
    async with AsyncWebCrawler() as crawler:
        # Configure CrawlerRunConfig with css_selector
        config = CrawlerRunConfig(
            css_selector="#documents",
            cache_mode=CacheMode.BYPASS
        )

        result = await crawler.arun(
            url=f"https://www.screener.in/company/ENGINERSIN/",
            config=config
        )

        if result.markdown:
            parsed_json = parse_documents(result.markdown)
            if parsed_json:
                print(json.dumps(parsed_json, indent=2))
            else:
                print("Unable to parse documents data into JSON. Returning plain text:")
                print(result.markdown)
        else:
            print("No documents data found.")


if __name__ == "__main__":
    asyncio.run(main())