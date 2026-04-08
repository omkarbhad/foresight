"""Per-mention Claude analysis: sentiment, crisis score, reach, amplify flag"""

from ..utils.llm_client import get_llm_client
from ..utils.logger import get_logger
from ..models.mention import Mention

logger = get_logger('foresight.analyzer')

ANALYSIS_PROMPT = """Analyze this media mention for a PR monitoring system.

Title: {title}
Source: {source}
Content: {content}

Respond with JSON containing:
- sentiment_score: float -1.0 (very negative) to 1.0 (very positive)
- sentiment_label: one of "positive", "negative", "neutral", "mixed"
- crisis_score: float 0.0 (no crisis) to 1.0 (severe crisis)
- reach_estimate: integer estimated audience reach (0 if unknown)
- amplify_worthy: boolean - true if this is positive coverage worth amplifying
- analysis_summary: string 1-2 sentence summary of the mention's significance
- topics: array of 1-5 topic tags"""


def analyze_mention(mention):
    try:
        client = get_llm_client()
        result = client.chat_json(
            messages=[{
                "role": "user",
                "content": ANALYSIS_PROMPT.format(
                    title=mention.title or "N/A",
                    source=mention.source,
                    content=(mention.content or "")[:3000],
                )
            }],
            system="You are a PR and media analysis expert. Analyze mentions accurately and return structured JSON.",
        )

        Mention.update_analysis(
            mention_id=mention.mention_id,
            sentiment_score=result.get('sentiment_score', 0.0),
            sentiment_label=result.get('sentiment_label', 'neutral'),
            crisis_score=result.get('crisis_score', 0.0),
            reach_estimate=result.get('reach_estimate', 0),
            amplify_worthy=result.get('amplify_worthy', False),
            analysis_summary=result.get('analysis_summary', ''),
            topics=result.get('topics', []),
        )

        logger.info(f"Analyzed mention {mention.mention_id}: sentiment={result.get('sentiment_label')}, crisis={result.get('crisis_score')}")
        return result

    except Exception as e:
        logger.error(f"Failed to analyze mention {mention.mention_id}: {e}")
        return None


def analyze_unprocessed(limit=20):
    mentions = Mention.list_unanalyzed(limit=limit)
    results = []
    for m in mentions:
        result = analyze_mention(m)
        if result:
            results.append(result)
    logger.info(f"Analyzed {len(results)}/{len(mentions)} unprocessed mentions")
    return results
