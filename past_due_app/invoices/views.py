from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render
import httpx

from .services.ksef_auth import (
    generate_certificates,
    get_auth_challenge,
    sign_xml_with_xades,
)


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

        reference_number = response["referenceNumber"]  # noqa: F841
        token = response["authenticationToken"]["token"]  # noqa: F841

    # print(response)

    return JsonResponse(response)
