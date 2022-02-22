from django.core.management.base import BaseCommand  # CommandError


class Command(BaseCommand):
    help = "Mint non deployed NFT's by triggering celery tasks"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Hello World"))

        # 1. get all NFT’s without mint_tx
        # 2. generate 1 or more txs depending on amount of nfts to deploy
        # 3. update all nfts with their respective tx
        # 4. signal celery task that check’s tx status every 5s
