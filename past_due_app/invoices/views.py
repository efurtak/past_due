from pathlib import Path
from datetime import datetime, timedelta

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import httpx

from .services.ksef_auth import (
    generate_certificates,
    get_auth_challenge,
    sign_xml_with_xades,
    get_auth_status,
)

from .tasks import refresh_access_token


def index(request):
    return render(request, "invoices/index.html")


async def login_to_ksef(request):
    # get challenge
    challenge = await get_auth_challenge()

    # generate certificates
    file_path = Path("private_key.pem")
    if file_path.is_file():
        print("private_key.pem already exists.")
    else:
        generate_certificates()

    # send xades signature
    url = "https://api-test.ksef.mf.gov.pl/v2/auth/xades-signature"
    signed_xml = sign_xml_with_xades(auth_challenge=challenge)
    headers = {"Content-Type": "application/xml"}

    async with httpx.AsyncClient() as client:
        res = await client.post(url, content=signed_xml, headers=headers)

        response = res.json()

        reference_number = response["referenceNumber"]
        token = response["authenticationToken"]["token"]

    # get auth status
    code = await get_auth_status(token=token, reference_number=reference_number)

    # redeem auth token
    if code == 200:
        access_token = cache.get("access_token")

        if access_token is None:
            url = "https://api-test.ksef.mf.gov.pl/v2/auth/token/redeem"
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers)
            
                response = res.json()

                # print(response)

                access_token = response["accessToken"]["token"]
                cache.set("access_token", access_token, timeout=900)

                access_valid_until = response["accessToken"]["validUntil"]
                cache.set("access_valid_until", access_valid_until, timeout=900)

                refresh_token = response["refreshToken"]["token"]
                cache.set("refresh_token", refresh_token, timeout=604800)

                refresh_valid_until = response["refreshToken"]["validUntil"]
                cache.set("refresh_valid_until", refresh_valid_until, timeout=604800)

        time = datetime.fromisoformat(cache.get("access_valid_until")) - timedelta(minutes=5)

        refresh_access_token.apply_async(eta=time)

    return JsonResponse({"status": "success"})