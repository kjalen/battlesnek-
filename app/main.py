import json
import os
import random
import bottle
import numpy as np
import math
import operator
import datetime

from api import ping_response, start_response, move_response, end_response

# STATES
TURTLE      =   0
FIND_FOOD    =   1

#TYPES
HUFF_HEAD   =   1
HUFF_BODY   =   2
HUFF_TAIL   =   3
THEM_HEAD   =   4
THEM_BODY   =   5
THEM_TAIL   =   6
FOOD        =   9



directions = ['up', 'down', 'left', 'right']

class Snake:
    def __init__(self):
        self.head = []
        self.tail = []
        self.body = []
        self.health = 100

    def set_head(self, coord):
        self.head = coord

    def set_tail(self, coord):
        self.tail = coord

    def add_body(self, coord):
        self.body.append(coord)

    def is_head(self, coord):
        return coord == self.head

    def is_tail(self, coord):
        return coord == self.tail

    def is_body(self, coord):
        return coord in self.body

    def set_health(self, hp):
        self.health = hp

    def get_health(self):
        return self.health

    def __repr__(self):
        s = "<Head: [" + str(self.head[0]) + "][" + str(self.head[1])
        s = s + "] Body: "
        for b in self.body:
            s = s + "[" + str(b[0]) + "][" + str(b[1]) + "] "
        s = s + "Tail: [" + str(self.tail[0]) + "][" + str(self.tail[1]) + "]>"
        return s

class Snakes:
    def __init__(self):
        self.heads = []
        self.tails = []
        self.bodies = []

    def add_head(self, coord):
        self.heads.append(coord)

    def add_tail(self, coord):
        self.tails.append(coord)

    def add_body(self, coord):
        self.bodies.append(coord)

    def is_head(self, coord):
        return coord in self.heads

    def is_tail(self, coord):
        return coord in self.tails

    def is_body(self, coord):
        return coord in self.bodies

    def is_body_or_head(self, coord):
        return self.is_body(coord) or self.is_head(coord)


def init_gameboard(data):
    you = data['you']
    data = data['board']
    width = data['width']
    height = data['height']

    gameboard = np.zeros((width, height))
    me = Snake()
    others = Snakes()

    for snake in data['snakes']:
        if snake['id'] == you['id']:
            me.set_health(snake['health'])
            for i, coord in enumerate(snake['body']):
                if i == 0:
                    gameboard[coord['y']][coord['x']] = HUFF_HEAD
                    me.set_head(coord)
                elif i == (len(snake['body']) - 1):
                    gameboard[coord['y']][coord['x']] = HUFF_TAIL
                    me.set_tail(coord)
                else:
                    gameboard[coord['y']][coord['x']] = HUFF_BODY
                    me.add_body(coord)
        else:
            for i, coord in enumerate(snake['body']):
                if i == 0:
                    gameboard[coord['y']][coord['x']] = THEM_HEAD
                    others.add_head(coord)
                elif i == (len(snake['body']) - 1):
                    gameboard[coord['y']][coord['x']] = THEM_TAIL
                    others.add_tail(coord)
                else:
                    gameboard[coord['y']][coord['x']] = THEM_BODY
                    others.add_body(coord)

    #print(gameboard)
    return gameboard, me, others


def determine_state(data, me, others):
    data = data['board']

    state = TURTLE

    num_food = len(data['food'])
    num_snakes = len(others.heads) + 1
    our_health = me.get_health()

    ## Be cautious if there are 6 or more snakes
    if num_snakes >= 6 and (our_health < (data['height'] + data['width']) / 2):
        state = FIND_FOOD

    ## If we're hungry, find food
    elif our_health < (data['height'] + data['width']):
        state = FIND_FOOD

    ## if there's less food than snakes, always find food
    elif num_food <= num_snakes:
        state = FIND_FOOD

    return state


def state_find_food(data, gameboard, me, others, dirs, dirs_weights):
    move = random.choice(dirs)


    temp_dist = 0
    huff_dist_to_food = 9999

    if (len(data['food']) > 0):
        huff_food = data['food'][0]
    else:
        return random.choice(dirs)

    ## Find optimal food
    #print('I am at (' + str(me.head['x']) + ', ' + str(me.head['y']) + ')')
    for food in data['food']:
        ## distance formula
        temp_dist = round(math.sqrt(math.pow(food['x'] - me.head['x'], 2) + math.pow(food['y'] - me.head['y'], 2)))
        #print('I am ' + str(temp_dist) + ' squares away from the food at (' + str(food['x']) + ', ' + str(food['y']) + ')')
        if temp_dist < huff_dist_to_food:
            huff_food = food
            huff_dist_to_food = temp_dist

    ## If you and the food are on the same X
    if me.head['x'] - huff_food['x'] == 0:
        ## If the food is below you, go down
        if me.head['y'] - huff_food['y'] < 0:
            if 'down' in dirs:
                move = 'down'
            # else:
            #     move = max(dirs_weights.iteritems(), key=operator.itemgetter(1))[0]
        ## If the food is above you, go up
        else:
            if 'up' in dirs:
                move = 'up'
            # else:
            #     move = max(dirs_weights.iteritems(), key=operator.itemgetter(1))[0]
    ## Adjust X coord if you're not on the same X
    else:
        if me.head['x'] - huff_food['x'] < 0:
            if 'right' in dirs:
                move = 'right'
            # else:
            #     move = max(dirs_weights.iteritems(), key=operator.itemgetter(1))[0]
        else:
            if 'left' in dirs:
                move = 'left'
            # else:
            #     move = max(dirs_weights.iteritems(), key=operator.itemgetter(1))[0]
    if move not in dirs:
        move = random.choice(dirs)
    return move


def state_turtle(data, gameboard, me, others, dirs, dirs_weights):
    bound_x = data['width'] - 5
    bound_y = data['height'] - 5

    my_coord = me.head
    my_x = my_coord['x']
    my_y = my_coord['y']

    move = random.choice(dirs)

    if my_x < (bound_x - 2) and 'right' in dirs:
        move = 'right'
        pass
    elif my_x > (bound_x +2) and 'left' in dirs:
        move = 'left'
        pass
    elif my_y < (bound_y - 2) and 'down' in dirs:
        move = 'down'
        pass
    elif my_y > (bound_y +2) and 'up' in dirs:
        move = 'up'
        pass
    else:
        pass

    if move in dirs:
        return move
    else:
        if len(dirs) == 0:
            move = 'left'
            return move
        elif len(dirs) > 0:
            return random.choice(dirs)
        else:
            move = max(dirs_weights.iteritems(), key=operator.itemgetter(1))[0]
            return move


def next_move(data, gameboard, me, others, state):
    data = data['board']
    width = data['width']
    height = data['height']

    dirs = [d for d in directions]
    dirs_weights = {'left': 0, 'right': 0, 'up': 0, 'down': 0}
    avoid_wall_dir_filter(me, width, height, dirs)
    avoid_self_dir_filter(me, dirs)
    avoid_others_dir_filter(me, others, dirs)
    avoid_hoh_filter(me, others, dirs)

    # look_ahead(data, me, others, dirs, dirs_weights)

    if state == TURTLE:
        move = state_turtle(data, gameboard, me, others, dirs, dirs_weights)
    if state == FIND_FOOD:
        move = state_find_food(data, gameboard, me, others, dirs, dirs_weights)

    # print me
    print("Available Directions: ")
    for d in dirs:
        print("  " + d)
    if len(dirs) == 0:
        move = 'left' # :(

    return {
        'move': move
    }


def avoid_wall_dir_filter(me, width, height, dirs):
    my_coord = me.head
    my_x = my_coord['x']
    my_y = my_coord['y']
    # print('my_x' + str(my_x))
    # print('my_y' + str(my_y))

    if my_x == 0:
        dirs.remove('left')

    if my_x == width - 1:
        dirs.remove('right')

    if my_y == 0:
        dirs.remove('up')

    if my_y == height - 1:
        dirs.remove('down')


def avoid_self_dir_filter(me, dirs):
    my_coord = me.head
    my_x = my_coord['x']
    my_y = my_coord['y']

    if 'left' in dirs and me.is_body({'y':my_y, 'x':my_x-1}):
        dirs.remove('left')

    if 'right' in dirs and me.is_body({'y':my_y, 'x':my_x+1}):
        dirs.remove('right')

    if 'up' in dirs and me.is_body({'y':my_y-1, 'x':my_x}):
        dirs.remove('up')

    if 'down' in dirs and me.is_body({'y':my_y+1, 'x':my_x}):
        dirs.remove('down')


def avoid_others_dir_filter(me, others, dirs):
    my_coord = me.head
    my_x = my_coord['x']
    my_y = my_coord['y']

    if 'left' in dirs and others.is_body_or_head({'y':my_y, 'x':my_x-1}):
        dirs.remove('left')

    if 'right' in dirs and others.is_body_or_head({'y':my_y, 'x':my_x+1}):
        dirs.remove('right')

    if 'up' in dirs and others.is_body_or_head({'y':my_y-1, 'x':my_x}):
        dirs.remove('up')

    if 'down' in dirs and others.is_body_or_head({'y':my_y+1, 'x':my_x}):
        dirs.remove('down')

def avoid_hoh_filter(me, others, dirs):
    my_coord = me.head
    my_x = my_coord['x']
    my_y = my_coord['y']

    danger_points_up = [[0,-2],[-1,-1],[1,-1]]
    danger_points_down = [[-1,1],[0,2],[1,1]]
    danger_points_left = [[-1,1],[-2,0],[-1,-1]]
    danger_points_right = [[1,1],[2,0],[1,-1]]

    for dir in dirs:
        if dir == 'up':
            for point in danger_points_up:
                if others.is_head({'x':my_x + point[0], 'y':my_y + point[1]}):
                    print('in danger from above!')
                    dirs.remove('up')
                    
        if dir == 'down':
            for point in danger_points_down:
                if others.is_head({'x':my_x + point[0], 'y':my_y + point[1]}):
                    print('in danger from below!')
                    dirs.remove('down')
                    
        if dir == 'left':
            for point in danger_points_left:
                if others.is_head({'x':my_x + point[0], 'y':my_y + point[1]}):
                    print('in danger from the left!')
                    dirs.remove('left')
                    
        if dir == 'right':
            for point in danger_points_right:
                if others.is_head({'x':my_x + point[0], 'y':my_y + point[1]}):
                    print('in danger from the right!')
                    dirs.remove('right')
                    

def look_ahead(data, me, others, dirs, dirs_weights):
    width = data['width']
    height = data['height']

    my_coord = me.head
    my_x = my_coord['x']
    my_y = my_coord['y']

    new_me = Snake()

    for dir in dirs:
        weights = [d for d in directions]

        if dir == 'left':
            new_me.set_head([my_x-1, my_y])

            avoid_wall_dir_filter(me, width, height, weights)
            avoid_self_dir_filter(me, weights)
            avoid_others_dir_filter(me, others, weights)
            dirs_weights['left'] = len(weights)

        if dir == 'right':
            new_me.set_head([my_x+1, my_y])
            avoid_wall_dir_filter(me, width, height, weights)
            avoid_self_dir_filter(me, weights)
            avoid_others_dir_filter(me, others, weights)
            dirs_weights['right'] = len(weights)

        if dir == 'up':
            new_me.set_head([my_x, my_y-1])
            avoid_wall_dir_filter(me, width, height, weights)
            avoid_self_dir_filter(me, weights)
            avoid_others_dir_filter(me, others, weights)
            dirs_weights['up'] = len(weights)

        if dir == 'down':
            new_me.set_head([my_x, my_y+1])
            avoid_wall_dir_filter(me, width, height, weights)
            avoid_self_dir_filter(me, weights)
            avoid_others_dir_filter(me, others, weights)
            dirs_weights['down'] = len(weights)

@bottle.route('/')
def index():
    return '''
    Battlesnake documentation can be found at
       <a href="https://docs.battlesnake.io">https://docs.battlesnake.io</a>.
    '''

@bottle.route('/static/<path:path>')
def static(path):
    """
    Given a path, return the static file located relative
    to the static folder.

    This can be used to return the snake head URL in an API response.
    """
    return bottle.static_file(path, root='static/')

@bottle.post('/ping')
def ping():
    """
    A keep-alive endpoint used to prevent cloud application platforms,
    such as Heroku, from sleeping the application instance.
    """
    return ping_response()

@bottle.post('/start')
def start():
    data = bottle.request.json

    """
    TODO: If you intend to have a stateful snake AI,
            initialize your snake state here using the
            request's data if necessary.
    """
    print(json.dumps(data))

    ##color = "#00FF00"
    color = "#0000FF" #blue

    return start_response(color)


@bottle.post('/move')
def move():
    data = bottle.request.json

    """
    TODO: Using the data from the endpoint request object, your
            snake AI must choose a direction to move in.
    """
    data = bottle.request.json
    gameboard, me, others = init_gameboard(data)
    state = determine_state(data, me, others)
    #print('state is: ' + str(state))
    # state = FIND_FOOD

    move = next_move(data, gameboard, me, others, state)
    print(data['turn'])
    print(move)
    return move


@bottle.post('/end')
def end():

    return end_response()

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()

if __name__ == '__main__':
    bottle.run(
        application,
        host=os.getenv('IP', '0.0.0.0'),
        port=os.getenv('PORT', '8080'),
        debug=os.getenv('DEBUG', True)
    )
