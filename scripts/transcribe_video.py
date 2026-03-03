# scripts/transcribe_video.py
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from dashscope import Generation

def is_chinese(text, threshold=0.3):
    """判断文本是否主要为中文"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    return chinese_chars / len(text) > threshold if text else False

def translate_to_chinese(text):
    """使用 Qwen-Max 将英文翻译为流畅中文"""
    if not text.strip():
        return ""
    
    prompt = f"""你是一位专业科技翻译。请将以下英文内容准确、流畅地翻译为简体中文，保留技术术语和人名原样：

{text[:8000]}  # 控制长度防超限
"""
    try:
        response = Generation.call(
            model='qwen-max-2026-01-23',
            prompt=prompt,
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            max_tokens=2000
        )
        return response.output.text.strip()
    except Exception as e:
        print(f"⚠️ 翻译失败: {e}")
        return text  # 降级返回原文

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        original_text = ""
        language = "unknown"

        # 1. 优先找中文字幕
        try:
            transcript = transcript_list.find_transcript(['zh-Hans', 'zh-CN'])
            language = "zh"
        except:
            # 2. 找英文字幕
            try:
                transcript = transcript_list.find_transcript(['en'])
                language = "en"
            except:
                # 3. 任意语言（fallback）
                try:
                    transcript = next(iter(transcript_list))
                    language = transcript.language_code
                except:
                    return "字幕不可用"

        if transcript:
            original_text = " ".join([t['text'] for t in transcript.fetch()])
            original_text = original_text[:10000]  # 截断过长内容

            # 3. 判断是否需要翻译
            if language == "zh" or is_chinese(original_text):
                print(f"  → 字幕语言: 中文")
                return original_text
            else:
                print(f"  → 字幕语言: {language}，正在翻译为中文...")
                translated = translate_to_chinese(original_text)
                return translated if translated else original_text
        else:
            return "字幕不可用"
            
    except Exception as e:
        return f"字幕获取失败: {str(e)}"
