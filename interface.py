import pygame
import pygame.freetype
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass

@dataclass
class UIState:
    selected_x: int = 8
    selected_y: int = 8
    message: str = "Welcome, Majesty."
    code: int = 1  # Military unit size code
    save_number: int = 1
    help_content: List[str] = None  # Content of help file
    help_scroll: int = 0  # Current scroll position in help content
    active_screen: str = None  # Current active game screen

class Interface:
    def __init__(self, screen_width: int = 900, screen_height: int = 600):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Hegemony 3.0")
        
        # References to game state
        self.current_player = None
        self.all_players = None
        
        # Load title screen image and motto
        try:
            self.title_image = pygame.image.load("HGM.BMP")
            self.title_image = pygame.transform.scale(self.title_image, (screen_width, screen_height))
            
            # Load motto
            with open("motto.txt", 'r') as f:
                self.motto = f.read().strip()
            
            self.show_motto_screen = True
            self.show_title_screen = False
        except (pygame.error, FileNotFoundError) as e:
            print(f"Could not load title assets: {e}")
            self.show_motto_screen = False
            self.show_title_screen = False
            self.motto = ""
            
        # Country selection state
        self.show_country_select = False
        self.selected_country = 0  # Index of selected country
        self.countries = [
            "England", "Spain", "France", "Sweden", "Germany",
            "Italy", "Hungary", "Poland", "Balcan"
        ]
        
        # Initialize fonts
        pygame.freetype.init()
        self.font = pygame.freetype.SysFont("Arial", 14)
        self.title_font = pygame.freetype.SysFont("Arial", 18, bold=True)
        
        # Colors (matching QBasic colors)
        self.colors = {
            0: (0, 0, 0),        # Black
            1: (0, 0, 170),      # Blue
            2: (0, 170, 0),      # Green
            3: (0, 170, 170),    # Cyan
            4: (170, 0, 0),      # Red
            5: (170, 0, 170),    # Magenta
            6: (170, 85, 0),     # Brown
            7: (170, 170, 170),  # Light Gray
            8: (85, 85, 85),     # Dark Gray
            9: (85, 85, 255),    # Light Blue
            10: (85, 255, 85),   # Light Green
            11: (85, 255, 255),  # Light Cyan
            12: (255, 85, 85),   # Light Red
            13: (255, 85, 255),  # Light Magenta
            14: (255, 255, 85),  # Yellow
            15: (255, 255, 255), # White
        }
        
        self.state = UIState()
        
        # Menu definitions
        self.main_menu = [
            ("Empires", [
                ("Information", "i"),
                ("Treasury", "t"),
                ("Science", "s"),
                ("Diplomacy", "d"),
            ]),
            ("Territories", [
                ("Examine", "1-9"),
                ("Move army", "Shift+arrows"),
                ("Embark army", "b"),
                ("Build", [
                    ("Fort", "f"),
                    ("Church", "c"),
                    ("University", "u"),
                    ("Mills, Mines, Mints", "m"),
                    ("Army", "a"),
                    ("Navy", "n"),
                ]),
                ("Sell/Destroy", [
                    ("Fort", "F"),
                    ("Church", "C"),
                    ("University", "U"),
                    ("Mills, etc.", "M"),
                    ("Army", "A"),
                    ("Navy", "N"),
                ]),
            ]),
            ("Other", [
                ("End turn", "E"),
                ("Save game", "g"),
                ("Help", "h"),
                ("Quit", "Q"),
            ]),
        ]
    
    def draw_title(self):
        """Draw the game title and copyright"""
        self.title_font.render_to(
            self.screen,
            (10, 10),
            "HEGEMONY 3.0",
            self.colors[4]  # Red
        )
        self.font.render_to(
            self.screen,
            (400, 10),
            "Copyright: Akos Ivanyi (21.07.2003)",
            self.colors[7]  # Light Gray
        )
        pygame.draw.line(
            self.screen,
            self.colors[7],
            (0, 35),
            (self.screen_width, 35)
        )
    
    def draw_map(
        self,
        terrain_map: List[List[int]],
        owner_map: List[List[int]],
        owner_colors: List[int],
        terrain_colors: List[int],
        cell_size: int = 20,
        offset_x: int = 130,
        offset_y: int = 80
    ):
        """Draw the game map"""
        for y in range(len(terrain_map)):
            for x in range(len(terrain_map[0])):
                # Draw cell border
                rect = pygame.Rect(
                    offset_x + x * cell_size,
                    offset_y + y * cell_size,
                    cell_size,
                    cell_size
                )
                pygame.draw.rect(self.screen, self.colors[0], rect, 1)
                
                # Fill with terrain color
                inner_rect = rect.inflate(-2, -2)
                terrain_color = self.colors[terrain_colors[terrain_map[y][x]]]
                pygame.draw.rect(self.screen, terrain_color, inner_rect)
                
                # Draw owner indicator
                if owner_map[y][x] != 0:
                    owner_rect = pygame.Rect(
                        offset_x + x * cell_size + cell_size - 5,
                        offset_y + y * cell_size + cell_size - 5,
                        5, 5
                    )
                    owner_color = self.colors[owner_colors[owner_map[y][x]]]
                    pygame.draw.rect(self.screen, owner_color, owner_rect)
                
                # Highlight selected cell
                if x == self.state.selected_x and y == self.state.selected_y:
                    pygame.draw.rect(self.screen, self.colors[15], rect, 1)
    
    def draw_info_panel(
        self,
        player_name: str,
        turn: int,
        money: int,
        territory_info: Dict
    ):
        """Draw the information panel"""
        x = 455
        y = 80
        
        # Draw panel background
        pygame.draw.rect(
            self.screen,
            self.colors[0],
            (x, y, 185, 260)
        )
        
        # Draw player info
        self.font.render_to(
            self.screen,
            (x + 5, y + 5),
            f"{player_name}'s turn: {turn}",
            self.colors[7]
        )
        
        # Draw territory info
        y += 30
        self.font.render_to(
            self.screen,
            (x + 5, y),
            f"Location: {self.state.selected_x}, {self.state.selected_y}",
            self.colors[7]
        )
        
        for key, value in territory_info.items():
            y += 20
            self.font.render_to(
                self.screen,
                (x + 5, y),
                f"{key}: {value}",
                self.colors[7]
            )
        
        # Draw money and naval info
        self.font.render_to(
            self.screen,
            (x + 5, y + 40),
            f"Gold: {money}",
            self.colors[14]  # Yellow
        )
        
        # Draw naval information
        if self.current_player:
            y += 20
            self.font.render_to(
                self.screen,
                (x + 5, y + 40),
                f"Embarked Units: {self.current_player.sea_army + self.current_player.sea_moved}/{self.current_player.navy}",
                self.colors[7]  # Light Gray
            )
    
    def draw_menu(self):
        """Draw the main menu"""
        x = 10
        y = 80
        
        for section_name, items in self.main_menu:
            self.font.render_to(
                self.screen,
                (x, y),
                section_name,
                self.colors[7]
            )
            y += 20
            
            for item_name, key in items:
                if isinstance(key, list):
                    # Submenu
                    for sub_name, sub_key in key:
                        self.font.render_to(
                            self.screen,
                            (x + 20, y),
                            f"{sub_name} ({sub_key})",
                            self.colors[7]
                        )
                        y += 15
                else:
                    self.font.render_to(
                        self.screen,
                        (x + 10, y),
                        f"{item_name} ({key})",
                        self.colors[7]
                    )
                    y += 15
            y += 10
    
    def draw_message(self):
        """Draw the current message"""
        self.font.render_to(
            self.screen,
            (10, self.screen_height - 30),
            self.state.message,
            self.colors[7]
        )
    
    def draw_unit_size(self):
        """Draw the current military unit size"""
        sizes = [1, 2, 5, 10, 20, 50, 100]
        self.font.render_to(
            self.screen,
            (10, self.screen_height - 50),
            f"Unit size: {sizes[self.state.code - 1]}",
            self.colors[7]
        )
    
    def handle_input(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input events and return command if any"""
        if event.type == pygame.KEYDOWN:
            # Handle ESC key for all screens
            if event.key == pygame.K_ESCAPE:
                if self.state.help_content:
                    self.state.help_content = None
                    self.state.help_scroll = 0
                    return None
                elif self.state.active_screen:
                    self.state.active_screen = None
                    return None
            
            # Handle treasury screen controls
            if self.state.active_screen == "treasury":
                if event.key == pygame.K_LEFT:
                    return "decrease_tax"
                elif event.key == pygame.K_RIGHT:
                    return "increase_tax"
                return None
            
            # Handle science screen controls
            elif self.state.active_screen == "science":
                # Science spending (1-6)
                if event.unicode in "123456":
                    return f"science {event.unicode}"
                # Spy placement (player numbers)
                elif (event.unicode.isdigit() and 
                      int(event.unicode) in self.all_players and 
                      int(event.unicode) != self.current_player.id):
                    target_id = int(event.unicode)
                    target = self.all_players[target_id]
                    
                    # Check if already spying
                    if not self.current_player.science.spied_empires.get(target_id, False):
                        spy_cost = self.current_player.get_spy_cost(target)
                        if self.current_player.money >= spy_cost:
                            return f"spy {target_id}"
                        else:
                            self.state.message = "Not enough gold to place spy"
                    else:
                        self.state.message = "Already spying on this empire"
                return None
            
            # Handle diplomacy screen controls
            elif self.state.active_screen == "diplomacy":
                # Check for number keys 1-9 for diplomatic actions
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, 
                               pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]:
                    try:
                        target_id = int(event.unicode)
                        if target_id != self.current_player.id:  # Can't interact with yourself
                            return f"set_negative_{target_id}"
                    except ValueError:
                        # If the unicode character isn't a valid number, ignore it
                        pass
                # Check for direct key presses for improving relations
                elif event.unicode in ['o', 'p', '[', ']', 'l', "'", ',', '.', '/']:
                    # Map each key to a specific nation
                    key_to_nation = {
                        'o': 1,
                        'p': 2,
                        '[': 3,
                        ']': 4,
                        'l': 5,
                            "'": 6,
                            ',': 7,
                            '.': 8,
                            '/': 9
                        }
                    target_id = key_to_nation.get(event.unicode)
                    if target_id and target_id != self.current_player.id:  # Can't interact with yourself
                        # Check if relations have already been changed this turn
                        if not self.current_player.relations_changed.get(target_id, False):
                            return f"improve_relations_{target_id}"
                return None
            
            # If a game screen is active, only handle specific keys
            if self.state.active_screen:
                return None
            
            # Movement
            mods = pygame.key.get_mods()
            if event.key == pygame.K_UP:
                if mods & pygame.KMOD_SHIFT:
                    return "move_up"
                elif self.state.selected_y > 0:
                    self.state.selected_y -= 1
            elif event.key == pygame.K_DOWN:
                if mods & pygame.KMOD_SHIFT:
                    return "move_down"
                elif self.state.selected_y < 14:
                    self.state.selected_y += 1
            elif event.key == pygame.K_LEFT:
                if mods & pygame.KMOD_SHIFT:
                    return "move_left"
                elif self.state.selected_x > 0:
                    self.state.selected_x -= 1
            elif event.key == pygame.K_RIGHT:
                if mods & pygame.KMOD_SHIFT:
                    return "move_right"
                elif self.state.selected_x < 14:
                    self.state.selected_x += 1
            
            # Unit size
            elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):  # Handle =, +, and numpad +
                if self.state.code < 7:
                    self.state.code += 1
                    sizes = [1, 2, 5, 10, 20, 50, 100]
                    self.state.message = f"Unit size increased to {sizes[self.state.code - 1]}"
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):  # Handle -, and numpad -
                if self.state.code > 1:
                    self.state.code -= 1
                    sizes = [1, 2, 5, 10, 20, 50, 100]
                    self.state.message = f"Unit size decreased to {sizes[self.state.code - 1]}"
            
            # Help screen controls
            if self.state.help_content:
                if event.key == pygame.K_UP:
                    if self.state.help_scroll > 0:
                        self.state.help_scroll -= 1
                    return None
                elif event.key == pygame.K_DOWN:
                    visible_lines = (self.screen_height - 70) // 20
                    if self.state.help_scroll < len(self.state.help_content) - visible_lines:
                        self.state.help_scroll += 1
                    return None
                return None  # Ignore other keys when help screen is shown
            
            # Menu commands
            elif event.key == pygame.K_i:
                return "info"
            elif event.key == pygame.K_t:
                return "treasury"
            elif event.key == pygame.K_s:
                return "science"
            elif event.key == pygame.K_d:
                return "diplomacy"
            # Handle sell commands first (capital letters)
            elif mods & pygame.KMOD_SHIFT:
                if event.key == pygame.K_m:  # Capital M
                    return "sell_mill"
                elif event.key == pygame.K_a:  # Capital A
                    return "sell_army"
                elif event.key == pygame.K_n:  # Capital N
                    return "sell_navy"
                elif event.key == pygame.K_f:  # Capital F
                    return "sell_fort"
                elif event.key == pygame.K_c:  # Capital C
                    return "sell_church"
                elif event.key == pygame.K_u:  # Capital U
                    return "sell_university"
            # Then handle build commands (lowercase letters)
            elif event.key == pygame.K_f:
                return "build_fort"
            elif event.key == pygame.K_c:
                return "build_church"
            elif event.key == pygame.K_u:
                return "build_university"
            elif event.key == pygame.K_m:
                return "build_mill"
            elif event.key == pygame.K_a:
                return "build_army"
            elif event.key == pygame.K_n:
                return "build_navy"
            elif event.key == pygame.K_b:
                return "embark"
            elif event.key == pygame.K_e:
                return "end_turn"
            elif event.key == pygame.K_g:
                return "save_game"
            elif event.key == pygame.K_h:
                return "help"
            elif event.key == pygame.K_q:
                return "quit"
        
        return None
    
    def update(self):
        """Update the display"""
        pygame.display.flip()
    
    def show_motto(self) -> bool:
        """Show motto screen and return True if a key was pressed"""
        self.screen.fill(self.colors[0])  # Black background
        
        # Draw motto with word wrapping
        words = self.motto.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            text = ' '.join(current_line)
            if self.font.get_rect(text)[2] > self.screen_width - 100:  # Leave 50px margin on each side
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        total_height = len(lines) * 20  # Calculate total height of text
        y = (self.screen_height - total_height) // 2  # Center vertically
        
        for line in lines:
            text_rect = self.font.get_rect(line)
            x = (self.screen_width - text_rect[2]) // 2  # Center horizontally
            self.font.render_to(
                self.screen,
                (x, y),
                line,
                self.colors[15]  # White
            )
            y += 20  # Line spacing
        
        self.font.render_to(
            self.screen,
            (self.screen_width // 2 - 100, self.screen_height - 50),
            "Press any key to continue",
            self.colors[15]  # White
        )
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYDOWN:
                self.show_motto_screen = False
                self.show_title_screen = True
                return True
        return False
        
    def show_title(self) -> bool:
        """Show title screen and return True if a key was pressed"""
        self.screen.blit(self.title_image, (0, 0))
        
        self.font.render_to(
            self.screen,
            (self.screen_width // 2 - 100, self.screen_height - 50),
            "Press any key to start",
            self.colors[15]  # White
        )
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYDOWN:
                self.show_title_screen = False
                self.show_country_select = True
                return True
        return False
        
    def show_country_selection(self) -> Optional[int]:
        """Show country selection screen and return selected country index if confirmed"""
        self.screen.fill(self.colors[0])  # Black background
        
        # Draw title
        self.title_font.render_to(
            self.screen,
            (10, 10),
            "Select Your Country",
            self.colors[15]  # White
        )
        
        # Draw country list
        y = 50
        for i, country in enumerate(self.countries):
            color = self.colors[14] if i == self.selected_country else self.colors[7]  # Yellow if selected
            self.font.render_to(
                self.screen,
                (50, y),
                country,
                color
            )
            y += 30
            
        # Draw instructions
        self.font.render_to(
            self.screen,
            (10, self.screen_height - 50),
            "Use Up/Down arrows to select, Enter to confirm",
            self.colors[14]  # Yellow
        )
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return -1
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_country = (self.selected_country - 1) % len(self.countries)
                elif event.key == pygame.K_DOWN:
                    self.selected_country = (self.selected_country + 1) % len(self.countries)
                elif event.key == pygame.K_RETURN:
                    self.show_country_select = False
                    return self.selected_country + 1  # Return 1-based index for player ID
        return None

    def draw_help_screen(self):
        """Draw help content in full screen"""
        if not self.state.help_content:
            return
            
        self.screen.fill(self.colors[0])  # Clear screen with black background
        
        # Draw title
        title = self.state.help_content[0]
        self.title_font.render_to(
            self.screen,
            (10, 10),
            title,
            self.colors[15]  # White
        )
        
        # Draw content
        y = 50
        line_height = 20
        visible_lines = (self.screen_height - 70) // line_height  # Leave space for title and footer
        
        for i in range(self.state.help_scroll, min(len(self.state.help_content), self.state.help_scroll + visible_lines)):
            line = self.state.help_content[i]
            # Skip separator lines (lines with only = characters)
            if not all(c == '=' for c in line.strip()):
                self.font.render_to(
                    self.screen,
                    (10, y),
                    line,
                    self.colors[7]  # Light Gray
                )
                y += line_height
        
        # Draw scroll indicator
        if len(self.state.help_content) > visible_lines:
            self.font.render_to(
                self.screen,
                (10, self.screen_height - 20),
                "Use Up/Down arrows to scroll, ESC to return",
                self.colors[14]  # Yellow
            )

    def draw_information_screen(self, player):
        """Draw empire information screen"""
        self.screen.fill(self.colors[0])
        
        self.title_font.render_to(
            self.screen,
            (10, 10),
            "Empire Information",
            self.colors[15]
        )
        
        # Basic info
        y = 50
        self.font.render_to(self.screen, (10, y), f"Empire: {player.name}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (10, y), f"Trust Level: {player.trust:.1f}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (10, y), f"Tax Rate: {player.tax_rate:.1f}%", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (10, y), f"Morale: {player.morale:.2f}", self.colors[7])
        
        # Population breakdown
        y += 30
        self.title_font.render_to(self.screen, (10, y), "Population", self.colors[15])
        y += 25
        self.font.render_to(self.screen, (20, y), f"Total: {player.population}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (20, y), f"Peasants: {player.peasants}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (20, y), f"Fishers: {player.fishers}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (20, y), f"Workers: {player.workers}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (20, y), f"Merchants: {player.merchants}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (20, y), f"Unemployed: {player.unemployed}", self.colors[7])
        
        # Income breakdown
        x = 300
        y = 50
        self.title_font.render_to(self.screen, (x, y), "Income", self.colors[15])
        y += 25
        
        # Calculate income from each source
        peasant_income = int(player.peasants * (player.tax_rate/100) * player.morale * player.science.agriculture * 4)
        fisher_income = int(player.fishers * (player.tax_rate/100) * player.morale * player.science.sailing * 4)
        worker_income = int(player.workers * (player.tax_rate/100) * player.morale * player.science.industry * 8)
        merchant_income = int(player.merchants * (player.tax_rate/100) * player.morale * player.science.trade * 16)
        
        # Interest income/expense
        interest = 0
        if player.money > 0:
            interest = int(player.money * 0.04)  # 4% interest on positive balance
        else:
            interest = -int(abs(player.money) * 0.12)  # 12% interest on debt
        
        self.font.render_to(self.screen, (x + 10, y), f"From Peasants: {peasant_income}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (x + 10, y), f"From Fishers: {fisher_income}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (x + 10, y), f"From Workers: {worker_income}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (x + 10, y), f"From Merchants: {merchant_income}", self.colors[7])
        y += 20
        color = self.colors[10] if interest > 0 else self.colors[12]  # Green if positive, red if negative
        self.font.render_to(self.screen, (x + 10, y), f"Interest: {interest}", color)
        
        # Expenses
        y += 30
        self.title_font.render_to(self.screen, (x, y), "Expenses", self.colors[15])
        y += 25
        
        # Calculate maintenance costs
        mill_cost = int(player.mills * player.science.industry * 20)
        fort_cost = int(player.forts * 30)
        church_cost = int(player.churches * 3)
        university_cost = int(player.universities * 25)
        navy_cost = int(player.navy * 20)
        army_cost = int(player.soldiers * 30)
        
        self.font.render_to(self.screen, (x + 10, y), f"Mills: -{mill_cost}", self.colors[12])
        y += 20
        self.font.render_to(self.screen, (x + 10, y), f"Forts: -{fort_cost}", self.colors[12])
        y += 20
        self.font.render_to(self.screen, (x + 10, y), f"Churches: -{church_cost}", self.colors[12])
        y += 20
        self.font.render_to(self.screen, (x + 10, y), f"Universities: -{university_cost}", self.colors[12])
        y += 20
        self.font.render_to(self.screen, (x + 10, y), f"Navy: -{navy_cost}", self.colors[12])
        y += 20
        self.font.render_to(self.screen, (x + 10, y), f"Army: -{army_cost}", self.colors[12])
        
        # Total income
        y += 30
        total_income = (peasant_income + fisher_income + worker_income + merchant_income + interest - 
                       mill_cost - fort_cost - church_cost - university_cost - navy_cost - army_cost)
        color = self.colors[10] if total_income > 0 else self.colors[12]  # Green if positive, red if negative
        self.title_font.render_to(self.screen, (x, y), f"Total Income: {total_income}", color)
        
        # Military info
        x = 600
        y = 50
        self.title_font.render_to(self.screen, (x, y), "Military", self.colors[15])
        y += 25
        self.font.render_to(self.screen, (x + 10, y), f"Naval Capacity: {player.navy}", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (x + 10, y), f"Embarked Units: {player.sea_army + player.sea_moved}", self.colors[7])
        
        self.font.render_to(
            self.screen,
            (10, self.screen_height - 20),
            "Press ESC to return",
            self.colors[14]
        )

    def draw_treasury_screen(self, player):
        """Draw treasury management screen"""
        self.screen.fill(self.colors[0])
        
        self.title_font.render_to(
            self.screen,
            (10, 10),
            "Treasury Management",
            self.colors[15]
        )
        
        # Your empire's info
        y = 50
        self.title_font.render_to(self.screen, (10, y), "Your Empire", self.colors[15])
        y += 25
        self.font.render_to(self.screen, (10, y), f"Current Gold: {player.money}", self.colors[14])
        y += 20
        self.font.render_to(self.screen, (10, y), f"Tax Rate: {player.tax_rate:.1f}%", self.colors[7])
        y += 20
        self.font.render_to(self.screen, (10, y), "(Use Left/Right arrows to adjust)", self.colors[7])
        
        # Calculate and show projected income
        from player import PlayerManager
        pm = PlayerManager()
        projected_income = pm.calculate_income(player)
        y += 20
        self.font.render_to(self.screen, (10, y), f"Projected Income: {projected_income}", self.colors[14])
        
        # Other nations' info
        y = 50
        x = 300
        self.title_font.render_to(self.screen, (x, y), "Other Nations", self.colors[15])
        y += 25
        
        # Diplomatic status names and info levels
        status_names = {
            1: "War",
            2: "Hostile",
            3: "Neutral",
            4: "Friendly",
            5: "Allied"
        }
        
        for other_player in self.all_players.values():
            if other_player.id != player.id:
                # Get diplomatic status
                status = player.diplomatic_relations.get(other_player.id, 3)  # Default to Neutral
                
                # Draw nation name and status
                self.font.render_to(
                    self.screen,
                    (x, y),
                    f"{other_player.name} ({status_names[status]})",
                    self.colors[other_player.id]
                )
                y += 20
                
                # Show info based on diplomatic status
                if status >= 5:  # Allied - show everything
                    self.font.render_to(self.screen, (x + 20, y), f"Gold: {other_player.money}", self.colors[7])
                    y += 20
                    self.font.render_to(self.screen, (x + 20, y), f"Tax Rate: {other_player.tax_rate:.1f}%", self.colors[7])
                    y += 20
                    income = pm.calculate_income(other_player)
                    self.font.render_to(self.screen, (x + 20, y), f"Income: {income}", self.colors[7])
                    y += 20
                    self.font.render_to(self.screen, (x + 20, y), f"Population: {other_player.population}", self.colors[7])
                    y += 20
                elif status == 4:  # Friendly - show most info
                    self.font.render_to(self.screen, (x + 20, y), f"Gold: {other_player.money}", self.colors[7])
                    y += 20
                    self.font.render_to(self.screen, (x + 20, y), f"Tax Rate: {other_player.tax_rate:.1f}%", self.colors[7])
                    y += 20
                    self.font.render_to(self.screen, (x + 20, y), f"Population: {other_player.population}", self.colors[7])
                    y += 20
                elif status == 3:  # Neutral - show basic info
                    self.font.render_to(self.screen, (x + 20, y), f"Population: {other_player.population}", self.colors[7])
                    y += 20
                else:  # Hostile/War - show no info
                    self.font.render_to(self.screen, (x + 20, y), "No information available", self.colors[8])
                    y += 20
                
                y += 10  # Space between nations
        
        self.font.render_to(
            self.screen,
            (10, self.screen_height - 20),
            "Use Left/Right arrows to adjust tax rate, ESC to return",
            self.colors[14]
        )

    def draw_science_screen(self, player):
        """Draw science management screen"""
        self.screen.fill(self.colors[0])
        
        self.title_font.render_to(
            self.screen,
            (10, 10),
            "Science Management",
            self.colors[15]
        )
        
        # Science branch names and keys
        science_branches = {
            1: ("Agriculture", "1"),
            2: ("Industry", "2"),
            3: ("Trade", "3"),
            4: ("Sailing", "4"),
            5: ("Military", "5"),
            6: ("Medicine", "6")
        }
        
        # Draw current gold
        self.font.render_to(
            self.screen,
            (10, 40),
            f"Gold: {player.money}",
            self.colors[14]
        )
        
        # Draw science levels and spending options
        y = 70
        for i in range(1, 7):
            level = player.science.get_level(i)
            name, key = science_branches[i]
            
            # Calculate max spendable amount
            max_spend = min(player.money, int((level ** 3) * 1000))
            
            # Draw level and spending info
            self.font.render_to(
                self.screen,
                (10, y),
                f"{name}: Level {level:.1f}",
                self.colors[7]
            )
            self.font.render_to(
                self.screen,
                (250, y),
                f"Press {key} to spend (max: {max_spend})",
                self.colors[14]
            )
            y += 30
        
        # Draw relative science graph
        graph_x = 500
        graph_y = 70
        graph_width = 350
        graph_height = 200
        
        # Draw graph background
        pygame.draw.rect(
            self.screen,
            self.colors[8],  # Dark gray
            (graph_x, graph_y, graph_width, graph_height),
            1
        )
        
        # Get max science level across all visible players for scaling
        max_level = 1.0
        for p in self.all_players.values():
            if player.can_view_science(p):
                for i in range(1, 7):
                    max_level = max(max_level, p.science.get_level(i))
        
        # Draw bars for each player
        bar_width = graph_width / (len(self.all_players) * 6 + len(self.all_players) - 1)
        x = graph_x + 5
        
        for p in self.all_players.values():
            can_view = player.can_view_science(p)
            for i in range(1, 7):
                level = p.science.get_level(i) if can_view else 0
                bar_height = (level / max_level) * (graph_height - 10)
                
                # Use black for non-visible science levels
                color = self.colors[0] if not can_view else self.colors[p.id]
                
                pygame.draw.rect(
                    self.screen,
                    color,
                    (x, graph_y + graph_height - bar_height - 5, bar_width - 2, bar_height)
                )
                x += bar_width
            x += bar_width  # Add space between players
        
        # Draw legend with spy options
        legend_y = graph_y + graph_height + 10
        x = graph_x
        for p in self.all_players.values():
            if p.id != player.id:  # Don't show spy option for own empire
                pygame.draw.rect(
                    self.screen,
                    self.colors[p.id],
                    (x, legend_y, 20, 20)
                )
                
                # Show spy status or cost
                if player.science.spied_empires.get(p.id, False):
                    spy_text = "Spying"
                    text_color = self.colors[2]  # Green
                else:
                    spy_cost = player.get_spy_cost(p)
                    spy_text = f"Spy ({spy_cost}g)"
                    text_color = self.colors[14]  # Gold
                
                self.font.render_to(
                    self.screen,
                    (x + 25, legend_y + 5),
                    f"{p.name} - {spy_text}",
                    text_color
                )
                
                # Add key hint for spying
                if not player.science.spied_empires.get(p.id, False):
                    self.font.render_to(
                        self.screen,
                        (x + 150, legend_y + 5),
                        f"(Press {p.id} to spy)",
                        self.colors[7]
                    )
                
                x += 200
        
        # Instructions
        self.font.render_to(
            self.screen,
            (10, self.screen_height - 40),
            "Press 1-6 to spend on science",
            self.colors[14]
        )
        self.font.render_to(
            self.screen,
            (10, self.screen_height - 20),
            "Press player number to place spy, ESC to return",
            self.colors[14]
        )
    
    def draw_diplomacy_screen(self, player, all_players):
        """Draw diplomacy management screen"""
        self.screen.fill(self.colors[0])
        
        self.title_font.render_to(
            self.screen,
            (10, 10),
            "Diplomacy",
            self.colors[15]
        )
        
        # Diplomatic status names
        status_names = {
            1: "War",
            2: "Hostile",
            3: "Neutral",
            4: "Friendly",
            5: "Allied"
        }
        
        y = 50
        for other_player in all_players.values():
            if other_player.id != player.id:
                # Get current diplomatic status
                status = player.diplomatic_relations.get(other_player.id, 3)  # Default to Neutral
                
                # Draw nation name and current status
                self.font.render_to(
                    self.screen,
                    (10, y),
                    f"{other_player.name}: {status_names[status]}",
                    self.colors[7]
                )
                
                # Draw options to change relations
                options = []
                
                # Option to decrease relations (declare war)
                if status > 1:  # Can lower if not at war
                    self.font.render_to(
                        self.screen,
                        (300, y),
                        f"Press {other_player.id} to set negative relations",
                        self.colors[4]  # Red color for negative option
                    )
                
                # Option to increase relations
                if status < 5:  # Can increase if not already allied
                    key_list = ["o","p","[","]","l","\\","l",".","/"]
                if 1 <= other_player.id <= len(key_list):
                    key = key_list[other_player.id - 1]
                else:
                    key = '?'
                self.font.render_to(
                    self.screen,
                    (550, y),
                    f"Press {key} to improve relations",
                                        self.colors[2]  # Green color for improve option
                                    )
                y += 30
                                
        self.font.render_to(
            self.screen,
            (10, self.screen_height - 20),
            "Press number to declare war, o p [ ] l ; ' , .  to improve relations (one change per nation per turn), ESC to return",
            self.colors[14]
        )
    
    def clear(self):
        """Clear the screen"""
        if self.show_title_screen:
            return
            
        # Clear screen with black background
        self.screen.fill(self.colors[0])
        
        # Draw active screen if any
        if self.state.help_content:
            self.draw_help_screen()
            return
        elif self.state.active_screen == "info":
            self.draw_information_screen(self.current_player)
            return
        elif self.state.active_screen == "treasury":
            self.draw_treasury_screen(self.current_player)
            return
        elif self.state.active_screen == "science":
            self.draw_science_screen(self.current_player)
            return
        elif self.state.active_screen == "diplomacy":
            self.draw_diplomacy_screen(self.current_player, self.all_players)
            return
