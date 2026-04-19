#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QQ聊天记录解析模块

提供QQ PC端导出的TXT格式群聊记录的解析和清洗功能
"""

import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


def parse_qq_log(file_path: str) -> List[Dict[str, str]]:
    """
    解析QQ PC端导出的TXT格式群聊记录

    Args:
        file_path: QQ群聊记录TXT文件的完整路径

    Returns:
        包含字典的列表，每个字典代表一条完整消息：
        - 'time'：消息发送时间，格式为"YYYY-MM-DD HH:MM:SS"
        - 'sender'：发送者昵称
        - 'uin'：发送者QQ号
        - 'content'：合并后的完整消息内容

    Raises:
        FileNotFoundError: 文件不存在
        IOError: 文件无法读取
    """
    header_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ([^\(（]+)[\(（]([^\)）]+)[\)）]$')

    result = []
    current_message = None

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.rstrip('\n')

                match = header_pattern.match(line)
                if match:
                    if current_message:
                        result.append(current_message)

                    time_str = match.group(1)
                    sender = match.group(2).strip()
                    uin = match.group(3).strip()

                    current_message = {
                        'time': time_str,
                        'sender': sender,
                        'uin': uin,
                        'content': ''
                    }
                elif current_message and line.strip():
                    if current_message['content']:
                        current_message['content'] += '\n' + line
                    else:
                        current_message['content'] = line

        if current_message:
            result.append(current_message)

    except FileNotFoundError:
        raise FileNotFoundError(f"文件不存在: {file_path}")
    except Exception as e:
        raise IOError(f"文件读取错误: {str(e)}")

    return result


def clean_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    消息清洗函数，对消息列表进行多规则过滤

    Args:
        messages: 包含消息字典的列表

    Returns:
        清洗后的消息列表
    """
    MEDIA_TAGS = ["[图片]", "[表情]", "[视频]", "[文件]", "[语音消息]", "[戳了戳]"]
    SYSTEM_PATTERNS = [
        "撤回了一条消息", "撤回了消息", "加入了本群", "离开了本群",
        "邀请", "加入了本群", "已将群聊设为"
    ]

    filtered = []

    for msg in messages:
        content = msg['content']

        if content in MEDIA_TAGS:
            continue

        for pattern in SYSTEM_PATTERNS:
            if pattern in content:
                break
        else:
            if len(content) >= 4:
                filtered.append({
                    'time': msg['time'],
                    'sender': msg['sender'],
                    'uin': msg['uin'],
                    'content': msg['content']
                })

    return filtered


def format_messages_for_prompt(messages: List[Dict[str, str]]) -> str:
    """格式化消息列表用于生成提示"""
    formatted = []
    for msg in messages:
        formatted.append(f"[{msg['time']}] {msg['sender']}: {msg['content']}")
    return "\n".join(formatted)


def save_to_markdown(summary_text: str, output_filename: Optional[str] = None) -> bool:
    """
    将总结文本保存为Markdown文件

    Args:
        summary_text: 总结文本内容
        output_filename: 输出文件名，若为None则自动生成

    Returns:
        bool: 保存是否成功
    """
    try:
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"chat_summary_{timestamp}.md"

        output_path = Path(output_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# 聊天记录总结\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(summary_text)

        return True
    except Exception:
        return False


def get_chat_stats(messages: List[Dict[str, str]]) -> Dict:
    """获取聊天统计信息"""
    if not messages:
        return {
            'total_messages': 0,
            'total_members': 0,
            'date_range': '-',
            'media_count': 0
        }

    dates = [msg['time'][:10] for msg in messages]
    members = set(msg['sender'] for msg in messages)

    media_count = sum(1 for msg in messages if any(tag in msg['content'] for tag in ['[图片]', '[视频]', '[表情]']))

    return {
        'total_messages': len(messages),
        'total_members': len(members),
        'date_range': f"{min(dates)} ~ {max(dates)}",
        'media_count': media_count
    }


if __name__ == "__main__":
    print("QQ聊天记录解析模块")
    print("使用方法: from qq_parser import parse_qq_log, clean_messages")