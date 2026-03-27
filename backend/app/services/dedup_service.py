"""Content deduplication service"""

import hashlib
from ..models.mention import Mention
from ..utils.logger import get_logger

logger = get_logger('foresight.dedup')


def compute_content_hash(source, title, content):
    text = f"{source}|{title or ''}|{content or ''}"
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:32]


def is_duplicate(content_hash):
    return Mention.exists_by_hash(content_hash)
