import json
from django.core.management.base import BaseCommand
from summoners.models import Augment

class Command(BaseCommand):
    help = 'Imports scraped ARAM Mayhem augments into the database'

    def handle(self, *args, **options):
        # Data scraped from apexlol.info
        augments_data = [
            {"name": "Typhoon", "tier": "Silver", "description": "Basic attacks fire a bolt at an additional target dealing 50% damage. This bolt can critically strike and applies on-hit effects.", "image_url": "https://apexlol.info/images/hextech/87.webp"},
            {"name": "Self Destruct", "tier": "Silver", "description": "Automatically attach a bomb to yourself that detonates after a delay, dealing magic damage to nearby enemies.", "image_url": "https://apexlol.info/images/hextech/SelfDestruct.webp"},
            {"name": "Ice Cold", "tier": "Silver", "description": "Your slow effects reduce the movement speed of targets by an additional 15%.", "image_url": "https://apexlol.info/images/hextech/44.webp"},
            {"name": "Demon's Dance", "tier": "Gold", "description": "Gain the Fleet Footwork and Grasp of the Undying keystone runes.", "image_url": "https://apexlol.info/images/hextech/23.webp"},
            {"name": "Marksmage", "tier": "Gold", "description": "Basic attacks deal 'bonus' magic damage equal to 100% of your Ability Power. (Only triggers once every 0.1s against the same target)", "image_url": "https://apexlol.info/images/hextech/129.webp"},
            {"name": "Searing Dawn", "tier": "Gold", "description": "Your abilities mark enemies, dealing 24 - 160 'bonus' magic damage on your next basic attack.", "image_url": "https://apexlol.info/images/hextech/72.webp"},
            {"name": "Cerberus", "tier": "Prismatic", "description": "Gain the Attack resets increase the attack limit by 150 for 5s. Your attacks also deal additional damage.", "image_url": "https://apexlol.info/images/hextech/323.webp"},
            {"name": "Quantum Computing", "tier": "Prismatic", "description": "Automatically cast an improved version of Camille's Tactical Sweep in a circle around you.", "image_url": "https://apexlol.info/images/hextech/66.webp"},
            {"name": "Blade Waltz", "tier": "Prismatic", "description": "Replaces the summoner spell in the slot not occupied by Flash. Dash to a target and deal physical damage while becoming untargetable.", "image_url": "https://apexlol.info/images/hextech/6.webp"},
            {"name": "Quest: Urf's Champion", "tier": "Prismatic", "description": "Quest: Score 18 champion takedowns. Reward: Upon completion, gain the Golden Spatula item.", "image_url": "https://apexlol.info/images/hextech/154.webp"},
            {"name": "Master of Duality", "tier": "Prismatic", "description": "Basic attacks on-hit grant 6 to 18 ability power and physical attacks grant 3 to 9 attack damage, stacking indefinitely.", "image_url": "https://apexlol.info/images/hextech/54.webp"},
            {"name": "Stuck In Here With Me", "tier": "Prismatic", "description": "Gain 30 Ultimate Haste. After casting your Ultimate, create a zone that traps enemies inside.", "image_url": "https://apexlol.info/images/hextech/stuckinherewithme.webp"},
            {"name": "???", "tier": "Prismatic", "description": "Your Missing Pings launch a missile at the targeted location, dealing damage based on your missing health.", "image_url": "https://apexlol.info/images/hextech/missingping.webp"}
        ]

        count = 0
        for aug in augments_data:
            obj, created = Augment.objects.update_or_create(
                name=aug['name'],
                defaults={
                    'tier': aug['tier'],
                    'description': aug['description'],
                    'image_url': aug['image_url']
                }
            )
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {count} augments!"))
