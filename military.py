from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import random
from player import Player
from terrain import TerrainManager

@dataclass
class BattleResult:
    attacker_losses: int
    defender_losses: int
    territory_captured: bool
    population_exchange: int
    fort_damage: int
    message: str

class MilitaryManager:
    def __init__(self, terrain_manager: TerrainManager):
        self.terrain_manager = terrain_manager
        
        # Building costs
        self.FORT_COST = 700
        self.CHURCH_COST = 100
        self.UNIVERSITY_COST = 500
        self.MILL_COST = 200
        self.NAVY_COST = 200
        self.ARMY_COST = 150
        
        # Sell values (% of cost)
        self.FORT_SELL = 0.10  # 70
        self.CHURCH_SELL = 0.10  # 10
        self.UNIVERSITY_SELL = 0.50  # 250
        self.MILL_SELL = 0.90  # 180
        self.NAVY_SELL = 0.90  # 180
        self.ARMY_SELL = 0.50  # 75
    
    def calculate_battle(
        self,
        attacker: Player,
        defender: Player,
        attack_force: int,
        defend_force: int,
        terrain_type: int,
        fort_level: int,
        is_naval: bool = False
    ) -> BattleResult:
        """Calculate the result of a battle between two forces"""
        
        # Base attack strength
        attack_strength = (
            attack_force * 
            attacker.science.military * 
            (0.9 + random.random() * 0.2)  # Random factor 0.9-1.1
        )
        
        if is_naval:
            attack_strength *= attacker.science.sailing
        
        # Base defense strength
        defense_strength = (
            defend_force * 
            defender.science.military * 
            (0.9 + random.random() * 0.2)  # Random factor 0.9-1.1
        )
        
        if is_naval:
            defense_strength *= defender.science.sailing
        else:
            # Apply terrain and fort defense bonuses
            terrain_bonus = self.terrain_manager.get_defense_bonus(terrain_type)
            fort_bonus = fort_level * 0.3
            defense_strength *= (1 + terrain_bonus + fort_bonus)
        
        # Calculate battle outcome
        territory_captured = False
        fort_damage = 0
        population_exchange = 0
        message = ""
        
        if attack_strength > defense_strength:
            # Attacker wins
            victory_ratio = attack_strength / defense_strength
            
            # Calculate losses
            if is_naval:
                attacker_losses = int(attack_force * (1 - (defense_strength / attack_strength) ** 2 / 3))
                defender_losses = int(defend_force * (1 - 1 / 3))
                # Naval victory means destroying enemy navy, allowing for territory capture
                territory_captured = True
                defender.navy = max(0, defender.navy - defender_losses)
            else:
                attacker_losses = int(attack_force * (1 - victory_ratio / (victory_ratio + 1)))
                defender_losses = defend_force
                territory_captured = True
                
                # Calculate fort damage
                if fort_level > 0 and defense_strength > attack_strength / 4:
                    fort_damage = int(fort_level / 2 * random.random() + 0.5)
                
                # Calculate population exchange
                if defender.population > 0:
                    population_exchange = int(
                        defender.population * 
                        self.terrain_manager.get_food_potential(terrain_type) / 
                        max(defender.population, 1)
                    )
            
            message = f"Attacker wins! Losses - Attacker: {attacker_losses}, Defender: {defender_losses}"
            
        else:
            # Defender wins
            defense_ratio = defense_strength / attack_strength
            
            # Calculate losses
            if is_naval:
                attacker_losses = int(attack_force * (1 - 1 / 3))
                defender_losses = int(defend_force * (1 - (attack_strength / defense_strength) ** 2 / 3))
            else:
                attacker_losses = attack_force
                defender_losses = int(defend_force * (1 - attack_strength / defense_strength))
            
            message = f"Defender wins! Losses - Attacker: {attacker_losses}, Defender: {defender_losses}"
        
        return BattleResult(
            attacker_losses=attacker_losses,
            defender_losses=defender_losses,
            territory_captured=territory_captured,
            population_exchange=population_exchange,
            fort_damage=fort_damage,
            message=message
        )
    
    def calculate_revolt_chance(
        self,
        owner: Player,
        original_owner: Player,
        population: int,
        food_ratio: float,
        terrain_food: float,
        revolt_bonus: float = 1.0
    ) -> Tuple[bool, int]:
        """Calculate if a revolt occurs and its strength"""
        
        # Base revolt size based on population pressure and terrain
        revolt_size = int(
            population / 
            max(food_ratio, 0.001) * 
            terrain_food / 
            20 * 
            random.random() * 
            (original_owner.morale ** 2)
        )
        
        # Apply revolt bonus (from neighboring friendly territories)
        revolt_size = int(revolt_size * revolt_bonus)
        
        # Revolt chance increases with low morale
        revolt_chance = (1 - owner.morale ** 2) * (revolt_bonus / 5)
        
        will_revolt = random.random() < revolt_chance
        
        return will_revolt, revolt_size
    
    def move_army(
        self,
        amount: int,
        from_x: int,
        from_y: int,
        to_x: int,
        to_y: int,
        owner: Player,
        army_map: List[List[int]],
        moved_map: List[List[int]],
        terrain_map: List[List[int]]
    ) -> bool:
        """Move army units from one tile to another"""
        
        # Validate coordinates
        if not (0 <= from_x < 15 and 0 <= from_y < 15 and 
                0 <= to_x < 15 and 0 <= to_y < 15):
            return False
            
        # Check if enough units available
        if army_map[from_y][from_x] < amount:
            return False
            
        # Only handle land movement
        if terrain_map[to_y][to_x] == 0:  # Can't move directly to sea
            return False
            
        army_map[from_y][from_x] -= amount
        moved_map[to_y][to_x] += amount
        return True
    
    def embark_army(
        self,
        amount: int,
        from_x: int,
        from_y: int,
        to_x: int,
        to_y: int,
        owner: Player,
        army_map: List[List[int]],
        terrain_map: List[List[int]]
    ) -> bool:
        """Embark army units onto a sea tile"""
        
        # Validate coordinates
        if not (0 <= from_x < 15 and 0 <= from_y < 15 and 
                0 <= to_x < 15 and 0 <= to_y < 15):
            return False
            
        # Check if enough units available
        if army_map[from_y][from_x] < amount:
            return False
            
        # Check if destination is sea
        if terrain_map[to_y][to_x] != 0:  # Not a sea tile
            return False
            
        # Check naval capacity
        if owner.sea_moved + owner.sea_army + amount > owner.navy:
            return False
            
        # Embark the units
        owner.sea_moved += amount
        army_map[from_y][from_x] -= amount
        army_map[to_y][to_x] += amount
        return True
