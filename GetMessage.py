#! /usr/bin/env python
#coding:utf-8
import sys,os
import random
import time
import tty,termios

MAP_WIDTH = 8
MAP_HEIGHT = 5
AI_GATEKEEPER = True

class _Getch():
    def __call__(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def get_action():
    getch = _Getch()
    action = ord(getch())
    if action == 27:
        action = ord(getch())
        if action == 27:
            ## Double prese esc to exit
            return "ESC"
        action = ord(getch())
        if action == 65:
            return "UP"
        elif action == 66:
            return "DOWN"
        elif action == 67:
            return "RIGHT"
        elif action == 68:
            return "LEFT"
        else:
            print "Pressed x1b[%s value:actionm type:3"%(chr(action),action)
            return "ESC"
    elif action == 3:
        return "ESC"
    else:
        return chr(action).upper()

class MapModel():
    def __init__(self):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.cell_size = (self.width, self.height)
        self.grid_width = self.width*4+1
        self.grid_height = self.height*4+1
        #for each cell there should be 3*3 size empty, and 1 for edge wall
        self.grid_size = (self.grid_width, self.grid_height)

        self.item_list = ["unknown","wall","space",\
                          "door_1","door_2","door_3","door_4",\
                          "key_1","key_2","key_3","key_4",\
                          "player_A","player_B","gatekeeper"]

        self.grid_dict = {x:{y:"space" for y in xrange(self.grid_height)} \
                                         for x in xrange(self.grid_width)} \
                          #{[grid_x][grid_y]: itemid}
                          #initialize grid map        
        self.cell_dict = {x:{y:[] for y in xrange(self.height)} \
                                       for x in xrange(self.width)} 
                          #{[cell_x][cell_y]: [itemid]}
                          #initialize cell map

        self.player_loc = {}
                          #itemid: [cell_x][cell_y]

        self._generate_random_map()
    
    def _generate_random_map(self):

        #generate wall
        for x in xrange(self.grid_width):
            for y in xrange(self.grid_height):
                if (y%4 == 0) or (x %4 == 0):
                    self.grid_dict[x][y] = "wall"

        #generate door list
        door_list = []
        for x in xrange(1,self.grid_width-1):
            for y in xrange(1,self.grid_height-1):
                if x%2 == 0 and x%4 != 0 and y%4 == 0:
                    door_list.append((x,y))
                if y%2 == 0 and y%4 != 0 and x%4 == 0:
                    door_list.append((x,y))

        #Randomized Kruskal's algorithm
        #initiate door2cell and cell2set
        door2cell = {}  #door: linked cell by this door
        cell2set = {}  #initial: all cell at one set
        for door in door_list:
            if door[0]%4 != 0:
                door2cell[door] = (((door[0]-2)/4,door[1]/4),((door[0]-2)/4,(door[1]-4)/4))
            if door[1]%4 != 0:
                door2cell[door] = ((door[0]/4,(door[1]-2)/4),((door[0]-4)/4,(door[1]-2)/4))

        for x in xrange(self.width):
            for y in xrange(self.height):
                cell2set[(x,y)] = set([(x,y)])

        #shuffle door list
        random.shuffle(door_list)
        open_door_list = [] #the opened door list
        
        #if the two cell linked by a door are not in one set, open the door, join the cell
        for door in door_list:
            cell1,cell2 = door2cell[door]
            if cell2set[cell1] != cell2set[cell2]:
                open_door_list.append(door)
                cell2set[cell2] |= cell2set[cell1] 
                for cell in cell2set[cell2]:
                    cell2set[cell] = cell2set[cell2]

        for (x,y) in open_door_list:
            self.grid_dict[x][y] = "space"
        
        #set rest door to closed door
        for (x,y) in set(door_list) - set(open_door_list):
            self.grid_dict[x][y] = random.choice(["door_1","door_2","door_3","door_4"])
                                               #four kinds of doors

        #drop keys in inner cells
        inner_cells = []
        for x in xrange(1,self.width-1):
            for y in xrange(1,self.height-1):
                inner_cells.append((x,y))

        random.shuffle(inner_cells)

        for i,key in enumerate(["key_1","key_2","key_3","key_4"]):
                            # four kinds of keys, each can open one kind of doors
            x,y = inner_cells[i]
            self.cell_dict[x][y].append(key)

        #Add players in outer cells
        outer_cells = []
        for x in xrange(self.width):
            for y in xrange(self.height):
                if x == 0 or x == self.width-1 or y == 0 or y == self.height-1:
                    outer_cells.append((x,y))

        random.shuffle(outer_cells)

        for i,player in enumerate(["player_A","player_B","gatekeeper"]):
            x,y = outer_cells[i]
            self.cell_dict[x][y].append(player)
            self.player_loc[player] = (x,y)

class MapView():
    def __init__(self):
        ###Object Colors
        self.grey = "\033[90m%s\033[0m"
        self.red = "\033[91m%s\033[0m"
        self.green = "\033[92m%s\033[0m"
        self.yellow = "\033[93m%s\033[0m"
        self.purple = "\033[94m%s\033[0m"
        self.pink = "\033[95m%s\033[0m"
        self.blue = "\033[96m%s\033[0m"

        ###Grid Item Represents
        self.item2represent = {
             "unknown":".",\
             "wall"   :unichr(0x2588), # This is unicode for a full block
             "space"  : " ",
             "door_1" : self.red%unichr(0x2588),
             "door_2" : self.green%unichr(0x2588),
             "door_3" : self.purple%unichr(0x2588),
             "door_4" : self.pink%unichr(0x2588),
             "key_1"  : self.red%"F",
             "key_2"  : self.green%"F",
             "key_3"  : self.purple%"F",
             "key_4"  : self.pink%"F",

             "player_A"   : self.blue%"A",
             "player_B"   : self.yellow%"B",
             "gatekeeper" : self.grey%"G",
             "message_A"  : self.blue%"@",
             "message_B"  : self.yellow%"@",
             "empty"      : "_"
             }

    def show_map(self,mapm,turn,step,package_dict):

        os.system("clear")
        ###Add grid_items
        content_1 = [[self.item2represent[mapm.grid_dict[x][y]] \
                for x in xrange(mapm.grid_width)] \
                for y in xrange(mapm.grid_height)]

        ###Add cell_items
        for x in xrange(mapm.width):
            for y in xrange(mapm.height):
                if len(mapm.cell_dict[x][y]) == 0:
                    continue
                elif len(mapm.cell_dict[x][y]) == 1:
                    content_1[y*4+2][x*4+2] = self.item2represent[mapm.cell_dict[x][y][0]]
                    ##if only one item in that cell, put it in the center of the cell
                else:
                    count_item = len(mapm.cell_dict[x][y])
                    locuses = [(4*x+2,4*y+2),(4*x+1,4*y+1),(4*x+2,4*y+1),\
                               (4*x+3,4*y+1),(4*x+1,4*y+2),(4*x+3,4*y+2),\
                               (4*x+1,4*y+3),(4*x+2,4*y+3),(4*x+3,4*y+3)][:count_item]
                    ##Represent 9 items in cell at most
                    for item,loc in zip(mapm.cell_dict[x][y][0:9],locuses):
                        content_1[loc[1]][loc[0]] = self.item2represent[item]

        ###Content info: User Info
        content_2 = ["","",turn,""]
        content_2 += ["################################"]
        ##replace itemsid with items represents
        for itemid in ["message_A","message_B","key_1","key_2","key_3","key_4"]:
            if itemid in step:
                step = step.replace(itemid,self.item2represent[itemid])

        content_2 += step.split("\t")
        content_2 += ["################################","",""]
        for player in ["player_A","player_B","gatekeeper"]:
            content_2.append("%s's Package"%player)
            player_package = [self.item2represent[item] for item in package_dict[player]]
            content_2 += [" ".join(player_package),""]

        for i in xrange(len(content_1)):
            line_1 = "".join(content_1[i])
            line_2 = content_2[i] if i < len(content_2) else ""
            sys.stdout.write("%s    %s\n"%(line_1,line_2))

class GameController():
    def __init__(self):
        self.gamemap = MapModel()
        self.mapview = MapView()
        self.package_dict = {"player_A":["message_A","message_A","message_A","message_A"],\
                             "player_B":["message_B","message_B","message_B","message_B"],\
                             "gatekeeper":["empty","empty","empty","empty"]}

    def _playerturn(self,player):
        turn_info = "%s's Turn"%player
        step_info = "Rolling Dicer...\t      Press anykey to stop"
        self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
        get_action()
        step_left = random.randint(1,6)
        step_info = "You got %d step left\t"%step_left
        self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)

        ##Move 
        while step_left > 0:
            step_info = "You got %d step left\t"%step_left
            self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)

            move = get_action()
            ## If not valid_move, continue
            valid_move = False
            
            ##Exit if move == "ESC" (double pres Esc or control+c)
            if move == "ESC":
                return "ESC"
                ##TODO save current game/ensure exit
            if move not in set(["UP","DOWN","RIGHT","LEFT"]):
                continue

            current_cell = self.gamemap.player_loc[player]
            if move == "UP":
                adj_cell = (current_cell[0],current_cell[1]-1)
            elif move == "DOWN":
                adj_cell = (current_cell[0],current_cell[1]+1)
            elif move == "LEFT":
                adj_cell = (current_cell[0]-1,current_cell[1])
            elif move == "RIGHT":
                adj_cell = (current_cell[0]+1,current_cell[1])
            
            grid_between_cell = (2*current_cell[0]+2*adj_cell[0]+2,\
                                 2*current_cell[1]+2*adj_cell[1]+2)
            item_bewteen_cell = self.gamemap.grid_dict[grid_between_cell[0]]\
                                                      [grid_between_cell[1]]
            ##Check if adjacent is wall or space
            if item_bewteen_cell == "wall":
                continue
            elif item_bewteen_cell == "space":
                valid_move = True
            else:
                ##There should be no forth option except for["wall","space","door_x"] 
                assert item_bewteen_cell.startswith("door_")
                door_id = item_bewteen_cell.split("_")[1]
                for item in self.package_dict[player]:
                    ##If player has key and the key number == door numbe
                    if item.startswith("key_") and item.split("_")[1] == door_id:
                        valid_move = True
            
            if valid_move:
                ## If it is a valid_move, move and continue
                self.gamemap.cell_dict[current_cell[0]][current_cell[1]].remove(player)
                self.gamemap.cell_dict[adj_cell[0]][adj_cell[1]].append(player)
                self.gamemap.player_loc[player] = adj_cell
                step_left -= 1
        
        ##Do Action after move
        ##Only one action can be done each turn
        step_info = "Action: (D)rop   (P)ick   (E)nd\t"
        self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)

        action = get_action()
        player_loc = self.gamemap.player_loc[player]
        cell_items = self.gamemap.cell_dict[player_loc[0]][player_loc[1]]

        while action not in set(["D","P","E","ESC"]):
            step_info = "%s id not a valid action\tAction: (D)rop   (P)ick   (E)nd"%action
            self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
            action = get_action()

        if action == "ESC":
            return "ESC"
        
        elif action == "E":
            step_info = "\tYour Turn is End"
            self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
            time.sleep(1)
            return 1

        elif action == "D":
            dropable_items = ["message_A","message_B","key_1","key_2","key_3","key_4"]
            dropable_items_in_package = []
            for item in self.package_dict[player]:
                if item in dropable_items:
                    dropable_items_in_package.append(item)
            dropable_items_in_package = list(set(dropable_items_in_package))

            ## If cell is full, you can not drop anything
            if len(cell_items) >= 9:
                step_info = "Cell is full, you can not drop here\tYour Turn is End"
                self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
                time.sleep(1)
                return 1

            ## If player's package has nothing, end turn
            if len(dropable_items_in_package) == 0:
                step_info = "You have nothing to Drop, \tYour Turn is End"
                self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
                time.sleep(1)
                return 1
            
            if len(dropable_items_in_package) == 1:
                choice = 0
            else:
                drop_choice = []
                for i,item in enumerate(dropable_items_in_package):
                    ##drop_choice index starts from 1, while real list index starts from 0
                    drop_choice.append("%d:%s"%(i+1,item))
                step_info = "Choose Something to Drop, \t %s"%" ".join(drop_choice)
                self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
                choice = get_action()
                if choice not in set([str(i+1) for i in xrange(len(dropable_items_in_package))]):
                    step_info = "%s is not a valid choice\tYour Turn is End"%choice
                    self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
                    time.sleep(1)
                    return 1
                else:
                    choice = int(choice)-1

            item = dropable_items_in_package[choice]
            cell_items.append(item)
            ##replace first item with "empty"
            self.package_dict[player][self.package_dict[player].index(item)] = "empty"
            step_info = "You droped %s \tYour Turn is End"%item
            self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
            time.sleep(1)
            return 1

        elif action == "P":##Pick up something is possible
            pickable_items = ["message_A","message_B","key_1","key_2","key_3","key_4"]
            pickable_items_in_cell = []
            for item in cell_items:
                if item in pickable_items:
                    pickable_items_in_cell.append(item)
            ##filter out redundant items 
            pickable_items_in_cell = list(set(pickable_items_in_cell))

            if len(pickable_items_in_cell) == 0:
                step_info = "There is nothing pickable in this cell \t Your Turn is End"
                self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
                time.sleep(1)
                return 1

            if "empty" not in self.package_dict[player]:
                step_info = "Your package is full, drop something first \t Your Turn is End"
                self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
                time.sleep(1)
                return 1

            ## if only one kind of item in that cell, pick that
            if len(pickable_items_in_cell) == 1:
                choice = 0
            else:
                pick_choice = []
                for i,item in enumerate(pickable_items_in_cell):
                    pick_choice.append("%d:%s"%(i+1,item))
                step_info = "Pickup something \t %s"%" ".join(pick_choice)
                self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
                choice = get_action()
                if choice not in set([str(i+1) for i in xrange(len(pickable_items_in_cell))]):
                    step_info = "%s is not a valid choice\tYour Turn is End"%choice
                    self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
                    time.sleep(1)
                    return 1
                else:
                    choice = int(choice)-1

            item = pickable_items_in_cell[0]
            cell_items.remove(item)
            self.package_dict[player][self.package_dict[player].index("empty")] = item
            step_info = "Picked %s \t Your Turn is End"%(item)
            self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
            time.sleep(1)
        return 1

    def _AIgetekeeper_turn(self):
        player = "gatekeeper"
        turn_info = "AIgatekeeper's Turn"
        step_info = "Rolling Dicer...\t"
        self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
        time.sleep(1)
        step_left = random.randint(1,6)
        step_info = "AIgatekeeper got %d step left\t"%(step_left)
        self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
        time.sleep(1)

        ##Target locate
        ##If there is any message on map, target = All msg
        ##If there is no message on map, target = Player_B location
        target_loc_set = set([])
        for x in xrange(self.gamemap.width):
            for y in xrange(self.gamemap.height):
                for items in self.gamemap.cell_dict[x][y]:
                    if items.startswith("message"):
                        target_loc_set.add((x,y))
        if len(target_loc_set) == 0:
            target_loc_set.add(self.gamemap.player_loc["player_B"])

        start_cell = self.gamemap.player_loc[player]
        visited_cells = set([start_cell])
        target_paths = []
        ##if start_cell already in target_loc, target_paths add start_cell
        if start_cell in target_loc_set:
            target_paths.append([start_cell])
        temp_paths = [[start_cell]]
        ##temp_paths is a path FILO stack, record all paths to target_loc
        while temp_paths:
            current_path = temp_paths.pop(0)
            current_cell = current_path[-1]
            x,y = current_cell
            for adj_cell in [(x-1,y),(x,y-1),(x+1,y),(x,y+1)]:
                grid_between_cell = (2*current_cell[0]+2*adj_cell[0]+2,\
                                     2*current_cell[1]+2*adj_cell[1]+2)
                item_bewteen_cell = self.gamemap.grid_dict[grid_between_cell[0]]\
                                                          [grid_between_cell[1]]
                ##if adj_cell can be visit and not been visited, visit it.
                if (item_bewteen_cell) != "space" or (adj_cell in visited_cells):
                    continue

                current_path_clone = [a for a in current_path]
                current_path_clone.append(adj_cell)
                visited_cells.add(adj_cell)

                if adj_cell in target_loc_set:
                    target_paths.append(current_path_clone)
                temp_paths.append(current_path_clone)

        for path in target_paths:
            # The first cell of path == current gatekeeper cell, so starts with 1
            if len(path[1:]) == 0:
                ##Path has only one cell, the gatekeeper just in that the cell
                ##Find a adjancent available cell, walk repeat these two cells
                x,y = path[0]
                last_node = path[0]
                for adj_cell in [(x-1,y),(x,y-1),(x+1,y),(x,y+1)]:
                    grid_between_cell = (2*x+2*adj_cell[0]+2,\
                                         2*y+2*adj_cell[1]+2)
                    item_bewteen_cell = self.gamemap.grid_dict[grid_between_cell[0]]\
                                                              [grid_between_cell[1]]
                    if item_bewteen_cell == "space":
                        second_last_node = adj_cell
                        break
                for i in xrange(step_left-0):
                    if i%2 == 0:
                        path.append(second_last_node) 
                    else:
                        path.append(last_node)

            elif len(path[1:]) < step_left:
                #if path to target < step_left, fill it with last two step
                last_node = path[-1]
                second_last_node = path[-2]
                for i in xrange(step_left - len(path[1:])):
                    if i%2 == 0:
                        path.append(second_last_node)
                    else:
                        path.append(last_node)

        best_path = None
        second_path = None
        other_path = None
        for path in target_paths:
            if len(path[1:]) == step_left and path[-1] in target_loc_set:
                best_path = path
                break
            elif len(path[1:]) == step_left:
                second_path = path
            else:
                other_path = path

        if best_path != None:
            gatekeeper_path = best_path
        elif second_path != None:
            gatekeeper_path = second_path
        else:
            gatekeeper_path = other_path

        last_cell = gatekeeper_path.pop(0)

        while gatekeeper_path and step_left != 0:
            current_cell = gatekeeper_path.pop(0)
            self.gamemap.cell_dict[last_cell[0]][last_cell[1]].remove(player)
            self.gamemap.cell_dict[current_cell[0]][current_cell[1]].append(player)
            self.gamemap.player_loc[player] = current_cell
            step_left -= 1
            step_info = "AIgatekeeper got %d step left\t"%(step_left)
            self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
            time.sleep(0.5) 
            last_cell = current_cell

        for item in self.gamemap.cell_dict[last_cell[0]][last_cell[1]]:
            ##if cell has message, pickup message
            if item.startswith("message_"):
                self.gamemap.cell_dict[last_cell[0]][last_cell[1]].remove(item)
                self.package_dict[player][self.package_dict[player].index("empty")] = item
                step_info = "Picked up %s\t AIgatekeeper's Turn is End"%(item)
                self.mapview.show_map(self.gamemap,turn_info,step_info,self.package_dict)
                time.sleep(1)
                return 1
        return 1

    def play(self,AIgatekeeper=None):
        if AIgatekeeper == None:
            AIgatekeeper == False

        game_not_end = True
        while game_not_end:
            for player in ["player_A","player_B","gatekeeper"]:
                if AIgatekeeper and player == "gatekeeper":
                    flag = self._AIgetekeeper_turn()
                else:
                    flag = self._playerturn(player)
                if flag == "ESC":
                    game_not_end = False
                    break
                if set(self.package_dict["gatekeeper"]) == set(["message_A","message_B"]):
                    self.mapview.show_map(self.gamemap,"","    GateKeeper WIN\t",self.package_dict)
                    game_not_end = False
                    break
                elif self.package_dict["player_A"].count("message_B") +\
                        self.package_dict["player_B"].count("message_A") >= 5:
                    self.mapview.show_map(self.gamemap,"","Player_A & Player_B WIN\t\t",self.package_dict)
                    game_not_end = False
                    break
                else:
                    continue

def main():
    game = GameController()
    game.play(AI_GATEKEEPER)

if __name__ == "__main__":
    main()
