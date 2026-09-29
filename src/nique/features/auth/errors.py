from nique.shared.exceptions import NiqueError


class AuthError(NiqueError):
    """Base password and token authorization error."""


class AccountNotFoundError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class AccountBlockedError(AuthError):
    pass


class VerificationRequiredError(AuthError):
    pass


class UnsupportedVerificationError(AuthError):
    pass


class CaptchaRequiredError(AuthError):
    """VK requires an external captcha flow before authorization can continue."""

    def __init__(
        self,
        *,
        sid: str | None = None,
        url: str | None = None,
    ) -> None:
        self.sid = sid
        self.url = url
        super().__init__("VK requires an external captcha challenge resolver")


class AuthFloodControlError(AuthError):
    pass


class AuthProtocolError(AuthError):
    pass


class OAuthAuthorizationError(AuthError):
    pass


class OAuthTokenError(AuthError):
    pass


class TokenValidationError(AuthError):
    pass
