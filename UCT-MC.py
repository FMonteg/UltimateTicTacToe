import sys
import math

import datetime
from random import choice, shuffle

possible_lines = [[0,1,2], [3,4,5], [6,7,8],
                  [0,3,6], [1,4,7], [2,5,8],
                  [0,4,8], [2,4,6]]

class Board(object):
    def start(self):
        grid = [[0 for j in range(9)] for i in range(9)]
        lock = -1
        return flatten((grid, lock))
    
    def current_player(self, state):
        player = 1
        grid, lock = unflatten(state)
        for i in range(9):
            for j in range(9):
                if grid[i][j] == 1:
                    player +=1
                elif grid[i][j] == 2:
                    player -=1
        return player

    def next_state(self, state, play):
        grid, lock = unflatten(state)
        player = self.current_player(state)

        grid[play[0]][play[1]] = player
        lock = play[1]
        return flatten((grid, lock))
    
    def legal_plays(self, state_history):
        state = state_history[-1]
        grid, lock = unflatten(state)
        subgrids = [self.subgrid_status(state, i) for i in range(9)]
        plays = []
        
        if lock >= 0 and subgrids[lock][0] == 'A':
            plays = [(lock, slot) for slot in range(9) if grid[lock][slot] == 0]
        else:
            plays = [(l, slot) for l in range(9) for slot in range(9) if grid[l][slot] == 0 and subgrids[l][0]=='A' ]
        shuffle(plays)
        return plays

    def subgrid_status(self, state, index):
        subgrid = unflatten(state)[0][index]
        winner = 0
        status = 'FULL'
        scores = [0,0]

        for line in possible_lines:
            temp = [subgrid[i] for i in line]
            temp.sort()
            if temp[0] == temp[1] and temp[0] == temp[2] and temp[0] > 0:
                winner = temp[0]
                status = 'WON ' + str(winner)
                break
            elif temp[1] == temp[2] and temp[1] > 0:
                scores[temp[1]-1] += 1
                status = 'AVAILABLE {0} {1}'.format(scores[0], scores[1])
            elif temp[0] == 0:
                status = 'AVAILABLE {0} {1}'.format(scores[0], scores[1])
            
        return status

    def winner(self, state_history, A, a):
        if len(state_history)>1:
            delta_score = self.score(state_history[-1], A, a)-self.score(state_history[-2], A, a)
        if delta_score > 0:
            return 1
        elif delta_score < 0:
            return 2
        else:
            return 0

    def winner_full(self, state_history):
        state = state_history[-1]
        grid = [0 for i in range(9)]

        for i in range(9):
            status = self.subgrid_status(state, i)
            if status[0] == 'A':
                return 0
            elif status[0] == 'W':
                grid[i] = int(status[-1])
        
        for line in possible_lines:
            temp = sum([grid[i] for i in line])
            if temp%3 == 0 and temp > 0:
                return temp/3
        
        scores = [0,0]
        for i in range(9):
            if grid[i] > 0:
                scores[grid[i]-1] += 1
        
        winner = 3
        if scores[0] > scores[1]:
            winner = 1
        elif scores[0] < scores[1]:
            winner = 2

        return winner
    
    def score(self, state, A, a):
        scores = [0, 0]

        for i in range(9):
            status = self.subgrid_status(state, i)
            if status[0] == 'W':
                scores[int(status[-1])-1] += A
            else:
                temp = [int(status[-3]), int(status[-1])]
                scores[0] += a*temp[0]
                scores[1] += a*temp[1]
                

        return scores[0]-scores[1]


class MonteCarlo(object):
    def __init__(self, board, **kwargs):
        self.board = board
        self.states = kwargs.get('states',[])

        seconds = kwargs.get('time', 30)
        self.calculation_time = datetime.timedelta(seconds=seconds)

        self.max_moves = kwargs.get('max_moves', 100)

        self.wins = {}
        self.plays = {}

        self.C = kwargs.get('C', 1.4)
        self.A = kwargs.get('A', 10)
        self.a = kwargs.get('a', 1)
        pass

    def set_calculation_time(self, seconds):
        self.calculation_time = datetime.timedelta(seconds=seconds)
        pass

    def update (self, play):
        self.states.append(self.board.next_state(self.states[-1], play))
        pass
    
    def get_play(self):
        self.max_depth = 0
        state = self.states[-1]
        player = self.board.current_player(state)
        legal = self.board.legal_plays(self.states[:])

        if not legal:
            return
        if len(legal) == 1:
            return legal[0]

        games = 0
        begin = datetime.datetime.utcnow()
        while datetime.datetime.utcnow()-begin < self.calculation_time:
            self.run_simulation()
            games += 1
        
            
        moves_states = [(p, self.board.next_state(state, p)) for p in legal]

        #percent_wins, move = max((self.wins.get((player, S), 0)/self.plays.get((player, S), 1), p) for p, S in moves_states)
        max_percent = max((self.wins.get((player, S), 0)/self.plays.get((player, S), 1)) for p, S in moves_states)
        move = choice([p for p, S in moves_states if (self.wins.get((player, S), 0)/self.plays.get((player, S), 1)) == max_percent])

        """
        for x in sorted(
            ((100*-self.wins.get((player, S),0)/
            self.plays.get((player, S), 1),
            self.wins.get((player, S), 0),
            self.plays.get((player, S), 0), p)
            for p, S in moves_states),
            reverse = True
        ):
            pass
            #print("{3}: {0:.2f}%({1}/{2})".format(*x))
        print("Maximum depth reached:", self.max_depth)
        """

        return move 

    def run_simulation(self):
        plays, wins = self.plays, self.wins
        visited_states = set()
        states_copy = self.states[:]
        state = states_copy[-1]
        player = self.board.current_player(state)

        expand = True
        for t in range(1, self.max_moves+1):
            legal = self.board.legal_plays(states_copy)
            moves_states = [(p, self.board.next_state(state, p)) for p in legal]

            if all(plays.get((player, S)) for p, S in moves_states):
                log_total = math.log(sum(plays[(player, S)] for p, S in moves_states))
                value, move, state = max(((wins[(player, S)]/plays[(player, S)])+self.C*math.sqrt(log_total/plays[(player, S)]),p,S) for p,S in moves_states)
            else:
                move, state = choice(moves_states)
            states_copy.append(state)

            if expand and (player, state) not in plays:
                expand = False
                plays[(player, state)] = 0
                wins[(player, state)] = 0
                if t > self.max_depth:
                    self.max_depth = t
            visited_states.add((player, state))
            player = self.board.current_player(state)
            winner = self.board.winner(states_copy, self.A, self.a)
            if winner:
                break

        for player, state in visited_states:
            if (player, state) not in plays:
                continue
            plays[(player, state)] += 1
            if player == winner:
                wins[(player, state)] +=1
        pass


def convert_global_local(row, col):
    grid = 3*(row//3) + col//3
    pos = 3*(row%3) + col%3
    return grid, pos

def convert_local_global(grid, pos):
    row = 3*(grid//3) + pos//3
    col = 3*(grid%3) + pos%3
    return row, col

def flatten(state):
    grid, lock = state
    flat = []
    for i in range(9):
        for j in range (9):
            flat.append(grid[i][j])
    flat.append(lock)
    return tuple(flat)

def unflatten(state):
    return ([[state[j] for j in range(9*i,9*(i+1))] for i in range(9)], state[-1])

board = Board()
MC = MonteCarlo(board, states=[board.start()], time = 0.9)

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
        opponent_play = convert_global_local(opponent_row, opponent_col)
        MC.update(opponent_play)
        MC.set_calculation_time(0.09)

    play = MC.get_play()
    MC.update(play)


    row, col = convert_local_global(play[0], play[1])
    print(' '.join([str(row), str(col)]))
    