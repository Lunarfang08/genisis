class SimulationError(RuntimeError):
    """Base error for deterministic engine failures."""


class InvalidCommandError(SimulationError):
    """Raised when a command cannot be applied in the current state."""


class InvariantViolation(SimulationError):
    """Raised when a system proposes invalid world state."""


class SnapshotIntegrityError(SimulationError):
    """Raised when snapshot content does not match its checksum."""
