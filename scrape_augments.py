import os
import asyncio
from playwright.async_api import async_playwright
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loltracker.settings')
django.setup()

from summoners.models import Augment

from asgiref.sync import sync_to_async

async def save_augment(name, tier, description, image_url):
    await sync_to_async(Augment.objects.update_or_create)(
        name=name,
        defaults={
            'tier': tier,
            'description': description,
            'image_url': image_url
        }
    )

async def scrape_augments():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🚀 Navigating to the Index...")
        await page.goto("https://apexlol.info/en/hextech/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        tiers = ["silver", "gold", "prismatic"]
        augment_links = [] # Format: (url, tier, name, image_url)

        # Step 1: Collect ALL links and basic info from the index
        for tier in tiers:
            print(f"📂 Scanning {tier.capitalize()} list...")
            await page.click(f"button.tab-btn.{tier}")
            await asyncio.sleep(2)
            
            # Ensure all cards are loaded
            last_height = await page.evaluate("document.body.scrollHeight")
            while True:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height: break
                last_height = new_height

            cards = await page.query_selector_all(".hex-card")
            for card in cards:
                href = await card.get_attribute("href")
                name_el = await card.query_selector(".name")
                img_el = await card.query_selector("img")
                
                if href and name_el and img_el:
                    name = await name_el.inner_text()
                    img_src = await img_el.get_attribute("src")
                    img_url = f"https://apexlol.info{img_src}" if img_src.startswith('/') else img_src
                    augment_links.append({
                        "url": f"https://apexlol.info{href}",
                        "tier": tier.capitalize(),
                        "name": name.strip(),
                        "image_url": img_url
                    })

        print(f"✅ Found {len(augment_links)} total augments. Starting Deep Extraction...")

        # Step 2: Visit each page for the FULL description
        count = 0
        for aug in augment_links:
            try:
                print(f"🔍 [{count+1}/{len(augment_links)}] Extracting Full Description: {aug['name']}")
                await page.goto(aug['url'], wait_until="domcontentloaded", timeout=30000)
                
                desc_el = await page.query_selector(".description-box")
                if desc_el:
                    full_desc = await desc_el.inner_text()
                    await save_augment(aug['name'], aug['tier'], full_desc.strip(), aug['image_url'])
                    count += 1
                else:
                    print(f"⚠️ Warning: No description found for {aug['name']}")
            except Exception as e:
                print(f"❌ Error scraping {aug['name']}: {e}")

        await browser.close()
        print(f"🎉 Success! {count} augments updated with full descriptions.")

if __name__ == "__main__":
    asyncio.run(scrape_augments())
