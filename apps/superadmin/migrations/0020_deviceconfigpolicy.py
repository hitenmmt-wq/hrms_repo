from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0019_alter_userdevicetoken_tracking_token"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeviceConfigPolicy",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_deleted", models.BooleanField(default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "key",
                    models.CharField(default="default", max_length=50, unique=True),
                ),
                ("version", models.PositiveIntegerField(default=1)),
                ("idle_threshold_seconds", models.IntegerField(default=60)),
                ("heartbeat_seconds", models.IntegerField(default=60)),
                ("send_interval_seconds", models.IntegerField(default=5)),
                ("timeout_seconds", models.IntegerField(default=5)),
                ("config_reload_seconds", models.IntegerField(default=30)),
                ("remote_config_refresh_seconds", models.IntegerField(default=60)),
            ],
        ),
    ]
