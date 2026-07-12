from datetime import datetime, timedelta, timezone
import asyncio
import base64

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree
import httpx
import xmlsec


async def get_auth_challenge():
    async with httpx.AsyncClient() as client:
        res = await client.post("https://api-test.ksef.mf.gov.pl/v2/auth/challenge")

        response = res.json()

        return response["challenge"]


def generate_certificates():
    # generating private_key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # extracting public_key
    public_key = private_key.public_key()

    # creating metadata
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.GIVEN_NAME, "Jan"),
            x509.NameAttribute(NameOID.SURNAME, "Kowalski"),
            x509.NameAttribute(NameOID.SERIAL_NUMBER, "NIP-1234567890"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Jan Kowalski"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "PL"),
        ]
    )

    # building certificate
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(private_key, hashes.SHA256())
    )

    # saving private_key to PEM file
    with open("private_key.pem", "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # saving certificate to PEM file
    with open("certificate.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


def sign_xml_with_xades(auth_challenge):
    # prepare xml structure
    root = etree.Element(
        "AuthTokenRequest", xmlns="http://ksef.mf.gov.pl/auth/token/2.0"
    )
    challenge = etree.SubElement(root, "Challenge")
    challenge.text = auth_challenge
    context_identifier = etree.SubElement(root, "ContextIdentifier")
    nip = etree.SubElement(context_identifier, "Nip")
    nip.text = "1234567890"
    subject_identifier_type = etree.SubElement(root, "SubjectIdentifierType")
    subject_identifier_type.text = "certificateSubject"

    # opening private_key and certificate
    with open("private_key.pem", "r") as key_file:
        private_key = key_file.read()

    with open("certificate.pem", "r") as cert_file:
        certificate = cert_file.read()

    # lines below based on:
    # https://github.com/smekcio/ksef-client-python/blob/main/src/ksef_client/services/xades.py
    cert = x509.load_pem_x509_certificate(certificate.encode("ascii"))
    cert_digest = base64.b64encode(cert.fingerprint(hashes.SHA256())).decode("ascii")

    signature_id = "Signature"
    signed_props_id = "SignedProperties"

    # public_key = cert.public_key()
    signature_transform = xmlsec.Transform.RSA_SHA256

    signature_node = xmlsec.template.create(
        root,
        xmlsec.Transform.EXCL_C14N,
        signature_transform,
        ns="ds",
    )
    signature_node.set("Id", signature_id)
    root.append(signature_node)

    # Reference to the whole document (enveloped)
    ref = xmlsec.template.add_reference(signature_node, xmlsec.Transform.SHA256, uri="")
    xmlsec.template.add_transform(ref, xmlsec.Transform.ENVELOPED)
    xmlsec.template.add_transform(ref, xmlsec.Transform.EXCL_C14N)

    # XAdES SignedProperties
    # python-xmlsec exposes helpers for references/transforms/key-info, but not for
    # ds:Object. Create it manually to keep compatibility across versions.
    if hasattr(xmlsec.template, "add_object"):  # pragma: no cover
        obj = xmlsec.template.add_object(signature_node)
    else:
        obj = etree.SubElement(signature_node, f"{{{xmlsec.constants.DSigNs}}}Object")
    xades_ns = "http://uri.etsi.org/01903/v1.3.2#"
    ds_ns = xmlsec.constants.DSigNs
    qual_props = etree.SubElement(
        obj,
        f"{{{xades_ns}}}QualifyingProperties",
        nsmap={"xades": xades_ns, "ds": ds_ns},
    )
    qual_props.set("Target", f"#{signature_id}")

    signed_props = etree.SubElement(qual_props, f"{{{xades_ns}}}SignedProperties")
    signed_props.set("Id", signed_props_id)
    signed_sig_props = etree.SubElement(
        signed_props, f"{{{xades_ns}}}SignedSignatureProperties"
    )

    signing_time = etree.SubElement(signed_sig_props, f"{{{xades_ns}}}SigningTime")
    signing_time.text = datetime.now(timezone.utc).isoformat()

    signing_cert = etree.SubElement(
        signed_sig_props, f"{{{xades_ns}}}SigningCertificate"
    )
    cert_node = etree.SubElement(signing_cert, f"{{{xades_ns}}}Cert")
    cert_digest_node = etree.SubElement(cert_node, f"{{{xades_ns}}}CertDigest")
    digest_method = etree.SubElement(
        cert_digest_node, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod"
    )
    digest_method.set("Algorithm", xmlsec.Transform.SHA256.href)
    digest_value = etree.SubElement(
        cert_digest_node, "{http://www.w3.org/2000/09/xmldsig#}DigestValue"
    )
    digest_value.text = cert_digest

    issuer_serial = etree.SubElement(cert_node, f"{{{xades_ns}}}IssuerSerial")
    issuer_name = etree.SubElement(
        issuer_serial, "{http://www.w3.org/2000/09/xmldsig#}X509IssuerName"
    )
    issuer_name.text = cert.issuer.rfc4514_string()
    serial_number = etree.SubElement(
        issuer_serial, "{http://www.w3.org/2000/09/xmldsig#}X509SerialNumber"
    )
    serial_number.text = str(cert.serial_number)

    # Reference to SignedProperties
    ref_props = xmlsec.template.add_reference(
        signature_node,
        xmlsec.Transform.SHA256,
        uri=f"#{signed_props_id}",
        type="http://uri.etsi.org/01903#SignedProperties",
    )
    xmlsec.template.add_transform(ref_props, xmlsec.Transform.EXCL_C14N)

    key_info = xmlsec.template.ensure_key_info(signature_node)
    xmlsec.template.add_x509_data(key_info)

    ctx = xmlsec.SignatureContext()
    ctx.key = xmlsec.Key.from_memory(private_key, xmlsec.KeyFormat.PEM, None)
    ctx.key.load_cert_from_memory(certificate, xmlsec.KeyFormat.PEM)
    ctx.sign(signature_node)

    signed_xml = etree.tostring(root, encoding="utf-8", xml_declaration=True).decode(
        "utf-8"
    )

    # print(signed_xml)

    return signed_xml


async def get_auth_status(token, reference_number):
    url = f"https://api-test.ksef.mf.gov.pl/v2/auth/{reference_number}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        while True:
            res = await client.get(url, headers=headers)
            
            response = res.json()

            print(response)

            code = response["status"]["code"]
            
            if code == 200:
                return code

            asyncio.sleep(5)