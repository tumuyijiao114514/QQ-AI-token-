#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API 聊天记录总结脚本

安装依赖：
pip install google-genai

使用方法：
from gemini_summarizer import generate_summary

chat_content = '''群聊记录内容'''
summary = generate_summary(chat_content)
print(summary)
"""

import os
import google.genai as genai


def generate_summary(chat_content: str) -> str:
    """
    使用 Gemini API 生成聊天记录总结
    
    Args:
        chat_content: 完整的聊天记录文本字符串
    
    Returns:
        str: Markdown格式的总结文本
    
    Raises:
        ValueError: 输入参数异常
        Exception: API调用异常
    """
    # 验证输入参数
    if not chat_content or not isinstance(chat_content, str):
        raise ValueError("聊天记录内容必须是非空字符串")
    
    # 从环境变量获取API密钥
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("环境变量 GEMINI_API_KEY 未设置")
    
    # 配置Gemini API
    genai.configure(api_key=api_key)
    
    # 系统指令
    system_instruction = (
        "你是一个专业的知识整理专家。请从以下群聊记录中，提取出：\n"
        "1. 核心讨论话题\n"
        "2. 有价值的结论/技巧\n"
        "3. 分享的资源链接\n"
        "\n"
        "忽略所有的日常闲聊、表情包代称和无意义回复。\n"
        "请使用精简的Markdown格式输出，包含清晰的层级结构。"
    )
    
    # 创建模型实例
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )
    
    try:
        # 生成总结
        response = model.generate_content(chat_content)
        
        # 检查响应
        if not response or not response.text:
            raise Exception("API返回为空")
        
        return response.text
        
    except Exception as e:
        if "StopCandidate" in str(e):
            raise Exception("API生成内容被停止")
        elif "BlockedPrompt" in str(e):
            raise Exception("输入内容被API阻止")
        else:
            raise Exception(f"API调用失败: {str(e)}")


if __name__ == "__main__":
    """测试示例"""
    test_content = """
[2023-01-01 10:00:00] 张三: 大家好，今天我们讨论一下Python性能优化
[2023-01-01 10:01:00] 李四: 好的，我最近在做一些性能优化的工作
[2023-01-01 10:02:00] 王五: 我听说使用生成器可以提高内存效率
[2023-01-01 10:03:00] 赵六: 是的，生成器比列表推导式更省内存，特别是处理大量数据时
[2023-01-01 10:04:00] 李四: 还有使用局部变量比全局变量更快
[2023-01-01 10:05:00] 张三: 对了，推荐大家看一下这个文档 https://docs.python.org/3/library/profile.html
[2023-01-01 10:06:00] 王五: 哈哈哈哈
[2023-01-01 10:07:00] 赵六: 👍
[2023-01-01 10:08:00] 李四: 还有一个工具 cProfile 可以用来分析代码性能
[2023-01-01 10:09:00] 张三: 好的，今天讨论很有收获
"""
    
    try:
        summary = generate_summary(test_content)
        print("总结结果:")
        print(summary)
    except Exception as e:
        print(f"错误: {str(e)}")
        print("请确保设置了 GEMINI_API_KEY 环境变量")