from django.apps import AppConfig


class LeaveConfig(AppConfig):
    name = "modules.leave"
    label = "leave"

    def ready(self):
        # Leave-specific checks would be registered here if applicable.
        pass
