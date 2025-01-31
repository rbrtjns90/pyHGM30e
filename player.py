from dataclasses import dataclass
from typing import List, Dict, Optional
import random

@dataclass
class Science:
    agriculture: float = 1.0
    industry: float = 1.0
    trade: float = 1.0
    sailing: float = 1.0
    military: float = 1.0
    medicine: float = 1.0
    
    def get_level(self, index: int) -> float:
        """Get science level by index"""
        levels = [
            self.agriculture,
            self.industry,
            self.trade,
            self.sailing,
            self.military,
            self.medicine
        ]
        return levels[index - 1] if 1 <= index <= 6 else 1.0
    
    def set_level(self, index: int, value: float):
        """Set science level by index"""
        if 1 <= index <= 6:
            if index == 1: self.agriculture = value
            elif index == 2: self.industry = value
            elif index == 3: self.trade = value
            elif index == 4: self.sailing = value
            elif index == 5: self.military = value
            elif index == 6: self.medicine = value

@dataclass
class Player:
    id: int
    name: str = ""
    control: str = "human"  # "human" or AI file name
    
    # Resources
    money: int = 0
    population: int = 0
    
    # Military
    navy: int = 0
    sea_army: int = 0
    sea_moved: int = 0
    
    # Territory
    land_count: int = 0
    sea_ratio: float = 0.0
    
    # Economy
    tax_rate: float = 0.0
    morale: float = 1.0
    trust: float = 1.0
    
    # Population groups
    peasants: int = 0
    fishers: int = 0
    workers: int = 0
    merchants: int = 0
    soldiers: int = 0
    unemployed: int = 0
    
    # Buildings
    forts: int = 0
    churches: int = 0
    universities: int = 0
    mills: int = 0
    
    def __post_init__(self):
        self.science = Science()
        self.diplomatic_relations: Dict[int, int] = {}  # player_id -> relation level (1-5)
        self.diplomatic_actions: Dict[int, int] = {}  # player_id -> action (-1, 0, 1)

class PlayerManager:
    def __init__(self):
        self.players: Dict[int, Player] = {}
        self.current_player_id: int = 1
        self.max_players: int = 9
        
    def add_player(self, id: int, name: str, control: str = "human") -> Player:
        """Add a new player"""
        if id not in self.players and 1 <= id <= self.max_players:
            player = Player(id=id, name=name, control=control)
            
            # Initialize working population groups based on starting population
            if player.population > 0:
                # Default distribution:
                # 40% peasants (farming)
                # 20% fishers (sea-based)
                # 25% workers (industry)
                # 10% merchants (trade)
                # 5% unemployed
                player.peasants = int(player.population * 0.4)
                player.fishers = int(player.population * 0.2)
                player.workers = int(player.population * 0.25)
                player.merchants = int(player.population * 0.1)
                # Any remaining population goes to unemployed
                player.unemployed = (player.population - 
                    (player.peasants + player.fishers + 
                     player.workers + player.merchants))
            
            self.players[id] = player
            return player
        return None
    
    def get_player(self, id: int) -> Optional[Player]:
        """Get player by ID"""
        return self.players.get(id)
    
    def next_player(self) -> Optional[Player]:
        """Get next player in turn order"""
        # Store initial position to detect full loop
        start_id = self.current_player_id
        
        # Try to find next valid player
        while True:
            # Get next ID
            next_id = self.current_player_id + 1
            if next_id > self.max_players:
                next_id = 1
                
            # If we've looped back to start, no valid players found
            if next_id == start_id:
                return None
            
            # Update current ID
            self.current_player_id = next_id
            
            # Check if this is a valid player
            player = self.get_player(next_id)
            if player and player.land_count > 0:
                return player
    
    def calculate_morale(self, player: Player):
        """Calculate player's morale based on various factors"""
        base_morale = 1.0
        
        # Tax penalty
        tax_penalty = (player.tax_rate/100) * 2
        
        # Unemployment penalty
        unemployment_rate = player.unemployed / max(player.population, 1)
        unemployment_penalty = unemployment_rate
        
        # Trust bonus
        trust_bonus = player.trust / 2
        
        # Debt penalty
        debt_penalty = min(0, player.money) / (10 * max(player.population, 1))
        
        player.morale = max(0, min(1, 
            base_morale * 
            (1 - tax_penalty) * 
            (1 - unemployment_penalty) * 
            (1 + trust_bonus) +
            debt_penalty
        ))
    
    def calculate_income(self, player: Player) -> int:
        """Calculate player's income for the turn"""
        income = 0
        
        # Base income from population groups
        income += int(player.peasants * (player.tax_rate/100) * player.morale * player.science.agriculture * 4)
        income += int(player.fishers * (player.tax_rate/100) * player.morale * player.science.sailing * 4)
        income += int(player.workers * (player.tax_rate/100) * player.morale * player.science.industry * 8)
        income += int(player.merchants * (player.tax_rate/100) * player.morale * player.science.trade * 16)
        
        # Maintenance costs
        income -= int(player.mills * player.science.industry * 20)  # Mill maintenance
        income -= int(player.forts * 30)  # Fort maintenance
        income -= int(player.churches * 3)  # Church maintenance
        income -= int(player.universities * 25)  # University maintenance
        income -= int(player.navy * 20)  # Navy maintenance
        income -= int(player.soldiers * 30)  # Army maintenance
        
        # Interest on treasury
        if player.money > 0:
            income += int(player.money * 0.04)  # 4% interest on positive balance
        else:
            income -= int(abs(player.money) * 0.12)  # 12% interest on debt
            
        return income
    
    def update_science(self, player: Player):
        """Update player's science levels"""
        for i in range(1, 7):
            current_level = player.science.get_level(i)
            
            # Science progress based on universities
            uni_factor = 1 + (player.universities / max(player.population, 1) * 50)
            
            # Base progress rate
            if player.population >= 100:
                progress = (1000 / (10000 * current_level ** 3)) * uni_factor
                progress = min(progress, 0.3)  # Cap progress at 0.3
                
                player.science.set_level(i, current_level + progress)
    
    def calculate_population_growth(self, player: Player, terrain_food_potential: float) -> int:
        """Calculate population growth for the turn"""
        if player.population <= 0:
            return 0
            
        # Base growth rate (0.5% per turn)
        base_growth_rate = 0.005
        
        # Modify growth rate based on factors
        # Medicine science bonus (up to +100% at max level)
        medicine_bonus = (player.science.medicine - 1.0)
        
        # Food potential bonus (scales with agriculture science)
        food_bonus = terrain_food_potential * player.science.agriculture * 0.01
        
        # Church bonus (each church adds 2% up to a cap)
        church_bonus = min(player.churches * 0.02, 0.1)  # Cap at 10%
        
        # Morale impact (low morale reduces growth)
        morale_factor = player.morale
        
        # Calculate final growth rate
        growth_rate = (base_growth_rate + medicine_bonus + food_bonus + church_bonus) * morale_factor
        
        # Calculate population increase
        growth = int(player.population * growth_rate)
        
        # Ensure at least 1 person grows if there's any growth at all
        return max(1, growth) if growth_rate > 0 else 0
