import functools
import logging
import random
from collections import defaultdict
from enum import Enum, auto


class SuppressInfoFilter(logging.Filter):
    def __init__(self, suppress=True):
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
    TURN_START = auto()  # 回合开始前
    MY_TURN = auto()  # 自己行动时
    TURN_END = auto()  # 回合结束后


# 技能钩子装饰器，用于注册在某个时机触发的技能函数
def skill_hook(timing):
    def decorator(func):
        func._skill_timing = timing
        return func

    return decorator


# === 团子基类 ===
class Cube:
    def __init__(self, name,pos=0):
        self.name = name  # 团子名称
        self.pos = pos  # 当前所在位置
        self.finished = False  # 是否完成比赛
        self._registered_skills = {t: [] for t in SkillTiming}
        # 注册技能方法
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, '_skill_timing'):
                self._registered_skills[attr._skill_timing].append(attr)

    def __repr__(self):
        return self.name

    # 掷骰子，默认1~3
    def roll_dice(self, game):
        return random.randint(1, 3)

    # 触发技能
    def trigger_skills(self, timing, game):
        for skill_func in self._registered_skills.get(timing, []):
            skill_func(game)


# TODO :判定时刻是否为开始时
class Jinhsi(Cube):
    """
    Jinhsi团子
    """

    @skill_hook(SkillTiming.TURN_START)
    def top_jump(self, game):
        """
        有概率跳到顶层
        :param game:
        :return:
        """
        stack = game.positions[self.pos]
        if len(stack) > 1 and stack[-1] != self:
            if random.random() < 0.4:
                logging.info(f"{self.name}触发技能")
                stack.remove(self)
                stack.append(self)

    @skill_hook(SkillTiming.MY_TURN)
    def move(self, game):
        """
        掷骰子并移动
        :param game:
        :return:
        """
        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        game.move(self, step)


class Changli(Cube):
    """
    Changli团子
    """

    def __init__(self, name, pos=0):
        super().__init__(name, pos)
        self.delay_next_turn = False

    @skill_hook(SkillTiming.TURN_END)
    def maybe_delay(self, game):
        """
        65%概率延迟下次行动
        :param game:
        :return:
        """
        stack = game.positions[self.pos]
        if len(stack) > 1 and stack[0] != self:
            logging.info(f"{self.name}下方堆叠团子，开始判定")
            if random.random() < 0.65:
                logging.info(f"{self.name}判定成功，延迟下次行动")
                self.delay_next_turn = True

    def wants_to_delay(self):
        """
        判定是否延迟下次行动
        :return:
        """
        if self.delay_next_turn:
            self.delay_next_turn = False
            return True
        return False

    @skill_hook(SkillTiming.MY_TURN)
    def move(self, game):
        """
        掷骰子并移动
        :param game:
        :return:
        """
        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        game.move(self, step)


class Calcharo(Cube):
    """
    Calcharo团子
    """

    @skill_hook(SkillTiming.MY_TURN)
    def boost_if_last(self, game):
        """
        如果是最后一个团子，额外走3步
        :param game:
        :return:
        """
        # TODO : 与其他团子重叠时，是否算最后一个团子，目前是算的
        last_pos = min(d.pos for d in game.cubes)
        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        if self.pos == last_pos:
            logging.info(f"{self.name}触发技能")
            step += 3
        # 移动团子
        game.move(self, step)


class Shorekeeper(Cube):
    """
    Shorekeeper团子
    """

    def roll_dice(self, game):
        return random.choice([2, 3])

    @skill_hook(SkillTiming.MY_TURN)
    def move(self, game):
        """
        掷骰子并移动
        :param game:
        :return:
        """
        steps = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{steps}")
        game.move(self, steps)


class Camellya(Cube):
    """
    Camellya团子
    """

    @skill_hook(SkillTiming.MY_TURN)
    def selfish_boost(self, game):
        """
        50%概率不带团子移动，格子上每多1团子+1步
        :param game:
        :return:
        """
        logging.info(f"{self.name}进行技能判定")
        boost = 0
        if random.random() < 0.5:
            logging.info(f"{self.name}触发技能")
            others = [d for d in game.positions[self.pos] if d != self]
            boost = len(others)
            logging.info(f"{self.name}获得额外{boost}步")
        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        game.move(self, step + boost, carry_others=False)


class Carlotta(Cube):
    """
    Carlotta团子
    """

    @skill_hook(SkillTiming.MY_TURN)
    def double_move(self, game):
        """
        28%概率额外掷一次骰子
        :param game:
        :return:
        """
        steps = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{steps}")
        if random.random() < 0.28:
            logging.info(f"{self.name}触发技能")
            steps *= 2
        game.move(self, steps)

class Roccia(Cube):
    """
    Roccia团子
    """

    @skill_hook(SkillTiming.MY_TURN)
    def boost(self, game):
        """
        如果是最后一个团子，额外走2步
        :param game:
        :return:
        """
        order = game.current_order
        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        if order and order[-1] == self:
            logging.info(f"{self.name}是最后一个移动，触发技能")
            step += 2
        game.move(self, step)

class Brant(Cube):
    """
    Brant团子
    """

    @skill_hook(SkillTiming.MY_TURN)
    def boost(self, game):
        """
        如果是第一个移动，额外走2步
        :param game:
        :return:
        """
        order = game.current_order
        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        if order and order[0] == self:
            logging.info(f"{self.name}是第一个移动，触发技能")
            step += 2
        game.move(self, step)

class Cantarella(Cube):
    """
    Cantarella团子
    """
    def __init__(self, name, pos=0):
        super().__init__(name, pos)
        self.has_triggered = False

    @skill_hook(SkillTiming.MY_TURN)
    def sticky_move(self, game):
        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        if not self.has_triggered:
            # 检查每步是否遇到团子
            # TODO 最后一格不知道算不算，现在不算
            for i in range(1, step):
                pos = self.pos + i
                if game.positions[pos]:
                    logging.info(f"{self.name}在第{i}步遇到团子，触发技能")
                    last = step -i
                    # 移到该团子上面
                    game.positions[self.pos].remove(self)
                    self.pos = pos
                    # 整体移动团子
                    carried = game.positions[pos]
                    for d in carried:
                        game.positions[d.pos].remove(d)
                        d.pos += last
                        game.positions[d.pos].append(d)
                    self.has_triggered = True
                    return
        # 如果没有触发技能，正常移动
        game.move(self, step)

class Zani(Cube):
    """
    Zani团子
    """
    def __init__(self, name, pos=0):
        super().__init__(name, pos)
        self.next_bonus = False
        self.current_bonus = False

    def roll_dice(self, game):
        return random.choice([1, 3])

    @skill_hook(SkillTiming.TURN_START)
    def get_bonus(self,game):
        """
        如果是堆叠状态，40%概率下回合额外+2
        :param game:
        :return:
        """
        if self.next_bonus:
            self.current_bonus = True
            self.next_bonus = False
        stack = game.positions[self.pos]
        idx = stack.index(self)

        if len(stack) > 1:
            logging.info(f"{self.name}为堆叠状态，开始判定")
            if random.random() < 0.4:
                logging.info(f"{self.name}当前为堆叠状态，下回合获得额外2格机会")
                self.next_bonus = True


    @skill_hook(SkillTiming.MY_TURN)
    def move(self, game):
        """
        掷骰子只会掷出1或3，若本轮移动前处于堆叠状态，下轮40%概率额外+2（每轮生效）
        :param game:
        :return:
        """

        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        if self.current_bonus:
            logging.info(f"{self.name}获得额外2格奖励")
            step += 2
            self.next_bonus = False
        game.move(self, step)

class Cartethyia(Cube):
    """
    Cartethyia团子
    """
    def __init__(self, name, pos=0):
        super().__init__(name, pos)
        self.triggered = False

    @skill_hook(SkillTiming.MY_TURN)
    def move(self, game):
        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        if self.triggered:
            logging.info(f"{self.name}技能判定")
            if random.random() < 0.6:
                logging.info(f"{self.name}触发技能")
                step += 2
        game.move(self, step)

    @skill_hook(SkillTiming.TURN_END)
    def last_place(self, game):
        """
        若自身移动后仍为最后一名，每局仅触发一次，之后每轮有概率+2格
        :param game:
        :return:
        """
        if self.triggered:
            return
        pos_list = [cube.pos for cube in game.cubes]
        pos_list.sort(reverse=False)
        if self.pos == pos_list[0]:
            logging.info(f"{self.name}为最后一名，触发技能")
            self.triggered = True

class Phoebe(Cube):
    """
    Phoebe团子
    """

    @skill_hook(SkillTiming.MY_TURN)
    def lucky_boost(self, game):
        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        if random.random() < 0.5:
            logging.info(f"{self.name}触发技能，额外前进2格")
            step += 2
        game.move(self, step)





class GameEventDispatcher:
    """
    技能事件派发器，统一调度技能函数
    """
    def __init__(self, game):
        self.game = game

    def dispatch(self, timing, dumpling):
        dumpling.trigger_skills(timing, self.game)



class GameField:
    """
    游戏场地，包含团子列表和格子位置
    """
    def __init__(self, cube_list, finish_line=23,given_order=False):
        self.cubes = cube_list  # 团子列表
        self.finish_line = finish_line
        self.positions = defaultdict(list)  # 每格对应的团子堆栈
        self.dispatcher = GameEventDispatcher(self)
        self._first = True  # 是否第一次初始化
        self.current_order = []  # 当前行动顺序
        # 初始化团子位置
        if not given_order:
            random.shuffle(cube_list)
        for d in cube_list:
            self.positions[d.pos].insert(0,d)

    # 移动团子及其上方堆叠团子
    def move(self, cube, steps, carry_others=True):
        """
        移动团子及其上方堆叠团子
        :param cube: 选定团子
        :param steps: 移动步数
        :param carry_others: 是否携带上方团子
        :return:
        """
        pos = cube.pos
        carried = []
        if carry_others:
            stack = self.positions[pos]
            if cube not in stack:
                logging.error("团子不在当前格子")
                return
            idx = stack.index(cube)
            carried = stack[idx:]
            # 原来的格子移除团子
            for d in carried:
                self.positions[d.pos].remove(d)
        else:
            carried = [cube]
            self.positions[cube.pos].remove(cube)
        logging.info(f"{cube.name}携带{carried}移动{steps}步")
        for d in carried:
            d.pos += steps
            self.positions[d.pos].append(d)
        logging.info(f"当前格子为{self.positions[cube.pos]}")

    def get_winner(self):
        """
        返回获胜者
        :return:
        """
        pos_list = [cube.pos for cube in self.cubes]
        pos_list.sort(reverse=True)
        rank = []
        for pos in pos_list:
            for cube in self.positions[pos][::-1]:
                if cube not in rank:
                    rank.append(cube)
        return rank[0] if rank else None

    # 执行一局游戏，返回获胜者
    def play_game(self):
        while True:
            order = []
            if self._first:
                self._first = False
                order = self.cubes
            else:
                # 随机行动顺序
                order = sorted(self.cubes, key=lambda _: random.random())
                # 延迟行动团子放最后
                delayed = [d for d in order if isinstance(d, Changli) and d.wants_to_delay()]
                order = [d for d in order if d not in delayed] + delayed

            current_order = order
            for d in order:
                if d.finished:
                    continue
                self.dispatcher.dispatch(SkillTiming.TURN_START, d)
                self.dispatcher.dispatch(SkillTiming.MY_TURN, d)
                self.dispatcher.dispatch(SkillTiming.TURN_END, d)
                if d.pos >= self.finish_line:
                    d.finished = True
                    return self.get_winner()


# === 执行模拟若干次，返回胜率 ===
@suppress_info_logs
def simulate_games(num_games=10000):
    winners = defaultdict(int)
    for _ in range(num_games):
        cubes = [
            Calcharo("卡卡罗"),
            Carlotta("珂莱塔", -1),
            Changli("长离",-1),
            Jinhsi("今汐",-2),
            Camellya("椿", -2),
            Shorekeeper("守岸人",-3),
        ]
        game = GameField(cubes,given_order=True)
        winner = game.play_game()
        winners[winner.name] += 1
    return winners


# simulate_games(1000)  # 小规模模拟预览
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,filename='log.log',encoding='utf-8')
    print(simulate_games())  # 大规模模拟
