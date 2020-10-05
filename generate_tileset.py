
import os, sys, json
from pathlib import Path

import numpy as np
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData
from panda3d.core import AntialiasAttrib
from panda3d.core import OrthographicLens

from tiles import tiles, Train
from utils.lights import ambient_light, directional_light


if __name__ == '__main__':
    loadPrcFileData("", """
        window-type none
        show-frame-rate-meter 0
        sync-video 0
    """ )

    aspect = 1.5

    width = 128
    height = int(128 * aspect)

    base = ShowBase()

    tile_lists = tiles(base)

    base.set_background_color(33/255, 46/255, 56/255)

    # use antialiasing
    base.render.setAntialias(AntialiasAttrib.MMultisample)

    # move camera
    lens = OrthographicLens()

    # TODO: How do the default camera controls work?
    base.disable_mouse()

    # create a light
    ambient = ambient_light((.3, .3, .3, 1))
    ambient = base.render.attach_new_node(ambient)
    base.render.set_light(ambient)

    # create another light
    directional = directional_light((1, 1, 1, 1), (-1, -2, -3))
    directional = base.render.attach_new_node(directional)
    base.render.set_light(directional)

    for filename, tile_list in tile_lists.items():
        cols = 8
        rows = max(tile.tile_id for tile in tile_list.values()) // cols + 1

        win = base.openWindow(type='offscreen', size=(cols * width, rows * height), makeCamera=True)

        level = base.render.attachNewNode("level")

        for tile in tile_list.values():
            placeholder = level.attachNewNode("tile-placeholder")
            col = tile.tile_id % cols
            row = tile.tile_id // cols
            placeholder.setPos((cols - col - 1) + 0.5, 0, -((row + 1.0) * aspect - 0.5) * 2**0.5 - 0.1)
            tile.node.instanceTo(placeholder)
            if isinstance(tile, Train):
                train_node = tile.train.instanceTo(placeholder)

        lens.setFilmSize(cols, rows * aspect)
        base.camNode.setLens(lens)
        base.camera.set_pos(cols / 2, 8, -rows * 2**0.5 * aspect / 2 + 8)
        base.camera.look_at(cols / 2, 0, -rows * 2**0.5 * aspect / 2)

        base.graphicsEngine.renderFrame()
        base.screenshot(namePrefix=Path('data') / filename, defaultFilename=False)

        level.removeNode()
        base.closeWindow(win)
