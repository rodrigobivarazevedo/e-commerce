# Generated by Django 5.0.2 on 2024-02-23 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0003_rename_minimum_price_auctionlisting_starting_bid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='auctionlisting',
            name='current_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
