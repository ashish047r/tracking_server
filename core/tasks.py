# import time
# from celery import shared_task
# from django.utils import timezone

# from .models import Mapping
# from .services import generate_suffix_burst



# @shared_task(bind=True)
# def run_burst_task(self, mapping_id):
#     mapping = Mapping.objects.get(id=mapping_id)

#     window_sec = mapping.window_ms / 1000
#     interval = window_sec / mapping.frequency

#     for i in range(mapping.frequency):
#         generate_suffix_burst(mapping)

#         if i < mapping.frequency - 1:
#             time.sleep(interval)


from celery import shared_task
from .models import Mapping
from .services import run_mapping


@shared_task
def refresh_all_mappings():
    for mapping in Mapping.objects.all():
        run_mapping(mapping)
