# -*- coding: utf-8 -*-

from __future__ import print_function
import numpy as np
import pygame
import sys
import tkinter as tk


from tkinter import *
from tkinter import messagebox
from pygame.locals import QUIT, KEYDOWN


class Board(object):

    def __init__(self, **kwargs):
        self.width = int(kwargs.get('width', 8))  # 读取width的值 默认为8 下同
        self.height = int(kwargs.get('height', 8))
        # board 存在 dict 里,
        # key: move as location on the board,
        # value: player as pieces type
        self.states = {}
        # need how many pieces in a row to win
        self.n_in_row = int(kwargs.get('n_in_row', 5))
        self.players = [1, 2]  # player1 and player2

    def init_board(self, start_player=0):  # 初始化棋盘
        if self.width < self.n_in_row or self.height < self.n_in_row:
            raise Exception('board width and height can not be '
                            'less than {}'.format(self.n_in_row))
        self.current_player = self.players[start_player]  # 先手玩家
        # 生成一个合法落子列表
        self.availables = list(range(self.width * self.height))
        self.states = {}
        self.last_move = -1

    def move_to_location(self, move):  # 下标转坐标
        h = move // self.width
        w = move % self.width
        return [h, w]

    def location_to_move(self, location):  # 坐标转下标
        if len(location) != 2:
            return -1
        h = location[0]
        w = location[1]
        move = h * self.width + w
        if move not in range(self.width * self.height):
            return -1
        return move

    def current_state(self):
        """
        从当前玩家的角度返回棋盘状态。
        状态形状：4*宽*高
        """

        square_state = np.zeros((4, self.width, self.height))  # 三维数组 4 宽 高
        if self.states:
            moves, players = np.array(list(zip(*self.states.items())))
            move_curr = moves[players == self.current_player]
            move_oppo = moves[players != self.current_player]
            square_state[0][move_curr // self.width,
                            move_curr % self.height] = 1.0  # 当前玩家的棋子位置
            square_state[1][move_oppo // self.width,
                            move_oppo % self.height] = 1.0  # 对手的棋子位置
            square_state[2][self.last_move // self.width,  # 最后一步落子位置
                            self.last_move % self.height] = 1.0
        if len(self.states) % 2 == 0:
            square_state[3][:, :] = 1.0  # 表示下棋的玩家是黑是白
        return square_state[:, ::-1, :]

    def do_move(self, move):  # 落子
        self.states[move] = self.current_player
        self.availables.remove(move)  # 从合法列表中删除该位置
        # 更新行动玩家
        self.current_player = (
            self.players[0] if self.current_player == self.players[1]
            else self.players[1]
        )
        self.last_move = move



    def has_a_winner(self):  # 检查胜利
        width = self.width
        height = self.height
        states = self.states
        n = self.n_in_row

        moved = list(set(range(width * height)) - set(self.availables))
        if len(moved) < self.n_in_row * 2 - 1:
            return False, -1

        for m in moved:
            h = m // width
            w = m % width
            player = states[m]

            if (w in range(width - n + 1) and
                    len(set(states.get(i, -1) for i in range(m, m + n))) == 1):
                return True, player

            if (h in range(height - n + 1) and
                    len(set(states.get(i, -1) for i in range(m, m + n * width, width))) == 1):
                return True, player

            if (w in range(width - n + 1) and h in range(height - n + 1) and
                    len(set(states.get(i, -1) for i in range(m, m + n * (width + 1), width + 1))) == 1):
                return True, player

            if (w in range(n - 1, width) and h in range(height - n + 1) and
                    len(set(states.get(i, -1) for i in range(m, m + n * (width - 1), width - 1))) == 1):
                return True, player

        return False, -1
    def show_win_message(self):
        print("you win")

        
        win_message = tk.Tk()
        win_message.geometry("500x200")
        win_message.title("游戏结束")

        label = tk.Label(win_message, text="你赢了！", foreground="black")

        label.grid(row=0, column=0, sticky="nsew")
        win_message.after(3000, win_message.destroy)
        win_message.mainloop()

    def game_end(self):  # 检查游戏是否结束 胜利方or平局
        win, winner = self.has_a_winner()
        if win:
            return True, winner
        elif not len(self.availables):
            return True, -1
        return False, -1

    def get_current_player(self):
        return self.current_player


class Game(object):

    def __init__(self, board, **kwargs):
        self.board = board

    def graphic(self, board, player1, player2, screen):  # 输出棋盘
        width = board.width
        height = board.height

        print("Player", player1, "with X".rjust(3))
        print("Player", player2, "with O".rjust(3))
        print()
        for x in range(width):
            print("{0:8}".format(x), end='')
        print('\r\n')
        for i in range(height - 1, -1, -1):
            print("{0:4d}".format(i), end='')
            for j in range(width):
                loc = i * width + j
                p = board.states.get(loc, -1)
                if p == player1:
                    pygame.draw.circle(screen, [0, 0, 0], [500 - (40 + i * 60), 40 + j * 60], 28, 0)
                    # over_pos.append([[10+i*30, 10+y*30], black_color])
                    print('X'.center(8), end='')
                elif p == player2:
                    pygame.draw.circle(screen, [255, 255, 255], [500 - (40 + i * 60), 40 + j * 60], 28, 0)
                    print('O'.center(8), end='')
                else:
                    print('_'.center(8), end='')
            print('\r\n\r\n')
        pygame.display.update()  # 刷新显示

    def start_play(self, player1, player2, start_player=0, is_shown=1):
        pygame.init()
        screen = pygame.display.set_mode((500, 500))
        screen_color = [238, 154, 73]
        line_color = [0, 0, 0]  # 设置线条颜色，[0,0,0]对应黑色
        screen.fill(screen_color)  # 清屏
        win_width=500
        win_height=500
        # 设置文本字体和大小
        font = pygame.font.Font(None, 120)

        # 创建文本对象
        text1 = font.render("YOU WIN", True, (150, 150, 150))
        text2 = font.render("YOU LOSE", True, (150, 150, 150))
        text3 = font.render("TIE", True, (150, 150, 150))

        # 获取文本矩形对象并计算居中显示的位置
        text_rect = text2.get_rect()
        text_rect.centerx = win_width // 2
        text_rect.centery = win_height // 2

        for i in range(40, 500, 60):
            # 先画竖线
            if i == 40 or i == 500 - 40:  # 边缘线稍微粗一些
                pygame.draw.line(screen, line_color, [i, 40], [i, 500 - 40], 4)
            else:
                pygame.draw.line(screen, line_color, [i, 40], [i, 500 - 40], 2)
            # 再画横线
            if i == 40 or i == 500 - 40:  # 边缘线稍微粗一些
                pygame.draw.line(screen, line_color, [40, i], [500 - 40, i], 4)
            else:
                pygame.draw.line(screen, line_color, [40, i], [500 - 40, i], 2)
        pygame.display.update()  # 刷新显示

        if start_player not in (0, 1):
            raise Exception('start_player should be either 0 (player1 first) '
                            'or 1 (player2 first)')
        self.board.init_board(start_player)
        p1, p2 = self.board.players
        player1.set_player_ind(p1)
        player2.set_player_ind(p2)
        players = {p1: player1, p2: player2}
        if is_shown:
            self.graphic(self.board, player1.player, player2.player, screen)

        while True:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
            pygame.display.update()
            current_player = self.board.get_current_player()
            player_in_turn = players[current_player]
            move = player_in_turn.get_action(self.board)
            self.board.do_move(move)
            if is_shown:

                self.graphic(self.board, player1.player, player2.player, screen)
            end, winner = self.board.game_end()
            if end:


                if is_shown:

                    if winner != -1:

                        # 渲染文本到窗口中心
                        if players[winner] == player1:
                            screen.blit(text1, text_rect)
                        else:
                            screen.blit(text2, text_rect)
                        # 更新屏幕显示
                        pygame.display.flip()

                        print("Game end. Winner is", players[winner])
                        #
                        # Tk().wm_withdraw()
                        # messagebox.showinfo('白棋获胜', '恭喜白棋一方获胜')
                        # else:
                        #     Tk().wm_withdraw()
                        #    messagebox.showinfo('黑棋获胜', '恭喜黑棋一方获胜')

                    else:
                        screen.blit(text3, text_rect)
                        print("Game end. Tie")
                while True:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit();
                            sys.exit()
                return winner

    def start_self_play(self, player, is_shown=0, temp=1e-3):
        self.board.init_board()
        p1, p2 = self.board.players
        states, mcts_probs, current_players = [], [], []
        while True:
            move, move_probs = player.get_action(self.board,
                                                 temp=temp,
                                                 return_prob=1)  # 使用mtcs算法获取下一步走法
            # store the data
            states.append(self.board.current_state())  # 存入当前局面
            mcts_probs.append(move_probs)  # 存入概率分布
            current_players.append(self.board.current_player)  # 存入执子方
            # perform a move
            self.board.do_move(move)
            if is_shown:
                self.graphic(self.board, p1, p2)
            end, winner = self.board.game_end()
            if end:
                # winner from the perspective of the current player of each state
                winners_z = np.zeros(len(current_players))
                if winner != -1:
                    winners_z[np.array(current_players) == winner] = 1.0
                    winners_z[np.array(current_players) != winner] = -1.0
                # reset MCTS root node
                player.reset_player()
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is player:", winner)
                    else:
                        print("Game end. Tie")
                return winner, zip(states, mcts_probs, winners_z)
