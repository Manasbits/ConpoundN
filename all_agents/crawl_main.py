import asyncio
import os
import json
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from dotenv import load_dotenv
from supabase import create_client, Client  # Import Supabase library
from openai import AsyncOpenAI # Import OpenAI library
from dataclasses import dataclass
from typing import List, Dict, Any
from urllib.parse import urlparse
from datetime import datetime, timezone

load_dotenv()
openai_api_key = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI and Supabase clients
openai_client = AsyncOpenAI(api_key=openai_api_key)
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_service_key)


@dataclass
class ProcessedChunk:
    url: str
    chunk_number: int
    title: str
    summary: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]

async def find_stock_symbol(user_input):
    """
    Finds stock exchange and name based on user input from Google Search.
    """
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=f"https://www.google.com/search?q={user_input}+stock+price",
            css_selector="[class^='loJjTe']"
        )
        if result.markdown:
            exchange, stock_name = result.markdown.split(": ")
            return {"exchange": exchange, "stock_name": stock_name}
        return None

def parse_basic_data(markdown_text):
    """Parses basic data markdown text into a JSON object."""
    basic_data_json = {}
    try:
        lines = markdown_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("* "):
                parts = line[2:].split('  ', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    basic_data_json[key] = value
        return basic_data_json
    except Exception:
        return None

async def fetch_basic_data(company_symbol):
    """Fetches and parses basic data from screener.in."""
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(css_selector="#top-ratios", cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(
            url=f"https://www.screener.in/company/{company_symbol}/",
            config=config
        )
        if result.markdown:
            parsed_json = parse_basic_data(result.markdown)
            if parsed_json:
                return parsed_json
            else:
                return {"error": "Unable to parse basic data", "plain_text": result.markdown}
        else:
            return {"error": "No basic data found"}

def parse_quarterly_results(text):
    """Parses quarterly results markdown text into a JSON object."""
    lines = text.strip().split('\n')
    quarters = []
    data_values = {}
    upcoming_result_date = ""
    try:
        for i, line in enumerate(lines):
            line = line.strip()
            if i == 3:
                quarters = [q.strip() for q in line.split('|') if q.strip()]
            elif i > 4 and "Upcoming result date:" not in line and line and "---" not in line:
                parts = [part.strip() for part in line.split('|')]
                if len(parts) > 1:
                    metric_name = parts[0]
                    values = parts[1:]
                    data_values[metric_name] = values
            elif "Upcoming result date:" in line:
                upcoming_result_date = line.split(": **")[1][:-2]

        quarterly_json = {}
        for metric, values in data_values.items():
            quarterly_json[metric] = values
        quarterly_json["Quarters"] = quarters
        if upcoming_result_date:
            quarterly_json["Upcoming result date"] = upcoming_result_date
        return quarterly_json
    except Exception:
        return None

async def fetch_quarterly_results(company_symbol):
    """Fetches and parses quarterly results from screener.in."""
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(css_selector="#quarters", cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(
            url=f"https://www.screener.in/company/{company_symbol}/",
            config=config
        )
        if result.markdown:
            parsed_json = parse_quarterly_results(result.markdown)
            if parsed_json:
                return parsed_json
            else:
                return {"error": "Unable to parse quarterly results", "plain_text": result.markdown}
        else:
            return {"error": "No quarterly results data found."}

def parse_balance_sheet(markdown_text):
    """Parses balance sheet markdown text into a JSON object."""
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
        balance_sheet_data = {"Years": year_headers}
        start_parsing = False

        for i in range(header_line_index + 1, len(lines)):
            line = lines[i].strip()
            if line == '---|---|---|---|---|---|---|---|---|---|---|---|---':
                start_parsing = True
                continue
            if start_parsing and line and "Total Assets" not in line:
                parts = [part.strip() for part in line.split('|')]
                if parts and parts[0]:
                    metric_name = parts[0]
                    values = parts[1:] if len(parts) > 1 else []
                    balance_sheet_data[metric_name] = values
        return balance_sheet_data
    except Exception as e:
        print(f"Parsing error in balance sheet: {e}")
        return None

async def fetch_balance_sheet(company_symbol):
    """Fetches and parses balance sheet data from screener.in."""
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(css_selector="#balance-sheet", cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(
            url=f"https://www.screener.in/company/{company_symbol}/",
            config=config
        )
        if result.markdown:
            parsed_json = parse_balance_sheet(result.markdown)
            if parsed_json:
                return parsed_json
            else:
                return {"error": "Unable to parse balance sheet data", "plain_text": result.markdown}
        else:
            return {"error": "No balance sheet data found."}

def parse_peer_comparison(markdown_text):
    """Parses peer comparison markdown text into a JSON object."""
    try:
        lines = [line for line in markdown_text.strip().split('\n') if line.strip()]
        if len(lines) < 3:
            return None

        separator_line_index = -1
        for i, line in enumerate(lines):
            if '---' in line:
                separator_line_index = i
                break

        if separator_line_index == -1 or separator_line_index == 0:
            return None

        header_line = lines[separator_line_index - 1]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]

        if not headers:
            return None

        peer_list = []

        for i in range(separator_line_index + 1, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith("Detailed Comparison with:"):
                continue

            parts = [part.strip() for part in line.split('|')]
            if len(parts) == len(headers):
                peer_data = {}
                for j, header in enumerate(headers):
                    peer_data[header] = parts[j]
                peer_list.append(peer_data)
            elif line.startswith("Median:"):
                median_parts = [part.replace("Median:","").strip() for part in line.split('|')]
                median_parts = [part.strip() for part in median_parts]
                if len(median_parts) == len(headers):
                    median_data = {}
                    for j, header in enumerate(headers):
                        median_data[header] = median_parts[j]
                    peer_list.append(median_data)
        return peer_list
    except Exception:
        return None

async def fetch_peer_comparison(company_symbol):
    """Fetches and parses peer comparison data from screener.in."""
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(css_selector="#peers", cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(
            url=f"https://www.screener.in/company/{company_symbol}/",
            config=config
        )
        if result.markdown:
            parsed_json = parse_peer_comparison(result.markdown)
            if parsed_json:
                return parsed_json
            else:
                return {"error": "Unable to parse peer comparison data", "plain_text": result.markdown}
        else:
            return {"error": "No peer comparison data found."}

def parse_cash_flow(markdown_text):
    """Parses cash flow markdown text into a JSON object."""
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
        cash_flow_data = {}
        start_parsing = False

        for i in range(header_line_index + 1, len(lines)):
            line = lines[i].strip()
            if line == '---|---|---|---|---|---|---|---|---|---|---|---|---':
                start_parsing = True
                continue
            if start_parsing and line and "Net Cash Flow" not in line:
                parts = [part.strip() for part in line.split('|')]
                if parts and parts[0]:
                    metric_name = parts[0]
                    values = parts[1:] if len(parts) > 1 else []
                    cash_flow_data[metric_name] = values
        return cash_flow_data
    except Exception:
        return None

async def fetch_cash_flow(company_symbol):
    """Fetches and parses cash flow data from screener.in."""
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(css_selector="#cash-flow", cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(
            url=f"https://www.screener.in/company/{company_symbol}/",
            config=config
        )
        if result.markdown:
            parsed_json = parse_cash_flow(result.markdown)
            if parsed_json:
                return parsed_json
            else:
                return {"error": "Unable to parse cash flow data", "plain_text": result.markdown}
        else:
            return {"error": "No cash flow data found."}

def parse_profit_loss(markdown_text):
    """Parses profit & loss markdown text into a JSON object."""
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
        profit_loss_data = {"Years": year_headers, "Growth Ratios": {}}
        start_parsing_metrics = False
        current_growth_section = None

        for i in range(header_line_index + 1, len(lines)):
            line = lines[i].strip()
            if line == '---|---|---|---|---|---|---|---|---|---|---|---|---':
                start_parsing_metrics = True
                continue

            if start_parsing_metrics:
                if "Compounded Sales Growth" in line:
                    current_growth_section = "Compounded Sales Growth"
                    profit_loss_data["Growth Ratios"][current_growth_section] = {}
                    continue
                elif "Compounded Profit Growth" in line:
                    current_growth_section = "Compounded Profit Growth"
                    profit_loss_data["Growth Ratios"][current_growth_section] = {}
                    continue
                elif "Stock Price CAGR" in line:
                    current_growth_section = "Stock Price CAGR"
                    profit_loss_data["Growth Ratios"][current_growth_section] = {}
                    continue
                elif "Return on Equity" in line:
                    current_growth_section = "Return on Equity"
                    profit_loss_data["Growth Ratios"][current_growth_section] = {}
                    continue
                elif current_growth_section:
                    if ":" in line:
                        ratio_parts = [part.strip() for part in line.split(':')]
                        if len(ratio_parts) == 2:
                            time_period = ratio_parts[0]
                            value = ratio_parts[1]
                            profit_loss_data["Growth Ratios"][current_growth_section][time_period] = value
                    elif not line:
                        current_growth_section = None
                elif line and "Compounded Sales Growth" not in line and "Compounded Profit Growth" not in line and "Stock Price CAGR" not in line and "Return on Equity" not in line:
                    parts = [part.strip() for part in line.split('|')]
                    if parts and parts[0]:
                        metric_name = parts[0]
                        values = parts[1:] if len(parts) > 1 else []
                        profit_loss_data[metric_name] = values

        return profit_loss_data
    except Exception as e:
        print(f"Parsing error in profit & loss: {e}")
        return None

async def fetch_profit_loss(company_symbol):
    """Fetches and parses profit & loss data from screener.in."""
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(css_selector="#profit-loss", cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(
            url=f"https://www.screener.in/company/{company_symbol}/",
            config=config
        )
        if result.markdown:
            parsed_json = parse_profit_loss(result.markdown)
            if parsed_json:
                return parsed_json
            else:
                return {"error": "Unable to parse profit & loss data", "plain_text": result.markdown}
        else:
            return {"error": "No profit & loss data found."}

def parse_ratios(markdown_text):
    """Parses ratios markdown text into a JSON object."""
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
        ratios_data = {"Years": year_headers}
        start_parsing = False

        for i in range(header_line_index + 1, len(lines)):
            line = lines[i].strip()
            if line == '---|---|---|---|---|---|---|---|---|---|---|---|---':
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
        print(f"Parsing error in ratios: {e}")
        return None

async def fetch_ratios(company_symbol):
    """Fetches and parses ratios data from screener.in."""
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(css_selector="#ratios", cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(
            url=f"https://www.screener.in/company/{company_symbol}/",
            config=config
        )
        if result.markdown:
            parsed_json = parse_ratios(result.markdown)
            if parsed_json:
                return parsed_json
            else:
                return {"error": "Unable to parse ratios data", "plain_text": result.markdown}
        else:
            return {"error": "No ratios data found."}

def parse_shareholding(markdown_text):
    """Parses shareholding pattern markdown text into a JSON object."""
    try:
        lines = [line for line in markdown_text.strip().split('\n') if line.strip()]
        if len(lines) < 5:
            return None

        quarterly_data = {}
        yearly_data = {}
        current_section = None

        for i, line in enumerate(lines):
            line = line.strip()

            if "Quarterly" in line:
                current_section = "Quarterly"
                quarterly_data["Quarters"] = []
                continue
            elif "Yearly" in line:
                current_section = "Yearly"
                yearly_data["Years"] = []
                continue
            elif "---" in line:
                continue
            elif i > 2 and current_section == "Quarterly":
                if not quarterly_data.get("Quarters"):
                    quarterly_headers = [h.strip() for h in lines[i-1].split('|') if h.strip()]
                    quarterly_data["Quarters"] = quarterly_headers
                else:
                    parts = [part.strip() for part in line.split('|')]
                    if parts and parts[0]:
                        metric_name = parts[0]
                        values = parts[1:] if len(parts) > 1 else []
                        quarterly_data[metric_name] = values
            elif i > 7 and current_section == "Yearly":
                if not yearly_data.get("Years"):
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
        print(f"Parsing error in shareholding: {e}")
        return None

async def fetch_shareholding_pattern(company_symbol):
    """Fetches and parses shareholding pattern data from screener.in."""
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(css_selector="#shareholding", cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(
            url=f"https://www.screener.in/company/{company_symbol}/",
            config=config
        )
        if result.markdown:
            parsed_json = parse_shareholding(result.markdown)
            if parsed_json:
                return parsed_json
            else:
                return {"error": "Unable to parse shareholding data", "plain_text": result.markdown}
        else:
            return {"error": "No shareholding data found."}

def parse_documents(markdown_text):
    """Parses documents, EXCLUDING concalls, markdown text into a JSON object."""
    try:
        documents_data = {}
        current_section = None
        lines = markdown_text.strip().split('\n')

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
                continue # Skip Concalls section

            elif line.startswith("*"):
                if current_section == "Credit Ratings":
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
                elif current_section == "Announcements":
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
                elif current_section == "Annual Reports":
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
        print(f"Parsing error in documents: {e}")
        return None

async def fetch_documents(company_symbol):
    """Fetches and parses documents data from screener.in (excluding concalls)."""
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(css_selector="#documents", cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(
            url=f"https://www.screener.in/company/{company_symbol}/",
            config=config
        )
        if result.markdown:
            parsed_json = parse_documents(result.markdown)
            if parsed_json:
                return parsed_json
            else:
                return {"error": "Unable to parse documents data", "plain_text": result.markdown}
        else:
            return {"error": "No documents data found."}

def parse_concalls(markdown_text):
    """Parses concalls markdown text into a JSON object."""
    concalls_data = []
    entries = markdown_text.split('* ') # Split by each concall entry
    for entry in entries:
        entry = entry.strip()
        if not entry or entry.startswith("### Concalls") or entry.startswith("Add Missing"):
            continue

        lines = entry.split('\n')
        date = lines[0].strip()

        concall_entry = {"Date": date}
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("[ Transcript ]"):
                transcript_match = re.search(r'\[ Transcript \] ?\((.*?)\)', line)
                if transcript_match:
                    url_with_prefix = transcript_match.group(1)
                    url = url_with_prefix.split("<")[-1].split(">")[0] if "<" in url_with_prefix else url_with_prefix
                    concall_entry["Transcript"] = url.strip('"')
            elif line.startswith("Notes"):
                concall_entry["Notes"] = True # Simply mark presence of notes
            elif line.startswith("[ PPT ]"):
                ppt_match = re.search(r'\[ PPT \] ?\((.*?)\)', line)
                if ppt_match:
                    url_with_prefix = ppt_match.group(1)
                    url = url_with_prefix.split("<")[-1].split(">")[0] if "<" in url_with_prefix else url_with_prefix
                    concall_entry["PPT"] = url.strip('"')
            elif line.startswith("[ REC ]"):
                rec_match = re.search(r'\[ REC \] ?\((.*?)\)', line)
                if rec_match:
                    url_with_prefix = rec_match.group(1)
                    url = url_with_prefix.split("<")[-1].split(">")[0] if "<" in url_with_prefix else url_with_prefix
                    concall_entry["REC"] = url.strip('"')
        concalls_data.append(concall_entry)
    return concalls_data

async def fetch_concalls(company_symbol):
    """Fetches and parses concalls data from screener.in and returns structured JSON."""
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(css_selector=".concalls", cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(
            url=f"https://www.screener.in/company/{company_symbol}/",
            config=config
        )
        if result.markdown:
            parsed_json = parse_concalls(result.markdown) # Parse markdown here
            if parsed_json:
                return parsed_json
            else:
                return {"error": "Unable to parse concalls data", "plain_text": result.markdown}
        else:
            return {"error": "No concalls data found."}

async def get_embedding(text: str) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small", # Using small embedding model for cost efficiency
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error, adjust dimension if needed

async def insert_chunk(chunk: ProcessedChunk):
    """Insert a processed chunk into Supabase."""
    try:
        data = {
            "url": chunk.url,
            "chunk_number": chunk.chunk_number,
            "title": chunk.title,
            "summary": chunk.summary,
            "content": chunk.content,
            "metadata": chunk.metadata,
            "embedding": chunk.embedding
        }

        result = supabase.table("stock_info").insert(data).execute() # Changed table name to "stock_info"
        print(f"Inserted chunk {chunk.chunk_number} for {chunk.url} - {chunk.title}") # Added title to print output
        return result
    except Exception as e:
        print(f"Error inserting chunk: {e}")
        return None

async def process_and_store_chunk(company_symbol, section_name, section_data, chunk_number):
    """Process a single data section and store it as a chunk."""
    if not section_data or "error" in section_data:
        print(f"Skipping {section_name} due to missing or error data.")
        return None

    content_string = json.dumps(section_data) # Convert JSON data to string for content and embedding

    # Generate embedding for the JSON string content
    embedding = await get_embedding(content_string)

    # Create metadata
    metadata = {
        "source": "screener.in",
        "data_type": "stock_data",
        "company_symbol": company_symbol,
        "section_name": section_name,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    # Construct URL - using screener URL and appending section name for uniqueness
    base_url = f"https://www.screener.in/company/{company_symbol}/"
    chunk_url = f"{base_url}#{section_name}"

    # Create ProcessedChunk object - Removed summary as per request, kept title
    processed_chunk = ProcessedChunk(
        url=chunk_url,
        chunk_number=chunk_number,
        title=section_name.replace('_', ' ').title(), # Title case, e.g., "Basic Data"
        summary=f"Data chunk for {section_name} of {company_symbol}", # Basic summary, can be improved with LLM if needed
        content=content_string, # Store JSON string as content
        metadata=metadata,
        embedding=embedding
    )
    return await insert_chunk(processed_chunk) # Insert chunk into database

async def main():
    user_input = input("Enter a stock symbol or company name: ")
    stock_info = await find_stock_symbol(user_input)

    if stock_info:
        company_symbol = stock_info["stock_name"].replace(" ", "").upper()
        screener_url = f"https://www.screener.in/company/{company_symbol}/" # Define screener_url here
        print(f"Fetching data for: {stock_info['exchange']}: {stock_info['stock_name']} ({company_symbol}) from {screener_url}") # Added screener URL to print

        # Fetch data from different sections
        basic_data = await fetch_basic_data(company_symbol)
        quarterly_results = await fetch_quarterly_results(company_symbol)
        balance_sheet = await fetch_balance_sheet(company_symbol)
        peer_comparison = await fetch_peer_comparison(company_symbol)
        cash_flow = await fetch_cash_flow(company_symbol)
        profit_loss = await fetch_profit_loss(company_symbol)
        ratios = await fetch_ratios(company_symbol)
        shareholding_pattern = await fetch_shareholding_pattern(company_symbol)
        documents = await fetch_documents(company_symbol)
        concalls = await fetch_concalls(company_symbol)

        company_data_sections = { # Data sections in ordered dict to control chunk_number
            "basic_data": basic_data,
            "quarterly_results": quarterly_results,
            "balance_sheet": balance_sheet,
            "peer_comparison": peer_comparison,
            "profit_loss": profit_loss,
            "cash_flow": cash_flow,
            "ratios": ratios,
            "shareholding_pattern": shareholding_pattern,
            "documents": documents,
            "concalls": concalls,
        }

        chunk_number = 1 # Initialize chunk number
        for section_name, section_data in company_data_sections.items():
            await process_and_store_chunk(company_symbol, section_name, section_data, chunk_number)
            chunk_number += 1 # Increment chunk number for next section

        print(f"\nData insertion completed for {stock_info['stock_name']} ({company_symbol}) into Supabase.")

    else:
        print("Could not find stock symbol. Please check the company name or symbol.")

if __name__ == "__main__":
    asyncio.run(main())