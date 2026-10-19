from dataclasses import dataclass, field


@dataclass
class ResearchResult:
    topic: str
    summary: str
    sources: list[str]
    steps_used: int
    errors: list[str] = field(default_factory=list)