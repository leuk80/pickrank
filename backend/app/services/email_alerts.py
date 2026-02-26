"""
Email alerts service – Phase 5 implementation.
Sends performance digests and subscription confirmations via SendGrid.
"""


async def send_confirmation_email(email: str, language: str = "de") -> None:
    """Send a subscription confirmation email."""
    raise NotImplementedError("Implemented in Phase 5")


async def send_weekly_digest(email: str) -> None:
    """Send the weekly creator performance digest to a subscriber."""
    raise NotImplementedError("Implemented in Phase 5")
