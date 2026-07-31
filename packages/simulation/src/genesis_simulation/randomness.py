import random
from typing import cast

type RandomStateValue = int | None | tuple[RandomStateValue, ...]


class DeterministicRandom:
    """Private PRNG wrapper that prevents accidental use of module randomness."""

    algorithm = "python-mt19937"
    version = 1

    def __init__(self, *, seed: int | None = None, state: RandomStateValue | None = None) -> None:
        self._random = random.Random()
        if state is not None:
            self._random.setstate(cast(tuple[int, tuple[int, ...], None], state))
        elif seed is not None:
            self._random.seed(seed, version=2)
        else:
            raise ValueError("seed or state is required")

    def randint(self, minimum: int, maximum: int) -> int:
        return self._random.randint(minimum, maximum)

    def random(self) -> float:
        return self._random.random()

    def choice_index(self, length: int) -> int:
        if length <= 0:
            raise ValueError("length must be positive")
        return self._random.randrange(length)

    def get_state(self) -> RandomStateValue:
        return cast(RandomStateValue, self._random.getstate())


def state_to_json(value: RandomStateValue) -> int | None | list[object]:
    if isinstance(value, tuple):
        return [state_to_json(item) for item in value]
    return value


def state_from_json(value: int | None | list[object]) -> RandomStateValue:
    if isinstance(value, list):
        return tuple(state_from_json(cast(int | None | list[object], item)) for item in value)
    return value
