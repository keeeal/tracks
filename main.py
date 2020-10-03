
import os, sys, json

import numpy as np
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile
from panda3d.core import AntialiasAttrib
from pathlib import Path
import pytmx

from tiles import tiles
from utils.lights import ambient_light, directional_light
from utils.grid import from_hex

config_dir = Path('config')
data_dir = Path('data')

config = config_dir / 'config.prc'
loadPrcFile(config)


class Game(ShowBase):
    def __init__(self, controls):
        super().__init__()

        self.set_background_color(33/255, 46/255, 56/255)

        tile_list = tiles(self)

        def extract_tile_id(filename, flags, tileset):
            def inner(rect, flags):
                x, y, w, h = rect
                return x // w + y // h * tileset.columns
            return inner

        tiled_map = pytmx.TiledMap(data_dir / "level_01.tmx", image_loader=extract_tile_id)

        level = self.render.attachNewNode("level")
        width = tiled_map.width
        height = tiled_map.height * 3**0.5 / 2
        level.setPos(width / 2, -height / 2, 0)
        for layer in tiled_map:
            for x, y, tile_id in layer.tiles():
                tile_type = tile_list.get(tile_id)
                if tile_type is not None:
                    tile = level.attachNewNode("tile")
                    tile.setPos(*from_hex(x, y), 0)
                    tile_type.node.instanceTo(tile)

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
    parser.add_argument(
        '--controls', '-c',
        default=config_dir / 'controls.json',
    )
    game = Game(**vars(parser.parse_args()))
    game.run()
