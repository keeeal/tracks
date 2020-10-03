
import os, sys, json

import numpy as np
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData
from panda3d.core import AntialiasAttrib
from panda3d.core import OrthographicLens

from tiles import tiles
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

    tile_list = tiles(base)

    cols = 4
    rows = max(tile_id for tile_id in tile_list) // cols + 1

    base.openWindow(type='offscreen', size=(cols * width, rows * height), makeCamera=True)

    base.set_background_color(33/255, 46/255, 56/255)

    for tile in tile_list.values():
        placeholder = base.render.attachNewNode("tile-placeholder")
        col = tile.tile_id % cols
        row = tile.tile_id // cols
        placeholder.setPos((cols - col - 1) + 0.5, (row + 0.0625) * 2**0.5 * aspect, 0)
        tile.node.instanceTo(placeholder)

    # use antialiasing
    base.render.setAntialias(AntialiasAttrib.MMultisample)

    # move camera
    lens = OrthographicLens()
    lens.setFilmSize(cols, rows * aspect)
    base.camNode.setLens(lens)
    base.camera.set_pos(cols / 2, rows * 2**0.5 / 2 + 8, 8)
    base.camera.look_at(cols / 2, rows * 2**0.5 / 2, 0)

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

    base.graphicsEngine.renderFrame()
    base.screenshot(namePrefix='data/tileset.png', defaultFilename=False)
