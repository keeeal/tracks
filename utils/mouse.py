from panda3d.core import CollisionHandlerQueue, CollisionTraverser, CollisionNode, GeomNode, CollisionRay

class MouseHandler:
    def __init__(self, camera, level):
        self.camera = camera
        self.level = level
        self.handler = CollisionHandlerQueue()
        self.traverser = CollisionTraverser('traverser')
        pickerNode = CollisionNode('mouseRay')
        pickerNP = self.camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)
        self.traverser.addCollider(pickerNP, self.handler)

    def pick_node(self, mpos):
        self.pickerRay.setFromLens(self.camera.getChild(0).node(), mpos.getX(), mpos.getY())
        self.traverser.traverse(self.level)

        if self.handler.getNumEntries() > 0:
            self.handler.sortEntries()
            node = self.handler.getEntry(0).getIntoNodePath()
            if not node.isEmpty():
                return node
