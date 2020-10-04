
import sys
from pathlib import Path
from configparser import ConfigParser

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage

from panda3d.core import loadPrcFile
from panda3d.core import AntialiasAttrib
from panda3d.core import TransparencyAttrib

from pytmx import TiledMap

from tiles import tiles
from utils.lights import ambient_light, directional_light
from utils.grid import from_hex

config_dir = Path('config')
data_dir = Path('data')

window = config_dir / 'window.prc'
loadPrcFile(window)


class Game(ShowBase):
    def __init__(self, level, controls):
        super().__init__()

        self.set_background_color(33/255, 46/255, 56/255)

        tile_list = tiles(self)

        def extract_tile_id(filename, flags, tileset):
            def inner(rect, flags):
                x, y, w, h = rect
                return x // w + y // h * tileset.columns
            return inner

        tiled_map = TiledMap(level, image_loader=extract_tile_id)

        level = self.render.attach_new_node("level")
        width = tiled_map.width
        height = tiled_map.height * 3**0.5 / 2
        level.set_pos(width / 2, -height / 2, 0)

        z = {}

        for layer in tiled_map:
            for x, y, tile_id in layer.tiles():
                if (tile_type := tile_list.get(tile_id)) is not None:
                    tile = level.attach_new_node("tile")
                    tile.set_pos(*from_hex(x, y), z.get((x, y), 0))
                    z[(x, y)] = z.get((x, y), 0) + tile_type.height
                    tile_type.node.instance_to(tile)

        # use antialiasing
        self.render.set_antialias(AntialiasAttrib.MMultisample)

        # position camera
        self.camera.set_pos(0, 8, 8)
        self.camera.look_at(0, 0, 0)
        self.disable_mouse()

        # create a light
        ambient = ambient_light(colour=(.3, .3, .3, 1))
        ambient = self.render.attach_new_node(ambient)
        self.render.set_light(ambient)

        # create another light
        directional = directional_light(
            colour=(1, 1, 1, 1), direction=(-1, -2, -3))
        directional = self.render.attach_new_node(directional)
        self.render.set_light(directional)

        # load control scheme from file
        self.load_controls(controls)
        self.task_mgr.add(self.loop, 'loop')

        # create a ui
        tile_tray = OnscreenImage(image='data/black.png',
            pos=(0, 0, -1.66), color=(0, 0, 0, .3), parent=self.render2d)
        tile_tray.setTransparency(TransparencyAttrib.MAlpha)





    def load_controls(self, controls: str):
        parser = ConfigParser()
        parser.read(controls)
        default = parser['DEFAULT']
        self.actions = {a: False for a in default}

        for action, key in default.items():
            self.accept(key, self.actions.update, [{action: True}])
            self.accept(key + '-up', self.actions.update, [{action: False}])


    def loop(self, task):
        for action, value in self.actions.items():
            if value:
                print(action)

        if self.mouseWatcherNode.has_mouse():
            x = self.mouseWatcherNode.get_mouse_x()
            y = self.mouseWatcherNode.get_mouse_y()
            print(x, y)

        if self.actions['exit']:
            sys.exit()

        return task.cont


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument(
        '-l', '--level',
        default=data_dir / 'level_01.tmx',
    )
    parser.add_argument(
        '-c', '--controls',
        default=config_dir / 'controls.ini',
    )
    game = Game(**vars(parser.parse_args()))
    game.run()
