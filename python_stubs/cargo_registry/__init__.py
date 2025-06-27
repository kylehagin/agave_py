"""Python representation of the `cargo-registry` service."""

class CargoRegistryService:
    """Mirrors the service defined in the Rust crate."""

    async def run(self) -> None:  # noqa: D401
        """Start serving requests."""

    async def handle_publish_request(self, request) -> None:
        """Handle a crate publish request."""

    async def handle_download_crate_request(self, path: str) -> None:
        """Handle a crate download request."""

