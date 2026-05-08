"""
© Ocado Group
Created on 19/03/2024 at 12:14:34(+00:00).

Dotdigital helpers.
"""

import json
import logging
import typing as t
from dataclasses import dataclass

import requests
from django.conf import settings

from .types import JsonDict


@dataclass
class Preference:
    """The marketing preferences for a Dotdigital contact."""

    @dataclass
    class Preference:
        """
        The preference values to set in the category. Only supply if
        is_preference is false, and therefore referring to a preference
        category.
        """

        id: int
        is_preference: bool
        is_opted_in: bool

    id: int
    is_preference: bool
    preferences: t.Optional[t.List[Preference]] = None
    is_opted_in: t.Optional[bool] = None


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def add_contact(
    email: str,
    opt_in_type: t.Optional[
        t.Literal["Unknown", "Single", "Double", "VerifiedDouble"]
    ] = None,
    email_type: t.Optional[t.Literal["PlainText, Html"]] = None,
    data_fields: t.Optional[t.Dict[str, str]] = None,
    consent_fields: t.Optional[t.List[t.Dict[str, str]]] = None,
    preferences: t.Optional[t.List[Preference]] = None,
    region: str = "r1",
    auth: t.Optional[str] = None,
    timeout: int = 30,
):
    # pylint: disable=line-too-long
    """Add a new contact to Dotdigital.

    https://developer.dotdigital.com/reference/create-contact-with-consent-and-preferences

    Args:
        email: The email address of the contact.
        opt_in_type: The opt-in type of the contact.
        email_type: The email type of the contact.
        data_fields: Each contact data field is a key-value pair; the key is a string matching the data field name in Dotdigital.
        consent_fields: The consent fields that apply to the contact.
        preferences: The marketing preferences to be applied.
        region: The Dotdigital region id your account belongs to e.g. r1, r2 or r3.
        auth: The authorization header used to enable API access. If None, the value will be retrieved from the MAIL_AUTH environment variable.
        timeout: Send timeout to avoid hanging.

    Raises:
        AssertionError: If failed to add contact.
    """
    # pylint: enable=line-too-long

    if auth is None:
        auth = settings.MAIL_AUTH()

    contact: JsonDict = {"email": email.lower()}
    if opt_in_type is not None:
        contact["optInType"] = opt_in_type
    if email_type is not None:
        contact["emailType"] = email_type
    if data_fields is not None:
        contact["dataFields"] = [
            {"key": key, "value": value} for key, value in data_fields.items()
        ]

    body: JsonDict = {"contact": contact}
    if consent_fields is not None:
        body["consentFields"] = [
            {
                "fields": [
                    {"key": key, "value": value}
                    for key, value in fields.items()
                ]
            }
            for fields in consent_fields
        ]
    if preferences is not None:
        body["preferences"] = [
            {
                "id": preference.id,
                "isPreference": preference.is_preference,
                **(
                    {}
                    if preference.is_opted_in is None
                    else {"isOptedIn": preference.is_opted_in}
                ),
                **(
                    {}
                    if preference.preferences is None
                    else {
                        "preferences": [
                            {
                                "id": _preference.id,
                                "isPreference": _preference.is_preference,
                                "isOptedIn": _preference.is_opted_in,
                            }
                            for _preference in preference.preferences
                        ]
                    }
                ),
            }
            for preference in preferences
        ]

    if not settings.MAIL_ENABLED:
        logging.info(
            "Added contact to DotDigital:\n%s", json.dumps(body, indent=2)
        )
        return

    response = requests.post(
        # pylint: disable-next=line-too-long
        url=f"https://{region}-api.dotdigital.com/v2/contacts/with-consent-and-preferences",
        json=body,
        headers={
            "accept": "application/json",
            "authorization": auth,
        },
        timeout=timeout,
    )

    assert response.ok, (
        "Failed to add contact."
        f" Reason: {response.reason}."
        f" Text: {response.text}."
    )


# pylint: disable-next=unused-argument
def remove_contact(
    value: str,
    identifier: t.Literal["contact-id", "email", "mobile-number"] = "email",
    region: str = "r1",
    auth: t.Optional[str] = None,
    timeout: int = 30,
):
    # pylint: disable=line-too-long
    """Remove an existing contact from Dotdigital.

    https://developer.dotdigital.com/reference/deletecontact-1

    Args:
        value: The unique value to identify the contact. Note: Must be the same type as the identifier.
        identifier: Field to use to uniquely identify the contact.
        region: The Dotdigital region id your account belongs to e.g. r1, r2 or r3.
        auth: The authorization header used to enable API access. If None, the value will be retrieved from the MAIL_AUTH environment variable.
        timeout: Send timeout to avoid hanging.

    Raises:
        AssertionError: If failed to delete contact.

    Returns:
        A flag designating whether the contact was removed. True if the contact
        was found, False if the contact was not found.
    """
    # pylint: enable=line-too-long

    if identifier == "email":
        value = value.lower()

    if not settings.MAIL_ENABLED:
        logging.info("Removed contact from DotDigital: %s", value)
        return True

    if auth is None:
        auth = settings.MAIL_AUTH()

    response = requests.delete(
        # pylint: disable-next=line-too-long
        url=f"https://{region}-api.dotdigital.com/contacts/v3/{identifier}/{value}",
        headers={
            "accept": "application/json",
            "authorization": auth,
        },
        timeout=timeout,
    )

    not_found = response.status_code == 404

    assert response.ok or not_found, (
        "Failed to delete contact."
        f" Reason: {response.reason}."
        f" Text: {response.text}."
    )

    return not not_found


@dataclass
class EmailAttachment:
    """An email attachment for a Dotdigital triggered campaign."""

    file_name: str
    mime_type: str
    content: str


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def send_mail(
    campaign_id: int,
    to_addresses: t.List[str],
    cc_addresses: t.Optional[t.List[str]] = None,
    bcc_addresses: t.Optional[t.List[str]] = None,
    from_address: t.Optional[str] = None,
    personalization_values: t.Optional[t.Dict[str, str]] = None,
    metadata: t.Optional[str] = None,
    attachments: t.Optional[t.List[EmailAttachment]] = None,
    region: str = "r1",
    auth: t.Optional[str] = None,
    timeout: int = 30,
):
    # pylint: disable=line-too-long
    """Send a triggered email campaign using DotDigital's API.

    https://developer.dotdigital.com/reference/send-transactional-email-using-a-triggered-campaign

    Args:
        campaign_id: The ID of the triggered campaign, which needs to be included within the request body.
        to_addresses: The email address(es) to send to.
        cc_addresses: The CC email address or address to to send to. separate email addresses with a comma. Maximum: 100.
        bcc_addresses: The BCC email address or address to to send to. separate email addresses with a comma. Maximum: 100.
        from_address: The From address for your email. Note: The From address must already be added to your account. Otherwise, your account's default From address is used.
        personalization_values: Each personalisation value is a key-value pair; the placeholder name of the personalization value needs to be included in the request body.
        metadata: The metadata for your email. It can be either a single value or a series of values in a JSON object.
        attachments: A Base64 encoded string. All attachment types are supported. Maximum file size: 15 MB.
        region: The Dotdigital region id your account belongs to e.g. r1, r2 or r3.
        auth: The authorization header used to enable API access. If None, the value will be retrieved from the MAIL_AUTH environment variable.
        timeout: Send timeout to avoid hanging.

    Raises:
        AssertionError: If failed to send email.
    """
    # pylint: enable=line-too-long

    if auth is None:
        auth = settings.MAIL_AUTH()

    body = {
        "campaignId": campaign_id,
        "toAddresses": to_addresses,
    }
    if cc_addresses is not None:
        body["ccAddresses"] = cc_addresses
    if bcc_addresses is not None:
        body["bccAddresses"] = bcc_addresses
    if from_address is not None:
        body["fromAddress"] = from_address
    if personalization_values is not None:
        body["personalizationValues"] = [
            {
                "name": key,
                "value": value,
            }
            for key, value in personalization_values.items()
        ]
    if metadata is not None:
        body["metadata"] = metadata
    if attachments is not None:
        body["attachments"] = [
            {
                "fileName": attachment.file_name,
                "mimeType": attachment.mime_type,
                "content": attachment.content,
            }
            for attachment in attachments
        ]

    if not settings.MAIL_ENABLED:
        logging.info(
            "Sent a triggered email with DotDigital:\n%s",
            json.dumps(body, indent=2),
        )
        return

    response = requests.post(
        url=f"https://{region}-api.dotdigital.com/v2/email/triggered-campaign",
        json=body,
        headers={
            "accept": "text/plain",
            "authorization": auth,
        },
        timeout=timeout,
    )

    assert response.ok, (
        "Failed to send email."
        f" Reason: {response.reason}."
        f" Text: {response.text}."
    )
