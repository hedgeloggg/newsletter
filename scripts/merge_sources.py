# scripts/merge_sources.py
import os
import json

def main():
    # 读取视频和播客
    videos = []
    podcasts = []
    
    if os.path.exists('output/today_videos.json'):
        with open('output/today_videos.json') as f:
            videos = json.load(f)
    
    if os.path.exists('output/podcasts.json'):
        with open('output/podcasts.json') as f:
            podcasts = json.load(f)
    
    # 合并
    unified = videos + podcasts
    
    # 按唯一 ID 去重（video_id 或 episode_id）
    seen = set()
    unique_items = []
    for item in unified:
        uid = item.get('video_id') or item.get('episode_id')
        if uid and uid not in seen:
            seen.add(uid)
            unique_items.append(item)
    
    # 保存统一结果
    with open('output/unified_today.json', 'w') as f:
        json.dump(unique_items, f, ensure_ascii=False, indent=2)
    
    print(f"🔀 Merged {len(videos)} videos + {len(podcasts)} podcasts → {len(unique_items)} unique items")

if __name__ == '__main__':
    main()
