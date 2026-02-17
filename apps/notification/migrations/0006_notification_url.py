from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notification", "0005_devicetoken"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="url",
            field=models.CharField(blank=True, default="/home", max_length=500),
        ),
    ]
