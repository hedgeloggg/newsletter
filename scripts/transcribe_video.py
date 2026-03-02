# scripts/transcribe_video.py
from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        
        # Prefer Chinese, then English
        try:
            transcript = transcript_list.find_transcript(['zh-Hans', 'zh-CN'])
        except:
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                pass
        
        if transcript:
            text = " ".join([t['text'] for t in transcript.fetch()])
            return text[:12000]  # Truncate to fit Qwen context
        else:
            return "字幕不可用"
    except Exception as e:
        return f"字幕获取失败: {str(e)}"
