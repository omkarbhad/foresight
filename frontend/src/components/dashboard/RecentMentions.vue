<template>
  <div class="recent-mentions">
    <div class="mentions-header">
      <h3 class="mentions-title">Recent Mentions</h3>
      <span class="mentions-count">{{ mentions.length }}</span>
    </div>
    <div v-if="mentions.length === 0" class="mentions-empty">
      No recent mentions found.
    </div>
    <ul v-else class="mentions-list">
      <li
        v-for="mention in mentions"
        :key="mention.mention_id"
        class="mention-item"
      >
        <div class="mention-top">
          <span class="source-badge" :class="`source-${mention.source.toLowerCase()}`">
            {{ mention.source }}
          </span>
          <span
            class="sentiment-pill"
            :class="`sentiment-${mention.sentiment_label.toLowerCase()}`"
          >
            {{ mention.sentiment_label }}
            <span class="sentiment-score">{{ formatScore(mention.sentiment_score) }}</span>
          </span>
        </div>
        <div class="mention-title">{{ mention.title }}</div>
        <div v-if="mention.content" class="mention-content">
          {{ truncate(mention.content, 140) }}
        </div>
        <div class="mention-time">{{ formatTime(mention.ingested_at) }}</div>
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'RecentMentions',
  props: {
    mentions: {
      type: Array,
      required: true,
      default: () => [],
    },
  },
  methods: {
    formatScore(score) {
      if (score == null) return '';
      const sign = score > 0 ? '+' : '';
      return `${sign}${score.toFixed(2)}`;
    },
    formatTime(timestamp) {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMin = Math.floor(diffMs / 60000);
      const diffHr = Math.floor(diffMs / 3600000);
      const diffDay = Math.floor(diffMs / 86400000);

      if (diffMin < 1) return 'Just now';
      if (diffMin < 60) return `${diffMin}m ago`;
      if (diffHr < 24) return `${diffHr}h ago`;
      if (diffDay < 7) return `${diffDay}d ago`;
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
      });
    },
    truncate(text, maxLen) {
      if (!text || text.length <= maxLen) return text;
      return text.slice(0, maxLen).trimEnd() + '\u2026';
    },
  },
};
</script>

<style scoped>
.recent-mentions {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
}

.mentions-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.mentions-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.mentions-count {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--border);
  padding: 2px 8px;
  border-radius: 10px;
}

.mentions-empty {
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
  padding: 24px 0;
}

.mentions-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.mention-item {
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}

.mention-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.mention-item:first-child {
  padding-top: 0;
}

.mention-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.source-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--neutral);
  color: var(--surface);
}

.source-badge.source-twitter,
.source-badge.source-x {
  background: #1da1f2;
  color: #fff;
}

.source-badge.source-reddit {
  background: #ff4500;
  color: #fff;
}

.source-badge.source-news {
  background: var(--primary);
  color: #fff;
}

.source-badge.source-blog {
  background: #8b5cf6;
  color: #fff;
}

.source-badge.source-facebook {
  background: #1877f2;
  color: #fff;
}

.sentiment-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: auto;
}

.sentiment-pill.sentiment-positive {
  background: color-mix(in srgb, var(--success) 14%, transparent);
  color: var(--success);
}

.sentiment-pill.sentiment-negative {
  background: color-mix(in srgb, var(--danger) 14%, transparent);
  color: var(--danger);
}

.sentiment-pill.sentiment-neutral {
  background: color-mix(in srgb, var(--neutral) 14%, transparent);
  color: var(--text-secondary);
}

.sentiment-pill.sentiment-mixed {
  background: color-mix(in srgb, var(--warning) 14%, transparent);
  color: var(--warning);
}

.sentiment-score {
  font-weight: 500;
  opacity: 0.8;
}

.mention-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
  line-height: 1.4;
}

.mention-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 6px;
}

.mention-time {
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.7;
}
</style>
