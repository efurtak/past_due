from celery import shared_task
from django.core.cache import cache
import httpx
from datetime import datetime, timedelta


@shared_task(name="past_due_app.invoices.tasks.refresh_access_token")
def refresh_access_token():
    refresh_token = cache.get("refresh_token")
    url = "https://api-test.ksef.mf.gov.pl/v2/auth/token/refresh"
    headers = {"Authorization": f"Bearer {refresh_token}"}

    with httpx.Client() as client:
        res = client.post(url, headers=headers)

        response = res.json()

        access_token = response["accessToken"]["token"]
        cache.set("access_token", access_token, timeout=900)

        access_valid_until = response["accessToken"]["validUntil"]
        cache.set("access_valid_until", access_valid_until, timeout=900)
    
    time = datetime.fromisoformat(cache.get("access_valid_until")) - timedelta(minutes=5)

    print(f"*** time: {time} ***")

    refresh_access_token.apply_async(eta=time)