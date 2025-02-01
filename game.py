import os
import sys
import pygame
from typing import Dict, List, Optional
from player import Player, PlayerManager

from terrain import TerrainManager
from player import PlayerManager
from military import MilitaryManager
from ai import AI
from interface import Interface

class Game:
    def __init__(self):
        pygame.init()
        
        # Initialize managers
        self.terrain_manager = TerrainManager()
        self.player_manager = PlayerManager()
        self.military_manager = MilitaryManager(self.terrain_manager)
        self.ai = AI(self.player_manager, self.terrain_manager, self.military_manager)
        self.interface = Interface()
        
        # Game state
        self.running = True
        self.turn = 0
        self.game_map = {
            "owner": [[0] * 15 for _ in range(15)],
            "original": [[0] * 15 for _ in range(15)],
            "terrain": [[0] * 15 for _ in range(15)],
            "fort": [[0] * 15 for _ in range(15)],
            "church": [[0] * 15 for _ in range(15)],
            "university": [[0] * 15 for _ in range(15)],
            "mill": [[0] * 15 for _ in range(15)],
            "army": [[0] * 15 for _ in range(15)],
            "moved": [[0] * 15 for _ in range(15)]
        }
        
    def load_scenario(self, filename: str) -> bool:
        """Load a scenario file"""
        try:
            with open(filename, 'r') as f:
                # Read scenario data
                num_players = int(f.readline())
                current_player = int(f.readline())
                self.turn = int(f.readline())
                
                # Skip science money
                for _ in range(6):
                    _ = int(f.readline())
                
                # Read player data
                for i in range(1, num_players + 1):
                    name = f.readline().strip()
                    control = f.readline().strip()
                    player = self.player_manager.add_player(i, name, control)
                    
                    player.population = int(f.readline())
                    player.distribute_population()
                    player.money = int(f.readline())
                    player.navy = int(f.readline())
                    player.sea_army = int(f.readline())
                    player.sea_moved = int(f.readline())
                    player.tax_rate = float(f.readline())
                    player.trust = float(f.readline())
                    
                    # Read science levels
                    for j in range(1, 7):
                        player.science.set_level(j, float(f.readline()))
                    
                    # Skip diplomatic data for now
                    for _ in range(num_players * 2):
                        _ = f.readline()
                
                # Read map data
                map_data = ["owner", "original", "terrain", "fort", "church", 
                           "university", "mill", "army", "moved"]
                
                for data_type in map_data:
                    for i in range(15):
                        # Handle comma-separated values
                        row = list(map(int, f.readline().strip().replace(' ', '').split(',')))
                        for j in range(15):
                            self.game_map[data_type][i][j] = row[j]
                            
                            # Update player land count when processing owner data
                            if data_type == "owner" and row[j] != 0:
                                player = self.player_manager.get_player(row[j])
                                if player:
                                    player.land_count += 1
                            
            return True
            
        except Exception as e:
            print(f"Error loading scenario: {e}")
            return False
    
    def save_game(self, filename: str) -> bool:
        """Save the current game state"""
        try:
            with open(filename, 'w') as f:
                # Write basic game data
                f.write(f"{len(self.player_manager.players)}\n")
                f.write(f"{self.player_manager.current_player_id}\n")
                f.write(f"{self.turn}\n")
                
                # Write placeholder science money
                for _ in range(6):
                    f.write("0\n")
                
                # Write player data
                for player in self.player_manager.players.values():
                    f.write(f"{player.name}\n")
                    f.write(f"{player.control}\n")
                    f.write(f"{player.population}\n")
                    f.write(f"{player.money}\n")
                    f.write(f"{player.navy}\n")
                    f.write(f"{player.sea_army}\n")
                    f.write(f"{player.sea_moved}\n")
                    f.write(f"{player.tax_rate}\n")
                    f.write(f"{player.trust}\n")
                    
                    # Write science levels
                    for i in range(1, 7):
                        f.write(f"{player.science.get_level(i)}\n")
                    
                    # Write diplomatic data
                    for i in range(len(self.player_manager.players)):
                        f.write("2\n")  # Placeholder diplomatic relations
                    for i in range(len(self.player_manager.players)):
                        f.write("0\n")  # Placeholder diplomatic actions
                
                # Write map data
                for data_type in ["owner", "original", "terrain", "fort", "church",
                                "university", "mill", "army", "moved"]:
                    for row in self.game_map[data_type]:
                        f.write(", ".join(map(str, row)) + "\n")
                        
            return True
            
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def get_territory_info(self, x: int, y: int) -> Dict:
        """Get information about the selected territory"""
        info = {}
        
        # Get owner
        owner_id = self.game_map["owner"][y][x]
        if owner_id != 0:
            owner = self.player_manager.get_player(owner_id)
            info["Owner"] = owner.name if owner else "Unknown"
            
            # Get original owner
            original_id = self.game_map["original"][y][x]
            original = self.player_manager.get_player(original_id)
            info["Original Owner"] = original.name if original else "Unknown"
        
        # Get terrain info
        terrain_id = self.game_map["terrain"][y][x]
        terrain = self.terrain_manager.get_terrain(terrain_id)
        info["Terrain"] = terrain.name
        info["Food"] = f"{terrain.food_potential:.1f}"
        info["Resources"] = f"{terrain.production_potential:.1f}"
        info["Defense"] = f"{terrain.defense_bonus * 100:.0f}%"
        
        # Get building info
        info["Forts"] = self.game_map["fort"][y][x]
        info["Churches"] = self.game_map["church"][y][x]
        info["Universities"] = self.game_map["university"][y][x]
        info["Mills"] = self.game_map["mill"][y][x]
        info["Army"] = self.game_map["army"][y][x]
        
        return info
    
    def _display_help_file(self, filename: str):
        """Load and display help file content"""
        try:
            with open(filename, 'r') as f:
                content = f.read()
                # Split content into lines and store in interface state
                self.interface.state.help_content = content.splitlines()
                self.interface.state.help_scroll = 0
        except Exception as e:
            self.interface.state.message = f"Could not load help file: {e}"

    def handle_command(self, command: Optional[str]):
        """Handle game commands"""
        if not command:
            return
            
        current_player = self.player_manager.get_player(
            self.player_manager.current_player_id
        )
        if not current_player:
            return
            
        x = self.interface.state.selected_x
        y = self.interface.state.selected_y
        
        # Split command into parts
        parts = command.split()
        cmd = parts[0]
        
        if cmd == "spy":
            if len(parts) == 2:
                target_id = int(parts[1])
                target = self.player_manager.get_player(target_id)
                if target:
                    spy_cost = current_player.get_spy_cost(target)
                    if current_player.money >= spy_cost:
                        current_player.money -= spy_cost
                        current_player.science.spied_empires[target_id] = True
                        self.interface.state.message = f"Spy placed in {target.name}"
                    else:
                        self.interface.state.message = "Not enough gold to place spy"
        
        # Handle game screen commands
        elif cmd == "info":
            self.interface.current_player = current_player
            self.interface.state.active_screen = "info"
        elif cmd == "treasury":
            self.interface.current_player = current_player
            self.interface.state.active_screen = "treasury"
        elif cmd == "decrease_tax":
            if current_player.tax_rate >= 10:
                current_player.tax_rate = max(0, current_player.tax_rate - 10)
                self.interface.state.message = f"Tax rate decreased to {current_player.tax_rate:.1f}%"
                # Update treasury screen to show new projected income
                if self.interface.state.active_screen == "treasury":
                    self.interface.current_player = current_player
        elif cmd == "increase_tax":
            if current_player.tax_rate <= 90:
                current_player.tax_rate = min(100, current_player.tax_rate + 10)
                self.interface.state.message = f"Tax rate increased to {current_player.tax_rate:.1f}%"
                # Update treasury screen to show new projected income
                if self.interface.state.active_screen == "treasury":
                    self.interface.current_player = current_player
        elif cmd == "science":
            self.interface.current_player = current_player
            self.interface.state.active_screen = "science"
        elif cmd == "diplomacy":
            self.interface.current_player = current_player
            self.interface.all_players = self.player_manager.players
            self.interface.state.active_screen = "diplomacy"
        elif cmd == "help":
            self._display_help_file("how.hlp")
        # Handle other commands
        elif command == "end_turn" or command == "E":
            self._handle_end_turn()
        elif command == "save_game":
            save_num = self.interface.state.save_number
            filename = f"save{save_num}.scn"
            if self.save_game(filename):
                self.interface.state.message = f"Game saved as {filename}"
                self.interface.state.save_number += 1
        elif command == "quit":
            self.running = False
        elif command.startswith("build_"):
            self._handle_build_command(command[6:], current_player, x, y)
        elif command.startswith("sell_"):
            self._handle_sell_command(command[5:], current_player, x, y)
        elif command.startswith("move_"):
            self._handle_move_command(command[5:], current_player, x, y)
        elif command == "embark":
            self._handle_embark_command(current_player, x, y)
        elif command.startswith("spend_science_"):
            # Parse branch and amount from command (format: spend_science_1_1000)
            _, _, branch, amount = command.split("_")
            branch = int(branch)
            amount = int(amount)
            
            # Spend money on science
            progress = self.player_manager.spend_on_science(current_player, branch, amount)
            if progress > 0:
                branch_names = {
                    1: "Agriculture",
                    2: "Industry", 
                    3: "Trade",
                    4: "Sailing",
                    5: "Military",
                    6: "Medicine"
                }
                self.interface.state.message = f"Advanced {branch_names[branch]} by {progress:.2f} levels"
            else:
                self.interface.state.message = "Could not advance science"
                
        elif command.startswith("set_negative_"):
            target_id = int(command.split("_")[-1])
            target_player = self.player_manager.get_player(target_id)
            if target_player:
                # Set diplomatic relations to hostile (2)
                current_player.diplomatic_relations[target_id] = 2
                target_player.diplomatic_relations[current_player.id] = 2
                self.interface.state.message = f"Relations with {target_player.name} set to hostile"
        elif command.startswith("improve_relations_"):
            target_id = int(command.split("_")[-1])
            if self.player_manager.change_diplomatic_relation(current_player, target_id, 1):
                target_player = self.player_manager.get_player(target_id)
                if target_player:
                    # Also improve relations for target player
                    target_player.diplomatic_relations[current_player.id] = current_player.diplomatic_relations[target_id]
                    self.interface.state.message = f"Relations improved with {target_player.name}"
    
    def _handle_embark_command(self, player: Player, x: int, y: int):
        """Handle army embarking and naval invasions"""
        unit_size = [1, 2, 5, 10, 20, 50, 100][self.interface.state.code - 1]
        
        # Check if trying to invade enemy territory
        if self.game_map["owner"][y][x] != player.id and self.game_map["owner"][y][x] != 0:
            # Look for adjacent friendly territory with enough units and sea tiles
            friendly_territory_found = False
            friendly_x, friendly_y = None, None
            sea_tile_found = False
            
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < 15 and 0 <= new_y < 15:
                    # Check for friendly territory with enough units
                    if (self.game_map["owner"][new_y][new_x] == player.id and 
                        self.game_map["army"][new_y][new_x] >= unit_size):
                        friendly_territory_found = True
                        friendly_x, friendly_y = new_x, new_y
                    # Check for sea tile
                    elif self.game_map["terrain"][new_y][new_x] == 0:
                        sea_tile_found = True
            
            if friendly_territory_found and sea_tile_found:
                enemy_id = self.game_map["owner"][y][x]
                enemy = self.player_manager.get_player(enemy_id)
                if enemy:
                    # First embark the units from friendly territory to sea
                    if self.military_manager.embark_army(
                        unit_size, friendly_x, friendly_y, friendly_x, friendly_y,
                        player,
                        self.game_map["army"],
                        self.game_map["terrain"]
                    ):
                        # Then initiate naval battle
                        battle_result = self.military_manager.calculate_battle(
                            player, enemy,
                            unit_size, enemy.navy,
                            0,  # terrain type (sea)
                            0,  # fort level
                            True  # naval battle
                        )
                        
                        # Apply battle results
                        if battle_result.territory_captured:
                            # Update territory ownership
                            self.game_map["owner"][y][x] = player.id
                            # Transfer any remaining army units
                            remaining_units = unit_size - battle_result.attacker_losses
                            if remaining_units > 0:
                                self.game_map["army"][y][x] = remaining_units
                            # Update message
                            self.interface.state.message = f"Victory! Territory captured from {enemy.name}"
                        else:
                            self.interface.state.message = battle_result.message
                        return
            else:
                if not friendly_territory_found:
                    self.interface.state.message = "No adjacent friendly territory with enough units"
                elif not sea_tile_found:
                    self.interface.state.message = "No adjacent sea tiles for naval invasion"
                return
        
        # Handle normal embarking from owned territory
        if self.game_map["owner"][y][x] != player.id:
            self.interface.state.message = "You don't own this territory"
            return
            
        # Check if enough units available
        if self.game_map["army"][y][x] < unit_size:
            self.interface.state.message = f"Not enough units (need {unit_size})"
            return
        
        # Look for adjacent sea tiles and check for enemy territories
        enemy_territory_found = False
        enemy_id = None
        sea_tile_found = False
        embark_x, embark_y = None, None
        
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < 15 and 0 <= new_y < 15:
                # Check for enemy territory
                owner_id = self.game_map["owner"][new_y][new_x]
                if owner_id != 0 and owner_id != player.id:
                    enemy_territory_found = True
                    enemy_id = owner_id
                # Check for sea tile
                if self.game_map["terrain"][new_y][new_x] == 0:
                    sea_tile_found = True
                    embark_x, embark_y = new_x, new_y
        
        # If there's enemy territory adjacent, initiate battle
        if enemy_territory_found and sea_tile_found:
            enemy = self.player_manager.get_player(enemy_id)
            if enemy:
                # First embark the units
                if self.military_manager.embark_army(
                    unit_size, x, y, embark_x, embark_y,
                    player,
                    self.game_map["army"],
                    self.game_map["terrain"]
                ):
                    # Then initiate naval battle
                    battle_result = self.military_manager.calculate_battle(
                        player, enemy,
                        unit_size, enemy.navy,
                        0,  # terrain type (sea)
                        0,  # fort level
                        True  # naval battle
                    )
                    
                    # Apply battle results
                    if battle_result.territory_captured:
                        # Update territory ownership
                        self.game_map["owner"][y][x] = player.id
                        # Transfer any remaining army units
                        remaining_units = unit_size - battle_result.attacker_losses
                        if remaining_units > 0:
                            self.game_map["army"][y][x] = remaining_units
                        # Update message
                        self.interface.state.message = f"Victory! Territory captured from {enemy.name}"
                    else:
                        self.interface.state.message = battle_result.message
                    return
        
        # If no enemy territory or just embarking to sea
        if sea_tile_found:
            if self.military_manager.embark_army(
                unit_size, x, y, embark_x, embark_y,
                player,
                self.game_map["army"],
                self.game_map["terrain"]
            ):
                self.interface.state.message = f"Embarked {unit_size} units"
                return
        
        self.interface.state.message = "No adjacent sea tiles to embark to"
    
    def _handle_end_turn(self):
        """Handle end of turn processing"""
        current_player = self.player_manager.get_player(
            self.player_manager.current_player_id
        )
        
        # Update current player state
        self.player_manager.calculate_morale(current_player)
        self.player_manager.update_science(current_player)
        
        # Calculate total food potential from owned territories
        total_food_potential = 0
        territory_count = 0
        for y in range(15):
            for x in range(15):
                if self.game_map["owner"][y][x] == current_player.id:
                    terrain_id = self.game_map["terrain"][y][x]
                    total_food_potential += self.terrain_manager.get_food_potential(terrain_id)
                    territory_count += 1
        
        # Calculate average food potential per territory
        avg_food_potential = total_food_potential / max(territory_count, 1)
        
        # Calculate and apply population growth
        growth = self.player_manager.calculate_population_growth(current_player, avg_food_potential)
        current_player.population += growth
        
        # Distribute new population into working groups
        if growth > 0:
            # Calculate ratios based on terrain types in owned territories
            land_tiles = 0
            sea_tiles = 0
            total_production = 0
            trade_routes = 0
            
            for y in range(15):
                for x in range(15):
                    if self.game_map["owner"][y][x] == current_player.id:
                        terrain_id = self.game_map["terrain"][y][x]
                        terrain = self.terrain_manager.get_terrain(terrain_id)
                        
                        if terrain_id == 0:  # Sea terrain
                            sea_tiles += 1
                        else:
                            land_tiles += 1
                            
                        if terrain.production_potential > 0:
                            total_production += 1
                        
                        # Count adjacent owned territories as trade routes
                        adjacent_owned = 0
                        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                            nx, ny = x + dx, y + dy
                            if (0 <= nx < 15 and 0 <= ny < 15 and 
                                self.game_map["owner"][ny][nx] == current_player.id):
                                adjacent_owned += 1
                        if adjacent_owned > 0:
                            trade_routes += 1
            
            # Distribute new population based on territory composition
            total_tiles = max(1, land_tiles + sea_tiles)
            
            peasant_ratio = land_tiles / total_tiles * 0.4  # 40% of land-based population
            fisher_ratio = sea_tiles / total_tiles * 0.4    # 40% of sea-based population
            worker_ratio = (total_production / total_tiles) * 0.3  # 30% based on production tiles
            merchant_ratio = (trade_routes / total_tiles) * 0.2    # 20% based on trade routes
            
            # Ensure ratios sum to 1
            total_ratio = peasant_ratio + fisher_ratio + worker_ratio + merchant_ratio
            if total_ratio > 0:
                peasant_ratio /= total_ratio
                fisher_ratio /= total_ratio
                worker_ratio /= total_ratio
                merchant_ratio /= total_ratio
            
            # Distribute new population
            new_peasants = int(growth * peasant_ratio)
            new_fishers = int(growth * fisher_ratio)
            new_workers = int(growth * worker_ratio)
            new_merchants = int(growth * merchant_ratio)
            
            # Add remaining population to unemployed
            remaining = growth - (new_peasants + new_fishers + new_workers + new_merchants)
            
            current_player.peasants += new_peasants
            current_player.fishers += new_fishers
            current_player.workers += new_workers
            current_player.merchants += new_merchants
            current_player.unemployed += remaining
        
        # Update player's money with income
        income = self.player_manager.calculate_income(current_player)
        current_player.money += income
        
        # Recalculate land counts for all players
        for player in self.player_manager.players.values():
            player.land_count = 0
            for y in range(15):
                for x in range(15):
                    if self.game_map["owner"][y][x] == player.id:
                        player.land_count += 1
        
        # Get next player
        next_player = self.player_manager.next_player()
        
        if not next_player:
            # No valid players left
            self.interface.state.message = "Game Over - No valid players remaining"
            self.running = False
            return
            
        # Reset state for next player's turn
        self.player_manager.reset_diplomatic_changes(next_player)
        
        # Reset moved units for all territories
        for y in range(15):
            for x in range(15):
                self.game_map["moved"][y][x] = 0
                
        # Process AI turns immediately
        while next_player and next_player.control != "human":
            # Let AI make decisions
            self.ai.make_decisions(next_player, self.game_map)
            
            # Update AI player state
            self.player_manager.calculate_morale(next_player)
            self.player_manager.update_science(next_player)
            
            # Update AI player's money with income
            income = self.player_manager.calculate_income(next_player)
            next_player.money += income
            
            # Reset moved units for next AI player
            for y in range(15):
                for x in range(15):
                    self.game_map["moved"][y][x] = 0
            
            # Get next player
            next_player = self.player_manager.next_player()
            
            # Check if game is over
            if not next_player:
                self.interface.state.message = "Game Over - No valid players remaining"
                self.running = False
                return
        
        if next_player.id == 1:  # Back to first player
            self.turn += 1
            
        # Update interface references and game state
        self.interface.current_player = next_player
        self.interface.all_players = self.player_manager.players  # Ensure player list is updated
        self.interface.state.message = f"{next_player.name}'s turn"
        self.player_manager.current_player_id = next_player.id  # Ensure current player ID is updated
    
    def _handle_build_command(self, building: str, player: Player, x: int, y: int):
        """Handle building construction"""
        if self.game_map["owner"][y][x] != player.id:
            self.interface.state.message = "You don't own this territory"
            return
            
        terrain_type = self.terrain_manager.get_terrain(self.game_map["terrain"][y][x])
        terrain_name = terrain_type.name.lower()
        
        # Initialize cost
        cost = 0
        
        # Check terrain restrictions
        if building == "fort":
            if terrain_name == "sea":
                self.interface.state.message = "Cannot build fort on sea"
                return
            elif terrain_name == "swamp":
                self.interface.state.message = "Cannot build fort in swamp"
                return
            cost = self.military_manager.FORT_COST
            if player.money < cost:
                self.interface.state.message = f"Not enough gold (need {cost})"
                return
            self.game_map["fort"][y][x] += 1
            player.money -= cost
            self.interface.state.message = f"Built fort for {cost} gold"
                
        elif building == "church":
            if terrain_name == "sea":
                self.interface.state.message = "Cannot build church on sea"
                return
            elif terrain_name == "mountain":
                self.interface.state.message = "Cannot build church on mountain"
                return
            cost = self.military_manager.CHURCH_COST
            if player.money < cost:
                self.interface.state.message = f"Not enough gold (need {cost})"
                return
            self.game_map["church"][y][x] += 1
            player.money -= cost
            self.interface.state.message = f"Built church for {cost} gold"
                
        elif building == "university":
            if terrain_name == "sea":
                self.interface.state.message = "Cannot build university on sea"
                return
            elif terrain_name in ["mountain", "swamp", "desert"]:
                self.interface.state.message = f"Cannot build university on {terrain_name}"
                return
            cost = self.military_manager.UNIVERSITY_COST
            if player.money < cost:
                self.interface.state.message = f"Not enough gold (need {cost})"
                return
            self.game_map["university"][y][x] += 1
            player.money -= cost
            self.interface.state.message = f"Built university for {cost} gold"
                
        elif building == "mill":
            if terrain_name == "sea":
                self.interface.state.message = "Cannot build mill on sea"
                return
            elif terrain_name in ["desert", "tundra"]:
                self.interface.state.message = f"Cannot build mill on {terrain_name}"
                return
            cost = self.military_manager.MILL_COST
            if player.money < cost:
                self.interface.state.message = f"Not enough gold (need {cost})"
                return
            self.game_map["mill"][y][x] += 1
            player.money -= cost
            self.interface.state.message = f"Built mill for {cost} gold"
                
        elif building == "army":
            if terrain_name == "sea":
                self.interface.state.message = "Cannot recruit army on sea"
                return
                
            unit_size = [1, 2, 5, 10, 20, 50, 100][self.interface.state.code - 1]
            cost = self.military_manager.ARMY_COST * unit_size
            
            if player.money < cost:
                self.interface.state.message = f"Not enough gold (need {cost})"
                return
                
            # Calculate total available population
            total_available = (player.unemployed + player.peasants + 
                            player.workers + player.merchants)
            
            if total_available < unit_size:
                self.interface.state.message = f"Not enough population (need {unit_size}, have {total_available})"
                return
            
            # Deduct population in priority order
            remaining = unit_size
            
            # First use unemployed
            if remaining > 0 and player.unemployed > 0:
                used = min(remaining, player.unemployed)
                player.unemployed -= used
                remaining -= used
            
            # Then use peasants
            if remaining > 0 and player.peasants > 0:
                used = min(remaining, player.peasants)
                player.peasants -= used
                remaining -= used
            
            # Then use workers
            if remaining > 0 and player.workers > 0:
                used = min(remaining, player.workers)
                player.workers -= used
                remaining -= used
            
            # Finally use merchants
            if remaining > 0 and player.merchants > 0:
                used = min(remaining, player.merchants)
                player.merchants -= used
                remaining -= used
            
            self.game_map["army"][y][x] += unit_size
            player.money -= cost
            self.interface.state.message = f"Recruited army of {unit_size} for {cost} gold"
            
        elif building == "navy":
            # Check if we're trying to build on a sea tile
            if terrain_name != "sea":
                self.interface.state.message = "Must build navy on sea tile"
                return
                
            # Check if there's adjacent owned land
            has_adjacent_land = False
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                new_x, new_y = x + dx, y + dy
                if (0 <= new_x < 15 and 0 <= new_y < 15 and 
                    self.game_map["owner"][new_y][new_x] == player.id and
                    self.game_map["terrain"][new_y][new_x] != 0):  # Not sea
                    has_adjacent_land = True
                    break
                    
            if not has_adjacent_land:
                self.interface.state.message = "Must build navy adjacent to owned land"
                return
                
            unit_size = [1, 2, 5, 10, 20, 50, 100][self.interface.state.code - 1]
            cost = self.military_manager.NAVY_COST * unit_size
            
            if player.money < cost:
                self.interface.state.message = f"Not enough gold (need {cost})"
                return
                
            player.navy += unit_size
            player.money -= cost
            self.interface.state.message = f"Built {unit_size} ships for {cost} gold"
            
        else:
            self.interface.state.message = f"Unknown building type: {building}"
    
    def _handle_sell_command(self, building: str, player: Player, x: int, y: int):
        """Handle selling buildings and units"""
        if self.game_map["owner"][y][x] != player.id:
            self.interface.state.message = "You don't own this territory"
            return
            
        refund = 0
        if building == "fort" and self.game_map["fort"][y][x] > 0:
            refund = int(self.military_manager.FORT_COST * self.military_manager.FORT_SELL)
            self.game_map["fort"][y][x] -= 1
        elif building == "church" and self.game_map["church"][y][x] > 0:
            refund = int(self.military_manager.CHURCH_COST * self.military_manager.CHURCH_SELL)
            self.game_map["church"][y][x] -= 1
        elif building == "university" and self.game_map["university"][y][x] > 0:
            refund = int(self.military_manager.UNIVERSITY_COST * self.military_manager.UNIVERSITY_SELL)
            self.game_map["university"][y][x] -= 1
        elif building == "mill" and self.game_map["mill"][y][x] > 0:
            refund = int(self.military_manager.MILL_COST * self.military_manager.MILL_SELL)
            self.game_map["mill"][y][x] -= 1
        elif building == "army" and self.game_map["army"][y][x] > 0:
            unit_size = [1, 2, 5, 10, 20, 50, 100][self.interface.state.code - 1]
            if self.game_map["army"][y][x] >= unit_size:
                refund = int(self.military_manager.ARMY_COST * self.military_manager.ARMY_SELL * unit_size)
                self.game_map["army"][y][x] -= unit_size
            else:
                self.interface.state.message = f"Not enough units (need {unit_size})"
                return
        elif building == "navy" and player.navy > 0:
            unit_size = [1, 2, 5, 10, 20, 50, 100][self.interface.state.code - 1]
            if player.navy >= unit_size:
                refund = int(self.military_manager.NAVY_COST * self.military_manager.NAVY_SELL * unit_size)
                player.navy -= unit_size
            else:
                self.interface.state.message = f"Not enough naval units (need {unit_size})"
                return
        
        if refund > 0:
            player.money += refund
            self.interface.state.message = f"Sold {building} for {refund} gold"
        else:
            self.interface.state.message = f"Nothing to sell"

    def _handle_move_command(self, direction: str, player: Player, x: int, y: int):
        """Handle army movement"""
        if self.game_map["owner"][y][x] != player.id:
            return
            
        unit_size = [1, 2, 5, 10, 20, 50, 100][self.interface.state.code - 1]
        
        new_x, new_y = x, y
        if direction == "up": new_y -= 1
        elif direction == "down": new_y += 1
        elif direction == "left": new_x -= 1
        elif direction == "right": new_x += 1
        
        if 0 <= new_x < 15 and 0 <= new_y < 15:
            if self.military_manager.move_army(
                unit_size, x, y, new_x, new_y,
                player,
                self.game_map["army"],
                self.game_map["moved"],
                self.game_map["terrain"]
            ):
                self.interface.state.message = f"Moved {unit_size} units"
            else:
                self.interface.state.message = "Invalid move"
    
    def run(self):
        """Main game loop"""
        # Set initial interface references
        current_player = self.player_manager.get_player(self.player_manager.current_player_id)
        if current_player:
            self.interface.current_player = current_player
            self.interface.all_players = self.player_manager.players
            
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    command = self.interface.handle_input(event)
                    self.handle_command(command)
            
            # Clear screen
            self.interface.clear()
            
            # Draw game state if no screen is active
            if not self.interface.state.help_content and not self.interface.state.active_screen:
                self.interface.draw_title()
                self.interface.draw_map(
                    self.game_map["terrain"],
                    self.game_map["owner"],
                    [0, 2, 4, 1, 14, 8, 15, 11, 13, 12],  # Owner colors
                    [t.color for t in self.terrain_manager.terrain_types]
                )
                
                current_player = self.player_manager.get_player(
                    self.player_manager.current_player_id
                )
                if current_player:
                    self.interface.draw_info_panel(
                        current_player.name,
                        self.turn,
                        current_player.money,
                        self.get_territory_info(
                            self.interface.state.selected_x,
                            self.interface.state.selected_y
                        )
                    )
                
                self.interface.draw_menu()
                self.interface.draw_message()
                self.interface.draw_unit_size()
            
            # Update display
            self.interface.update()
        
        pygame.quit()
        sys.exit()

    def set_player_control(self, player_id: int, control: str):
        """Set a player's control type (human/AI)"""
        player = self.player_manager.get_player(player_id)
        if player:
            player.control = control
            # Set as current player if human
            if control == "human":
                self.player_manager.current_player_id = player_id

if __name__ == "__main__":
    game = Game()
    
    # Show motto screen until key press
    while game.interface.show_motto_screen:
        if game.interface.show_motto():
            break
            
    # Show title screen until key press
    while game.interface.show_title_screen:
        if game.interface.show_title():
            break
    
    # Show country selection until confirmed
    selected_country = None
    while game.interface.show_country_select and selected_country is None:
        selected_country = game.interface.show_country_selection()
        if selected_country == -1:  # Quit
            pygame.quit()
            sys.exit()
        pygame.event.pump()  # Process events to keep window responsive
    
    # Load scenario and set player control
    if game.load_scenario("default.scn"):
        # Set all players to AI control except selected country
        for i in range(1, 10):  # Max 9 players
            control = "human" if i == selected_country else "default.ai"
            game.set_player_control(i, control)
        game.run()
