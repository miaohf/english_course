"""
日志配置模块

使用 loguru 配置日志，日志输出为英文
支持丰富的颜色配置，便于区分不同的日志部分
"""

import sys
import re
from loguru import logger

# ANSI 颜色代码映射
ANSI_COLORS = {
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'reset': '\033[0m',
    'bold': '\033[1m',
}


def convert_color_tags(text: str) -> str:
    """
    将颜色标签转换为 ANSI 转义序列
    
    Args:
        text: 包含颜色标签的文本，如 "<cyan>text</cyan>"
        
    Returns:
        转换为 ANSI 转义序列的文本
    """
    # 匹配颜色标签，如 <cyan>text</cyan>
    pattern = r'<(\w+)>(.*?)</\1>'
    
    def replace_tag(match):
        color_name = match.group(1).lower()
        content = match.group(2)
        
        # 如果是已知的颜色，转换为 ANSI 代码
        if color_name in ANSI_COLORS:
            return f"{ANSI_COLORS[color_name]}{content}{ANSI_COLORS['reset']}"
        # 如果不是已知颜色，移除标签
        return content
    
    return re.sub(pattern, replace_tag, text)


def strip_color_tags(text: str) -> str:
    """
    移除颜色标签（用于文件输出）
    
    Args:
        text: 包含颜色标签的文本
        
    Returns:
        移除标签后的纯文本
    """
    # 匹配并移除所有颜色标签
    pattern = r'</?\w+>'
    return re.sub(pattern, '', text)


def setup_logger(
    log_level: str = "INFO",
    log_file: str = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
    enable_console: bool = True
):
    """
    配置 loguru 日志
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为 None 则不写入文件
        rotation: 日志轮转大小
        retention: 日志保留时间
        enable_console: 是否启用控制台输出
    """
    # 移除默认的 handler
    logger.remove()
    
    # 使用 loguru 格式，支持消息中的颜色标记
    # 控制台输出 - 启用颜色，支持消息中的颜色标签
    # 注意：{message} 不使用 <level> 包装，以允许消息中的颜色标签生效
    if enable_console:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}",
            level=log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # 文件输出 - 使用纯文本格式（去除颜色标记和 ANSI 代码）
    if log_file:
        # 使用 filter 来去除消息中的颜色标签和 ANSI 代码
        def remove_colors_for_file(record):
            """去除文件输出中的颜色标签和 ANSI 代码"""
            # 去除颜色标签
            clean_message = strip_color_tags(str(record["message"]))
            # 去除 ANSI 转义序列
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_message = ansi_escape.sub('', clean_message)
            record["message"] = clean_message
            return True  # 返回 True 表示记录这条日志
        
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level=log_level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            colorize=False,  # 文件输出不需要颜色
            filter=remove_colors_for_file  # 使用 filter 来修改消息
        )
    
    return logger


# 默认配置
def get_logger():
    """
    获取配置好的 logger 实例
    
    注意：返回的 logger 支持在消息中使用颜色标签（如 <cyan>, <green> 等）
    颜色标签会自动转换为 ANSI 转义序列
    """
    # 创建一个包装，自动转换颜色标签为 ANSI 代码
    class AutoColoredLogger:
        def __init__(self, base_logger):
            self._logger = base_logger
        
        def __getattr__(self, name):
            attr = getattr(self._logger, name)
            if callable(attr) and name in ['info', 'success', 'warning', 'error', 'debug']:
                # 对于日志方法，自动转换颜色标签
                def wrapper(*args, **kwargs):
                    # 转换第一个参数（消息）中的颜色标签
                    if args and isinstance(args[0], str):
                        converted_msg = convert_color_tags(args[0])
                        return attr(converted_msg, *args[1:], **kwargs)
                    return attr(*args, **kwargs)
                return wrapper
            return attr
    
    return AutoColoredLogger(logger)


class ColoredLogger:
    """
    支持颜色标签的 Logger 包装类
    
    由于 loguru 在消息内容中使用颜色标签不太方便，
    这个包装类提供了更简单的方式来使用颜色日志。
    """
    
    def __init__(self, base_logger):
        self._logger = base_logger
    
    def info(self, message: str):
        """输出 INFO 级别的日志，支持颜色标签"""
        # 使用 opt(raw=True) 来禁用转义，让颜色标签生效
        self._logger.opt(raw=True).info(message)
    
    def success(self, message: str):
        """输出 SUCCESS 级别的日志，支持颜色标签"""
        self._logger.opt(raw=True).success(message)
    
    def warning(self, message: str):
        """输出 WARNING 级别的日志，支持颜色标签"""
        self._logger.opt(raw=True).warning(message)
    
    def error(self, message: str):
        """输出 ERROR 级别的日志，支持颜色标签"""
        self._logger.opt(raw=True).error(message)
    
    def debug(self, message: str):
        """输出 DEBUG 级别的日志，支持颜色标签"""
        self._logger.opt(raw=True).debug(message)
    
    def __getattr__(self, name):
        """转发其他方法到原始 logger"""
        return getattr(self._logger, name)


def get_colored_logger():
    """
    获取支持颜色标签的 logger 实例
    
    使用方式：
        from logger_config import get_colored_logger
        logger = get_colored_logger()
        logger.info("<cyan>This is cyan text</cyan>")
    """
    return ColoredLogger(logger)

