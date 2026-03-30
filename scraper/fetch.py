"""
Install the tools — pip install playwright then playwright install chromium (this downloads the actual browser binary)
Launch a browser — Playwright gives you a function to start a Chromium instance
Open a new page — like opening a new tab
Navigate to the URL — tell that tab to go to your URL, and wait until networkidle
Get the page content — Playwright has a method that returns the fully-rendered HTML as a string
Close the browser — always clean up
Print the result — just to confirm it worked

"""

import asyncio
import bs4
from playwright.async_api import async_playwright
from urllib.parse import urljoin
import requests
from pathlib import Path

async def fetchHtml(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        print(f"Navigating to {url}...")
        # `networkidle` can hang on sites with continuous trackers.
        # We use `domcontentloaded` or `load` instead, and wait explicitly for hydration if needed.
        await page.goto(url, wait_until="load", timeout=1000000)
        
        # Wait an extra 3 seconds to let client-side frameworks (React/Vue) hydrate
        await page.wait_for_timeout(10000)
        
        html = await page.content()
        await browser.close()

        # Add base tag so styles load from the live website!
        base_tag = f'<base href="{url}">'
        html = html.replace('<head>', f'<head>\n    {base_tag}')

        try:
            with open("cloned_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("HTML content saved to cloned_page.html")
        except Exception as e:
            print(f"Error saving HTML content: {e}")
            
        return html

"""
#Parse HTML → find all CSS and JS URLs (Layout Extraction Disabled)
def parseHTML(html: str, url: str) -> str:
    soup = bs4.BeautifulSoup(html, 'html.parser')
    css_links = soup.find_all('link', rel='stylesheet')
    css_hrefs = [link.get('href') for link in css_links]
    js_links = soup.find_all('script', src=True)
    js_srcs = [script.get('src') for script in js_links]
    
    print(f"Found {len(css_hrefs)} CSS files")
    print(f"Found {len(js_srcs)} JS files")
    
    #download css files
    for css_href in css_hrefs:
        css_url = urljoin(url, css_href)
        try:
            print(f"Downloading CSS file: {css_url}")
            css_content = requests.get(css_url).text
            Path("css").mkdir(exist_ok=True)
            with open(f"css/{Path(css_href).name}", "w", encoding="utf-8") as f:
                f.write(css_content)
        except Exception as e:
            print(f"❌ Error downloading CSS file: {e}")
        
    #download js files
    for js_src in js_srcs:
        js_url = urljoin(url, js_src)
        try:
            print(f"Downloading JS file: {js_url}")
            js_content = requests.get(js_url).text
            Path("js").mkdir(exist_ok=True)
            with open(f"js/{Path(js_src).name}", "w", encoding="utf-8") as f:
                f.write(js_content)
        except Exception as e:
            print(f"❌ Error downloading JS file: {e}")
        
    #replace all css and js urls with local file paths
    for css_link in css_links:
        css_link['href'] = f"css/{Path(css_link['href']).name}"
    for js_link in js_links:
        js_link['src'] = f"js/{Path(js_link['src']).name}"
    
    #save the modified html
    try:
        with open("cloned_page_modified.html", "w", encoding="utf-8") as f:
            f.write(str(soup))
        print("✅ Modified HTML content saved to cloned_page_modified.html")
    except Exception as e:
        print(f"❌ Error saving modified HTML content: {e}")
    
    return soup
"""

    
    


# Extract structural Data (Stats, Ranks, Match History)
def extractData(html: str) -> dict:
    soup = bs4.BeautifulSoup(html, 'html.parser')
    
    # 📝 This is just a starting point. We use BeautifulSoup to target specific HTML tags!
    data = {}
    
    # 1. Page Title
    data['title'] = soup.title.string if soup.title else "No Title"
    
    # 2. To get specific OP.GG stats, you would inspect the page and find the specific class names.
    # For example, to get their rank, OP.GG often uses a class like '.tier'
    # tier_element = soup.select_one(".tier")
    # data['rank'] = tier_element.text.strip() if tier_element else "Unranked"
    
    print("\n📊 --- EXTRACTED DATA --- 📊")
    print(data)
    print("----------------------------\n")
    
    return data


if __name__ == "__main__":
    target_url = "https://apexlol.info/zh/"
    
    # 1. Fetch the HTML exactly once (Playwright launches browser and gets full page)
    result = asyncio.run(fetchHtml(target_url))
    
    # 2. Extract the Data (Numbers, Stats, Usernames)
    stats_data = extractData(result)
    
    # # 3. Extract the Layout (HTML, CSS, JS files for your React frontend)
    # print("\n🎨 --- EXTRACTING VISUAL LAYOUT --- 🎨")
    # parseHTML(result, target_url)
    
    print(f"\nSuccessfully fetched and processed HTML ({len(result)} characters)")