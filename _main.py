
import sys
from pathlib import Path
from configparser import ConfigParser

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage

from panda3d.core import loadPrcFile
from panda3d.core import AntialiasAttrib
from panda3d.core import TransparencyAttrib
from panda3d.core import CollisionHandlerQueue, CollisionTraverser, CollisionNode, GeomNode, CollisionRay

from pytmx import TiledMap

from rhythm import Timeline
from tiles import tiles, Track
from utils.lights import ambient_light, directional_light
from utils.grid import from_hex, to_hex

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

        def extract_tile_id(filename, flags, tileset):
            def inner(rect, flags):
                x, y, w, h = rect
                return x // w + y // h * tileset.columns
            return inner

        tile_list = tiles(self)
        tiled_map = TiledMap(level, image_loader=extract_tile_id)
        level = self.render.attach_new_node("level")
        width = tiled_map.width
        height = tiled_map.height * 3**0.5 / 2
        level.set_pos(width / 2, -height / 2, 0)

        def get_track(x, y):
            for i, layer in enumerate(tiled_map):
                tile = tile_list.get(tiled_map.get_tile_image(x, y, i))
                if isinstance(tile, Track):
                    return tile
            return None

        z = {}
        for layer in tiled_map:
            for x, y, tile_id in layer.tiles():
                if (tile_type := tile_list.get(tile_id)) is not None:
                    tile = level.attach_new_node("tile")
                    tile.set_pos(*from_hex(x, y), z.get((x, y), 0))
                    z[(x, y)] = z.get((x, y), 0) + tile_type.height
                    tile_type.instance_to(tile)
                    tile_type.register(tile, self.timeline, x, y, get_track)

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

        thumbs = ['straight_thumb.png',
                  'straight_thumb.png',
                  'curved_thumb.png']

        for n, thumb in enumerate(thumbs):
            _thumb = OnscreenImage(image='data/' + thumb,
                pos=((n+1)*2/(len(thumbs) + 1) - 1, 0, -.82),
                scale=.15, parent=self.aspect2d)
            _thumb.setTransparency(TransparencyAttrib.MAlpha)

        selected_track = None

        myHandler = CollisionHandlerQueue()
        myTraverser = CollisionTraverser('traverser')
        pickerNode = CollisionNode('mouseRay')
        pickerNP = self.camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        pickerRay = CollisionRay()
        pickerNode.addSolid(pickerRay)
        myTraverser.addCollider(pickerNP, myHandler)

        def handle_mouse_move():
            mpos = self.mouseWatcherNode.getMouse()
            pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())
            myTraverser.traverse(self.render)

            if myHandler.getNumEntries() > 0:
                myHandler.sortEntries()
                pickedObj = myHandler.getEntry(0).getIntoNodePath()
                if not pickedObj.isEmpty():
                    tile = pickedObj.parent.parent.parent
                    x, y, z = tile.get_pos()
                    print(to_hex(x, y))

        def handle_mouse_click():
            mpos = self.mouseWatcherNode.getMouse()
            if mpos.y < -2/3:
                for n, thumb in enumerate(thumbs):
                    scale, aspect_ratio = .15, 16/9
                    x, y = (n+1)*2/(len(thumbs) + 1) - 1, -.82
                    if -scale < x - mpos.x*aspect_ratio < scale:
                        if thumbs[n] == 'straight_thumb.png':
                            tile_id = 0
                        elif thumbs[n] == 'curved_thumb.png':
                            tile_id = 1
                        tile_type = tile_list.get(tile_id))
                        tile = level.attach_new_node("tile")
                        tile.set_pos(*from_hex(x, y), z.get((x, y), 0))
                        z[(x, y)] = z.get((x, y), 0) + tile_type.height
                        tile_type.instance_to(tile)
                        tile_type.register(tile, self.timeline, x, y, get_track)

        self.handle_mouse_move = handle_mouse_move
        self.handle_mouse_click = handle_mouse_click



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
