from django.apps import AppConfig


class LabInventoryConfig(AppConfig):
    name = 'apps.lab_inventory'

    def ready(self):
        import apps.lab_inventory.signals  # noqa
