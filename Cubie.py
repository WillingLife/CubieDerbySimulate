import logging
import random
from decorators import skill_hook,SkillTiming

class Cube:
    """
    团子基类
    """
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
    def __init__(self, name="今汐", pos=0):
        super().__init__(name, pos)

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

    def __init__(self, name="长离", pos=0):
        super().__init__(name, pos)
        self.delay_next_turn = False

    @skill_hook(SkillTiming.GAME_END)
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
    def __init__(self, name="卡卡罗", pos=0):
        super().__init__(name, pos)

    @skill_hook(SkillTiming.MY_TURN)
    def boost_if_last(self, game):
        """
        如果是最后一个团子，额外走3步
        :param game:
        :return:
        """
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
    def __init__(self, name="守岸人", pos=0):
        super().__init__(name, pos)

    def roll_dice(self, game):
        return random.choice([2, 3])

    @skill_hook(SkillTiming.MY_TURN)
    def move(self, game):
        """
        掷骰子并移动 只能掷2或3
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
    def __init__(self, name="椿", pos=0):
        super().__init__(name, pos)

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
    def __init__(self, name="珂莱塔", pos=0):
        super().__init__(name, pos)

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
    def __init__(self, name="洛可可", pos=0):
        super().__init__(name, pos)


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
    def __init__(self, name="布兰特", pos=0):
        super().__init__(name, pos)

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
    def __init__(self, name="坎特蕾拉", pos=0):
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
    def __init__(self, name="赞妮", pos=0):
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
            self.current_bonus = False
            logging.info(f"{self.name}获得额外2格奖励")
            step += 2
            self.next_bonus = False
        game.move(self, step)

class Cartethyia(Cube):
    """
    Cartethyia团子
    """
    def __init__(self, name="卡提希娅", pos=0):
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

    def __init__(self, name="菲比", pos=0):
        super().__init__(name, pos)

    @skill_hook(SkillTiming.MY_TURN)
    def lucky_boost(self, game):
        step = self.roll_dice(game)
        logging.info(f"{self.name}掷骰子{step}")
        if random.random() < 0.5:
            logging.info(f"{self.name}触发技能，额外前进2格")
            step += 2
        game.move(self, step)