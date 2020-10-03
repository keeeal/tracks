
import os, sys, json

import numpy as np
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile
from panda3d.core import AntialiasAttrib

from utils.lights import *

config_dir = 'config'
config = os.path.join(config_dir, 'config.prc')
loadPrcFile(config)


class Game(ShowBase):
    def __init__(self, controls):
        super().__init__()

        base.set_background_color(33/255, 46/255, 56/255)

        # load a tile
        dirt = self.loader.load_model(os.path.join('models', 'dirt.dae'))
        dirt.set_hpr(0, 90, 0)
        dirt.reparent_to(self.render)

        # load another tile
        grass = loader.load_model(os.path.join('models', 'grass.dae'))
        grass.set_hpr(0, 90, 0)
        grass.set_pos(1, 0, 0)
        grass.reparent_to(self.render)

        # load another tile
        grass = loader.load_model(os.path.join('models', 'stone_mountain.dae'))
        grass.set_hpr(0, 90, 0)
        grass.set_pos(.5, -np.sqrt(3)/2, 0)
        grass.reparent_to(self.render)

        # use antialiasing
        self.render.setAntialias(AntialiasAttrib.MMultisample)

        # move camera
        self.camera.set_pos(8, 8, 8)
        self.camera.look_at(0, 0, 0)

        # TODO: How do the default camera controls work?
        self.disable_mouse()

        # create a light
        ambient = ambient_light((.3, .3, .3, 1))
        ambient = self.render.attach_new_node(ambient)
        self.render.set_light(ambient)

        # create another light
        directional = directional_light((1, 1, 1, 1), (-1, -2, -3))
        directional = self.render.attach_new_node(directional)
        self.render.set_light(directional)

        # load control scheme from file
        self.load_controls(controls)
        self.taskMgr.add(self.loop, 'loop')


    def load_controls(self, controls: str):
        with open(controls) as f:
            controls = json.load(f)

        self.actions = {a: False for a in controls.values()}

        def set_action(action: str, value: bool):
            self.actions[action] = value

        for key, action in controls.items():
            self.accept(key, set_action, [action, True])
            self.accept(key + '-up', set_action, [action, False])


    def loop(self, task):
        for action, value in self.actions.items():
            if value:
                print(action)

        if self.actions['exit']:
            sys.exit()

        return task.cont


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--controls', '-c',
        default=os.path.join('config', 'controls.json'))
    game = Game(**vars(parser.parse_args()))
    game.run()
