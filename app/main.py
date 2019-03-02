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

    print "Look here dummy"
    print data
    print width
    print height

    gameboard = np.zeros((width, height))
    me = Snake()
    others = Snakes()

    for snake in data['snakes']:
        if snake['id'] == you['id']:
            me.set_health(snake['health'])
            for i, coord in enumerate(snake['body']):
                if i == 0:
                    gameboard[coord['x']][coord['y']] = HUFF_HEAD
                    me.set_head(coord)
                elif i == (len(snake['body']) - 1):
                    gameboard[coord['x']][coord['y']] = HUFF_TAIL
                    me.set_tail(coord)
                else:
                    gameboard[coord['x']][coord['y']] = HUFF_BODY
                    me.add_body(coord)
        else:
            for i, coord in enumerate(snake['body']):
                if i == 0:
                    gameboard[coord['x']][coord['y']] = THEM_HEAD
                    others.add_head(coord)
                elif i == (len(snake['body']) - 1):
                    gameboard[coord['x']][coord['y']] = THEM_TAIL
                    others.add_tail(coord)
                else:
                    gameboard[coord['x']][coord['y']] = THEM_BODY
                    others.add_body(coord)

    print gameboard
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
    huff_food = data['food'][0]

    ## Find optimal food
    for food in data['food']:
        temp_dist = math.fabs(food[0] - me.head[0]) + math.fabs(food[1] - me.head[1])
        if temp_dist < huff_dist_to_food:
            huff_food = food
            huff_dist_to_food = temp_dist

    ## If you and the food are on the same X
    if me.head[0] - huff_food[0] == 0:
        ## If the food is below you, go down
        if me.head[1] - huff_food[1] < 0:
            if 'down' in dirs:
                move = 'down'
            else:
                move = max(dirs_weights.iteritems(), key=operator.itemgetter(1))[0]
        ## If the food is above you, go up
        else:
            if 'up' in dirs:
                move = 'up'
            else:
                move = max(dirs_weights.iteritems(), key=operator.itemgetter(1))[0]
    ## Adjust X coord if you're not on the same X
    else:
        if me.head[0] - huff_food[0] < 0:
            if 'right' in dirs:
                move = 'right'
            else:
                move = max(dirs_weights.iteritems(), key=operator.itemgetter(1))[0]
        else:
            if 'left' in dirs:
                move = 'left'
            else:
                move = max(dirs_weights.iteritems(), key=operator.itemgetter(1))[0]

    return move


def state_turtle(data, gameboard, me, others, dirs, dirs_weights):
    bound_x = data['width'] - 5
    bound_y = data['height'] - 5

    my_coord = me.head
    my_x = my_coord['x']
    my_y = my_coord['y']

    move = random.choice(dirs)

    if my_x < (bound_x - 2):
        move = 'right'
        pass
    elif my_x > (bound_x +2):
        move = 'left'
        pass
    elif my_y < (bound_y - 2):
        move = 'down'
        pass
    elif my_y > (bound_y +2):
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
    look_ahead(data, me, others, dirs, dirs_weights)

    # print dirs_weights

    if state == TURTLE:
        move = state_turtle(data, gameboard, me, others, dirs, dirs_weights)
    if state == FIND_FOOD:
        move = state_find_food(data, gameboard, me, others, dirs, dirs_weights)

    # print me
    # print "Available Directions: "
    for d in dirs:
        print "  " + d
    if len(dirs) == 0:
        move = 'left' # :(

    return {
        'move': move,
        'taunt': 'Point me!'
    }


def avoid_wall_dir_filter(me, width, height, dirs):
    my_coord = me.head
    my_x = my_coord['x']
    my_y = my_coord['y']

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

    if 'left' in dirs and me.is_body([my_x - 1, my_y]):
        dirs.remove('left')

    if 'right' in dirs and me.is_body([my_x + 1, my_y]):
        dirs.remove('right')

    if 'up' in dirs and me.is_body([my_x, my_y - 1]):
        dirs.remove('up')

    if 'down' in dirs and me.is_body([my_x, my_y + 1]):
        dirs.remove('down')


def avoid_others_dir_filter(me, others, dirs):
    my_coord = me.head
    my_x = my_coord['x']
    my_y = my_coord['y']

    if 'left' in dirs and others.is_body_or_head([my_x - 1, my_y]):
        dirs.remove('left')

    if 'right' in dirs and others.is_body_or_head([my_x + 1, my_y]):
        dirs.remove('right')

    if 'up' in dirs and others.is_body_or_head([my_x, my_y - 1]):
        dirs.remove('up')

    if 'down' in dirs and others.is_body_or_head([my_x, my_y + 1]):
        dirs.remove('down')


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


def goto_food(me, dirs, data):
    my_coord = me.head
    my_x = my_coord['x']
    my_y = my_coord['y']

    if 'left' in dirs:
        pass

    if 'right' in dirs:
        pass

    if 'up' in dirs:
        pass

    if 'down' in dirs:
        pass

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

    color = "#00FF00"

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
    # state = FIND_FOOD

    return next_move(data, gameboard, me, others, state)


@bottle.post('/end')
def end():
    data = bottle.request.json

    """
    TODO: If your snake AI was stateful,
        clean up any stateful objects here.
    """
    print(json.dumps(data))

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
