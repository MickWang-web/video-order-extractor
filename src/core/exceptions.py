"""
自定义异常
"""


class VideoProcessingError(Exception):
    """视频处理相关错误"""
    pass


class RecognitionError(Exception):
    """视觉识别相关错误"""
    pass


class DataParseError(Exception):
    """数据解析相关错误"""
    pass


class DatabaseError(Exception):
    """数据库相关错误"""
    pass


class ExcelGenerationError(Exception):
    """Excel生成相关错误"""
    pass
