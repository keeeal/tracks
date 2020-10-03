from dataclasses import dataclass, field
from direct.showbase import ShowBase
from panda3d.core import NodePath
from pathlib import Path
from typing import Mapping, Optional, Tuple


@dataclass(frozen=True)
class Tile:
    """A Tile object represents a specific type of terrain tile"""

    tile_id: int = field(compare=True)
    """Identifier for this specific tile type"""

    node: NodePath = field(compare=False)
    """Contains models for the tile"""

    height: float = field(compare=False)
    """Height of te surface of the tile for placing other models on top"""

    clear: bool = field(compare=False)
    """If clear is true, rails and other buildings can be placed on the tile"""



def tiles(base: ShowBase) -> Mapping[int, Tile]:
    """Initialises list of tiles and loads required models"""
    # TODO: consider loading this from a configuration file

    model_path = Path("models")

    def load_model(name: str, pos: Optional[Tuple[int, int, int]] = None, parent: Optional[NodePath] = None) -> NodePath:
        node = base.loader.load_model(model_path / f'{name}.dae')
        node.set_hpr(0, 90, 0)
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
        )
    }
