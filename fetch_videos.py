# fetch_videos.py
import os
import json
import yaml
import feedparser
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs

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
    
def get_video_id(url):
    u = urlparse(url)
    if u.hostname == 'youtu.be':
        return u.path[1:]
    if u.hostname in ('www.youtube.com', 'youtube.com'):
        if u.path == '/watch':
            return parse_qs(u.query)['v'][0]
    return None

def load_sources():
    with open('config/sources.yaml') as f:
        config = yaml.safe_load(f)
    # 只取 YouTube 类型的信源
    youtube_sources = [s for s in config['sources'] if s.get('type') == 'youtube']
    return config['keywords'], youtube_sources

def main():
    keywords, sources = load_sources()
    all_videos = []
    seen_ids = set()
    
    # Load history for deduplication
    if os.path.exists('output/history.json'):
        with open('output/history.json') as f:
            seen_ids = set(json.load(f))
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)  # ← 7天！
    
    for source in sources:
        try:
            print(f"🎥 Fetching from {source['name']}...")
            feed = feedparser.parse(source['rss_url'])
            
            for entry in feed.entries:
                # Parse published time (YouTube RSS is UTC)
                pub_str = entry.published
                if pub_str.endswith('Z'):
                    pub_str = pub_str[:-1] + '+00:00'
                pub_date = datetime.fromisoformat(pub_str)
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                
                if pub_date < cutoff:
                    continue
                
                video_id = get_video_id(entry.link)
                if not video_id or video_id in seen_ids:
                    continue
                
                # Match keywords in title + summary
                title = entry.title.lower()
                summary = getattr(entry, 'summary', '').lower()
                content = title + ' ' + summary
                
                matched = any(kw.lower() in content for kw in keywords)
                if not matched:
                    continue
                
                all_videos.append({
                    'title': entry.title,
                    'url': f"https://youtu.be/{video_id}",
                    'author': source['name'],
                    'published': entry.published,
                    'video_id': video_id,
                    'source_type': 'youtube'
                })
                seen_ids.add(video_id)
                print(f"  → Matched: {entry.title[:60]}...")
                
        except Exception as e:
            print(f"  ✘ Error fetching {source['name']}: {e}")
    
    # Save today's videos
    os.makedirs('output', exist_ok=True)
    with open('output/today_videos.json', 'w') as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)
    
    # Update history (merge with podcast IDs later in merge_sources.py)
    if os.path.exists('output/history.json'):
        with open('output/history.json') as f:
            existing_ids = set(json.load(f))
    else:
        existing_ids = set()
    existing_ids.update(seen_ids)
    
    with open('output/history.json', 'w') as f:
        json.dump(list(existing_ids), f)
    
    print(f"\n✅ Found {len(all_videos)} relevant YouTube videos in last 100 days")

if __name__ == '__main__':
    main()
