#!/usr/bin/env python3

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_rekt_scraper():
    """Test the Rekt News scraper directly"""
    
    async with aiohttp.ClientSession() as session:
        print("Fetching Rekt News main page...")
        async with session.get("https://rekt.news") as response:
            if response.status != 200:
                print(f"Failed to fetch page: {response.status}")
                return
            
            content = await response.text()
            print(f"Page content length: {len(content)}")
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Test different selectors
            selectors = [
                'h5.post-title a',
                '.post-title a', 
                'article.post .post-title a',
                'article a',  # Broader selector
                '.post a',    # Another broad selector
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                print(f"\nSelector '{selector}' found {len(elements)} elements:")
                
                for i, element in enumerate(elements[:5]):  # Show first 5
                    href = element.get('href')
                    text = element.get_text().strip()
                    print(f"  {i+1}. href='{href}' text='{text[:50]}...'")
            
            # Check for any links containing "rekt" or starting with "/"
            all_links = soup.find_all('a', href=True)
            rekt_links = [link for link in all_links if link.get('href', '').startswith('/') and 'rekt' in link.get('href', '').lower()]
            
            print(f"\n\nFound {len(rekt_links)} links containing 'rekt':")
            for i, link in enumerate(rekt_links[:10]):
                href = link.get('href')
                text = link.get_text().strip()
                print(f"  {i+1}. href='{href}' text='{text[:50]}...'")
            
            # Look for article containers
            articles = soup.find_all('article')
            print(f"\n\nFound {len(articles)} article containers")
            
            for i, article in enumerate(articles[:3]):
                print(f"\nArticle {i+1}:")
                title_link = article.find('a')
                if title_link:
                    href = title_link.get('href')
                    text = title_link.get_text().strip()
                    print(f"  First link: href='{href}' text='{text}'")

if __name__ == "__main__":
    asyncio.run(test_rekt_scraper())
