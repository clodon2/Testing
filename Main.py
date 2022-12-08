'''
Disclaimer: This solution is not scalable for creating a big world.
Creating a game like Minecraft requires specialized knowledge and is not as easy
to make as it looks.
You'll have to do some sort of chunking of the world and generate a combined mesh
instead of separate blocks if you want it to run fast. You can use the Mesh class for this.
You can then use blocks with colliders like in this example in a small area
around the player so you can interact with the world.
'''

# install "ursina"

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController


app = Ursina()

editor_camera = EditorCamera(enabled=False, ignore_paused=True)

# Define a Voxel class.
# By setting the parent to scene and the model to 'cube' it becomes a 3d button.

class Voxel(Button):
    def __init__(self, position=(0,0,0)):
        super().__init__(
            parent = scene,
            position = position,
            model = 'cube',
            origin_y = .5,
            texture = 'white_cube',
            color = color.color(0, 0, random.uniform(.9, 1.0)),
            highlight_color = color.lime,
        )


    def input(self, key):
         if self.hovered:
             if key == 'left mouse down':
                 voxel = Voxel(position=self.position + mouse.normal)

             if key == 'right mouse down':
                 destroy(self)


# create a grid that houses a "block" of voxels
def create_grid(size, position):
    grid = []
    for x in range(size[0]):
        for y in range(size[1]):
            for z in range(size[2]):
                # these variables are used to tell the voxel where to be,
                # the 4th value determines if the voxel is enabled or not (1 = enabled)
                grid.append([x + position[0], y + position[1], z + position[2], 1])
    return grid


# counts the "alive" neighbors of a certain grid spot
# currently set up as a basic Moore's automata
def count_neighbors(grid, position):
    neighbor = 0
    for l in grid:
        # if the neighbor is alive
        if l[3] == 1:
            # checks if the nighbor is within the neighbor limits
            # currently checks each axis separately, a neighbor is any grid postion
            # that is within the cube that surrounds the input position
            # x
            if position[0] - 1 <= l[0] <= position[0] + 1 and \
                    (position[1] - 1 <= l[1] <= position[1] + 1 or position[2] - 1 <= l[2] <= position[2] + 1):
                if position[1] - 1 <= l[1] <= position[1] + 1:
                    if position[2] - 1 <= l[2] <= position[2] + 1:
                        neighbor += 1
                elif position[2] - 1 <= l[2] <= position[2] + 1:
                    if position[1] - 1 <= l[1] <= position[1] + 1:
                        neighbor += 1
            # y
            elif position[1] - 1 <= l[1] <= position[1] + 1 and \
                    (position[0] - 1 <= l[0] <= position[0] + 1 or position[2] - 1 <= l[2] <= position[2] + 1):
                if position[0] - 1 <= l[0] <= position[0] + 1:
                    if position[2] - 1 <= l[2] <= position[2] + 1:
                        neighbor += 1
                elif position[2] - 1 <= l[2] <= position[2] + 1:
                    if position[0] - 1 <= l[0] <= position[0] + 1:
                        neighbor += 1
            # z
            elif position[2] - 1 <= l[2] <= position[2] + 1 and \
                    (position[1] == l[1] or position[0] == l[0]):
                if position[1] - 1 <= l[1] <= position[1] + 1:
                    if position[0] - 1 <= l[0] <= position[0] + 1:
                        neighbor += 1
                elif position[0] - 1 <= l[0] <= position[0] + 1:
                    if position[1] - 1 <= l[1] <= position[1] + 1:
                        neighbor += 1
    # gets rid of the original position that was detected
    neighbor -= 1
    return neighbor


# randomly disables grid spaces
def random_kill(grid, death_chance):
    for l in grid:
        if random.random() <= death_chance:
            l[3] = 0
    return grid


# Again based on Moore's automata, right now it is set up as
# 12-26/13-14/2/M
# basically 12-26 neighbors means survival, 0-11 means death,
# and 13-14 means (if that cell is "dead") it is enabled again
# 2/m is two-stage (alive or dead) and M is Moore
def run_step(grid):
    old_grid = grid
    for l in grid:
        cell_state = l[3]
        neighbors = count_neighbors(old_grid, l)
        # kills
        if 0 <= neighbors <= 11 and cell_state == 1:
            l[3] = 0
        # revives
        elif 13 >= neighbors >= 14 and cell_state == 0:
            l[3] = 1
    return grid


# used if the grid needs to be accessed multiple times/on input/in a function
class GridObject:
    def __init__(self, size, position):
        self.grid = create_grid(size, position)
        self.grid = random_kill(self.grid, .3)
        # voxel_list is used to store the actual voxels
        self.voxel_list = []
        for l in self.grid:
            voxel = Voxel([l[0], l[1], l[2]])
            if l[3] == 0:
                voxel.enabled = False
            self.voxel_list.append([voxel, l[3]])

    # runs 1 simulation step for the grid
    def grid_update(self):
        self.grid = run_step(self.grid)
        for l in self.grid:
            if l[3] != self.voxel_list[self.grid.index(l)][1]:
                self.voxel_list[self.grid.index(l)][1] = l[3]
                if l[3] == 1:
                    self.voxel_list[self.grid.index(l)][0].enabled = True
                if l[3] == 0:
                    self.voxel_list[self.grid.index(l)][0].enabled = False


# floor
for z in range(8):
    for x in range(8):
        voxel = Voxel(position=(x,0,z))

# testing grid
ez_grid = GridObject([10, 10, 10], [5, 0, 0])


def input(key):
    if key == 'left mouse down':
        hit_info = raycast(camera.world_position, camera.forward, distance=5)
        if hit_info.hit:
            Voxel(position=hit_info.entity.position + hit_info.normal)
    if key == 'p':
        ez_grid.grid_update()


def pause_input(key):
    if key == 'tab':    # press tab to toggle edit/play mode
        editor_camera.enabled = not editor_camera.enabled

        player.visible_self = editor_camera.enabled
        player.cursor.enabled = not editor_camera.enabled
        mouse.locked = not editor_camera.enabled
        editor_camera.position = player.position

        application.paused = editor_camera.enabled

pause_handler = Entity(ignore_paused=True, input=pause_input)



player = FirstPersonController()
app.run()