# Generated by Django 5.2.1 on 2025-05-26 21:51

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0002_content_delete_countlog"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="content",
            name="content",
        ),
        migrations.RemoveField(
            model_name="content",
            name="created_at",
        ),
        migrations.RemoveField(
            model_name="content",
            name="updated_at",
        ),
    ]
