from dataclasses import dataclass

@dataclass
class ResearchResult:
    topic : str 
    summary : str
    sources : list[str]
    step_used = int 
    errors = list[str] 