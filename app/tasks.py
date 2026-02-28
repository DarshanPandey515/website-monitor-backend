import time
import requests
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Avg


@shared_task
def monitor_websites():
    now = timezone.now()

    websites = Website.objects.filter(is_active=True)

    for website in websites:
        if website.last_checked is None:
            Website.objects.filter(id=website.id).update(last_checked=now)
            check_website.delay(website.id)
            continue

        next_check_time = website.last_checked + \
            timedelta(minutes=website.interval)

        if now >= next_check_time:
            Website.objects.filter(id=website.id).update(last_checked=now)
            check_website.delay(website.id)


@shared_task
def check_website(website_id):
    try:
        website = Website.objects.get(id=website_id)

        start = time.perf_counter()
        session = requests.Session()
        response = session.head(website.website_url, timeout=10)
        end = time.perf_counter()
        response_time = (end - start) * 1000

        is_up = response.status_code == 200

        CheckResult.objects.create(
            website=website,
            status=is_up,
            status_code=response.status_code,
            response_time=response_time,
        )

        website.last_status = is_up
        website.last_response_time = response_time
        website.save(update_fields=["last_status", "last_response_time"])

        channel_layer = get_channel_layer()

        now = timezone.now()
        last_24h = now - timedelta(hours=24)

        check_24h = website.checks.filter(checked_at__gte=last_24h)

        total_checks = check_24h.count()
        successful_checks = check_24h.filter(status=True).count()

        uptime = 0
        if total_checks > 0:
            uptime = round((successful_checks / total_checks) * 100, 2)

        avg_response = check_24h.aggregate(
            avg=Avg("response_time")
        )["avg"] or 0

        latest_check = website.checks.first()

        async_to_sync(channel_layer.group_send)(
            f"monitor_{website.user.id}",
            {
                "type": "website_updates",
                "data": {
                    "website": {
                        "id": website.id,
                        "last_checked": website.last_checked.isoformat(),
                        "last_status": website.last_status,
                        "last_response_time": website.last_response_time,
                    },
                    "metrics": {
                        "uptime_24h": uptime,
                        "avg_response_24h": avg_response,
                        "total_check_24h": total_checks
                    },
                    "new_check": {
                        "id": latest_check.id,
                        "checked_at": latest_check.checked_at.isoformat(),
                        "status": latest_check.status,
                        "status_code": latest_check.status_code,
                        "response_time": latest_check.response_time,
                    }
                }
            }
        )

    except Exception as e:
        CheckResult.objects.create(
            website=website,
            status=False,
            error_message=str(e),
        )

        website.last_checked = timezone.now()
        website.last_status = False
        website.save()
