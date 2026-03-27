"""Amplify service - surface positive, high-reach mentions worth promoting"""

from ..models.mention import Mention
from ..utils.logger import get_logger

logger = get_logger('foresight.amplify')


def get_amplify_queue(monitor_id=None, limit=20):
    mentions = Mention.list_amplify_worthy(monitor_id=monitor_id, limit=limit)
    return [m.to_dict() for m in mentions]
