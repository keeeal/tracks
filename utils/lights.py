
from panda3d.core import AmbientLight, DirectionalLight


def ambient_light(colour):
    light = AmbientLight("ambientLight")
    light.set_color(colour)
    return light


def directional_light(colour, direction, specular_colour=None):
    if specular_colour is None:
        specular_colour = colour

    light = DirectionalLight("directionalLight")
    light.set_color(colour)
    light.set_specular_color(specular_colour)
    light.set_direction(direction)
    return light
