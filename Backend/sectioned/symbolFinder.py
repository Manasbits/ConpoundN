import asyncio
from crawl4ai import *

userinput = input("Enter a stock symbol: ")

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=f"https://www.google.com/search?q={userinput}+stock+price",
            css_selector="[class^='loJjTe']"
        )
        
        # Segregating the string
        exchange, stock_name = result.markdown.split(": ")

        # Displaying the results
        print("Exchange:", exchange)
        print("Stock Name:", stock_name)

if __name__ == "__main__":
    asyncio.run(main())
