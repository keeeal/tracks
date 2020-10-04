from dataclasses import dataclass, field
from direct.showbase import ShowBase
from panda3d.core import NodePath
from pathlib import Path
from typing import Mapping, Optional, Tuple, List, Callable

from rhythm import Timeline, Beat
from utils.grid import from_hex


@dataclass(frozen=True)
class Tile:
    """A Tile object represents a specific type of terrain tile"""

    tile_id: int = field(compare=True)
    """Identifier for this specific tile type"""

    node: NodePath = field(compare=False)
    """Contains models for the tile"""

    height: float = field(compare=False)
    """Height of the surface of the tile for placing other models on top"""

    clear: bool = field(compare=False)
    """If clear is true, rails and other buildings can be placed on the tile"""


    def instance_to(self, node: NodePath) -> None:
        """Place the tile's model under the given node"""
        self.node.instanceTo(node)

    def register(self, node: NodePath, timeline: Timeline, tile_x: int, tile_y: int, get_track: Callable[[int, int], Optional["Track"]]) -> None:
        """Register any neccesary callbacks with timeline."""
        pass


@dataclass(frozen=True)
class Track(Tile):
    """A Track object represents a tile of railway track that the train can move on"""

    src: Tuple[int, int] = field(compare=False)
    """Relative coordinates of tile train enters from (or leaves to if reversed)"""

    dst: Tuple[int, int] = field(compare=False)
    """Relative coordinates of tile train leaves to (or enters from if reversed)"""

    path: Tuple[float, Tuple[float, float]] = field(compare=False)
    """List of cumulative costs and positions within the tile. 0 is entry time and 1 exit (or the opposite if reversed)"""

    removable: bool = field(compare=False)
    """Flag indicating whether the track can be moved by the player"""


@dataclass(frozen=True)
class Train(Track):
    """A Train object represents the starting position of a train"""

    train: NodePath = field(compare=False)
    """Contains model for the train"""

    speed: float = field(compare=False)
    """Cost travelled by the train in 1 second"""

    def __post_init__(self):
        self.train.reparentTo(self.node)

    def instance_to(self, node: NodePath) -> None:
        """Place the tile's model under the given node"""
        self.node.copyTo(node)

    def register(self, node: NodePath, timeline: Timeline, tile_x: int, tile_y: int, get_track: Callable[[int, int], Track]) -> None:
        """Register any neccesary callbacks with timeline."""
        offset: float = 0.5
        direction: int = 1
        x: int = tile_x
        y: int = tile_y
        node = node.getChild(0).getChild(1)

        def update_position(x: int, y: int, offset: float, direction: int, current_pos: float, current_tile: Track) -> Tuple[int, int, float, int, Track]:
            if current_tile is None:
                return x, y, offset, direction, None
            if current_pos > current_tile.path[-1][0]:
                if direction > 0:
                    delx, dely = current_tile.dst
                else:
                    delx, dely = current_tile.src
                next_tile = get_track(x + delx,  y + dely)
                if next_tile is not None:
                    if next_tile.src == (-delx, -dely):
                        return update_position(x + delx, y + dely, offset - current_tile.path[-1][0], 1, current_pos - current_tile.path[-1][0], next_tile)
                    elif next_tile.dst == (-delx, -dely):
                        return update_position(x + delx, y + dely, offset - current_tile.path[-1][0], -1, current_pos - current_tile.path[-1][0], next_tile)
            return x, y, offset, direction, current_tile

        def update(old: float, new: float) -> List[Beat]:
            nonlocal offset, direction, x, y
            if new + offset < 0:
                offset = 0.5
                x = tile_x
                y = tile_y
            current_pos = new * self.speed + offset
            current_tile = get_track(x, y)
            x, y, offset, direction, current_tile = update_position(x, y, offset, direction, current_pos, current_tile)
            current_pos = new * self.speed + offset

            oldpos = node.getPos()

            if direction > 0:
                path = iter(current_tile.path)
                dir_offset = 0
            else:
                path = iter(reversed(current_tile.path))
                dir_offset = current_tile.path[-1][0]
            prev_cost, (prev_x, prev_y) = next(path)
            for cost, (node_x, node_y) in path:
                cost = dir_offset + direction * cost
                if current_pos < cost:
                    frac = (current_pos - prev_cost) / (cost - prev_cost)
                    local_x = prev_x + (node_x - prev_x) * frac
                    local_y = prev_y + (node_y - prev_y) * frac
                    break
                prev_x, prev_y, prev_cost = node_x, node_y, cost
            else:
                local_x, local_y = prev_x, prev_y
            hex_x, hex_y = from_hex(x, y)
            origin_x, origin_y = from_hex(tile_x, tile_y)
            node.setPos(hex_x - origin_x + local_x, hex_y - origin_y + local_y, oldpos.z)

            return []

        timeline.subscribe(update)


def tiles(base: ShowBase) -> Mapping[int, Tile]:
    """Initialises list of tiles and loads required models"""
    # TODO: consider loading this from a configuration file

    model_path = Path("models")

    def load_model(name: str, pos: Optional[Tuple[int, int, int]] = None,
        rot: Optional[Tuple[int, int, int]] = (0, 90, 0), parent: Optional[NodePath] = None) -> NodePath:

        node = base.loader.load_model(model_path / f'{name}.dae')
        node.set_hpr(*rot)

        if pos is not None:
            node.set_pos(*pos)

        if parent is not None:
            node.reparent(parent)

        return node

    return {
        tile.tile_id: tile
        for tile in (
            Tile(
                tile_id=1,
                node=load_model("dirt"),
                height=0.1,
                clear=True,
            ),
            Tile(
                tile_id=2,
                node=load_model("dirt_lumber"),
                height=0.1,
                clear=False,
            ),
            Tile(
                tile_id=3,
                node=load_model("grass"),
                height=0.2,
                clear=True,
            ),
            Tile(
                tile_id=4,
                node=load_model("grass_forest"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=5,
                node=load_model("grass_hill"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=6,
                node=load_model("sand"),
                height=0.2,
                clear=True,
            ),
            Tile(
                tile_id=7,
                node=load_model("sand_rocks"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=8,
                node=load_model("stone"),
                height=0.2,
                clear=True,
            ),
            Tile(
                tile_id=9,
                node=load_model("stone_rocks"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=10,
                node=load_model("stone_hill"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=11,
                node=load_model("stone_mountain"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=12,
                node=load_model("water"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=13,
                node=load_model("water_rocks"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=14,
                node=load_model("water_island"),
                height=0.2,
                clear=False,
            ),
            Track(
                tile_id=15,
                node=load_model("trackStraight"),
                height=0.0,
                clear=False,
                removable=True,
                src=(-1, 0),
                dst=(1, 0),
                path=[(0, (0.5, 0)), (1, (-0.5, 0))],
            ),
            Train(
                tile_id=0,
                node=load_model("trackStraight"),
                train=load_model("trainLocomotive", rot=(0, 0, 0)),
                height=0.0,
                clear=False,
                removable=False,
                src=(-1, 0),
                dst=(1, 0),
                path=[(0, (0.5, 0)), (1, (-0.5, 0))],
                speed=1.0,
            ),
        )
    }
