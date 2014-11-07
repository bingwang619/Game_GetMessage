#! /usr/bin/env python
#coding:utf-8
import sys,os
import random
import time
import tty,termios

###  COLORS  ###
GREY_FORMAT = "\033[90m%s\033[0m"
RED_FORMAT = "\033[91m%s\033[0m"
GREEN_FORMAT = "\033[92m%s\033[0m"
YELLOW_FORMAT = "\033[93m%s\033[0m"
PURPLE_FORMAT = "\033[94m%s\033[0m"
PINK_FORMAT =  "\033[95m%s\033[0m"
BLUE_FORMAT = "\033[96m%s\033[0m"

###  MAPSIZE  ###

MAP_WIDTH = 5
MAP_HEIGHT = 5

###  ITEMS  ###

###This is unicode for a full block
WALL_REPRESENT = unichr(0x2588)
ROOM_REPRESENT = " "

PLAYER_1_REPRESENT = BLUE_FORMAT%"A"
PLAYER_2_REPRESENT = YELLOW_FORMAT%"B"
PLAYER_G_REPRESENT = GREY_FORMAT%"G"
PLAYER_1_MESSAGE = BLUE_FORMAT%"@"
PLAYER_2_MESSAGE = YELLOW_FORMAT%"@"

class ItemModel():
    def __init__(self,represent):
        self.represent = represent

class MapModel():
    def __init__(self):
        self.cell_size = (MAP_WIDTH, MAP_HEIGHT)
        self.grid_size = (MAP_WIDTH*4+1, MAP_HEIGHT*4+1)
        #for each cell there should be 3*3 size empty, and 1 for edge wall
        self.itemsdict = {} #{itemid: itemobj}
        self._generate_random_map()
    
    def _generate_random_map(self):

        #initiate pixel map        
        self.grid_map = [[ROOM_REPRESENT]*self.pix_x for i in range(self.pix_y)]
        #generate wall
        for y in xrange(self.pix_y):
            for x in xrange(self.pix_x):
                if (y%4 == 0) or (x %4 == 0):
                    self.pix_map[y][x] = WALL_REPRESENT
        #generate door list
        possible_door_list = []
        for y in xrange(1,self.pix_y-1):
            for x in xrange(1,self.pix_x-1):
                if x%2 == 0 and x%4 != 0 and y%4 == 0:
                    possible_door_list.append((x,y))
                if y%2 == 0 and y%4 != 0 and x%4 == 0:
                    possible_door_list.append((x,y))


class MapView():
    def __init__(self,mapmodel):
        pass

class GameController():
    def __init__(self):
        pass

def main():
    pass

if __name__ == "__main__":
    main()
