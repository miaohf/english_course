#!/usr/bin/env python3
"""
日志颜色测试脚本

测试 loguru 日志中的颜色标签是否正常工作
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置 loguru 日志
from logger_config import setup_logger, get_logger

# 设置日志（不写入文件，只输出到控制台）
setup_logger(
    log_level="DEBUG",
    log_file=None,  # 不写入文件，只测试控制台输出
    enable_console=True
)

logger = get_logger()

def test_colors():
    """测试各种颜色标签"""
    print("\n" + "=" * 60)
    print("Testing Loguru Color Tags")
    print("=" * 60 + "\n")
    
    # 测试基本颜色
    logger.info("<cyan>Cyan text - 青色文本</cyan>")
    logger.info("<blue>Blue text - 蓝色文本</blue>")
    logger.info("<green>Green text - 绿色文本</green>")
    logger.info("<yellow>Yellow text - 黄色文本</yellow>")
    logger.info("<magenta>Magenta text - 紫色文本</magenta>")
    logger.info("<red>Red text - 红色文本</red>")
    
    print("\n" + "-" * 60)
    print("Testing mixed colors in one message:")
    print("-" * 60 + "\n")
    
    # 测试混合颜色
    logger.info("<cyan>Step 1:</cyan> <green>Completed</green>")
    logger.info("<blue>Step 2:</blue> <yellow>In progress</yellow>")
    logger.info("<magenta>Translation:</magenta> <green>Success</green>")
    
    print("\n" + "-" * 60)
    print("Testing different log levels:")
    print("-" * 60 + "\n")
    
    # 测试不同日志级别
    logger.debug("<cyan>Debug message with cyan</cyan>")
    logger.info("<blue>Info message with blue</blue>")
    logger.success("<green>Success message with green</green>")
    logger.warning("<yellow>Warning message with yellow</yellow>")
    logger.error("<red>Error message with red</red>")
    
    print("\n" + "-" * 60)
    print("Testing real-world examples:")
    print("-" * 60 + "\n")
    
    # 测试实际使用场景
    logger.info("<cyan>Starting complete story generation for topic: 酒吧点酒</cyan>")
    logger.info("<magenta>Translating topic from Chinese: 酒吧点酒</magenta>")
    logger.info("<green>Topic translated to English: Ordering drinks at a bar</green>")
    logger.info("<blue>Step 1/9: Generating story framework...</blue>")
    logger.info("<green>Story framework generation completed</green>")
    logger.info("<green>✓ Framework saved: outputs/20260103/Ordering_drinks_at_a_bar/story_framework.md</green>")
    
    print("\n" + "-" * 60)
    print("Testing without color tags (should be normal):")
    print("-" * 60 + "\n")
    
    # 测试没有颜色标签的普通文本
    logger.info("Normal text without any color tags")
    logger.info("This is a regular log message")
    
    print("\n" + "=" * 60)
    print("Color test completed!")
    print("=" * 60 + "\n")
    print("If you see colors above, the color tags are working correctly.")
    print("If you see <cyan>, <green> etc. as plain text, colors are not working.")


if __name__ == "__main__":
    test_colors()

