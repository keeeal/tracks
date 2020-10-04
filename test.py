
from panda3d.core import TransparencyAttrib

import direct.directbase.DirectStart
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGui import *

from panda3d.core import TextNode

textObject = OnscreenImage(image='data/black.png', pos=(0, 0, -1.5), color=(0, 0, 0, .4), parent=base.render2d)
textObject.setTransparency(TransparencyAttrib.MAlpha)

# Run the tutorial
base.run()
