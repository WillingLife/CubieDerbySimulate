import logging
import functools
from enum import Enum, auto

class SuppressInfoFilter(logging.Filter):
    def __init__(self, suppress=True):
        super().__init__()
        self.suppress = suppress

    def filter(self, record):
        if self.suppress and record.levelno == logging.INFO:
            return False
        return True

def suppress_info_logs(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger()
        original_filters = logger.filters[:]
        logger.addFilter(SuppressInfoFilter())
        try:
            return func(*args, **kwargs)
        finally:
            logger.removeFilter(SuppressInfoFilter())
            logger.filters = original_filters
    return wrapper


# 枚举技能触发时机
class SkillTiming(Enum):
    TURN_START = auto()  # 移动前
    MY_TURN = auto()  # 自己行动时
    TURN_END = auto() # 移动后
    GAME_END = auto()  # 所有团子结束时


# 技能钩子装饰器，用于注册在某个时机触发的技能函数
def skill_hook(timing):
    def decorator(func):
        func._skill_timing = timing
        return func

    return decorator