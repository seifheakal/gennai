"""GenNAI: AI-assisted automated web testing (explore, generate, codegen, execute)."""


class GennaiError(Exception):
    """A user-facing failure (bad input, unreachable site, bad config). CLI exit code 2."""


class NoTestableElements(GennaiError):
    """The page has nothing the tool can test. CLI exit code 3."""
