# Generated by Django 3.2.11 on 2022-02-24 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nfts', '0005_nft_mint_tx'),
    ]

    operations = [
        migrations.AddField(
            model_name='nft',
            name='is_minted',
            field=models.BooleanField(default=False),
        ),
    ]
