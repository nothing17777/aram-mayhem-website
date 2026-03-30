import os
import asyncio
from playwright.async_api import async_playwright
import django
from asgiref.sync import sync_to_async

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loltracker.settings')
django.setup()

from summoners.models import Champion, Augment, ChampionAugmentRating

async def save_synergy(champ_name, aug_name, rating, note):
    try:
        champ = await sync_to_async(Champion.objects.filter(name__icontains=champ_name).first)()
        augment = await sync_to_async(Augment.objects.filter(name__icontains=aug_name).first)()
        
        if champ and augment:
            await sync_to_async(ChampionAugmentRating.objects.update_or_create)(
                champion=champ,
                augment=augment,
                defaults={
                    'rating': rating,
                    'note': note
                }
            )
            return True
    except Exception as e:
        print(f"⚠️ Error saving synergy: {e}")
    return False

async def scrape_synergies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🚀 Navigating to Champions Index...")
        await page.goto("https://apexlol.info/en/champions/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        champ_cards = await page.query_selector_all("a.champ-card")
        champ_links = []
        for card in champ_cards:
            href = await card.get_attribute("href")
            name_el = await card.query_selector(".name")
            if href and name_el:
                name = await name_el.inner_text()
                champ_links.append({"url": f"https://apexlol.info{href}", "name": name.strip()})
        
        print(f"📈 Found {len(champ_links)} Champions. Starting Synergy Extraction...")

        for i, champ_info in enumerate(champ_links):
            try:
                print(f"🧬 [{i+1}/{len(champ_links)}] Scanning Synergies for: {champ_info['name']}")
                await page.goto(champ_info['url'], wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                
                interaction_cards = await page.query_selector_all(".interaction-card")
                for icard in interaction_cards:
                    aug_name_el = await icard.query_selector(".hex-name")
                    rating_el = await icard.query_selector(".rating-badge")
                    note_el = await icard.query_selector(".note")
                    
                    if aug_name_el and rating_el:
                        aug_name = await aug_name_el.inner_text()
                        rating = await rating_el.inner_text()
                        note = await note_el.inner_text() if note_el else ""
                        await save_synergy(champ_info['name'], aug_name.strip(), rating.strip(), note.strip())

            except Exception as e:
                print(f"❌ Error scraping {champ_info['name']}: {e}")

        await browser.close()
        print("🎉 Success! Original setup restored and meta-data synced.")

if __name__ == "__main__":
    asyncio.run(scrape_synergies())
