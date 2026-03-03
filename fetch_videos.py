# fetch_videos.py
import os
import json
import yaml
import feedparser
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs


def get_video_id(url):
    u = urlparse(url)
    if u.hostname == 'youtu.be':
        return u.path[1:]
    if u.hostname in ('www.youtube.com', 'youtube.com'):
        if u.path == '/watch':
            return parse_qs(u.query)['v'][0]
    return None


def main():
    with open('config/leaders.yaml') as f:
        config = yaml.safe_load(f)
    
    all_videos = []
    seen_ids = set()
    
    # Load history for deduplication
    if os.path.exists('output/history.json'):
        with open('output/history.json') as f:
            seen_ids = set(json.load(f))
    
    for leader in config['leaders']:
        channel_id = leader['youtube_channel_id']
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        try:
            print(f"Fetching from {leader['name']}...")
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                # Parse UTC time correctly
                pub_str = entry.published
                if pub_str.endswith('Z'):
                    pub_str = pub_str[:-1] + '+00:00'
                pub_date = datetime.fromisoformat(pub_str)
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                
                # Check if within last 7 days (UTC)
                cutoff = datetime.now(timezone.utc) - timedelta(days=7)
                if pub_date < cutoff:
                    continue
                
                video_id = get_video_id(entry.link)
                if not video_id or video_id in seen_ids:
                    continue
                
                all_videos.append({
                    'title': entry.title,
                    'url': f"https://youtu.be/{video_id}",
                    'author': leader['name'],
                    'published': entry.published,
                    'video_id': video_id
                })
                seen_ids.add(video_id)
                print(f"  → New: {entry.title}")
        except Exception as e:
            print(f"  ✘ Error: {e}")
    
    # Save history
    os.makedirs('output', exist_ok=True)
    with open('output/history.json', 'w') as f:
        json.dump(list(seen_ids), f)
    
    # Save today's videos
    with open('output/today_videos.json', 'w') as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Found {len(all_videos)} new videos")


if __name__ == '__main__':
    main()
