# Generated by Django 3.2.11 on 2022-02-24 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nfts', '0006_nft_is_minted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nft',
            name='name',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='nfttype',
            name='name',
            field=models.CharField(max_length=60),
        ),
    ]