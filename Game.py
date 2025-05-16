import logging
from collections import defaultdict
import random

class GameEventDispatcher:
    """
    技能事件派发器，统一调度技能函数
    """
    def __init__(self, game):
        self.game = game

    def dispatch(self, timing, cube):
        cube.trigger_skills(timing, self.game)



class GameField:
    """
    游戏场地，包含团子列表和格子位置
    """
    def __init__(self, cube_list, finish_line=23,given_order=False):
        self.cubes = cube_list  # 团子列表
        self.finish_line = finish_line
        self.positions = defaultdict(list)  # 每格对应的团子堆栈
        self.dispatcher = GameEventDispatcher(self)
        self._first = True  # 是否第一次
        self.current_order = []  # 当前行动顺序
        # 初始化团子位置
        if not given_order:
            random.shuffle(cube_list)
        else:
            self._first = False
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
                order = self.cubes[::-1]  # 反向行动顺序
            else:
                # 随机行动顺序
                order = sorted(self.cubes, key=lambda _: random.random())
                # 延迟行动团子放最后
                delayed = [d for d in order if isinstance(d, Changli) and d.wants_to_delay()]
                order = [d for d in order if d not in delayed] + delayed

            self.current_order = order
            for d in order:
                if d.finished:
                    continue
                self.dispatcher.dispatch(SkillTiming.TURN_START, d)
                self.dispatcher.dispatch(SkillTiming.MY_TURN, d)
                self.dispatcher.dispatch(SkillTiming.TURN_END, d)
                if d.pos >= self.finish_line:
                    d.finished = True
                    return self.get_winner()

            # 轮次结束后的技能触发
            for d in self.cubes:
                self.dispatcher.dispatch(SkillTiming.GAME_END, d)

