from django.core.management.base import BaseCommand
from summoners import riot_service
from summoners.models import Champion

class Command(BaseCommand):
    help = 'Fetches all champions from Riot Data Dragon and saves them to the SQLite database'

    def handle(self, *args, **options):
        self.stdout.write("Fetching latest champions from Riot...")
        champs_data = riot_service.get_all_champions_data()
        version = riot_service.get_latest_version()
        
        count = 0
        for champion_id, data in champs_data.items():
            name = data['name']
            tags = data.get('tags', ['Unknown'])
            primary_tag = tags[0] if tags else 'Unknown'
            
            # Icon URL using the latest version
            image_url = f"http://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champion_id}.png"
            
            # Save to Database
            obj, created = Champion.objects.update_or_create(
                name=name,
                defaults={
                    'image_url': image_url,
                    'champion_class': primary_tag,
                }
            )
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Successfully sync'd {count} champions to the database!"))
