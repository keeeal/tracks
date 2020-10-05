
import sys
from pathlib import Path
from collections import defaultdict
from configparser import ConfigParser

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage

from panda3d.core import loadPrcFile
from panda3d.core import AntialiasAttrib
from panda3d.core import TransparencyAttrib

from pytmx import TiledMap

from rhythm import Timeline
from tiles import tiles, Track, Train, TrainInstance
from utils.lights import ambient_light, directional_light
from utils.grid import from_hex, to_hex
from utils.mouse import MouseHandler


config_dir = Path('config')
data_dir = Path('data')

window = config_dir / 'window.prc'
loadPrcFile(window)


class Game(ShowBase):
    def __init__(self, level, controls):
        super().__init__()

        self.set_background_color(33/255, 46/255, 56/255)

        # set up timing system
        self.timeline = Timeline()
        self.last_time = 0.0

        self.tile_list = tiles(self)

        def extract_tile(filename, flags, tileset):
            filename = Path(filename).name
            tiles = self.tile_list[filename]
            def inner(rect, flags):
                x, y, w, h = rect
                return tiles[x // w + y // h * tileset.columns]
            return inner

        tiled_map = TiledMap(level, image_loader=extract_tile)
        self.level = self.render.attach_new_node("level")
        self.tile_nodes = self.level.attach_new_node("tiles")
        width = tiled_map.width
        height = tiled_map.height * 3**0.5 / 2
        self.level.set_pos(width / 2, -height / 2, 0)

        self.z = defaultdict(int)
        self.track = {}
        self.clear = {}
        self.trains = []
        for layer in tiled_map:
            for x, y, tile_type in layer.tiles():
                if tile_type is not None:
                    print(tile_type)
                    if isinstance(tile_type, Train):
                        train_node = tile_type.train.copyTo(self.level)
                        train_node.set_pos(*from_hex(x, y), self.z[x, y])
                        self.trains.append(TrainInstance(tile_type, train_node, x, y))
                    if isinstance(tile_type, Track):
                        self.track[x, y] = tile_type
                    else:
                        tile = self.tile_nodes.attach_new_node("tile")
                        tile.set_pos(*from_hex(x, y), self.z[x, y])
                        self.z[x, y] += tile_type.height
                        self.clear[x, y] = self.clear.get((x, y), True) and tile_type.clear
                        tile_type.node.instanceTo(tile)

        self.track_nodes = None
        self.update_track()

        self.timeline.subscribe(self.update_trains)

        # use antialiasing
        self.render.set_antialias(AntialiasAttrib.MMultisample)

        # position camera
        self.camera.set_pos(0, 8, 8)
        self.camera.look_at(0, 0, 0)
        self.disable_mouse()

        # create a light
        ambient = ambient_light(colour=(.3, .3, .3, 1))
        self.ambient = self.render.attach_new_node(ambient)
        self.render.set_light(self.ambient)

        # create another light
        directional = directional_light(
            colour=(1, 1, 1, 1), direction=(-1, -2, -3))
        self.directional = self.render.attach_new_node(directional)
        self.render.set_light(self.directional)

        # load control scheme from file
        self.load_controls(controls)
        self.task_mgr.add(self.loop, 'loop')

        # create a ui
        self.tile_tray = OnscreenImage(image='data/black.png',
            pos=(0, 0, -1.66), color=(0, 0, 0, .3), parent=self.render2d)
        self.tile_tray.setTransparency(TransparencyAttrib.MAlpha)

        track_id_to_thumb = {
            1: 'straight_thumb.png',
            2: 'curved_thumb.png',
        }
        self.thumbs = [1, 1, 2]
        self.selected_thumb = None

        for n, thumb in enumerate(self.thumbs):
            _thumb = OnscreenImage(image='data/' + track_id_to_thumb[thumb],
                pos=((n+1)*2/(len(self.thumbs) + 1) - 1, 0, -.82),
                scale=.15, parent=self.aspect2d)
            _thumb.setTransparency(TransparencyAttrib.MAlpha)

        self.mouse_handler = MouseHandler(self.camera, self.tile_nodes)

    def update_track(self):
        if self.track_nodes is not None:
            self.track_nodes.removeNode()
        self.track_nodes = self.level.attach_new_node("track")
        for (x, y), tile_type in self.track.items():
            if tile_type is not None:
                tile = self.track_nodes.attach_new_node("tile")
                tile.set_pos(*from_hex(x, y), self.z[x, y])
                tile_type.node.instanceTo(tile)

    def update_trains(self, old, new):
        return [
            beat
            for train in self.trains
            for beat in train.update(old, new, self.track)
        ]

    def handle_mouse_move(self):
        mpos = self.mouseWatcherNode.getMouse()
        pickedObj = self.mouse_handler.pick_node(mpos)
        if pickedObj is not None:
            tile = pickedObj.parent.parent.parent
            x, y, z = tile.get_pos()
            self.mouse_tile_coords = to_hex(x, y)
        else:
            self.mouse_tile_coords = None

    def handle_mouse_click(self):
        mpos = self.mouseWatcherNode.getMouse()
        if mpos.y < -2/3:
            # handle tile tray clicked
            for n, thumb in enumerate(self.thumbs):
                scale, aspect_ratio = .15, 16/9
                x, y = (n+1)*2/(len(self.thumbs) + 1) - 1, -.82
                if -scale < x - mpos.x*aspect_ratio < scale:
                    self.selected_thumb = n
        else:
            # handle tile clicked
            if self.selected_thumb is not None:
                tile_x, tile_y = self.mouse_tile_coords
                if self.clear[tile_x, tile_y] and self.track.get((tile_x, tile_y)) is None:
                    self.track[tile_x, tile_y] = self.tile_list['tracks.png'][self.selected_thumb]
                    self.update_track()


    def load_controls(self, controls: str):
        parser = ConfigParser()
        parser.read(controls)
        default = parser['DEFAULT']
        self.actions = {a: False for a in default}

        for action, key in default.items():
            self.accept(key, self.actions.update, [{action: True}])
            self.accept(key + '-up', self.actions.update, [{action: False}])


    def loop(self, task):
        if self.mouseWatcherNode.hasMouse():
            self.handle_mouse_move()
            if self.actions['click']:
                self.handle_mouse_click()

        if self.actions['exit']:
            sys.exit()

        self.timeline.update(task.time - self.last_time)
        self.last_time = task.time

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
