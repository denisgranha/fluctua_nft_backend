# Generated by Django 3.2.11 on 2022-02-25 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nfts', '0010_nftclaim'),
    ]

    operations = [
        migrations.AddField(
            model_name='nft',
            name='contract_id',
            field=models.IntegerField(null=True),
        ),
    ]