import os

from celery import Celery

from modules.placement.schedule import (
    BEAT_SCHEDULE as PLACEMENT_SCHEDULE,
)
from modules.placement.schedule import (
    TASK_ROUTES as PLACEMENT_ROUTES,
)
from modules.leave.schedule import BEAT_SCHEDULE as LEAVE_SCHEDULE
from modules.leave.schedule import TASK_ROUTES as LEAVE_ROUTES

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
app = Celery("fusion_integrated")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(force=True)

# Keep registration deterministic for management commands and tests that
# inspect the beat catalogue before a worker has finalized the app.
from modules.placement import tasks as _placement_tasks  # noqa: F401,E402
from modules.leave import tasks as _leave_tasks  # noqa: F401,E402

# Each module owns its timers; this only merges them, so modules stay removable.
app.conf.beat_schedule = {**PLACEMENT_SCHEDULE, **LEAVE_SCHEDULE}
app.conf.task_routes = {**PLACEMENT_ROUTES, **LEAVE_ROUTES}
