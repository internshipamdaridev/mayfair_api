# Generated by Django 5.1.8 on 2025-05-02 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_category_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='image',
            field=models.FileField(blank=True, null=True, upload_to='category_images/'),
        ),
    ]
