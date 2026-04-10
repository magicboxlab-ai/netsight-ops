"""OAuth 2.0 backend registry for NetSight.

:class:`OAuthProvider` is an abstract base class that third-party integrations
should subclass to implement the authorisation-code flow for a specific
identity provider (Google, GitHub, Azure AD, etc.).

:class:`OAuthBackend` acts as a registry, letting the application register
multiple providers by name and retrieve them on demand.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class OAuthProvider(ABC):
    """Abstract interface for an OAuth 2.0 authorisation-code provider.

    Subclasses must implement both abstract methods to participate in the
    three-legged OAuth flow.
    """

    @abstractmethod
    def get_authorization_url(self, redirect_uri: str) -> str:
        """Return the URL to which the user-agent should be redirected.

        Args:
            redirect_uri: The URI to which the provider will redirect after
                          the user grants (or denies) consent.

        Returns:
            The full authorisation URL including all required query parameters.
        """
        ...

    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str) -> dict[str, str]:
        """Exchange an authorisation code for access (and optional refresh) tokens.

        Args:
            code:         The short-lived authorisation code returned by the
                          provider's redirect.
            redirect_uri: Must match the ``redirect_uri`` used in the initial
                          authorisation request.

        Returns:
            A mapping that must include at least ``"access_token"`` and
            typically also ``"token_type"``, ``"expires_in"``, and optionally
            ``"refresh_token"``.
        """
        ...


class OAuthBackend:
    """Registry that maps provider names to :class:`OAuthProvider` instances.

    Example::

        backend = OAuthBackend()
        backend.register_provider("google", GoogleOAuthProvider(...))
        provider = backend.get_provider("google")
        url = provider.get_authorization_url(redirect_uri="https://app/callback")
    """

    def __init__(self) -> None:
        self._providers: dict[str, OAuthProvider] = {}

    def register_provider(self, name: str, provider: OAuthProvider) -> None:
        """Register an OAuth provider under *name*.

        Args:
            name:     Identifier used to look up this provider later
                      (e.g. ``"google"``, ``"github"``).
            provider: A concrete :class:`OAuthProvider` instance.
        """
        self._providers[name] = provider

    def get_provider(self, name: str) -> OAuthProvider | None:
        """Return the provider registered under *name*, or ``None``.

        Args:
            name: The provider identifier.

        Returns:
            The :class:`OAuthProvider` if found, ``None`` otherwise.
        """
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """Return a sorted list of registered provider names.

        Returns:
            Alphabetically sorted list of provider name strings.
        """
        return sorted(self._providers.keys())
