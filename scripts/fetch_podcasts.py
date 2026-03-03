# scripts/fetch_podcasts.py
import os
import json
import yaml
import feedparser
from datetime import datetime, timedelta, timezone

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
                
                matched = any(kw.lower() in content for kw in keywords)
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
