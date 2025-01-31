from dataclasses import dataclass
from typing import List, Dict

@dataclass
class TerrainType:
    name: str
    food_potential: float
    production_potential: float
    defense_bonus: float
    color: int

class TerrainManager:
    def __init__(self):
        self.terrain_types: List[TerrainType] = [
            TerrainType("sea", 0, 0, 0, 1)  # Default sea terrain
        ]
        self.load_terrain_types()
    
    def load_terrain_types(self):
        """Load terrain types from terrain.typ file"""
        try:
            with open("terrain.typ", "r") as f:
                for _ in range(9):  # Load 9 terrain types (excluding sea)
                    name = f.readline().strip()
                    food = float(f.readline())
                    prod = float(f.readline())
                    defense = float(f.readline())
                    color = int(f.readline())
                    
                    self.terrain_types.append(TerrainType(
                        name=name,
                        food_potential=food,
                        production_potential=prod,
                        defense_bonus=defense,
                        color=color
                    ))
        except Exception as e:
            print(f"Error loading terrain types: {e}")
            # Add some default terrain types if file loading fails
            self.terrain_types.extend([
                TerrainType("plains", 1.0, 1.0, 0.1, 2),
                TerrainType("forest", 0.8, 1.2, 0.2, 6),
                TerrainType("hills", 0.6, 1.5, 0.3, 8),
                TerrainType("mountains", 0.4, 2.0, 0.4, 7),
                TerrainType("desert", 0.2, 0.5, 0.1, 14),
                TerrainType("swamp", 0.5, 0.7, 0.2, 5),
                TerrainType("tundra", 0.3, 0.8, 0.1, 15),
                TerrainType("grassland", 1.2, 0.9, 0.1, 10),
                TerrainType("jungle", 0.7, 1.1, 0.3, 4)
            ])
    
    def get_terrain(self, index: int) -> TerrainType:
        """Get terrain type by index"""
        if 0 <= index < len(self.terrain_types):
            return self.terrain_types[index]
        return self.terrain_types[0]  # Return sea terrain as default
    
    def get_terrain_names(self) -> List[str]:
        """Get list of all terrain names"""
        return [t.name for t in self.terrain_types]
    
    def get_terrain_color(self, index: int) -> int:
        """Get color index for terrain type"""
        return self.get_terrain(index).color
    
    def get_defense_bonus(self, index: int) -> float:
        """Get defense bonus for terrain type"""
        return self.get_terrain(index).defense_bonus
    
    def get_food_potential(self, index: int) -> float:
        """Get food production potential for terrain type"""
        return self.get_terrain(index).food_potential
    
    def get_production_potential(self, index: int) -> float:
        """Get resource production potential for terrain type"""
        return self.get_terrain(index).production_potential
