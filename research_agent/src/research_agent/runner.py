import re

from .prompt import TEMPLATES
from .researchresult import ResearchResult


def cited_urls(summary: str) -> list[str]:
    urls = re.findall(r'https?://[^\s\]\)]+', summary)
    # strip trailing punctuation like "." or "," that the regex can capture
    return [u.rstrip('.,;:') for u in urls]


def verify_citations(result: ResearchResult) -> list[str]:
    cited = set(cited_urls(result.summary))
    fetched = set(result.sources)
    return sorted(cited - fetched)


def get_observations(step) -> str:
    """Return the tool output text from a step, whether it's a dict or an object."""
    if isinstance(step, dict):
        obs = step.get("observations")
    else:
        obs = getattr(step, "observations", None)
    return str(obs) if obs else ""


def run_research(topic: str) -> ResearchResult:
    from .agents import get_agent

    agent = get_agent()
    prompt = TEMPLATES["short"].format(topic=topic)

    full_run = agent.run(prompt, return_full_result=True)

    summary = str(full_run.output)
    sources = set()
    errors = []

    for step in full_run.steps:
        obs = get_observations(step)
        if not obs:
            continue

        # fetch_page returns "SOURCE: <url>" at the top of its result
        sources.update(re.findall(r'SOURCE: (https?://[^\s\n]+)', obs))

        # our tools return "ERROR: ..." when something fails
        errors.extend(re.findall(r'ERROR: .*', obs))

    result = ResearchResult(
        topic=topic,
        summary=summary,
        sources=sorted(sources),
        steps_used=len(full_run.steps),
        errors=errors,
    )

    hallucinated_urls = verify_citations(result)
    if hallucinated_urls:
        result.errors.append(f"Hallucinated URLs found: {hallucinated_urls}")

    return result