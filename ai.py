from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import random
from player import Player, PlayerManager
from terrain import TerrainManager
from military import MilitaryManager

@dataclass
class AISettings:
    food_weight: float = 1.0
    production_weight: float = 1.0
    hate_weight: float = 1.0
    diplomacy_weight: float = 1.0
    friendliness: float = 0.5
    chance: float = 0.2
    trust_weight: float = 1.0
    remote_weight: float = 0.5
    min_trust: float = 0.3
    min_morale: float = 0.5
    min_tax: float = 0.1
    
    # Diplomatic thresholds
    trade_threshold: float = 0.6
    friend_threshold: float = 0.4
    ally_threshold: float = 0.2
    
    # Military settings
    war_military_spending: float = 0.4
    peace_military_spending: float = 0.2
    
    # Building priorities
    building_chance: float = 0.7
    church_priority: float = 0.2
    mill_priority: float = 0.3
    navy_priority: float = 0.2
    university_priority: float = 0.3
    
    # Science priorities
    science_priorities: List[float] = None
    
    def __post_init__(self):
        if self.science_priorities is None:
            self.science_priorities = [0.2] * 6  # Equal priority for all sciences

class AI:
    def __init__(
        self,
        player_manager: PlayerManager,
        terrain_manager: TerrainManager,
        military_manager: MilitaryManager
    ):
        self.player_manager = player_manager
        self.terrain_manager = terrain_manager
        self.military_manager = military_manager
        self.settings: Dict[str, AISettings] = {}
        self.load_ai_settings()
    
    def load_ai_settings(self):
        """Load AI settings from .ai files"""
        try:
            # Load default AI first
            self.load_ai_file("default.ai")
            
            # Load other AI files
            self.load_ai_file("land.ai")
            self.load_ai_file("seatrade.ai")
            
        except Exception as e:
            print(f"Error loading AI settings: {e}")
            # Use default settings if loading fails
            self.settings["default.ai"] = AISettings()
    
    def load_ai_file(self, filename: str):
        """Load a single AI settings file"""
        try:
            settings = AISettings()
            
            with open(filename, "r") as f:
                # Read basic weights
                settings.food_weight = float(f.readline())
                settings.production_weight = float(f.readline())
                settings.hate_weight = float(f.readline())
                settings.diplomacy_weight = float(f.readline())
                settings.friendliness = float(f.readline())
                settings.chance = float(f.readline())
                settings.trust_weight = float(f.readline())
                settings.remote_weight = float(f.readline())
                settings.min_trust = float(f.readline())
                
                # Read diplomatic thresholds
                settings.trade_threshold = float(f.readline())
                settings.friend_threshold = float(f.readline())
                settings.ally_threshold = float(f.readline())
                
                # Read other settings
                settings.min_morale = float(f.readline())
                settings.min_tax = float(f.readline())
                
                # Read fear diplomacy levels
                _ = [float(f.readline()) for _ in range(5)]  # fear_dipl values
                
                # Read military and building settings
                settings.war_military_spending = float(f.readline())
                settings.peace_military_spending = float(f.readline())
                settings.building_chance = float(f.readline())
                settings.church_priority = float(f.readline())
                settings.mill_priority = float(f.readline())
                settings.navy_priority = float(f.readline())
                settings.university_priority = float(f.readline())
                
                # Read science priorities
                settings.science_priorities = [float(f.readline()) for _ in range(6)]
            
            self.settings[filename] = settings
            
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            self.settings[filename] = AISettings()
    
    def make_decisions(self, player: Player, game_map: Dict[str, List[List[int]]]):
        """Make all decisions for an AI-controlled player's turn"""
        settings = self.settings.get(player.control, self.settings["default.ai"])
        
        # Adjust tax rate
        self._adjust_tax_rate(player, settings)
        
        # Make diplomatic decisions
        self._make_diplomatic_decisions(player, settings, game_map)
        
        # Make military decisions
        self._make_military_decisions(player, settings, game_map)
        
        # Handle construction
        if player.money > 0 and random.random() < settings.building_chance:
            self._handle_construction(player, settings, game_map)
    
    def _adjust_tax_rate(self, player: Player, settings: AISettings):
        """Adjust player's tax rate based on morale and unemployment"""
        
        # Calculate minimum acceptable morale based on unemployment
        min_morale = settings.min_morale * (
            1 - player.unemployed / max(player.population, 1)
        )
        
        # Try different tax rates
        best_tax = settings.min_tax
        for tax in range(1, 26):  # 0.01 to 0.25
            player.tax_rate = tax / 100
            self.player_manager.calculate_morale(player)
            if player.morale > min_morale:
                best_tax = tax / 100
        
        player.tax_rate = max(best_tax, settings.min_tax)
        self.player_manager.calculate_morale(player)
    
    def _make_diplomatic_decisions(self, player: Player, settings: AISettings, game_map: Dict[str, List[List[int]]]):
        """Handle diplomatic relations and actions"""
        for other_id, other_player in self.player_manager.players.items():
            if other_id == player.id or other_player.land_count == 0:
                continue
            
            # Calculate diplomatic value
            value = self._calculate_diplomatic_value(
                player, other_player, settings, game_map
            )
            
            # Decide action based on value
            if value > settings.ally_threshold:
                player.diplomatic_actions[other_id] = 1  # Try to improve relations
            elif value < -settings.ally_threshold:
                player.diplomatic_actions[other_id] = -1  # Worsen relations
            else:
                player.diplomatic_actions[other_id] = 0  # Stay neutral
    
    def _calculate_diplomatic_value(
        self,
        player: Player,
        other: Player,
        settings: AISettings,
        game_map: Dict[str, List[List[int]]]
    ) -> float:
        """Calculate diplomatic value of relationship with another player"""
        
        # Base value from relative strength
        relative_strength = other.land_count / max(player.land_count, 1)
        value = 1 - relative_strength
        
        # Modify based on trust
        value *= (1 + (other.trust - 1) * settings.trust_weight)
        
        # Calculate total army units for each player
        player_army = 0
        other_army = 0
        for y in range(15):
            for x in range(15):
                if game_map["owner"][y][x] == player.id:
                    player_army += game_map["army"][y][x]
                elif game_map["owner"][y][x] == other.id:
                    other_army += game_map["army"][y][x]
        
        # Consider military threat including science advantage
        military_threat = (
            (other_army + other.navy) / max(player_army + player.navy, 1) * 
            other.science.military / max(player.science.military, 1)
        )
        value -= military_threat * settings.hate_weight
        
        # Apply random variation
        value *= (1 - settings.chance + random.random() * 2 * settings.chance)
        
        return value
    
    def _make_military_decisions(
        self,
        player: Player,
        settings: AISettings,
        game_map: Dict[str, List[List[int]]]
    ):
        """Handle military movement and spending"""
        
        # Determine military spending ratio based on threats
        at_war = any(rel == 1 for rel in player.diplomatic_relations.values())
        military_ratio = (
            settings.war_military_spending if at_war 
            else settings.peace_military_spending
        )
        
        # Calculate military budget
        military_budget = int(player.money * military_ratio)
        
        if military_budget > 0:
            # Prioritize defense of threatened territories
            self._defend_territories(player, military_budget, game_map)
            
            # Build navy if coastal
            if self._has_coast(player, game_map):
                navy_budget = int(military_budget * settings.navy_priority)
                self._build_navy(player, navy_budget)
    
    def _defend_territories(
        self,
        player: Player,
        budget: int,
        game_map: Dict[str, List[List[int]]]
    ):
        """Defend territories based on threat levels"""
        # Find territories that need defense
        threatened_territories = []
        for y in range(len(game_map["terrain"])):
            for x in range(len(game_map["terrain"][0])):
                if game_map["owner"][y][x] == player.id:
                    # Check adjacent tiles for enemies
                    for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < len(game_map["terrain"][0]) and 
                            0 <= ny < len(game_map["terrain"]) and
                            game_map["owner"][ny][nx] != player.id and
                            game_map["owner"][ny][nx] != 0):  # Not empty
                            threatened_territories.append((x, y))
                            break
        
        # Build armies in threatened territories
        if threatened_territories:
            army_cost = self.military_manager.ARMY_COST
            armies_per_territory = max(1, budget // (len(threatened_territories) * army_cost))
            
            for x, y in threatened_territories:
                if player.money >= army_cost:
                    game_map["army"][y][x] += armies_per_territory
                    player.money -= armies_per_territory * army_cost
    
    def _has_coast(self, player: Player, game_map: Dict[str, List[List[int]]]) -> bool:
        """Check if player has coastal territories"""
        for y in range(len(game_map["terrain"])):
            for x in range(len(game_map["terrain"][0])):
                if game_map["owner"][y][x] == player.id:
                    # Check adjacent tiles for sea
                    for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < len(game_map["terrain"][0]) and 
                            0 <= ny < len(game_map["terrain"]) and
                            game_map["terrain"][ny][nx] == 0):
                            return True
        return False
    
    def _build_navy(self, player: Player, budget: int):
        """Build naval forces with available budget"""
        ships = budget // self.military_manager.NAVY_COST
        if ships > 0:
            player.navy += ships
            player.money -= ships * self.military_manager.NAVY_COST
    
    def _handle_construction(
        self,
        player: Player,
        settings: AISettings,
        game_map: Dict[str, List[List[int]]]
    ):
        """Handle construction of buildings"""
        # Find territories owned by the player
        owned_territories = []
        for y in range(len(game_map["terrain"])):
            for x in range(len(game_map["terrain"][0])):
                if game_map["owner"][y][x] == player.id:
                    owned_territories.append((x, y))
        
        if not owned_territories:
            return
            
        # Choose a random territory to build in
        x, y = random.choice(owned_territories)
        
        # Decide what to build based on priorities
        choices = [
            (settings.church_priority, "church", self.military_manager.CHURCH_COST),
            (settings.mill_priority, "mill", self.military_manager.MILL_COST),
            (settings.university_priority, "university", self.military_manager.UNIVERSITY_COST)
        ]
        
        # Filter out choices we can't afford
        affordable = [(p, b, c) for p, b, c in choices if player.money >= c]
        if not affordable:
            return
            
        # Weight choices by priority
        total = sum(p for p, _, _ in affordable)
        if total <= 0:
            return
            
        r = random.random() * total
        current = 0
        for priority, building, cost in affordable:
            current += priority
            if r <= current:
                # Build it
                game_map[building][y][x] += 1
                player.money -= cost
                break
    
    def _handle_science_development(self, player: Player, settings: AISettings):
        """Science development is automatic through universities"""
        pass
