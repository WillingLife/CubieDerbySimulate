from Cubie import *
from Game import GameField


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
        game = GameField(cubes,given_order=False)
        winner = game.play_game()
        winners[winner.name] += 1
    return winners

# simulate_games(1000)  # 小规模模拟预览
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,filename='log.log',encoding='utf-8')
    print(simulate_games())  # 大规模模拟