COMMON_RULES = """
Rules:
- Only cite URLs returned by search AND fetched with fetch_page.
- Do not invent URLs, dates, or facts.
- Search queries must be 2-6 words, not sentences.
- If a search fails, try a shorter query ONCE, then move on.
- Do not print more than 200 characters of any fetched page.
- Do NOT output raw JSON. Use the provided tools.
- Use standard square brackets for citations, e.g., [1].
"""


SHORT_TEMPLATE = f"""
Research {{topic}} and write a 150-250 word cited summary.

On EVERY step you must respond by calling a tool. Never reply with plain text.

Steps:
1. Call get_search_results_as_string exactly 3 times with different short queries.
2. Call fetch_page on the 2 best URLs (max_chars=2000).
3. Call submit_final_answer with a 150-250 word summary, inline [1]/[2]
   markers, and the list of fetched URLs at the end.

{COMMON_RULES}
"""

LONG_TEMPLATE = f"""
Research {{topic}} and write a 500-word cited summary with a section per sub-question.

Output format:
- Think in plain text. When you want to use a tool, use the tool-calling mechanism.
- Do NOT wrap anything in <code> tags.

Phases:
1. Plan — write 2 sub-questions in plain text.
2. Search — call get_search_results_as_string EXACTLY 3 times.
3. Read — call fetch_page on the 2 best URLs, max_chars=2000.
4. Summarize — 450-500 words, inline [1]/[2] markers, URL list at end.

{COMMON_RULES}
"""

COMPARE_TEMPLATE = f"""
Compare {{topic_a}} and {{topic_b}}. Write a 300-word summary with a comparison table.

Output format:
- Think in plain text. When you want to use a tool, use the tool-calling mechanism.
- Do NOT wrap anything in <code> tags.

Phases:
1. Plan — identify 3 comparison dimensions in plain text.
2. Search — call get_search_results_as_string for "{{topic_a}}" once, then for "{{topic_b}}" once, then for "{{topic_a}} vs {{topic_b}}" once.
3. Read — call fetch_page on the 2 most authoritative URLs, max_chars=2000.
4. Compare — write a 300-word summary containing a markdown table comparing them.

{COMMON_RULES}
"""

TEMPLATES = {
    "short": SHORT_TEMPLATE,
    "long": LONG_TEMPLATE,
    "compare": COMPARE_TEMPLATE,
}