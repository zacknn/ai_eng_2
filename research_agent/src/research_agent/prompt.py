COMMON_RULES = """
Rules:
- Only cite URLs returned by search AND fetched with fetch_page.
- Do not invent URLs, dates, or facts.
- Search queries must be 2-6 words, not sentences.
- If a search fails, try a shorter query ONCE, then move on.
- Do not print more than 200 characters of any fetched page.
- When done, call the final_answer tool with the summary.
"""

# still not completed

TEMPLATES = {
    "short": """
Research {{topic}} and write a 150-250 word cited summary.

Output format:
- Think in plain text. When you want to use a tool, use the tool-calling mechanism.
- Do NOT wrap anything in <code> tags.
- Use triple-quoted strings for multi-line text if you write any.

Phases:
1. Plan — write 2 sub-questions in plain text.
2. Search — call get_search_results_as_string EXACTLY 3 times.
3. Read — call fetch_page on the 2 best URLs, max_chars=2000.
4. Summarize — 150-250 words, inline [1]/[2] markers, URL list at end.

{COMMON_RULES}
""",
    "long": """
Research {topic} and write a 500-word cited summary with a section
per sub-question.

Output format:
- Think in plain text. When you want to use a tool, use the tool-calling mechanism.
- Do NOT wrap anything in <code> tags.
- Use triple-quoted strings for multi-line text if you write any.

Phases:
1. Plan — write 2 sub-questions in plain text.
2. Search — call get_search_results_as_string EXACTLY 3 times.
3. Read — call fetch_page on the 2 best URLs, max_chars=2000.
4. Summarize — 450 - 500 words, inline [1]/[2] markers, URL list at end.
""",
    "compare": """
Compare {topic_a} and {topic_b}. Write a 300-word summary with a
comparison table.

Output format:
- Think in plain text. When you want to use a tool, use the tool-calling mechanism.
- Do NOT wrap anything in <code> tags.
- Use triple-quoted strings for multi-line text if you write any.

Phases:
1. Plan — identify 3 comparison dimensions (e.g., cost, speed, use-cases) in plain text.
2. Search — call get_search_results_as_string for "{topic_a}" once, then for "{topic_b}" once, then for "{topic_a} vs {topic_b}" once.
3. Read — call fetch_page on the 2 most authoritative URLs (one per topic, or one comparison article), max_chars=2000.
4. Compare — write a 300-word summary containing:
   - One-sentence verdict on which is better for specific use cases
   - A markdown table with 3 rows (your dimensions) comparing {topic_a} vs {topic_b}
   - Inline [1]/[2] citation markers after specific claims
   - URL list at end

{COMMON_RULES}
""",
}

TASK = """
Research the origins of the Linux kernel and write a
short cited summary.

Output format:
- Every response must be a Python code block wrapped in <code>...</code>.
- Do NOT write prose outside the code block.
- To "write down" a plan or notes, use print() inside a code block.
- Use triple-quoted strings for multi-line text. Do NOT use \\n escapes.

Follow these phases IN ORDER:

Phase 1 — Plan (1 step only).
  Print 3 short sub-questions. Keep them under 10 words each.

Phase 2 — Search (EXACTLY 3 searches, then stop).
  For each sub-question, call get_search_results_as_string with a
  2-6 word query and num_results=3.

Phase 3 — Read (EXACTLY 2 fetches, then stop).
  Pick the 2 best URLs from your search results. Call fetch_page on each
  with max_chars=2000.

Phase 4 — Summarize (1 step).
  Write a 150-250 word summary. Every claim gets an inline marker [1] or [2].
  End with a numbered list of the URLs you actually fetched.
  Do NOT print the fetched page text again — you already have it.

Rules:
- Only cite URLs returned by search AND fetched with fetch_page.
- Do not invent URLs, dates, or facts.
- Search queries must be 2-6 words, not sentences.
- If a search fails, try a shorter query ONCE, then move on.
- Do not print more than 200 characters of any fetched page.

When done, call final_answer(...) with the summary text.
"""
