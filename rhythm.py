from dataclasses import dataclass, field
from typing import List, Callable, Sequence

@dataclass(frozen=True)
class Beat:
    timestamp: float
    """Time in seconds when the beat occurred"""

    train: int
    """Id of train that produced the beat"""


@dataclass
class Timeline:
    timestamp: float = 0.0
    """Current time in seconds"""

    speed: float = 1.0
    """Time dilation factor"""

    subscribers: List[Callable[[float, float], List[Beat]]] = field(default_factory=list)
    """List of update methods taking start and end times of update and returning any beats that were produced during the update"""

    beats: List[Beat] = field(default_factory=list)

    def reset(self) -> None:
        self.timestamp = 0.0
        for subscriber in self.subscribers:
            subscriber(0.0, 0.0)
        self.beats = []

    def subscribe(self, subscriber: Callable[[float, float], List[Beat]]) -> None:
        self.subscribers.append(subscriber)

    def update(self, dt: float) -> Sequence[Beat]:
        old = self.timestamp
        new = self.timestamp + dt * self.speed
        new_beats = []
        for subscriber in self.subscribers:
            new_beats += subscriber(old, new)
        new_beats = sorted(new_beats, key=lambda beat: beat.timestamp)
        self.beats += new_beats
        self.timestamp = new
        return new_beats
