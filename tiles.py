from dataclasses import dataclass, field
from direct.showbase import ShowBase
import numpy as np
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

    src: Callable[[int, int], Tuple[int, int]] = field(compare=False)
    """Relative coordinates of tile train enters from (or leaves to if reversed)"""

    dst: Callable[[int, int], Tuple[int, int]] = field(compare=False)
    """Relative coordinates of tile train leaves to (or enters from if reversed)"""

    path: Tuple[float, Tuple[float, float]] = field(compare=False)
    """List of cumulative costs and positions within the tile. 0 is entry time and 1 exit (or the opposite if reversed)"""

    removable: bool = field(compare=False)
    """Flag indicating whether the track can be moved by the player"""

    beats: List[float] = field(compare=False)
    """Timings of beats produced by this track, given in cumulative cost"""


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

        def update_position(x: int, y: int, offset: float, direction: int, old_pos: float, current_pos: float, current_tile: Track, beats: Optional[List[Beat]] = None) -> Tuple[int, int, float, int, Track, List[Beat]]:
            if beats is None:
                beats = []
            if current_tile is None:
                return x, y, offset, direction, None, beats
            if direction > 0:
                beats += [Beat(beat - offset, self.tile_id) for beat in current_tile.beats if beat > old_pos + offset and beat <= current_pos + offset]
            else:
                beats += [Beat(beat - offset, self.tile_id) for beat in current_tile.beats if current_tile.path[-1][0] - beat > old_pos + offset and current_tile.path[-1][0] - beat <= current_pos + offset]
            if current_pos + offset > current_tile.path[-1][0]:
                if direction > 0:
                    del_fun = current_tile.dst
                else:
                    del_fun = current_tile.src
                next_tile = get_track(*del_fun(x, y))
                if next_tile is not None:
                    if next_tile.src == del_fun.reverse:
                        return update_position(*del_fun(x, y), offset - current_tile.path[-1][0], 1, old_pos, current_pos, next_tile, beats)
                    elif next_tile.dst == del_fun.reverse:
                        return update_position(*del_fun(x, y), offset - current_tile.path[-1][0], -1, old_pos, current_pos, next_tile, beats)
            return x, y, offset, direction, current_tile, beats

        def update(old: float, new: float) -> List[Beat]:
            nonlocal offset, direction, x, y
            if new + offset < 0:
                offset = 0.5
                x = tile_x
                y = tile_y
            old_pos = old * self.speed
            current_pos = new * self.speed
            current_tile = get_track(x, y)
            x, y, offset, direction, current_tile, new_beats = update_position(x, y, offset, direction, old_pos, current_pos, current_tile)
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
                angle = np.degrees(np.arctan2(prev_y - node_y, prev_x - node_x))
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
            node.setHpr(60, 90, angle)

            return new_beats

        timeline.subscribe(update)


def left(x: int, y: int) -> Tuple[int, int]:
    return x - 1, y


def right(x: int, y: int) -> Tuple[int, int]:
    return x + 1, y


left.reverse = right
right.reverse = left


def up_left(x: int, y: int) -> Tuple[int, int]:
    return (x - 1 if y % 2 == 0 else x), y - 1


def down_right(x: int, y: int) -> Tuple[int, int]:
    return (x if y % 2 == 0 else x + 1), y + 1


up_left.reverse = down_right
down_right.reverse = up_left


def up_right(x: int, y: int) -> Tuple[int, int]:
    return (x if y % 2 == 0 else x + 1), y - 1


def down_left(x: int, y: int) -> Tuple[int, int]:
    return (x - 1 if y % 2 == 0 else x), y + 1


up_right.reverse = down_left
down_left.reverse = up_right


def tiles(base: ShowBase) -> Mapping[int, Tile]:
    """Initialises list of tiles and loads required models"""
    # TODO: consider loading this from a configuration file

    items_dir = Path('models') / 'items'
    tiles_dir = Path('models') / 'tiles'
    track_dir = Path('models') / 'track'
    train_dir = Path('models') / 'train'

    def load_model(path: str, pos: Optional[Tuple[int, int, int]] = None,
        rot: Optional[int] = 0, parent: Optional[NodePath] = None) -> NodePath:

        node = base.loader.load_model(path)
        node.set_hpr(60, 90, rot)

        if pos is not None:
            node.set_pos(*pos)

        if parent is not None:
            node.reparentTo(parent)

        return node

    def wrap_model(*args, parent: Optional[NodePath] = None, **kwargs):
        dummy = NodePath('dummy')
        load_model(*args, parent=dummy, **kwargs)
        if parent is not None:
            dummy.reparentTo(parent)
        return dummy

    return {
        tile.tile_id: tile
        for tile in (
            Tile(
                tile_id=0,
                node=load_model(tiles_dir / "building_cabin.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=1,
                node=load_model(tiles_dir / "building_castle.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=2,
                node=load_model(tiles_dir / "building_dock.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=3,
                node=load_model(tiles_dir / "building_farm.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=4,
                node=load_model(tiles_dir / "building_house.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=5,
                node=load_model(tiles_dir / "building_market.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=6,
                node=load_model(tiles_dir / "building_mill.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=7,
                node=load_model(tiles_dir / "building_mine.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=8,
                node=load_model(tiles_dir / "building_sheep.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=9,
                node=load_model(tiles_dir / "building_smelter.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=10,
                node=load_model(tiles_dir / "building_tower.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=11,
                node=load_model(tiles_dir / "building_village.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=12,
                node=load_model(tiles_dir / "building_wall.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=13,
                node=load_model(tiles_dir / "building_water.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=14,
                node=load_model(tiles_dir / "dirt.dae"),
                height=0.1,
                clear=True,
            ),
            Tile(
                tile_id=15,
                node=load_model(tiles_dir / "dirt_lumber.dae"),
                height=0.1,
                clear=False,
            ),
            Tile(
                tile_id=16,
                node=load_model(tiles_dir / "grass.dae"),
                height=0.2,
                clear=True,
            ),
            Tile(
                tile_id=17,
                node=load_model(tiles_dir / "grass_forest.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=18,
                node=load_model(tiles_dir / "grass_hill.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=19,
                node=load_model(tiles_dir / "river_corner.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=20,
                node=load_model(tiles_dir / "river_cornerSharp.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=21,
                node=load_model(tiles_dir / "river_crossing.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=22,
                node=load_model(tiles_dir / "river_end.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=23,
                node=load_model(tiles_dir / "river_intersectionA.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=24,
                node=load_model(tiles_dir / "river_intersectionB.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=25,
                node=load_model(tiles_dir / "river_intersectionC.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=26,
                node=load_model(tiles_dir / "river_intersectionD.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=27,
                node=load_model(tiles_dir / "river_intersectionE.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=28,
                node=load_model(tiles_dir / "river_intersectionF.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=29,
                node=load_model(tiles_dir / "river_intersectionG.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=30,
                node=load_model(tiles_dir / "river_intersectionH.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=31,
                node=load_model(tiles_dir / "river_start.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=32,
                node=load_model(tiles_dir / "river_straight.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=33,
                node=load_model(tiles_dir / "sand.dae"),
                height=0.2,
                clear=True,
            ),
            Tile(
                tile_id=34,
                node=load_model(tiles_dir / "sand_rocks.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=35,
                node=load_model(tiles_dir / "stone.dae"),
                height=0.2,
                clear=True,
            ),
            Tile(
                tile_id=36,
                node=load_model(tiles_dir / "stone_hill.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=37,
                node=load_model(tiles_dir / "stone_mountain.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=38,
                node=load_model(tiles_dir / "stone_rocks.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=39,
                node=load_model(tiles_dir / "water.dae"),
                height=0.1,
                clear=False,
            ),
            Tile(
                tile_id=40,
                node=load_model(tiles_dir / "water_island.dae"),
                height=0.2,
                clear=False,
            ),
            Tile(
                tile_id=41,
                node=load_model(tiles_dir / "water_rocks.dae"),
                height=0.2,
                clear=False,
            ),
            Track(
                tile_id=42,
                node=load_model(track_dir / "straight_1-2-3-4.dae"),
                height=0.0,
                clear=False,
                removable=True,
                src=left,
                dst=right,
                path=[(0, (0.5, 0)), (1, (-0.5, 0))],
                beats=[0, 0.25, 0.5, 0.75],
            ),
            Track(
                tile_id=43,
                node=load_model(track_dir / "curved_1-2-3-4.dae"),
                height=0.0,
                clear=False,
                removable=True,
                src=left,
                dst=right,
                path=[(0, (0.5, 0)), (1, (-0.5, 0))],
                beats=[0, 0.25, 0.5, 0.75],
            ),
            Train(
                tile_id=44,
                node=wrap_model(track_dir / "straight_1-2-3-4.dae"),
                train=load_model(train_dir / "train.dae"),
                height=0.0,
                clear=False,
                removable=False,
                src=left,
                dst=right,
                path=[(0, (0.5, 0)), (1, (-0.5, 0))],
                speed=1.0,
                beats=[],
            ),
        )
    }
