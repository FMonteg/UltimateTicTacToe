import sys
import math

import datetime
from random import choice, shuffle

possible_lines = [[0,1,2], [3,4,5], [6,7,8],
                  [0,3,6], [1,4,7], [2,5,8],
                  [0,4,8], [2,4,6]]


class Board(object):
    def __init__(self, **kwargs):
        self.state = self.start()
        self.strategy = 'OPENING'
        pass

    def start(self):
        grid = [[0 for j in range(9)] for i in range(9)]
        lock = -1
        return self.flatten((grid, lock))
    
    def flatten(self, state):
        grid, lock = state
        flat = []
        for i in range(9):
            for j in range (9):
                flat.append(grid[i][j])
        flat.append(lock)
        return tuple(flat)

    def unflatten(self, state):
        return ([[state[j] for j in range(9*i,9*(i+1))] for i in range(9)], state[-1])
    
    def current_player(self):
        player = 1
        grid, lock = self.unflatten(self.state)
        for i in range(9):
            for j in range(9):
                if grid[i][j] == 1:
                    player +=1
                elif grid[i][j] == 2:
                    player -=1
        return player
    

    def legal_plays(self):
        grid, lock = self.unflatten(self.state)
        subgrids = [self.subgrid_status(self.state, i) for i in range(9)]
        plays = []
        
        if lock >= 0 and subgrids[lock][0] == 'A':
            plays = [(lock, slot) for slot in range(9) if grid[lock][slot] == 0]
        else:
            plays = [(l, slot) for l in range(9) for slot in range(9) if grid[l][slot] == 0 and subgrids[l][0]=='A' ]
        shuffle(plays)
        return plays
    
    def subgrid_status(self, state, index):
        subgrid = self.unflatten(state)[0][index]
        winner = 0
        status = 'FULL'

        for line in possible_lines:
            temp = [subgrid[i] for i in line]
            temp.sort()
            if temp[0] == temp[1] and temp[0] == temp[2] and temp[0] > 0:
                winner = temp[0]
                status = 'WON ' + str(winner)
                break
            elif temp[0] == 0:
                status = 'AVAILABLE'
            
        return status

    def get_play(self):
        grid, lock = self.unflatten(self.state)

        if self.strategy == 'MIDGAME':
            legals = self.legal_plays()
            avoid = self.get_bad_subgrids()
            play = legals[0]
            for temp in legals:
                if temp[1] not in avoid:
                    play = temp
                    break
            for temp in self.target:
                if temp in legals:
                    play = temp
                    self.target.remove(play)
                    break
            if len(self.target) == 0:
                self.strategy = 'ENDGAME'
            
        elif self.strategy == 'OPENING':
            if lock == -1:
                play = [4,4]
            else:
                play = [lock, 4]
            if self.subgrid_status(self.state, 4) != 'AVAILABLE':
                self.strategy = 'MIDGAME'
                for line in possible_lines:
                    temp = [grid[4][i] for i in line]
                    if temp == [2,2,2]:
                        self.critical_line = line
                        self.parallel_line = self.get_parallel_line(line)
                        self.set_target()
                        break 
        return play


    def update(self, play):
        grid, lock = self.unflatten(self.state)
        player = self.current_player()

        grid[play[0]][play[1]] = player
        lock = play[1]
        self.state = self.flatten((grid, lock))
        pass

    def convert_global_local(self, row, col):
        grid = 3*(row//3) + col//3
        pos = 3*(row%3) + col%3
        return grid, pos

    def convert_local_global(self, grid, pos):
        row = 3*(grid//3) + pos//3
        col = 3*(grid%3) + pos%3
        return row, col

    def get_parallel_line(self, line):
        if 1 in line:
            return [3,5]
        elif 3 in line:
            return [1,7]
        elif 5 in line:
            return [1,7]
        elif 7 in line:
            return [3,5]
        
    def set_target(self):
        self.target = [[subgrid, square] for subgrid in self.critical_line for square in self.parallel_line]
        pass

    def get_bad_subgrids(self):
        bads = {4}
        for play in self.target:
            bads.add(play[0])
        for i in self.parallel_line:
            bads.add(i)
        return bads



board = Board()

# game loop
while True:
    #_____Input_______
    opponent_row, opponent_col = [int(i) for i in input().split()]
    valid_action_count = int(input())
    valid_actions = []
    for i in range(valid_action_count):
        row, col = [int(j) for j in input().split()]
        valid_actions.append((row, col))

    if opponent_row != -1:
        opponent_play = board.convert_global_local(opponent_row, opponent_col)
        board.update(opponent_play)


    play = board.get_play()
    board.update(play)
    row, col = board.convert_local_global(play[0], play[1])

    print(' '.join([str(row), str(col)]))

    