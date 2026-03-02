def analyze_video(title, author, transcript):
    prompt = f"""你是一位顶级科技产业分析师。请对以下视频内容进行深度拆解：

【视频标题】{title}
【主讲人】{author}
【全文转录】{transcript}

请严格按以下结构输出（中文）：
1. **核心论点**（≤3条，每条≤50字）
2. **证据链拆解**（技术/数据/逻辑支撑）
3. **历史一致性检验**（与该人物过去观点是否一致？引用具体事件）
4. **产业影响评估**（对AI芯片/模型/应用/监管的影响，分短期<1年、长期>3年）
5. **潜在风险提示**（技术滥用、夸大宣传、逻辑漏洞等）

要求：避免套话，用 bullet points，保持专业冷静。
"""
    try:
        response = Generation.call(
            model='qwen-max-012026',
            prompt=prompt,
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            max_tokens=2000,
            temperature=0.3,
            timeout=30  # 防止长时间挂起
        )
        
        # ✅ 关键：检查响应是否成功
        if response.status_code != 200 or not response.output:
            error_msg = f"【API调用失败】Code: {getattr(response, 'code', 'Unknown')}, Message: {getattr(response, 'message', 'No message')}"
            print(f"  ✘ {error_msg}")
            return error_msg
        
        result = response.output.text.strip()
        if not result:
            return "【分析返回空结果】"
        
        return result
        
    except Exception as e:
        error_msg = f"【AI分析异常】{str(e)[:150]}"
        print(f"  ✘ {error_msg}")
        return error_msg
