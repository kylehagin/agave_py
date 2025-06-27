"""Python interfaces for the `cli` crate."""

def process_command(args: list[str]) -> int:
    """Entry point matching the Rust CLI.

    Parameters
    ----------
    args : list[str]
        Command line arguments.
    """
    return 0


class CliConfig:
    """Configuration options used by the CLI."""

    def __init__(self) -> None:
        self.rpc_url: str = ""

