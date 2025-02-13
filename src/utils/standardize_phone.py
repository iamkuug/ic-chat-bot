import re


def standardize_phone_number(phone: str) -> str:
    # Remove any non-digit characters
    phone = re.sub(r"\D", "", phone)

    # Case 1: Already has country code (233xxxxxxxxx)
    if phone.startswith("233") and len(phone) == 12:
        return phone

    # Case 2: Starts with 0 (0xxxxxxxxx)
    if phone.startswith("0") and len(phone) == 10:
        return f"233{phone[1:]}"

    # Case 3: No country code or leading 0 (xxxxxxxxx)
    if not phone.startswith("0") and len(phone) == 9:
        return f"233{phone}"

    # Any other format is invalid
    raise ValueError(
        "Invalid phone number format. Expected formats: 0207412961, 207412961, or 233207412961"
    )
