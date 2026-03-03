# scripts/fetch_podcasts.py
import os
import json
import yaml
import feedparser
import re
from datetime import datetime, timedelta, timezone

def is_relevant(content: str, keywords: list) -> bool:
    """
    精准匹配：确保关键词作为完整单词出现（避免 'AI' 匹配到 'Guitarists'）
    支持中英文（中文无空格，所以用子串；英文用 word boundary）
    """
    content_lower = content.lower()
    
    for kw in keywords:
        kw_lower = kw.lower()
        if not kw_lower.strip():
            continue
        
        # 中文 or 无空格关键词 → 直接子串匹配
        if not any(c.isalpha() and c.isascii() for c in kw_lower):
            if kw_lower in content_lower:
                return True
        else:
            # 英文关键词 → 用正则 \b 边界
            pattern = r'\b' + re.escape(kw_lower) + r'\b'
            if re.search(pattern, content_lower):
                return True
    return False
    
def load_sources():
    with open('config/sources.yaml') as f:
        config = yaml.safe_load(f)
    # 只取 type: podcast 的信源
    podcast_sources = [s for s in config['sources'] if s.get('type') == 'podcast']
    return config['keywords'], podcast_sources

def main():
    keywords, sources = load_sources()
    all_episodes = []
    seen_ids = set()
    
    # 加载历史去重 ID
    if os.path.exists('output/history.json'):
        with open('output/history.json') as f:
            seen_ids = set(json.load(f))
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=100)
    
    for source in sources:
        try:
            print(f"🎧 Fetching podcast: {source['name']}")
            feed = feedparser.parse(source['rss_url'])
            
            for entry in feed.entries:
                # 解析发布时间
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                else:
                    continue
                
                if pub_date < cutoff:
                    continue
                
                # 获取唯一 ID（优先用 id，否则用 link）
                episode_id = getattr(entry, 'id', entry.link)
                if episode_id in seen_ids:
                    continue
                
                # 检查关键词匹配
                title = entry.title.lower()
                summary = getattr(entry, 'summary', '').lower()
                content = title + ' ' + summary
                
                matched = is_relevant(content, keywords)
                if not matched:
                    continue
                
                all_episodes.append({
                    'title': entry.title,
                    'url': entry.link,
                    'author': source['name'],
                    'published': entry.get('published', ''),
                    'episode_id': episode_id,
                    'source_type': 'podcast'
                })
                seen_ids.add(episode_id)
                print(f"  → Matched: {entry.title[:60]}...")
                
        except Exception as e:
            print(f"  ✘ Error fetching {source['name']}: {e}")
    
    # 保存播客单独输出（用于调试）
    os.makedirs('output', exist_ok=True)
    with open('output/podcasts.json', 'w') as f:
        json.dump(all_episodes, f, ensure_ascii=False, indent=2)
    
    # 合并到总历史
    with open('output/history.json', 'w') as f:
        json.dump(list(seen_ids), f)
    
    print(f"\n✅ Found {len(all_episodes)} relevant podcast episodes")

if __name__ == '__main__':
    main()
