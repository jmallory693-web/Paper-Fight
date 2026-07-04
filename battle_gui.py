import json
import os
import random
import tkinter as tk
from tkinter import messagebox, ttk


# --- Combat tuning constants ---
POWER_STRIKE_COOLDOWN = 2
POWER_STRIKE_BONUS = 3
REST_HEAL_BETWEEN_FIGHTS = 3
BLOCK_DAMAGE_REDUCTION = 4
STALEMATE_CHIP_DAMAGE = 1
RUN_SAVE_VERSION = 1
BUILD_SAVE_VERSION = 2
RESET_STAT_COST = 100
LOOT_DROP_CHANCE = 0.35
ADMIN_CLICKS_REQUIRED = 3

BASE_ATTACK = 6
BASE_DEFENSE = 2
BASE_HEALTH = 25

# Playable races: small bonuses applied on top of the 15-point allocation.
RACES = {
    "Human": {
        "attack": 0,
        "defense": 0,
        "health": 0,
        "desc": "Balanced and adaptable — no bonus, no weakness.",
    },
    "Elf": {
        "attack": 2,
        "defense": 0,
        "health": 0,
        "desc": "Keen reflexes: +2 Attack.",
    },
    "Dwarf": {
        "attack": 0,
        "defense": 3,
        "health": 10,
        "desc": "Stone-hard folk: +3 Defense, +10 Max HP.",
    },
    "Orc": {
        "attack": 3,
        "defense": 1,
        "health": 5,
        "desc": "Born for battle: +3 Attack, +1 Defense, +5 Max HP.",
    },
    "Halfling": {
        "attack": 0,
        "defense": 2,
        "health": 15,
        "desc": "Hardy survivors: +2 Defense, +15 Max HP.",
    },
}

EQUIPMENT_SLOTS = [
    "head",
    "chest",
    "legs",
    "arms",
    "weapon",
    "shield",
    "ring1",
    "ring2",
    "amulet",
]

SHOP_GEAR_TABS = [
    ("head", "Head"),
    ("chest", "Chest"),
    ("legs", "Legs"),
    ("arms", "Arms"),
    ("weapon", "Weapon"),
    ("shield", "Shield"),
    ("rings", "Rings"),
    ("amulet", "Amulet"),
]

# Gear the warrior begins each run with.
STARTING_EQUIPMENT = [
    {"id": "rusty_dagger", "name": "Rusty Dagger", "slot": "weapon", "attack": 1},
    {"id": "worn_tunic", "name": "Worn Tunic", "slot": "chest", "defense": 1},
    {"id": "wooden_shield", "name": "Wooden Shield", "slot": "shield", "defense": 1},
]

# Equipment available for purchase between fights.
SHOP_EQUIPMENT = [
    {"id": "iron_sword", "name": "Iron Sword", "slot": "weapon", "attack": 2, "price": 18},
    {"id": "steel_helm", "name": "Steel Helm", "slot": "head", "defense": 2, "price": 14},
    {"id": "chainmail", "name": "Chainmail", "slot": "chest", "defense": 3, "price": 22},
    {"id": "iron_greaves", "name": "Iron Greaves", "slot": "legs", "defense": 2, "price": 16},
    {"id": "brass_gauntlets", "name": "Brass Gauntlets", "slot": "arms", "attack": 1, "defense": 1, "price": 15},
    {"id": "tower_shield", "name": "Tower Shield", "slot": "shield", "defense": 3, "price": 20},
    {"id": "ring_of_might", "name": "Ring of Might", "slot": "ring1", "attack": 1, "price": 12},
    {"id": "ring_of_warding", "name": "Ring of Warding", "slot": "ring2", "defense": 1, "price": 12},
    {"id": "jade_amulet", "name": "Jade Amulet", "slot": "amulet", "health": 8, "price": 16},
]

# Themed foes: stat mods stack on top of base level scaling.
ENEMY_THEMES = [
    {
        "name": "Scrawny Rat",
        "flavor": "A scrawny rat darts from the rubble, teeth bared and tail lashing.",
        "min_level": 1,
        "attack_mod": 1,
        "defense_mod": -1,
        "health_mod": -7,
        "ai_style": "aggressive",
    },
    {
        "name": "Feral Cat",
        "flavor": "A feral cat slinks into the arena, fur bristling as it hisses.",
        "min_level": 1,
        "attack_mod": 2,
        "defense_mod": 0,
        "health_mod": -5,
        "ai_style": "aggressive",
    },
    {
        "name": "Goblin Scout",
        "flavor": "A goblin scout hops into view, grinning like it already has a trick planned.",
        "min_level": 2,
        "attack_mod": 0,
        "defense_mod": 1,
        "health_mod": -3,
        "ai_style": "tricky",
    },
    {
        "name": "Giant Spider",
        "flavor": "A giant spider descends on glistening thread, legs clicking on stone.",
        "min_level": 2,
        "attack_mod": 1,
        "defense_mod": 0,
        "health_mod": -2,
        "ai_style": "tricky",
    },
    {
        "name": "Wolf",
        "flavor": "A lean wolf circles you, hunger and caution warring in its gaze.",
        "min_level": 3,
        "attack_mod": 1,
        "defense_mod": 0,
        "health_mod": 0,
        "ai_style": "balanced",
    },
    {
        "name": "Bandit Raider",
        "flavor": "A bandit raider twirls a notched blade, sizing you up for plunder.",
        "min_level": 3,
        "attack_mod": 0,
        "defense_mod": 0,
        "health_mod": 2,
        "ai_style": "balanced",
    },
    {
        "name": "Orc Brute",
        "flavor": "An orc brute stomps forward, hoisting a crude axe with a rumbling war cry.",
        "min_level": 4,
        "attack_mod": 2,
        "defense_mod": 1,
        "health_mod": 5,
        "ai_style": "bruiser",
    },
    {
        "name": "Cave Troll",
        "flavor": "A cave troll lumbers into the torchlight, hide like stone and fists like boulders.",
        "min_level": 5,
        "attack_mod": 1,
        "defense_mod": 2,
        "health_mod": 8,
        "ai_style": "bruiser",
    },
]

# Mercenary roster templates — hired between fights, lost on game over / new run.
MAX_ACTIVE_MERCENARIES = 2
RECRUITMENT_POOL_SIZE = 3
MERCENARY_REST_HEAL = 2
MERCENARY_REVIVE_COST_BASE = 28

MERCENARY_TEMPLATES = [
    {
        "id": "grimhold",
        "name": "Grimhold",
        "race": "Dwarf",
        "role": "Tank",
        "attack": 4,
        "defense": 6,
        "health": 30,
        "ability": "fortify",
        "ability_desc": "Fortify: brace and recover 3 HP.",
        "ai_style": "defensive",
    },
    {
        "id": "swiftarrow",
        "name": "Swiftarrow",
        "race": "Elf",
        "role": "Archer",
        "attack": 7,
        "defense": 2,
        "health": 22,
        "ability": "volley",
        "ability_desc": "Volley: ranged strike ignores 2 defense.",
        "ai_style": "aggressive",
    },
    {
        "id": "ironjaw",
        "name": "Ironjaw",
        "race": "Orc",
        "role": "Berserker",
        "attack": 8,
        "defense": 1,
        "health": 26,
        "ability": "fury",
        "ability_desc": "Fury: reckless swing for +4 damage.",
        "ai_style": "aggressive",
    },
    {
        "id": "mira_leaf",
        "name": "Mira Leaf",
        "race": "Halfling",
        "role": "Healer",
        "attack": 3,
        "defense": 3,
        "health": 24,
        "ability": "mend",
        "ability_desc": "Mend: restore 6 HP to you or an ally.",
        "ai_style": "support",
    },
    {
        "id": "shade",
        "name": "Shade",
        "race": "Human",
        "role": "Scout",
        "attack": 6,
        "defense": 3,
        "health": 20,
        "ability": "ambush",
        "ability_desc": "Ambush: bonus damage when the foe is wounded.",
        "ai_style": "tricky",
    },
    {
        "id": "thornback",
        "name": "Thornback",
        "race": "Dwarf",
        "role": "Guardian",
        "attack": 5,
        "defense": 5,
        "health": 28,
        "ability": "shield_wall",
        "ability_desc": "Shield Wall: block and reduce your damage taken.",
        "ai_style": "defensive",
    },
    {
        "id": "ember",
        "name": "Ember",
        "race": "Elf",
        "role": "Mage",
        "attack": 6,
        "defense": 2,
        "health": 18,
        "ability": "arc_bolt",
        "ability_desc": "Arc Bolt: reliable magical hit for 5 damage.",
        "ai_style": "tricky",
    },
]


def mercenary_power_rating(template):
    """Rough power score used to scale hire and revive costs."""
    return template["attack"] + template["defense"] + template["health"] // 5


def mercenary_hire_cost(template):
    return 10 + mercenary_power_rating(template) * 2


def mercenary_revive_cost(mercenary):
    return MERCENARY_REVIVE_COST_BASE + mercenary_power_rating(mercenary.template) * 3


def get_mercenary_template(template_id, templates=None):
    pool = templates if templates is not None else MERCENARY_TEMPLATES
    for template in pool:
        if template["id"] == template_id:
            return template
    return None


def merge_custom_lists(base_list, custom_list, key="id"):
    """Merge admin/custom entries into runtime lists without duplicates."""
    merged = [dict(item) for item in base_list]
    seen = {item.get(key) or item.get("name") for item in merged}
    for item in custom_list:
        ident = item.get(key) or item.get("name")
        if ident and ident not in seen:
            merged.append(dict(item))
            seen.add(ident)
    return merged


class Combatant:
    def __init__(
        self,
        name,
        attack,
        defense,
        health,
        level=1,
        flavor="",
        ai_style="balanced",
        enemy_type="",
    ):
        self.name = name
        self.attack = attack
        self.defense = defense
        self.health = health
        self.max_health = health
        self.level = level
        self.flavor = flavor
        self.ai_style = ai_style
        self.enemy_type = enemy_type

    def alive(self):
        return self.health > 0


class Mercenary:
    """Hired ally that fights alongside the player for the current run."""

    def __init__(self, template):
        self.template = dict(template)
        self.name = template["name"]
        self.race = template["race"]
        self.role = template["role"]
        self.attack = template["attack"]
        self.defense = template["defense"]
        self.health = template["health"]
        self.max_health = template["health"]
        self.ability = template["ability"]
        self.ability_desc = template["ability_desc"]
        self.ai_style = template["ai_style"]
        self.ability_cooldown = 0
        self.last_action = "—"
        self.fallen = False

    def alive(self):
        return not self.fallen and self.health > 0

    def to_combatant(self):
        """Lightweight view for shared damage math."""
        return Combatant(self.name, self.attack, self.defense, self.health)

    def power_rating(self):
        return mercenary_power_rating(self.template)


class BattleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Battle Warriors")
        self.root.geometry("960x680")
        self.root.minsize(900, 640)
        self.root.configure(bg="#D2B48C")

        # Runtime content lists (base data + admin/custom additions) — before make_enemy.
        self.shop_equipment = [dict(item) for item in SHOP_EQUIPMENT]
        self.mercenary_templates = [dict(item) for item in MERCENARY_TEMPLATES]
        self.enemy_themes = [dict(item) for item in ENEMY_THEMES]
        self.battle_bonuses = {"xp_multiplier": 1.0, "coin_bonus": 0}
        self.custom_content_path = os.path.join(os.path.dirname(__file__), "game_custom.json")
        self.load_custom_content()

        # Progression and run state.
        self.player = Combatant("Player Warrior", BASE_ATTACK, BASE_DEFENSE, BASE_HEALTH)
        self.player_level = 1
        self.player_xp = 0
        self.enemy_level = 1
        self.coins = 10
        self.enemy = self.make_enemy(self.enemy_level)
        self.in_combat = False
        self.in_preparation = False
        self.awaiting_first_strike = False
        self.power_strike_cooldown = 0
        self.next_enemy_wounded = False
        self.awaiting_reward = False
        self.fight_timer_id = None
        self._player_damage_reduction_next = False

        # Build, race, equipment, and bonus tracking.
        self.selected_race = "Human"
        self.stat_bonuses = {"attack": 0, "defense": 0, "health": 0}
        self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        self.inventory = []

        # Character creation state.
        self.creation_points_left = 15
        self.creation_attack_points = 0
        self.creation_defense_points = 0
        self.creation_health_points = 0
        self.character_window = None
        self.game_over_window = None
        self.run_started = False

        # Mercenary party: up to two active allies, plus fallen allies eligible for revival.
        self.active_mercenaries = []
        self.fallen_mercenaries = []
        self.recruitment_pool = []
        self.build_active = False
        self.save_path = os.path.join(os.path.dirname(__file__), "player_build.json")
        self.build_save_path = os.path.join(os.path.dirname(__file__), "saved_build.json")
        self.run_save_path = os.path.join(os.path.dirname(__file__), "player_run.json")
        self.saved_equipment_from_build = None
        self.admin_unlocked = True
        self.title_click_count = 0
        self.pending_loot_item = None

        self.build_ui()
        self.show_main_menu()

    def build_ui(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#D2B48C")
        self.style.configure("TLabel", background="#D2B48C", foreground="black")
        self.style.configure("TButton", padding=6)
        self.style.configure("TLabelframe", background="#D2B48C")
        self.style.configure("TLabelframe.Label", foreground="black")

        self.menu_frame = ttk.Frame(self.root, padding=16)
        self.menu_title_label = ttk.Label(
            self.menu_frame, text="Battle Warriors", font=("Segoe UI", 20, "bold"), cursor="hand2"
        )
        self.menu_title_label.pack(pady=(16, 6))
        self.menu_title_label.bind("<Button-1>", self.on_menu_title_click)
        ttk.Label(
            self.menu_frame,
            text="Forge your warrior, climb the arena ladder, and survive the gauntlet.",
            wraplength=480,
        ).pack(pady=(0, 16))
        menu_buttons = ttk.Frame(self.menu_frame)
        menu_buttons.pack()
        ttk.Button(menu_buttons, text="New Build", command=self.start_new_build, width=22).pack(pady=4)
        ttk.Button(menu_buttons, text="Load Build", command=self.load_build_from_file, width=22).pack(pady=4)
        self.save_build_btn = ttk.Button(
            menu_buttons, text="Save Build", command=self.save_build_to_file, state=tk.DISABLED, width=22
        )
        self.save_build_btn.pack(pady=4)
        ttk.Separator(menu_buttons, orient="horizontal").pack(fill=tk.X, pady=8)
        self.save_run_btn = ttk.Button(
            menu_buttons, text="Save Run", command=self.save_run_to_file, state=tk.DISABLED, width=22
        )
        self.save_run_btn.pack(pady=4)
        self.load_run_btn = ttk.Button(
            menu_buttons, text="Load Run", command=self.load_run_from_file, state=tk.DISABLED, width=22
        )
        self.load_run_btn.pack(pady=4)
        ttk.Button(menu_buttons, text="Quit", command=self.quit_game, width=22).pack(pady=4)
        self.admin_btn = ttk.Button(
            self.menu_frame, text="Admin Mode", command=self.open_admin_panel, width=22
        )
        self.admin_btn.pack(pady=(10, 4))
        self.menu_status_var = tk.StringVar(value="Create or load a build to begin.")
        self.menu_status_label = ttk.Label(self.menu_frame, textvariable=self.menu_status_var)
        self.menu_status_label.pack(pady=(12, 0))

        # Character creation — full in-game screen (not a popup).
        self.creation_frame = ttk.Frame(self.root, padding=16)
        self.creation_frame.pack_forget()
        ttk.Label(self.creation_frame, text="Create Your Warrior", font=("Segoe UI", 18, "bold")).pack(
            pady=(12, 6)
        )
        ttk.Label(
            self.creation_frame,
            text="Choose a race, then spend 15 points across Attack, Defense, and Max Health.",
            wraplength=480,
        ).pack(pady=(0, 8))
        race_row = ttk.Frame(self.creation_frame)
        race_row.pack(pady=4)
        ttk.Label(race_row, text="Race:").pack(side=tk.LEFT, padx=(0, 8))
        self.race_var = tk.StringVar(value=self.selected_race)
        self.race_combo = ttk.Combobox(
            race_row,
            textvariable=self.race_var,
            values=list(RACES.keys()),
            state="readonly",
            width=14,
        )
        self.race_combo.pack(side=tk.LEFT)
        self.race_combo.bind("<<ComboboxSelected>>", self.on_race_changed)
        self.race_desc_var = tk.StringVar()
        ttk.Label(self.creation_frame, textvariable=self.race_desc_var, wraplength=480).pack(pady=(4, 8))
        self.creation_points_var = tk.StringVar(value="Points left: 15")
        ttk.Label(self.creation_frame, textvariable=self.creation_points_var, font=("Segoe UI", 11, "bold")).pack()
        rows = ttk.Frame(self.creation_frame)
        rows.pack(pady=8)
        ttk.Label(rows, text="Attack").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.attack_points_var = tk.StringVar(value="0")
        ttk.Label(rows, textvariable=self.attack_points_var).grid(row=0, column=1, padx=6, pady=4)
        ttk.Button(rows, text="-", command=lambda: self.adjust_creation_stat("attack", -1), width=3).grid(
            row=0, column=2, padx=2
        )
        ttk.Button(rows, text="+", command=lambda: self.adjust_creation_stat("attack", 1), width=3).grid(
            row=0, column=3, padx=2
        )
        ttk.Label(rows, text="Defense").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.defense_points_var = tk.StringVar(value="0")
        ttk.Label(rows, textvariable=self.defense_points_var).grid(row=1, column=1, padx=6, pady=4)
        ttk.Button(rows, text="-", command=lambda: self.adjust_creation_stat("defense", -1), width=3).grid(
            row=1, column=2, padx=2
        )
        ttk.Button(rows, text="+", command=lambda: self.adjust_creation_stat("defense", 1), width=3).grid(
            row=1, column=3, padx=2
        )
        ttk.Label(rows, text="Max Health").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        self.health_points_var = tk.StringVar(value="0")
        ttk.Label(rows, textvariable=self.health_points_var).grid(row=2, column=1, padx=6, pady=4)
        ttk.Button(rows, text="-", command=lambda: self.adjust_creation_stat("health", -1), width=3).grid(
            row=2, column=2, padx=2
        )
        ttk.Button(rows, text="+", command=lambda: self.adjust_creation_stat("health", 1), width=3).grid(
            row=2, column=3, padx=2
        )
        preview_frame = ttk.LabelFrame(self.creation_frame, text="Live Stat Preview", padding=10)
        preview_frame.pack(fill=tk.X, padx=40, pady=10)
        self.preview_attack_var = tk.StringVar()
        self.preview_defense_var = tk.StringVar()
        self.preview_health_var = tk.StringVar()
        ttk.Label(preview_frame, textvariable=self.preview_attack_var, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(preview_frame, textvariable=self.preview_defense_var, font=("Segoe UI", 11, "bold")).pack(
            anchor="w", pady=(2, 0)
        )
        ttk.Label(preview_frame, textvariable=self.preview_health_var, font=("Segoe UI", 11, "bold")).pack(
            anchor="w", pady=(2, 0)
        )
        ttk.Label(
            self.creation_frame, text="Each point gives +1 Attack, +1 Defense, or +5 Max Health."
        ).pack(pady=(4, 8))
        creation_actions = ttk.Frame(self.creation_frame)
        creation_actions.pack(pady=4)
        ttk.Button(creation_actions, text="Confirm Build", command=self.confirm_character_creation, width=16).pack(
            side=tk.LEFT, padx=6
        )
        ttk.Button(creation_actions, text="Main Menu", command=self.return_to_main_menu, width=16).pack(
            side=tk.LEFT, padx=6
        )

        # Battle screen — grid layout sized for 900x640 without scrolling.
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack_forget()
        self.main_frame.columnconfigure(0, weight=1, uniform="main")
        self.main_frame.columnconfigure(1, weight=0)
        self.main_frame.columnconfigure(2, weight=1, uniform="main")
        self.main_frame.rowconfigure(4, weight=1)

        # --- Row 0: compact top bar (run progress | current opponent) ---
        top_bar = ttk.Frame(self.main_frame)
        top_bar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        top_bar.columnconfigure(0, weight=1, uniform="top")
        top_bar.columnconfigure(1, weight=1, uniform="top")

        progress_panel = ttk.LabelFrame(top_bar, text="Run Progress", padding=6)
        progress_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self.progress_level_var = tk.StringVar(value="Level: 1")
        self.progress_xp_var = tk.StringVar(value="XP: 0 / 10")
        self.progress_coins_var = tk.StringVar(value="Coins: 10")
        self.progress_cooldown_var = tk.StringVar(value="Power Strike: ready")
        self.progress_race_var = tk.StringVar(value="Race: Human")
        progress_row = ttk.Frame(progress_panel)
        progress_row.pack(fill=tk.X)
        ttk.Label(progress_row, textvariable=self.progress_level_var, font=("Segoe UI", 10, "bold")).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Label(progress_row, textvariable=self.progress_xp_var).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(progress_row, textvariable=self.progress_coins_var).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(progress_row, textvariable=self.progress_cooldown_var).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(progress_row, textvariable=self.progress_race_var).pack(side=tk.LEFT)

        opponent_banner = ttk.LabelFrame(top_bar, text="Current Opponent", padding=6)
        opponent_banner.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self.enemy_banner_var = tk.StringVar(value="Awaiting challenger...")
        self.enemy_type_var = tk.StringVar(value="")
        ttk.Label(opponent_banner, textvariable=self.enemy_banner_var, font=("Segoe UI", 10, "bold")).pack(
            anchor="w"
        )
        ttk.Label(opponent_banner, textvariable=self.enemy_type_var).pack(anchor="w", pady=(1, 0))

        ttk.Separator(self.main_frame, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", pady=4)

        # --- Row 2: left (you + mercs) | center (actions) | right (opponent stats) ---
        left_col = ttk.Frame(self.main_frame)
        left_col.grid(row=2, column=0, sticky="nsew", padx=(0, 4))
        left_col.columnconfigure(0, weight=1)

        self.player_card = ttk.LabelFrame(left_col, text="You", padding=6)
        self.player_card.grid(row=0, column=0, sticky="ew")
        self.player_health_var = tk.StringVar(value="HP: 25 / 25")
        self.player_stats_var = tk.StringVar(value="Attack 6  Defense 2")
        self.player_equipment_var = tk.StringVar(value="Gear: none")
        self.player_bar = ttk.Progressbar(self.player_card, orient=tk.HORIZONTAL, mode="determinate")
        self.player_bar.pack(fill=tk.X, pady=(2, 4))
        ttk.Label(self.player_card, textvariable=self.player_health_var, font=("Segoe UI", 10, "bold")).pack(
            anchor="w"
        )
        ttk.Label(self.player_card, textvariable=self.player_stats_var).pack(anchor="w", pady=(1, 0))
        ttk.Label(self.player_card, textvariable=self.player_equipment_var, wraplength=260).pack(
            anchor="w", pady=(1, 0)
        )

        self.merc_panel = ttk.LabelFrame(left_col, text="Mercenaries", padding=6)
        self.merc_panel.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        self.merc_slot_frames = []
        self.merc_name_vars = []
        self.merc_health_vars = []
        self.merc_action_vars = []
        self.merc_bars = []
        for slot in range(MAX_ACTIVE_MERCENARIES):
            slot_frame = ttk.Frame(self.merc_panel)
            slot_frame.pack(fill=tk.X, pady=(0 if slot == 0 else 4, 0))
            name_var = tk.StringVar(value="Empty slot")
            health_var = tk.StringVar(value="—")
            action_var = tk.StringVar(value="")
            bar = ttk.Progressbar(slot_frame, orient=tk.HORIZONTAL, mode="determinate")
            bar.pack(fill=tk.X, pady=(0, 1))
            ttk.Label(slot_frame, textvariable=name_var, font=("Segoe UI", 9, "bold")).pack(anchor="w")
            ttk.Label(slot_frame, textvariable=health_var, font=("Segoe UI", 9)).pack(anchor="w")
            ttk.Label(slot_frame, textvariable=action_var, font=("Segoe UI", 8)).pack(anchor="w")
            self.merc_slot_frames.append(slot_frame)
            self.merc_name_vars.append(name_var)
            self.merc_health_vars.append(health_var)
            self.merc_action_vars.append(action_var)
            self.merc_bars.append(bar)

        action_panel = ttk.LabelFrame(self.main_frame, text="Choose Your Move", padding=6)
        action_panel.grid(row=2, column=1, sticky="ns", padx=4)
        self.swing_btn = ttk.Button(action_panel, text="Swing", command=lambda: self.take_turn("swing"), width=14)
        self.swing_btn.pack(pady=3)
        self.block_btn = ttk.Button(action_panel, text="Block", command=lambda: self.take_turn("block"), width=14)
        self.block_btn.pack(pady=3)
        self.power_btn = ttk.Button(
            action_panel, text="Power Strike", command=lambda: self.take_turn("power"), width=14
        )
        self.power_btn.pack(pady=3)

        right_col = ttk.Frame(self.main_frame)
        right_col.grid(row=2, column=2, sticky="nsew", padx=(4, 0))
        right_col.columnconfigure(0, weight=1)

        self.enemy_card = ttk.LabelFrame(right_col, text="Opponent", padding=6)
        self.enemy_card.grid(row=0, column=0, sticky="ew")
        self.enemy_health_var = tk.StringVar(value="HP: 29 / 29")
        self.enemy_stats_var = tk.StringVar(value="Attack 7  Defense 2")
        self.enemy_bar = ttk.Progressbar(self.enemy_card, orient=tk.HORIZONTAL, mode="determinate")
        self.enemy_bar.pack(fill=tk.X, pady=(2, 4))
        ttk.Label(self.enemy_card, textvariable=self.enemy_health_var, font=("Segoe UI", 10, "bold")).pack(
            anchor="w"
        )
        ttk.Label(self.enemy_card, textvariable=self.enemy_stats_var).pack(anchor="w", pady=(1, 0))

        ttk.Separator(self.main_frame, orient="horizontal").grid(row=3, column=0, columnspan=3, sticky="ew", pady=4)

        # --- Row 4: bottom half — battle log (left) + arena status (right) ---
        bottom_row = ttk.Frame(self.main_frame)
        bottom_row.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(0, 4))
        bottom_row.columnconfigure(0, weight=1, uniform="bottom")
        bottom_row.columnconfigure(1, weight=1, uniform="bottom")
        bottom_row.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(4, weight=1)

        log_frame = ttk.LabelFrame(bottom_row, text="Battle Log", padding=6)
        log_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_box = tk.Text(
            log_frame, height=8, wrap=tk.WORD, state=tk.DISABLED, bg="#F7E6C4", fg="black", font=("Segoe UI", 9)
        )
        self.log_box.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_box.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_box.configure(yscrollcommand=scroll.set)

        info_panel = ttk.LabelFrame(bottom_row, text="Arena Status", padding=6)
        info_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self.status_var = tk.StringVar(value="The arena waits for your first choice.")
        self.action_hint = tk.StringVar(
            value="Swing trades blows, Block softens hits, Power Strike deals heavy damage (2-turn cooldown)."
        )
        self.phase_info_var = tk.StringVar(value="Preparation: use Shop or Recruit, then strike to begin.")
        ttk.Label(info_panel, textvariable=self.status_var, font=("Segoe UI", 10, "bold"), wraplength=300).pack(
            anchor="nw", pady=(0, 6)
        )
        ttk.Separator(info_panel, orient="horizontal").pack(fill=tk.X, pady=4)
        ttk.Label(info_panel, text="Combat Tips", font=("Segoe UI", 9, "bold")).pack(anchor="nw")
        ttk.Label(info_panel, textvariable=self.action_hint, wraplength=300, font=("Segoe UI", 9)).pack(
            anchor="nw", pady=(2, 6)
        )
        ttk.Separator(info_panel, orient="horizontal").pack(fill=tk.X, pady=4)
        ttk.Label(info_panel, text="Run Notes", font=("Segoe UI", 9, "bold")).pack(anchor="nw")
        ttk.Label(info_panel, textvariable=self.phase_info_var, wraplength=300, font=("Segoe UI", 9)).pack(
            anchor="nw", pady=(2, 0)
        )

        ttk.Separator(self.main_frame, orient="horizontal").grid(row=5, column=0, columnspan=3, sticky="ew", pady=4)

        # --- Row 6: footer navigation ---
        footer = ttk.Frame(self.main_frame)
        footer.grid(row=6, column=0, columnspan=3, sticky="ew")
        self.main_menu_btn = ttk.Button(footer, text="Main Menu", command=self.return_to_main_menu)
        self.main_menu_btn.pack(side=tk.LEFT, padx=4)
        self.save_run_footer_btn = ttk.Button(
            footer, text="Save Run", command=self.save_run_to_file, state=tk.DISABLED
        )
        self.save_run_footer_btn.pack(side=tk.LEFT, padx=4)
        self.character_btn = ttk.Button(footer, text="Character", command=self.open_character_panel, state=tk.DISABLED)
        self.character_btn.pack(side=tk.RIGHT, padx=4)
        self.recruit_btn = ttk.Button(footer, text="Recruit", command=self.open_recruit, state=tk.DISABLED)
        self.recruit_btn.pack(side=tk.RIGHT, padx=4)
        self.shop_btn = ttk.Button(footer, text="Shop", command=self.open_shop, state=tk.DISABLED)
        self.shop_btn.pack(side=tk.RIGHT, padx=4)
        self.play_again_btn = ttk.Button(
            footer, text="Start New Run", command=self.start_new_run, state=tk.DISABLED
        )
        self.play_again_btn.pack(side=tk.RIGHT, padx=4)

        self._build_embedded_shop_screen()
        self._build_embedded_recruit_screen()
        self._build_embedded_admin_screen()

    def _build_embedded_shop_screen(self):
        """Shop as a full in-game screen (not a popup)."""
        self.shop_frame = ttk.Frame(self.root, padding=16)
        self.shop_frame.pack_forget()
        ttk.Label(self.shop_frame, text="Battle Warriors Shop", font=("Segoe UI", 18, "bold")).pack(
            pady=(8, 4)
        )
        self.shop_coins_var = tk.StringVar(value="Coins: 10")
        ttk.Label(self.shop_frame, textvariable=self.shop_coins_var, font=("Segoe UI", 11, "bold")).pack()
        ttk.Label(
            self.shop_frame,
            text="Preparation phase — browse freely, then return to the arena when ready.",
            wraplength=520,
        ).pack(pady=(4, 10))

        consumables = ttk.LabelFrame(self.shop_frame, text="Consumables", padding=8)
        consumables.pack(fill=tk.X, pady=6)
        ttk.Label(consumables, text="Health Salve — 10 coins — restores 12 HP").pack(anchor="w")
        ttk.Button(consumables, text="Buy Health Salve", command=self.buy_health_salve).pack(anchor="w", pady=4)
        ttk.Label(consumables, text="Iron Tonic — 15 coins — +1 Defense for this run").pack(anchor="w", pady=(6, 0))
        ttk.Button(consumables, text="Buy Iron Tonic", command=self.buy_iron_tonic).pack(anchor="w", pady=4)

        gear_section = ttk.LabelFrame(self.shop_frame, text="Equipment", padding=8)
        gear_section.pack(fill=tk.BOTH, expand=True, pady=6)
        self.shop_gear_notebook = ttk.Notebook(gear_section)
        self.shop_gear_notebook.pack(fill=tk.BOTH, expand=True)
        self.shop_gear_tab_frames = {}
        for slot_key, label in SHOP_GEAR_TABS:
            tab = ttk.Frame(self.shop_gear_notebook, padding=6)
            self.shop_gear_notebook.add(tab, text=label)
            self.shop_gear_tab_frames[slot_key] = self._build_scrollable_list_frame(tab)

        shop_actions = ttk.Frame(self.shop_frame)
        shop_actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(shop_actions, text="Back to Arena", command=self.close_shop, width=18).pack(side=tk.LEFT)

    def _build_embedded_recruit_screen(self):
        """Mercenary Hall as a full in-game screen (not a popup)."""
        self.recruit_frame = ttk.Frame(self.root, padding=16)
        self.recruit_frame.pack_forget()
        ttk.Label(self.recruit_frame, text="Mercenary Hall", font=("Segoe UI", 18, "bold")).pack(pady=(8, 4))
        self.recruit_coins_var = tk.StringVar(value="Coins: 10")
        ttk.Label(self.recruit_frame, textvariable=self.recruit_coins_var, font=("Segoe UI", 11, "bold")).pack()
        ttk.Label(
            self.recruit_frame,
            text=f"Hire up to {MAX_ACTIVE_MERCENARIES} allies. Fallen mercenaries can be revived for a steep fee.",
            wraplength=520,
        ).pack(pady=(4, 10))

        notebook = ttk.Notebook(self.recruit_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=6)
        self.recruit_hire_frame = ttk.Frame(notebook, padding=8)
        self.recruit_party_frame = ttk.Frame(notebook, padding=8)
        self.recruit_revive_frame = ttk.Frame(notebook, padding=8)
        notebook.add(self.recruit_hire_frame, text="Hire")
        notebook.add(self.recruit_party_frame, text="Party")
        notebook.add(self.recruit_revive_frame, text="Revive")

        recruit_actions = ttk.Frame(self.recruit_frame)
        recruit_actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(recruit_actions, text="Back to Arena", command=self.close_recruit, width=18).pack(side=tk.LEFT)

    def _build_embedded_admin_screen(self):
        """Admin tools as a full in-game screen (not a popup)."""
        self.admin_frame = ttk.Frame(self.root, padding=16)
        self.admin_frame.pack_forget()
        ttk.Label(self.admin_frame, text="Admin Mode", font=("Segoe UI", 18, "bold")).pack(pady=(8, 4))
        ttk.Label(
            self.admin_frame,
            text="Add custom items, mercenaries, enemies, and tune battle win bonuses.",
            wraplength=520,
        ).pack(pady=(0, 8))

        notebook = ttk.Notebook(self.admin_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=6)
        item_tab = ttk.Frame(notebook, padding=8)
        merc_tab = ttk.Frame(notebook, padding=8)
        enemy_tab = ttk.Frame(notebook, padding=8)
        bonus_tab = ttk.Frame(notebook, padding=8)
        notebook.add(item_tab, text="Items")
        notebook.add(merc_tab, text="Mercenaries")
        notebook.add(enemy_tab, text="Enemies")
        notebook.add(bonus_tab, text="Bonuses")

        item_form = ttk.Frame(item_tab)
        item_form.pack(fill=tk.X)
        self.admin_item_fields = {}
        for idx, (label, key, default) in enumerate(
            [
                ("ID", "id", "custom_item"),
                ("Name", "name", "Custom Blade"),
                ("Slot", "slot", "weapon"),
                ("Attack", "attack", "2"),
                ("Defense", "defense", "0"),
                ("Health", "health", "0"),
                ("Price", "price", "20"),
            ]
        ):
            ttk.Label(item_form, text=label).grid(row=idx, column=0, sticky="w", pady=2)
            var = tk.StringVar(value=default)
            self.admin_item_fields[key] = var
            ttk.Entry(item_form, textvariable=var, width=24).grid(row=idx, column=1, sticky="w", pady=2)
        ttk.Button(item_form, text="Add Item", command=self.admin_add_custom_item).grid(
            row=8, column=0, columnspan=2, pady=8
        )
        self.admin_items_list = self._build_admin_list_box(
            item_tab, "Existing Items", remove_command=self.admin_remove_selected_item
        )

        merc_form = ttk.Frame(merc_tab)
        merc_form.pack(fill=tk.X)
        self.admin_merc_fields = {}
        merc_defaults = [
            ("ID", "id", "custom_merc"),
            ("Name", "name", "Blade"),
            ("Race", "race", "Human"),
            ("Role", "role", "Fighter"),
            ("Attack", "attack", "5"),
            ("Defense", "defense", "3"),
            ("Health", "health", "24"),
            ("Ability Key", "ability", "swing"),
            ("Ability Desc", "ability_desc", "Strike: reliable attack."),
            ("AI Style", "ai_style", "balanced"),
        ]
        for idx, (label, key, default) in enumerate(merc_defaults):
            ttk.Label(merc_form, text=label).grid(row=idx, column=0, sticky="w", pady=2)
            var = tk.StringVar(value=default)
            self.admin_merc_fields[key] = var
            ttk.Entry(merc_form, textvariable=var, width=24).grid(row=idx, column=1, sticky="w", pady=2)
        ttk.Button(merc_form, text="Add Mercenary", command=self.admin_add_custom_merc).grid(
            row=len(merc_defaults), column=0, columnspan=2, pady=8
        )
        self.admin_mercs_list = self._build_admin_list_box(merc_tab, "Existing Mercenaries")

        enemy_form = ttk.Frame(enemy_tab)
        enemy_form.pack(fill=tk.X)
        self.admin_enemy_fields = {}
        enemy_defaults = [
            ("Name", "name", "Custom Fiend"),
            ("Flavor", "flavor", "A strange foe appears."),
            ("Min Level", "min_level", "1"),
            ("ATK Mod", "attack_mod", "0"),
            ("DEF Mod", "defense_mod", "0"),
            ("HP Mod", "health_mod", "0"),
            ("AI Style", "ai_style", "balanced"),
        ]
        for idx, (label, key, default) in enumerate(enemy_defaults):
            ttk.Label(enemy_form, text=label).grid(row=idx, column=0, sticky="w", pady=2)
            var = tk.StringVar(value=default)
            self.admin_enemy_fields[key] = var
            ttk.Entry(enemy_form, textvariable=var, width=28).grid(row=idx, column=1, sticky="w", pady=2)
        ttk.Button(enemy_form, text="Add Enemy Type", command=self.admin_add_custom_enemy).grid(
            row=len(enemy_defaults), column=0, columnspan=2, pady=8
        )
        self.admin_enemies_list = self._build_admin_list_box(
            enemy_tab, "Existing Monsters", remove_command=self.admin_remove_selected_enemy
        )

        bonus_form = ttk.Frame(bonus_tab)
        bonus_form.pack(fill=tk.X)
        ttk.Label(bonus_form, text="XP Multiplier").grid(row=0, column=0, sticky="w", pady=4)
        self.admin_xp_var = tk.StringVar(value=str(self.battle_bonuses.get("xp_multiplier", 1.0)))
        ttk.Entry(bonus_form, textvariable=self.admin_xp_var, width=10).grid(row=0, column=1, sticky="w")
        ttk.Label(bonus_form, text="Bonus Coins per Win").grid(row=1, column=0, sticky="w", pady=4)
        self.admin_coin_var = tk.StringVar(value=str(self.battle_bonuses.get("coin_bonus", 0)))
        ttk.Entry(bonus_form, textvariable=self.admin_coin_var, width=10).grid(row=1, column=1, sticky="w")
        ttk.Button(bonus_form, text="Save Bonuses", command=self.admin_save_bonuses).grid(
            row=3, column=0, columnspan=2, pady=12
        )
        self.admin_bonuses_list = self._build_admin_list_box(
            bonus_tab, "Current Bonuses", remove_command=self.admin_remove_selected_bonus
        )

        admin_actions = ttk.Frame(self.admin_frame)
        admin_actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(admin_actions, text="Back to Main Menu", command=self.close_admin_panel, width=18).pack(
            side=tk.LEFT
        )
        self.refresh_admin_lists()

    def _build_admin_list_box(self, parent, title, remove_command=None):
        section = ttk.LabelFrame(parent, text=title, padding=6)
        section.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        list_frame = ttk.Frame(section)
        list_frame.pack(fill=tk.BOTH, expand=True)
        list_box = tk.Listbox(list_frame, height=10, exportselection=False)
        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=list_box.yview)
        list_box.configure(yscrollcommand=scroll.set)
        list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        if remove_command is not None:
            ttk.Button(section, text="Remove Selected", command=remove_command).pack(anchor="w", pady=(6, 0))
        return list_box

    def _refresh_admin_listbox(self, widget, lines):
        widget.delete(0, tk.END)
        for line in lines:
            widget.insert(tk.END, line)
        if not lines:
            widget.insert(tk.END, "None yet.")

    def _format_admin_item_line(self, item):
        bits = []
        if item.get("attack"):
            bits.append(f"+{item['attack']} ATK")
        if item.get("defense"):
            bits.append(f"+{item['defense']} DEF")
        if item.get("health"):
            bits.append(f"+{item['health']} HP")
        detail = ", ".join(bits) if bits else "no bonus"
        custom = " (custom)" if item.get("id") not in {entry["id"] for entry in SHOP_EQUIPMENT} else ""
        return (
            f"{item['name']} [{item.get('id', '?')}] — {item['slot']} — "
            f"{item.get('price', 0)} coins — {detail}{custom}"
        )

    def _format_admin_merc_line(self, merc):
        custom = " (custom)" if merc.get("id") not in {entry["id"] for entry in MERCENARY_TEMPLATES} else ""
        return (
            f"{merc['name']} [{merc.get('id', '?')}] — {merc['race']} {merc['role']} — "
            f"ATK {merc['attack']} DEF {merc['defense']} HP {merc['health']} — "
            f"{merc.get('ability_desc', merc.get('ability', ''))}{custom}"
        )

    def _format_admin_enemy_line(self, enemy):
        custom = " (custom)" if enemy["name"] not in {entry["name"] for entry in ENEMY_THEMES} else ""
        return (
            f"{enemy['name']} — min lvl {enemy.get('min_level', 1)} — "
            f"ATK {enemy.get('attack_mod', 0):+d}, DEF {enemy.get('defense_mod', 0):+d}, "
            f"HP {enemy.get('health_mod', 0):+d} — {enemy.get('ai_style', 'balanced')}{custom}"
        )

    def refresh_admin_lists(self):
        if not hasattr(self, "admin_items_list"):
            return

        self._admin_items_entries = list(self.shop_equipment)
        self._refresh_admin_listbox(
            self.admin_items_list,
            [self._format_admin_item_line(item) for item in self._admin_items_entries],
        )
        self._refresh_admin_listbox(
            self.admin_mercs_list,
            [self._format_admin_merc_line(merc) for merc in self.mercenary_templates],
        )
        self._admin_enemies_entries = list(self.enemy_themes)
        self._refresh_admin_listbox(
            self.admin_enemies_list,
            [self._format_admin_enemy_line(enemy) for enemy in self._admin_enemies_entries],
        )
        self._admin_bonus_keys = ["xp_multiplier", "coin_bonus"]
        bonus_lines = [
            f"XP Multiplier: {self.battle_bonuses.get('xp_multiplier', 1.0)}",
            f"Bonus Coins per Win: {self.battle_bonuses.get('coin_bonus', 0)}",
        ]
        self._refresh_admin_listbox(self.admin_bonuses_list, bonus_lines)

    def admin_add_custom_item(self):
        try:
            entry = {
                "id": self.admin_item_fields["id"].get().strip(),
                "name": self.admin_item_fields["name"].get().strip(),
                "slot": self.admin_item_fields["slot"].get().strip(),
                "attack": int(self.admin_item_fields["attack"].get() or 0),
                "defense": int(self.admin_item_fields["defense"].get() or 0),
                "health": int(self.admin_item_fields["health"].get() or 0),
                "price": int(self.admin_item_fields["price"].get() or 10),
            }
        except ValueError:
            messagebox.showinfo("Admin", "Item stats must be numbers.")
            return
        if not entry["id"] or not entry["name"] or entry["slot"] not in EQUIPMENT_SLOTS:
            messagebox.showinfo("Admin", "Item needs id, name, and a valid equipment slot.")
            return
        custom = self._read_custom_file_lists()
        custom["custom_items"].append(entry)
        self.save_custom_content(**custom)
        self.refresh_admin_lists()
        messagebox.showinfo("Admin", f"Added item: {entry['name']}")

    def admin_add_custom_merc(self):
        try:
            entry = {
                "id": self.admin_merc_fields["id"].get().strip(),
                "name": self.admin_merc_fields["name"].get().strip(),
                "race": self.admin_merc_fields["race"].get().strip(),
                "role": self.admin_merc_fields["role"].get().strip(),
                "attack": int(self.admin_merc_fields["attack"].get()),
                "defense": int(self.admin_merc_fields["defense"].get()),
                "health": int(self.admin_merc_fields["health"].get()),
                "ability": self.admin_merc_fields["ability"].get().strip(),
                "ability_desc": self.admin_merc_fields["ability_desc"].get().strip(),
                "ai_style": self.admin_merc_fields["ai_style"].get().strip(),
            }
        except ValueError:
            messagebox.showinfo("Admin", "Mercenary stats must be numbers.")
            return
        if not entry["id"] or not entry["name"]:
            messagebox.showinfo("Admin", "Mercenary needs an id and name.")
            return
        custom = self._read_custom_file_lists()
        custom["custom_mercs"].append(entry)
        self.save_custom_content(**custom)
        self.refresh_admin_lists()
        messagebox.showinfo("Admin", f"Added mercenary: {entry['name']}")

    def admin_add_custom_enemy(self):
        try:
            entry = {
                "name": self.admin_enemy_fields["name"].get().strip(),
                "flavor": self.admin_enemy_fields["flavor"].get().strip(),
                "min_level": int(self.admin_enemy_fields["min_level"].get()),
                "attack_mod": int(self.admin_enemy_fields["attack_mod"].get()),
                "defense_mod": int(self.admin_enemy_fields["defense_mod"].get()),
                "health_mod": int(self.admin_enemy_fields["health_mod"].get()),
                "ai_style": self.admin_enemy_fields["ai_style"].get().strip(),
            }
        except ValueError:
            messagebox.showinfo("Admin", "Enemy mods must be numbers.")
            return
        if not entry["name"]:
            messagebox.showinfo("Admin", "Enemy needs a name.")
            return
        custom = self._read_custom_file_lists()
        custom["custom_enemies"].append(entry)
        self.save_custom_content(**custom)
        self.refresh_admin_lists()
        messagebox.showinfo("Admin", f"Added enemy: {entry['name']}")

    def admin_save_bonuses(self):
        try:
            self.battle_bonuses["xp_multiplier"] = float(self.admin_xp_var.get())
            self.battle_bonuses["coin_bonus"] = int(self.admin_coin_var.get())
        except ValueError:
            messagebox.showinfo("Admin", "Bonus values must be numeric.")
            return
        custom = self._read_custom_file_lists()
        self.save_custom_content(**custom)
        self.refresh_admin_lists()
        messagebox.showinfo("Admin", "Battle win bonuses updated.")

    def admin_remove_selected_item(self):
        selection = self.admin_items_list.curselection()
        if not selection:
            messagebox.showinfo("Admin", "Select an item to remove.")
            return
        item = self._admin_items_entries[selection[0]]
        item_id = item.get("id")
        if not item_id:
            return
        if not messagebox.askyesno("Admin", f"Remove item '{item['name']}' from the game?"):
            return

        custom = self._read_custom_file_lists()
        base_ids = {entry["id"] for entry in SHOP_EQUIPMENT}
        if item_id in base_ids:
            removed = list(custom["removed_shop_items"])
            if item_id not in removed:
                removed.append(item_id)
        else:
            custom["custom_items"] = [
                entry for entry in custom["custom_items"] if entry.get("id") != item_id
            ]
            removed = custom["removed_shop_items"]

        self.save_custom_content(
            custom["custom_items"],
            custom["custom_mercs"],
            custom["custom_enemies"],
            removed_shop_items=removed,
        )
        if self._embedded_screen_visible(self.shop_frame):
            self.refresh_shop_gear_list()
        self.refresh_admin_lists()
        messagebox.showinfo("Admin", f"Removed item: {item['name']}")

    def admin_remove_selected_enemy(self):
        selection = self.admin_enemies_list.curselection()
        if not selection:
            messagebox.showinfo("Admin", "Select a monster to remove.")
            return
        enemy = self._admin_enemies_entries[selection[0]]
        enemy_name = enemy.get("name")
        if not enemy_name:
            return
        if not messagebox.askyesno("Admin", f"Remove monster '{enemy_name}' from the game?"):
            return

        custom = self._read_custom_file_lists()
        base_names = {entry["name"] for entry in ENEMY_THEMES}
        if enemy_name in base_names:
            removed = list(custom["removed_enemies"])
            if enemy_name not in removed:
                removed.append(enemy_name)
        else:
            custom["custom_enemies"] = [
                entry for entry in custom["custom_enemies"] if entry.get("name") != enemy_name
            ]
            removed = custom["removed_enemies"]

        self.save_custom_content(
            custom["custom_items"],
            custom["custom_mercs"],
            custom["custom_enemies"],
            removed_enemies=removed,
        )
        self.refresh_admin_lists()
        messagebox.showinfo("Admin", f"Removed monster: {enemy_name}")

    def admin_remove_selected_bonus(self):
        selection = self.admin_bonuses_list.curselection()
        if not selection:
            messagebox.showinfo("Admin", "Select a bonus to remove.")
            return
        bonus_key = self._admin_bonus_keys[selection[0]]
        defaults = {"xp_multiplier": 1.0, "coin_bonus": 0}
        labels = {"xp_multiplier": "XP Multiplier", "coin_bonus": "Bonus Coins per Win"}
        current = self.battle_bonuses.get(bonus_key, defaults[bonus_key])
        default = defaults[bonus_key]
        if current == default:
            messagebox.showinfo("Admin", f"{labels[bonus_key]} is already at the default value.")
            return
        if not messagebox.askyesno("Admin", f"Reset {labels[bonus_key]} to default ({default})?"):
            return

        self.battle_bonuses[bonus_key] = default
        self.admin_xp_var.set(str(self.battle_bonuses["xp_multiplier"]))
        self.admin_coin_var.set(str(self.battle_bonuses["coin_bonus"]))
        custom = self._read_custom_file_lists()
        self.save_custom_content(
            custom["custom_items"],
            custom["custom_mercs"],
            custom["custom_enemies"],
            removed_shop_items=custom["removed_shop_items"],
            removed_enemies=custom["removed_enemies"],
        )
        self.refresh_admin_lists()
        messagebox.showinfo("Admin", f"Reset {labels[bonus_key]} to default.")

    def close_admin_panel(self):
        self.show_main_menu()

    def _embedded_screen_visible(self, frame):
        return bool(frame is not None and frame.winfo_manager())

    def _build_scrollable_list_frame(self, parent):
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(container, highlightthickness=0, bg="#D2B48C")
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def on_scroll_frame_configure(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfigure(window_id, width=event.width)

        scroll_frame.bind("<Configure>", on_scroll_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return scroll_frame

    def _shop_item_tab_key(self, slot):
        if slot in ("ring1", "ring2"):
            return "rings"
        return slot

    def refresh_shop_gear_list(self):
        """Rebuild the equipment list on the embedded shop screen."""
        if not hasattr(self, "shop_gear_tab_frames"):
            return

        grouped = {slot_key: [] for slot_key in self.shop_gear_tab_frames}
        for item in self.shop_equipment:
            tab_key = self._shop_item_tab_key(item.get("slot", ""))
            if tab_key in grouped:
                grouped[tab_key].append(item)

        for slot_key, frame in self.shop_gear_tab_frames.items():
            for child in frame.winfo_children():
                child.destroy()

            items = grouped.get(slot_key, [])
            if not items:
                ttk.Label(
                    frame,
                    text="No equipment available in this category.",
                    wraplength=420,
                ).pack(anchor="w")
                continue

            for item in items:
                detail = self.format_item_detail(item)
                row = ttk.Frame(frame)
                row.pack(fill=tk.X, pady=4)
                ttk.Label(
                    row,
                    text=f"{item['name']} — {item['price']} coins — {detail}",
                    wraplength=360,
                ).pack(side=tk.LEFT, anchor="w")
                ttk.Button(
                    row,
                    text=f"Buy ({item['price']})",
                    command=lambda gear=item: self.buy_equipment(gear),
                ).pack(side=tk.RIGHT, padx=(8, 0))

    def log(self, text):
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.configure(state=tk.DISABLED)
        self.log_box.see(tk.END)

    def get_race_bonuses(self):
        return RACES[self.selected_race]

    def get_equipment_bonuses(self):
        bonuses = {"attack": 0, "defense": 0, "health": 0}
        for item in self.equipment.values():
            if not item:
                continue
            bonuses["attack"] += item.get("attack", 0)
            bonuses["defense"] += item.get("defense", 0)
            bonuses["health"] += item.get("health", 0)
        return bonuses

    def compute_preview_stats(self):
        """Live preview during character creation (race + point allocation, no gear yet)."""
        race = self.get_race_bonuses()
        attack = BASE_ATTACK + self.creation_attack_points + race["attack"]
        defense = BASE_DEFENSE + self.creation_defense_points + race["defense"]
        health = BASE_HEALTH + self.creation_health_points * 5 + race["health"]
        return attack, defense, health

    def compute_player_stats(self):
        """Full runtime stats: base + race + allocation + run bonuses + equipment."""
        race = self.get_race_bonuses()
        gear = self.get_equipment_bonuses()
        attack = (
            BASE_ATTACK
            + self.creation_attack_points
            + race["attack"]
            + self.stat_bonuses["attack"]
            + gear["attack"]
        )
        defense = (
            BASE_DEFENSE
            + self.creation_defense_points
            + race["defense"]
            + self.stat_bonuses["defense"]
            + gear["defense"]
        )
        health = (
            BASE_HEALTH
            + self.creation_health_points * 5
            + race["health"]
            + self.stat_bonuses["health"]
            + gear["health"]
        )
        return attack, defense, health

    def apply_player_stats(self, heal_missing_max=False):
        """Push computed stats onto the live combatant, preserving current HP when possible."""
        old_max = self.player.max_health
        attack, defense, max_health = self.compute_player_stats()
        self.player.attack = attack
        self.player.defense = defense
        if heal_missing_max and max_health > old_max:
            self.player.health += max_health - old_max
        self.player.max_health = max_health
        self.player.health = min(self.player.health, self.player.max_health)

    def init_starting_equipment(self):
        """Equip the default starting loadout or gear from a saved build."""
        self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        if self.saved_equipment_from_build:
            for slot, item in self.saved_equipment_from_build.items():
                if slot in self.equipment and item:
                    self.equipment[slot] = dict(item)
        else:
            for item in STARTING_EQUIPMENT:
                self.equipment[item["slot"]] = dict(item)

    def add_to_inventory(self, item):
        self.inventory.append(dict(item))

    def remove_from_inventory(self, item):
        for idx, inv_item in enumerate(self.inventory):
            if inv_item is item:
                self.inventory.pop(idx)
                return True
        item_id = item.get("id")
        item_name = item.get("name")
        for idx, inv_item in enumerate(self.inventory):
            if inv_item.get("id") == item_id and inv_item.get("name") == item_name:
                self.inventory.pop(idx)
                return True
        return False

    def format_item_detail(self, item):
        bits = []
        if item.get("attack"):
            bits.append(f"+{item['attack']} ATK")
        if item.get("defense"):
            bits.append(f"+{item['defense']} DEF")
        if item.get("health"):
            bits.append(f"+{item['health']} HP")
        return ", ".join(bits) if bits else "no bonus"

    def equip_item(self, item):
        """Place an item into its slot, replacing anything already worn there."""
        slot = item["slot"]
        if slot == "ring1" and self.equipment["ring1"] and not self.equipment["ring2"]:
            slot = "ring2"
        elif slot == "ring1" and self.equipment["ring1"] and self.equipment["ring2"]:
            slot = "ring1"
        old = self.equipment.get(slot)
        self.equipment[slot] = dict(item)
        self.apply_player_stats(heal_missing_max=True)
        if old:
            self.add_to_inventory(old)
            self.log(f"You replace {old['name']} with {item['name']}.")
        else:
            self.log(f"You equip {item['name']}.")
        self.refresh_stats()

    def equip_from_inventory(self, item):
        if self.in_combat:
            messagebox.showinfo("Inventory", "You cannot change gear during an active duel.")
            return
        if not self.remove_from_inventory(item):
            messagebox.showinfo("Inventory", "That item is no longer in your inventory.")
            self.refresh_character_panel()
            return
        self.equip_item(item)
        self.refresh_character_panel()

    def equipment_summary_text(self):
        gear = self.get_equipment_bonuses()
        equipped_names = [item["name"] for item in self.equipment.values() if item]
        if not equipped_names:
            return "Gear: none"
        bonus_bits = []
        if gear["attack"]:
            bonus_bits.append(f"+{gear['attack']} ATK")
        if gear["defense"]:
            bonus_bits.append(f"+{gear['defense']} DEF")
        if gear["health"]:
            bonus_bits.append(f"+{gear['health']} HP")
        bonus_text = ", ".join(bonus_bits) if bonus_bits else "no bonuses"
        return f"Gear ({bonus_text}): {', '.join(equipped_names[:3])}" + (
            f" +{len(equipped_names) - 3} more" if len(equipped_names) > 3 else ""
        )

    def clear_mercenary_state(self):
        """Drop all hired and fallen mercenaries — used on new run / game over."""
        self.active_mercenaries = []
        self.fallen_mercenaries = []
        self.recruitment_pool = []

    def get_hired_template_ids(self):
        ids = {merc.template["id"] for merc in self.active_mercenaries}
        ids.update(merc.template["id"] for merc in self.fallen_mercenaries)
        return ids

    def refresh_recruitment_pool(self):
        """Roll a fresh hiring board excluding mercenaries already tied to this run."""
        hired_ids = self.get_hired_template_ids()
        available = [template for template in self.mercenary_templates if template["id"] not in hired_ids]
        count = min(RECRUITMENT_POOL_SIZE, len(available))
        self.recruitment_pool = random.sample(available, count) if count else []

    def refresh_mercenary_panel(self):
        """Update the compact mercenary strip on the battle screen."""
        for slot in range(MAX_ACTIVE_MERCENARIES):
            if slot < len(self.active_mercenaries):
                merc = self.active_mercenaries[slot]
                if merc.fallen:
                    label = f"{merc.name} ({merc.role}) — FALLEN"
                    hp_text = "Fallen — revive at Recruit"
                    action_text = merc.ability_desc
                    bar_max, bar_val = merc.max_health, 0
                else:
                    label = f"{merc.name} ({merc.race} {merc.role})"
                    hp_text = f"HP: {merc.health} / {merc.max_health}  ATK {merc.attack}  DEF {merc.defense}"
                    action_text = f"Last: {merc.last_action}"
                    bar_max, bar_val = merc.max_health, max(0, merc.health)
            else:
                label = "Empty slot"
                hp_text = "Visit Recruit between fights"
                action_text = ""
                bar_max, bar_val = 1, 0
            self.merc_name_vars[slot].set(label)
            self.merc_health_vars[slot].set(hp_text)
            self.merc_action_vars[slot].set(action_text)
            self.merc_bars[slot]["maximum"] = max(1, bar_max)
            self.merc_bars[slot]["value"] = bar_val

    def open_recruit(self):
        if self.in_combat:
            self.log("You cannot recruit during an active duel.")
            return
        if not self.recruitment_pool:
            self.refresh_recruitment_pool()
        self.hide_all_screens()
        self.recruit_frame.pack(fill=tk.BOTH, expand=True)
        self.refresh_recruit_window()

    def refresh_recruit_window(self):
        if not hasattr(self, "recruit_frame"):
            return
        self.recruit_coins_var.set(f"Coins: {self.coins}")

        for frame in (self.recruit_hire_frame, self.recruit_party_frame, self.recruit_revive_frame):
            for child in frame.winfo_children():
                child.destroy()

        if not self.recruitment_pool:
            ttk.Label(
                self.recruit_hire_frame,
                text="No mercenaries available right now. Close and reopen after the next victory.",
                wraplength=420,
            ).pack(anchor="w")
        else:
            for template in self.recruitment_pool:
                cost = mercenary_hire_cost(template)
                detail = (
                    f"{template['name']} — {template['race']} {template['role']} | "
                    f"ATK {template['attack']} DEF {template['defense']} HP {template['health']} | "
                    f"{template['ability_desc']}"
                )
                row = ttk.Frame(self.recruit_hire_frame)
                row.pack(fill=tk.X, pady=4)
                ttk.Label(row, text=detail, wraplength=420).pack(anchor="w")
                can_hire = len(self.active_mercenaries) < MAX_ACTIVE_MERCENARIES and self.coins >= cost
                ttk.Button(
                    row,
                    text=f"Hire for {cost} coins",
                    command=lambda tpl=template: self.hire_mercenary(tpl),
                    state=tk.NORMAL if can_hire else tk.DISABLED,
                ).pack(anchor="w", pady=(2, 0))

        if not self.active_mercenaries:
            ttk.Label(self.recruit_party_frame, text="No mercenaries hired yet.").pack(anchor="w")
        else:
            for merc in self.active_mercenaries:
                status = "Fallen" if merc.fallen else f"{merc.health}/{merc.max_health} HP"
                ttk.Label(
                    self.recruit_party_frame,
                    text=f"{merc.name} ({merc.race} {merc.role}) — {status} — {merc.ability_desc}",
                    wraplength=420,
                ).pack(anchor="w", pady=2)

        if not self.fallen_mercenaries:
            ttk.Label(self.recruit_revive_frame, text="No fallen mercenaries to revive.").pack(anchor="w")
        else:
            for merc in self.fallen_mercenaries:
                cost = mercenary_revive_cost(merc)
                row = ttk.Frame(self.recruit_revive_frame)
                row.pack(fill=tk.X, pady=4)
                ttk.Label(
                    row,
                    text=f"{merc.name} ({merc.role}) — revive for {cost} coins at half health",
                    wraplength=420,
                ).pack(anchor="w")
                can_revive = (
                    len(self.active_mercenaries) < MAX_ACTIVE_MERCENARIES and self.coins >= cost
                )
                ttk.Button(
                    row,
                    text=f"Revive {merc.name}",
                    command=lambda m=merc: self.revive_mercenary(m),
                    state=tk.NORMAL if can_revive else tk.DISABLED,
                ).pack(anchor="w", pady=(2, 0))

    def hire_mercenary(self, template):
        if self.in_combat:
            return
        if len(self.active_mercenaries) >= MAX_ACTIVE_MERCENARIES:
            messagebox.showinfo("Recruit", "Your party is full. Revive or finish the run before hiring more.")
            return
        cost = mercenary_hire_cost(template)
        if self.coins < cost:
            messagebox.showinfo("Recruit", "You do not have enough coins.")
            return

        self.coins -= cost
        merc = Mercenary(template)
        self.active_mercenaries.append(merc)
        self.recruitment_pool = [tpl for tpl in self.recruitment_pool if tpl["id"] != template["id"]]
        self.log(f"You hire {merc.name} the {merc.race} {merc.role} for {cost} coins.")
        self.refresh_stats()
        self.refresh_recruit_window()

    def revive_mercenary(self, mercenary):
        if self.in_combat:
            return
        if len(self.active_mercenaries) >= MAX_ACTIVE_MERCENARIES:
            messagebox.showinfo("Recruit", "Dismiss a living mercenary or wait for a slot to open.")
            return
        cost = mercenary_revive_cost(mercenary)
        if self.coins < cost:
            messagebox.showinfo("Recruit", "You do not have enough coins.")
            return

        self.coins -= cost
        mercenary.fallen = False
        mercenary.health = max(1, mercenary.max_health // 2)
        mercenary.ability_cooldown = 0
        mercenary.last_action = "Revived"
        if mercenary not in self.active_mercenaries:
            self.active_mercenaries.append(mercenary)
        self.fallen_mercenaries = [m for m in self.fallen_mercenaries if m is not mercenary]
        self.log(f"You revive {mercenary.name} for {cost} coins ({mercenary.health} HP).")
        self.refresh_stats()
        self.refresh_recruit_window()

    def close_recruit(self):
        if self.run_started:
            self.show_battle_screen()
            if self.in_preparation and not self.awaiting_reward:
                self.status_var.set("Ready to engage")
                self.phase_info_var.set(
                    "Preparation phase — Shop and Recruit are open. Strike first when you are ready."
                )
        else:
            self.show_main_menu()

    def mercenary_choice(self, mercenary):
        """Simple AI: role-aware swing / block / ability selection."""
        if mercenary.ability_cooldown <= 0:
            if mercenary.ai_style == "support" and (
                self.player.health < self.player.max_health * 0.6
                or any(m.alive() and m.health < m.max_health * 0.5 for m in self.active_mercenaries)
            ):
                return "ability"
            if mercenary.ai_style == "defensive" and mercenary.health <= mercenary.max_health * 0.35:
                return random.choice(["block", "ability"])
            if mercenary.ai_style == "aggressive" and self.enemy.health > 8:
                return random.choice(["swing", "swing", "ability"])
            if mercenary.ai_style == "tricky" and self.enemy.health < self.enemy.max_health * 0.5:
                return random.choice(["ability", "swing"])
        if mercenary.health <= mercenary.max_health * 0.3:
            return random.choice(["block", "block", "swing"])
        if mercenary.ai_style == "defensive":
            return random.choice(["block", "swing", "block"])
        if mercenary.ai_style == "support":
            return random.choice(["block", "swing"])
        return random.choice(["swing", "swing", "block"])

    def apply_mercenary_ability(self, mercenary):
        """Resolve a mercenary's special ability and set cooldown."""
        ability = mercenary.ability
        if ability == "fortify":
            mercenary.health = min(mercenary.max_health, mercenary.health + 3)
            mercenary.last_action = "Fortify (+3 HP)"
            self.log(f"{mercenary.name} fortifies and recovers 3 HP.")
        elif ability == "volley":
            damage = max(2, mercenary.attack - max(0, self.enemy.defense - 2))
            self.enemy.health -= damage
            mercenary.last_action = f"Volley ({damage} dmg)"
            self.log(f"{mercenary.name} looses a volley for {damage} damage!")
        elif ability == "fury":
            damage = max(2, self.compute_damage(mercenary.to_combatant(), self.enemy) + 4)
            self.enemy.health -= damage
            if random.random() < 0.45:
                counter = self.compute_damage(self.enemy, mercenary.to_combatant())
                mercenary.health -= counter
                self.log(
                    f"{mercenary.name} rages for {damage} damage but takes {counter} in return!"
                )
            else:
                self.log(f"{mercenary.name} unleashes fury for {damage} damage!")
            mercenary.last_action = f"Fury ({damage} dmg)"
        elif ability == "mend":
            targets = [self.player] + [m for m in self.active_mercenaries if m.alive() and m is not mercenary]
            target = min(targets, key=lambda unit: unit.health / unit.max_health)
            healed = min(6, target.max_health - target.health)
            target.health += healed
            who = "you" if target is self.player else target.name
            mercenary.last_action = f"Mend ({who} +{healed})"
            self.log(f"{mercenary.name} mends {who} for {healed} HP.")
        elif ability == "ambush":
            bonus = 3 if self.enemy.health < self.enemy.max_health * 0.5 else 0
            damage = max(1, self.compute_damage(mercenary.to_combatant(), self.enemy) + bonus)
            self.enemy.health -= damage
            mercenary.last_action = f"Ambush ({damage} dmg)"
            self.log(f"{mercenary.name} strikes from the shadows for {damage} damage!")
        elif ability == "shield_wall":
            mercenary.last_action = "Shield Wall"
            self.log(f"{mercenary.name} raises a shield wall — your next hit is softened.")
            self._player_damage_reduction_next = True
        elif ability == "arc_bolt":
            damage = 5
            self.enemy.health -= damage
            mercenary.last_action = f"Arc Bolt ({damage} dmg)"
            self.log(f"{mercenary.name} casts Arc Bolt for {damage} damage!")
        mercenary.ability_cooldown = 2

    def resolve_mercenary_turns(self):
        """After the player's exchange, each living mercenary acts with simple AI."""
        if not any(merc.alive() for merc in self.active_mercenaries):
            return

        self.log("Your mercenaries press the attack...")
        for mercenary in self.active_mercenaries:
            if not mercenary.alive() or self.enemy.health <= 0:
                continue

            action = self.mercenary_choice(mercenary)
            if action == "ability" and mercenary.ability_cooldown > 0:
                action = random.choice(["swing", "block"])
            if action == "ability":
                self.apply_mercenary_ability(mercenary)
            elif action == "swing":
                damage = self.compute_damage(mercenary.to_combatant(), self.enemy)
                self.enemy.health -= damage
                mercenary.last_action = f"Swing ({damage} dmg)"
                self.log(f"{mercenary.name} swings for {damage} damage.")
                if random.random() < 0.4:
                    counter = self.compute_damage(self.enemy, mercenary.to_combatant())
                    mercenary.health -= counter
                    self.log(f"{self.enemy.enemy_type} clips {mercenary.name} for {counter} damage!")
            else:
                mercenary.last_action = "Block"
                self.log(f"{mercenary.name} holds position and braces.")

            if mercenary.health <= 0 and not mercenary.fallen:
                mercenary.fallen = True
                mercenary.health = 0
                mercenary.last_action = "Fallen"
                self.fallen_mercenaries.append(mercenary)
                self.active_mercenaries = [m for m in self.active_mercenaries if not m.fallen]
                self.log(f"{mercenary.name} has fallen in battle!")

            if mercenary.ability_cooldown > 0 and action != "ability":
                mercenary.ability_cooldown -= 1

    def apply_mercenary_rest_heal(self):
        for mercenary in self.active_mercenaries:
            if mercenary.alive():
                healed = min(MERCENARY_REST_HEAL, mercenary.max_health - mercenary.health)
                if healed:
                    mercenary.health += healed

    def hide_all_screens(self):
        for frame_name in (
            "menu_frame",
            "creation_frame",
            "main_frame",
            "shop_frame",
            "recruit_frame",
            "admin_frame",
        ):
            frame = getattr(self, frame_name, None)
            if frame is not None:
                frame.pack_forget()

    def update_admin_button_visibility(self):
        """Keep the standalone Admin Mode button visible on the main menu."""
        if not hasattr(self, "admin_btn"):
            return
        if not self.admin_btn.winfo_manager():
            self.admin_btn.pack(pady=(10, 4))

    def show_main_menu(self):
        self.hide_all_screens()
        self.in_preparation = False
        self.awaiting_first_strike = False
        self.menu_frame.pack(fill=tk.BOTH, expand=True)
        self.update_admin_button_visibility()
        self.update_menu_buttons()

    def update_save_run_buttons(self):
        """Sync Save Run button state on the menu and battle footer."""
        can_save_run = self.run_started and self.player.alive()
        state = tk.NORMAL if can_save_run else tk.DISABLED
        if hasattr(self, "save_run_btn"):
            self.save_run_btn.configure(state=state)
        if hasattr(self, "save_run_footer_btn"):
            self.save_run_footer_btn.configure(state=state)

    def update_menu_buttons(self):
        if hasattr(self, "save_build_btn"):
            self.save_build_btn.configure(state=tk.NORMAL if self.build_active else tk.DISABLED)
        self.update_save_run_buttons()
        if hasattr(self, "load_run_btn"):
            self.load_run_btn.configure(
                state=tk.NORMAL if os.path.exists(self.run_save_path) else tk.DISABLED
            )
        if self.run_started and self.player.alive():
            self.menu_status_var.set("Run in progress. Load Run to resume, or start a New Build.")
        elif self.build_active:
            self.menu_status_var.set("Build ready. New Build, Load Build, Save Build, or begin a run.")
        else:
            self.menu_status_var.set("Create or load a build, or load a saved run.")

    def hide_battle_screen(self):
        if hasattr(self, "main_frame"):
            self.main_frame.pack_forget()

    def show_battle_screen(self):
        self.hide_all_screens()
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def close_auxiliary_windows(self):
        for attr in ("character_window", "game_over_window"):
            window = getattr(self, attr, None)
            if window is not None and window.winfo_exists():
                window.destroy()
            setattr(self, attr, None)

    def _prompt_save_run_before_leave(self, title, prompt):
        if self.run_started and self.player.alive():
            choice = messagebox.askyesnocancel(title, prompt)
            if choice is None:
                return False
            if choice and not self.save_run_to_file(show_message=True):
                return False
        return True

    def return_to_main_menu(self):
        if not self._prompt_save_run_before_leave("Main Menu", "Save Run before leaving?"):
            return
        self._finish_return_to_main_menu()

    def _finish_return_to_main_menu(self):
        self.close_auxiliary_windows()
        self.cancel_scheduled_fight()
        self.in_combat = False
        self.in_preparation = False
        self.awaiting_first_strike = False
        self.set_action_buttons_for_phase()
        self.show_main_menu()

    def start_new_build(self):
        self.creation_points_left = 15
        self.creation_attack_points = 0
        self.creation_defense_points = 0
        self.creation_health_points = 0
        self.selected_race = "Human"
        if hasattr(self, "race_var"):
            self.race_var.set(self.selected_race)
        self.show_character_creation_screen()

    def quit_game(self):
        if not self._prompt_save_run_before_leave("Quit", "Save Run before quitting?"):
            return
        self.root.destroy()

    def build_build_save_data(self):
        """Full character build: race, point allocation, and current equipment."""
        return {
            "version": BUILD_SAVE_VERSION,
            "race": self.selected_race,
            "attack": self.creation_attack_points,
            "defense": self.creation_defense_points,
            "health": self.creation_health_points,
            "equipment": {slot: (dict(item) if item else None) for slot, item in self.equipment.items()},
        }

    def save_build_to_file(self, show_message=True):
        if not self.build_active:
            if show_message:
                messagebox.showinfo("Save Build", "Create or load a build before saving.")
            return False
        data = self.build_build_save_data()
        try:
            with open(self.build_save_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
            # Legacy simple file for backward compatibility.
            with open(self.save_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "race": data["race"],
                        "attack": data["attack"],
                        "defense": data["defense"],
                        "health": data["health"],
                    },
                    handle,
                    indent=2,
                )
        except OSError as exc:
            if show_message:
                messagebox.showerror("Save Build", f"Could not save build:\n{exc}")
            return False
        if show_message:
            messagebox.showinfo("Build Saved", f"Build saved to {os.path.basename(self.build_save_path)}.")
        return True

    def mercenary_to_dict(self, mercenary):
        return {
            "template_id": mercenary.template["id"],
            "health": mercenary.health,
            "max_health": mercenary.max_health,
            "ability_cooldown": mercenary.ability_cooldown,
            "fallen": mercenary.fallen,
            "last_action": mercenary.last_action,
        }

    def mercenary_from_dict(self, data):
        template = get_mercenary_template(data["template_id"], self.mercenary_templates)
        if not template:
            return None
        mercenary = Mercenary(template)
        mercenary.health = data.get("health", mercenary.health)
        mercenary.max_health = data.get("max_health", mercenary.max_health)
        mercenary.ability_cooldown = data.get("ability_cooldown", 0)
        mercenary.fallen = data.get("fallen", False)
        mercenary.last_action = data.get("last_action", "—")
        return mercenary

    def enemy_to_dict(self):
        return {
            "name": self.enemy.name,
            "attack": self.enemy.attack,
            "defense": self.enemy.defense,
            "health": self.enemy.health,
            "max_health": self.enemy.max_health,
            "level": self.enemy.level,
            "flavor": self.enemy.flavor,
            "ai_style": self.enemy.ai_style,
            "enemy_type": self.enemy.enemy_type,
        }

    def enemy_from_dict(self, data):
        enemy = Combatant(
            data["name"],
            data["attack"],
            data["defense"],
            data.get("max_health", data["health"]),
            level=data["level"],
            flavor=data.get("flavor", ""),
            ai_style=data.get("ai_style", "balanced"),
            enemy_type=data.get("enemy_type", ""),
        )
        enemy.health = data["health"]
        return enemy

    def build_run_save_data(self):
        return {
            "version": RUN_SAVE_VERSION,
            "build": {
                "race": self.selected_race,
                "attack": self.creation_attack_points,
                "defense": self.creation_defense_points,
                "health": self.creation_health_points,
            },
            "run": {
                "player_level": self.player_level,
                "player_xp": self.player_xp,
                "coins": self.coins,
                "enemy_level": self.enemy_level,
                "stat_bonuses": dict(self.stat_bonuses),
                "power_strike_cooldown": self.power_strike_cooldown,
                "next_enemy_wounded": self.next_enemy_wounded,
                "player_health": self.player.health,
                "equipment": {slot: (dict(item) if item else None) for slot, item in self.equipment.items()},
                "inventory": [dict(item) for item in self.inventory],
                "active_mercenaries": [self.mercenary_to_dict(m) for m in self.active_mercenaries],
                "fallen_mercenaries": [self.mercenary_to_dict(m) for m in self.fallen_mercenaries],
                "recruitment_pool": [t["id"] for t in self.recruitment_pool],
                "enemy": self.enemy_to_dict(),
                "awaiting_reward": self.awaiting_reward,
            },
        }

    def save_run_to_file(self, show_message=True):
        if not self.run_started or not self.player.alive():
            if show_message:
                messagebox.showinfo("Save Run", "Start a run and survive before saving progress.")
            return False
        try:
            with open(self.run_save_path, "w", encoding="utf-8") as handle:
                json.dump(self.build_run_save_data(), handle, indent=2)
        except OSError as exc:
            if show_message:
                messagebox.showerror("Save Run", f"Could not save run:\n{exc}")
            return False
        self.update_menu_buttons()
        if show_message:
            messagebox.showinfo("Run Saved", f"Run saved to {os.path.basename(self.run_save_path)}.")
        return True

    def apply_run_save_data(self, data):
        build = data.get("build", {})
        run = data.get("run", {})
        race = build.get("race", "Human")
        if race not in RACES:
            race = "Human"
        self.selected_race = race
        self.creation_attack_points = int(build.get("attack", 0))
        self.creation_defense_points = int(build.get("defense", 0))
        self.creation_health_points = int(build.get("health", 0))
        self.creation_points_left = 0
        self.build_active = True
        self.stat_bonuses = {
            "attack": int(run.get("stat_bonuses", {}).get("attack", 0)),
            "defense": int(run.get("stat_bonuses", {}).get("defense", 0)),
            "health": int(run.get("stat_bonuses", {}).get("health", 0)),
        }
        self.equipment = {slot: None for slot in EQUIPMENT_SLOTS}
        for slot, item in run.get("equipment", {}).items():
            if slot in self.equipment and item:
                self.equipment[slot] = dict(item)
        self.inventory = [dict(item) for item in run.get("inventory", [])]
        self.player = Combatant(f"{self.selected_race} Warrior", BASE_ATTACK, BASE_DEFENSE, BASE_HEALTH)
        self.apply_player_stats()
        self.player.health = max(1, min(int(run.get("player_health", self.player.max_health)), self.player.max_health))
        self.player_level = int(run.get("player_level", 1))
        self.player_xp = int(run.get("player_xp", 0))
        self.coins = int(run.get("coins", 10))
        self.enemy_level = int(run.get("enemy_level", 1))
        self.power_strike_cooldown = int(run.get("power_strike_cooldown", 0))
        self.next_enemy_wounded = bool(run.get("next_enemy_wounded", False))
        self.awaiting_reward = bool(run.get("awaiting_reward", False))
        self.enemy = self.enemy_from_dict(run["enemy"])
        self.active_mercenaries = []
        for merc_data in run.get("active_mercenaries", []):
            merc = self.mercenary_from_dict(merc_data)
            if merc:
                self.active_mercenaries.append(merc)
        self.fallen_mercenaries = []
        for merc_data in run.get("fallen_mercenaries", []):
            merc = self.mercenary_from_dict(merc_data)
            if merc:
                self.fallen_mercenaries.append(merc)
        pool_ids = run.get("recruitment_pool", [])
        self.recruitment_pool = [
            get_mercenary_template(template_id, self.mercenary_templates)
            for template_id in pool_ids
            if get_mercenary_template(template_id, self.mercenary_templates)
        ]
        self.in_combat = False
        self.in_preparation = False
        self.awaiting_first_strike = False
        self._player_damage_reduction_next = False
        self.cancel_scheduled_fight()

    def load_run_from_file(self):
        if not os.path.exists(self.run_save_path):
            messagebox.showinfo("No Run Found", "No saved run was found yet.")
            return
        try:
            with open(self.run_save_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except OSError as exc:
            messagebox.showerror("Load Run", f"Could not read the save file:\n{exc}")
            return
        except json.JSONDecodeError as exc:
            messagebox.showerror("Load Run", f"The saved run file is corrupt or malformed:\n{exc}")
            return
        if not isinstance(data, dict):
            messagebox.showerror("Load Run", "The saved run file is corrupt or malformed.")
            return
        if data.get("version") != RUN_SAVE_VERSION:
            messagebox.showinfo("Load Run", "This save file is from an incompatible version.")
            return
        build = data.get("build", {})
        if not isinstance(build, dict):
            messagebox.showerror("Load Run", "The saved run file is missing a valid build section.")
            return
        try:
            total = int(build.get("attack", 0)) + int(build.get("defense", 0)) + int(build.get("health", 0))
        except (TypeError, ValueError):
            messagebox.showerror("Load Run", "The saved run has a malformed build.")
            return
        if total != 15:
            messagebox.showinfo("Load Run", "The saved run has an invalid build.")
            return
        run = data.get("run")
        if not isinstance(run, dict) or "enemy" not in run:
            messagebox.showerror("Load Run", "The saved run file is missing required run data.")
            return
        try:
            self.apply_run_save_data(data)
        except (KeyError, TypeError, ValueError) as exc:
            messagebox.showerror("Load Run", f"The saved run file is corrupt or malformed:\n{exc}")
            return
        self.run_started = True
        self.update_menu_buttons()
        self.show_battle_screen()
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.delete(1.0, tk.END)
        self.log_box.configure(state=tk.DISABLED)
        self.log("Saved run loaded. You return to the arena.")
        if self.awaiting_reward:
            self.enter_preparation_phase()
            self.log("Choose your victory reward before preparing for the next duel.")
            self.show_victory_reward_dialog(self.build_reward_options())
        else:
            self.enter_preparation_phase(announce_opponent=True)
        messagebox.showinfo("Run Loaded", f"Run loaded from {os.path.basename(self.run_save_path)}.")

    def load_build_from_file(self):
        path = self.build_save_path if os.path.exists(self.build_save_path) else self.save_path
        if not os.path.exists(path):
            messagebox.showinfo("No Build Found", "No saved build was found yet.")
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except OSError as exc:
            messagebox.showerror("Load Build", f"Could not read the build file:\n{exc}")
            return
        except json.JSONDecodeError as exc:
            messagebox.showerror("Load Build", f"The saved build file is corrupt or malformed:\n{exc}")
            return
        if not isinstance(data, dict):
            messagebox.showerror("Load Build", "The saved build file is corrupt or malformed.")
            return
        try:
            attack = int(data.get("attack", 0))
            defense = int(data.get("defense", 0))
            health = int(data.get("health", 0))
        except (TypeError, ValueError):
            messagebox.showerror("Load Build", "The saved build file has malformed stat values.")
            return
        race = data.get("race", "Human")
        if race not in RACES:
            race = "Human"
        total = attack + defense + health
        if total != 15:
            messagebox.showinfo("Build Error", "The saved build is invalid; it must use 15 total points.")
            return
        self.selected_race = race
        self.creation_attack_points = attack
        self.creation_defense_points = defense
        self.creation_health_points = health
        self.creation_points_left = 0
        self.saved_equipment_from_build = None
        if data.get("version") == BUILD_SAVE_VERSION and "equipment" in data:
            equipment = data.get("equipment")
            if not isinstance(equipment, dict):
                messagebox.showerror("Load Build", "The saved build file has malformed equipment data.")
                return
            try:
                self.saved_equipment_from_build = {
                    slot: (dict(item) if item else None) for slot, item in equipment.items()
                }
            except (TypeError, ValueError):
                messagebox.showerror("Load Build", "The saved build file has malformed equipment data.")
                return
        self.build_active = True
        self.update_menu_buttons()
        self.confirm_character_creation()

    def show_character_creation_screen(self):
        self.hide_all_screens()
        self.creation_frame.pack(fill=tk.BOTH, expand=True)
        self.update_creation_screen()

    def on_race_changed(self, _event=None):
        self.selected_race = self.race_var.get()
        self.update_creation_screen()

    def adjust_creation_stat(self, stat, delta):
        if delta > 0 and self.creation_points_left <= 0:
            return
        if delta < 0:
            if stat == "attack" and self.creation_attack_points <= 0:
                return
            if stat == "defense" and self.creation_defense_points <= 0:
                return
            if stat == "health" and self.creation_health_points <= 0:
                return
        if delta > 0:
            self.creation_points_left -= 1
        else:
            self.creation_points_left += 1

        if stat == "attack":
            self.creation_attack_points += delta
        elif stat == "defense":
            self.creation_defense_points += delta
        else:
            self.creation_health_points += delta

        self.update_creation_screen()

    def update_creation_screen(self):
        if hasattr(self, "race_var"):
            self.selected_race = self.race_var.get()
        self.creation_points_var.set(f"Points left: {self.creation_points_left}")
        self.attack_points_var.set(str(self.creation_attack_points))
        self.defense_points_var.set(str(self.creation_defense_points))
        self.health_points_var.set(str(self.creation_health_points))
        self.race_desc_var.set(RACES[self.selected_race]["desc"])
        attack, defense, health = self.compute_preview_stats()
        self.preview_attack_var.set(f"Attack: {attack}")
        self.preview_defense_var.set(f"Defense: {defense}")
        self.preview_health_var.set(f"Max Health: {health}")

    def confirm_character_creation(self):
        if self.creation_points_left != 0:
            messagebox.showinfo("Build Incomplete", "Spend all 15 points before starting your run.")
            return

        self.reset_run_state()
        self.run_started = True
        self.build_active = True
        self.update_menu_buttons()
        self.show_battle_screen()
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.delete(1.0, tk.END)
        self.log_box.configure(state=tk.DISABLED)
        self.log(f"A new run begins as a {self.selected_race} warrior.")
        self.log("Your chosen build is ready. The arena calls your name.")
        self.log("Take your time in preparation — Shop and Recruit are open before each duel.")
        self.log("Combat begins when you choose your first move.")
        self.enter_preparation_phase(first_fight=True, announce_opponent=True)

    def reset_run_state(self):
        """Reset a run to the player's saved build allocation, race, and starting equipment."""
        self.stat_bonuses = {"attack": 0, "defense": 0, "health": 0}
        self.inventory = []
        self.init_starting_equipment()
        self.player = Combatant(f"{self.selected_race} Warrior", BASE_ATTACK, BASE_DEFENSE, BASE_HEALTH)
        self.apply_player_stats()
        self.player.health = self.player.max_health
        self.player_level = 1
        self.player_xp = 0
        self.enemy_level = 1
        self.coins = 10
        self.enemy = self.make_enemy(self.enemy_level)
        self.in_combat = False
        self.in_preparation = False
        self.awaiting_first_strike = False
        self.power_strike_cooldown = 0
        self.next_enemy_wounded = False
        self.awaiting_reward = False
        self._player_damage_reduction_next = False
        self.cancel_scheduled_fight()
        self.clear_mercenary_state()
        self.refresh_recruitment_pool()

    def open_character_panel(self):
        """Detailed character sheet: stats, gear, mercenaries, reset, and save."""
        if self.character_window is not None and self.character_window.winfo_exists():
            self.character_window.lift()
            self.refresh_character_panel()
            return

        self.character_window = tk.Toplevel(self.root)
        self.character_window.title("Character Sheet")
        self.character_window.geometry("520x560")
        self.character_window.transient(self.root)
        self.character_window.configure(bg="#D2B48C")

        ttk.Label(self.character_window, text="Character Sheet", font=("Segoe UI", 14, "bold")).pack(
            pady=(10, 4)
        )
        notebook = ttk.Notebook(self.character_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        overview_tab = ttk.Frame(notebook, padding=8)
        gear_tab = ttk.Frame(notebook, padding=8)
        inventory_tab = ttk.Frame(notebook, padding=8)
        merc_tab = ttk.Frame(notebook, padding=8)
        notebook.add(overview_tab, text="Overview")
        notebook.add(gear_tab, text="Equipment")
        notebook.add(inventory_tab, text="Inventory")
        notebook.add(merc_tab, text="Mercenaries")

        self.char_overview_var = tk.StringVar()
        ttk.Label(overview_tab, textvariable=self.char_overview_var, wraplength=460, justify="left").pack(
            anchor="nw"
        )

        self.equipment_slot_vars = {}
        for idx, slot in enumerate(EQUIPMENT_SLOTS):
            label = slot.replace("ring1", "Ring 1").replace("ring2", "Ring 2").title()
            row_var = tk.StringVar()
            self.equipment_slot_vars[slot] = row_var
            ttk.Label(gear_tab, textvariable=row_var, wraplength=440).grid(row=idx, column=0, sticky="w", pady=2)

        self.char_inventory_frame = ttk.LabelFrame(inventory_tab, text="Carried Items", padding=8)
        self.char_inventory_frame.pack(fill=tk.BOTH, expand=True)

        self.char_merc_var = tk.StringVar()
        ttk.Label(merc_tab, textvariable=self.char_merc_var, wraplength=440, justify="left").pack(anchor="nw")

        actions = ttk.Frame(self.character_window)
        actions.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(
            actions,
            text=f"Reset Stats ({RESET_STAT_COST} coins)",
            command=self.open_reset_stats_dialog,
        ).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Save Build", command=self.save_build_to_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Close", command=self.character_window.destroy).pack(side=tk.RIGHT, padx=4)
        self.refresh_character_panel()

    def refresh_character_panel(self):
        if self.character_window is None or not self.character_window.winfo_exists():
            return
        race = self.get_race_bonuses()
        gear = self.get_equipment_bonuses()
        base_atk = BASE_ATTACK + self.creation_attack_points + race["attack"]
        base_def = BASE_DEFENSE + self.creation_defense_points + race["defense"]
        base_hp = BASE_HEALTH + self.creation_health_points * 5 + race["health"]
        overview = (
            f"Race: {self.selected_race} — {race['desc']}\n\n"
            f"Point Allocation: {self.creation_attack_points} ATK / "
            f"{self.creation_defense_points} DEF / {self.creation_health_points} HP\n"
            f"Run Level: {self.player_level}  |  XP: {self.player_xp} / {self.player_level * 10}  |  "
            f"Coins: {self.coins}\n\n"
            f"Base (race + points): {base_atk} ATK / {base_def} DEF / {base_hp} HP\n"
            f"Run Bonuses: +{self.stat_bonuses['attack']} ATK / +{self.stat_bonuses['defense']} DEF / "
            f"+{self.stat_bonuses['health']} HP\n"
            f"Equipment: +{gear['attack']} ATK / +{gear['defense']} DEF / +{gear['health']} HP\n\n"
            f"TOTAL: {self.player.attack} ATK / {self.player.defense} DEF / "
            f"{self.player.health} / {self.player.max_health} HP"
        )
        self.char_overview_var.set(overview)
        for slot in EQUIPMENT_SLOTS:
            item = self.equipment.get(slot)
            label = slot.replace("ring1", "Ring 1").replace("ring2", "Ring 2").title()
            if item:
                bits = []
                if item.get("attack"):
                    bits.append(f"+{item['attack']} ATK")
                if item.get("defense"):
                    bits.append(f"+{item['defense']} DEF")
                if item.get("health"):
                    bits.append(f"+{item['health']} HP")
                bonus = f" ({', '.join(bits)})" if bits else ""
                self.equipment_slot_vars[slot].set(f"{label}: {item['name']}{bonus}")
            else:
                self.equipment_slot_vars[slot].set(f"{label}: Empty")
        merc_lines = []
        if self.active_mercenaries:
            for merc in self.active_mercenaries:
                status = "Fallen" if merc.fallen else f"{merc.health}/{merc.max_health} HP"
                merc_lines.append(
                    f"• {merc.name} ({merc.race} {merc.role}) — {status}\n  {merc.ability_desc}"
                )
        else:
            merc_lines.append("No active mercenaries. Hire allies at Recruit between fights.")
        if self.fallen_mercenaries:
            merc_lines.append("\nFallen (revivable):")
            for merc in self.fallen_mercenaries:
                merc_lines.append(f"• {merc.name} ({merc.role})")
        self.char_merc_var.set("\n".join(merc_lines))
        self.refresh_character_inventory()

    def refresh_character_inventory(self):
        if not hasattr(self, "char_inventory_frame"):
            return
        for child in self.char_inventory_frame.winfo_children():
            child.destroy()
        if not self.inventory:
            ttk.Label(
                self.char_inventory_frame,
                text="No items in inventory. Buy gear at the Shop or stash loot drops.",
                wraplength=420,
            ).pack(anchor="w")
            return
        equip_state = tk.DISABLED if self.in_combat else tk.NORMAL
        for item in self.inventory:
            detail = self.format_item_detail(item)
            row = ttk.Frame(self.char_inventory_frame)
            row.pack(fill=tk.X, pady=4)
            ttk.Label(
                row,
                text=f"{item['name']} ({item['slot']}) — {detail}",
                wraplength=320,
            ).pack(side=tk.LEFT, anchor="w")
            ttk.Button(
                row,
                text="Equip",
                command=lambda gear=item: self.equip_from_inventory(gear),
                state=equip_state,
            ).pack(side=tk.RIGHT, padx=(8, 0))

    def cancel_scheduled_fight(self):
        if self.fight_timer_id is not None:
            self.root.after_cancel(self.fight_timer_id)
            self.fight_timer_id = None

    def set_action_buttons_for_phase(self):
        """Enable combat buttons during active combat or when ready to strike first."""
        can_act = self.in_combat or self.awaiting_first_strike
        state = tk.NORMAL if can_act else tk.DISABLED
        self.swing_btn.configure(state=state)
        self.block_btn.configure(state=state)
        self.update_power_strike_button()

    def update_power_strike_button(self):
        can_act = self.in_combat or self.awaiting_first_strike
        if not can_act:
            self.power_btn.configure(state=tk.DISABLED)
            return
        if self.power_strike_cooldown > 0:
            self.power_btn.configure(state=tk.DISABLED)
            self.progress_cooldown_var.set(f"Power Strike: {self.power_strike_cooldown} turn(s)")
        else:
            self.power_btn.configure(state=tk.NORMAL)
            self.progress_cooldown_var.set("Power Strike: ready")

    def enter_preparation_phase(self, first_fight=False, announce_opponent=False):
        """Pre-battle phase: Shop and Recruit freely; combat starts on first strike."""
        self.cancel_scheduled_fight()
        self.in_combat = False
        self.in_preparation = True
        self.awaiting_first_strike = not self.awaiting_reward
        ready = not self.awaiting_reward
        self.shop_btn.configure(state=tk.NORMAL if ready else tk.DISABLED)
        self.recruit_btn.configure(state=tk.NORMAL if ready else tk.DISABLED)
        self.character_btn.configure(state=tk.NORMAL)
        self.play_again_btn.configure(state=tk.DISABLED)
        self.main_menu_btn.configure(state=tk.NORMAL)
        self.update_save_run_buttons()
        self.set_action_buttons_for_phase()
        self.refresh_stats()
        if self.awaiting_reward:
            self.status_var.set("Victory! Choose your reward.")
            self.phase_info_var.set("Pick a reward, then prepare at Shop or Recruit.")
        elif first_fight:
            self.status_var.set("Ready to engage")
            self.phase_info_var.set(
                f"{self.enemy.enemy_type} stands across the arena. "
                "Use Shop or Recruit, then choose your first move."
            )
        else:
            self.status_var.set("Ready to engage")
            self.phase_info_var.set(
                "Preparation phase — Shop and Recruit are open. "
                "Strike first when you are ready."
            )
        if announce_opponent and not self.awaiting_reward:
            self.log(f"\n{self.enemy.enemy_type} awaits your challenge.")
            if self.enemy.flavor:
                self.log(self.enemy.flavor)

    def begin_combat(self):
        """Start the duel when the player chooses their first move."""
        if self.in_combat or not self.awaiting_first_strike:
            return
        self.in_preparation = False
        self.awaiting_first_strike = False
        if self.next_enemy_wounded:
            wound = max(1, int(self.enemy.max_health * 0.25))
            self.enemy.health = max(1, self.enemy.health - wound)
            self.log(f"Your opening strike wounds {self.enemy.enemy_type} for {wound} HP before the fight!")
            self.next_enemy_wounded = False
        self.in_combat = True
        self.shop_btn.configure(state=tk.DISABLED)
        self.recruit_btn.configure(state=tk.DISABLED)
        for mercenary in self.active_mercenaries:
            if mercenary.alive():
                mercenary.last_action = "Ready"
        self.set_action_buttons_for_phase()
        self.status_var.set(f"Duel underway against {self.enemy.enemy_type}.")
        self.phase_info_var.set("Mercenaries act automatically after your move each turn.")
        self.log(f"\nYou engage {self.enemy.enemy_type}!")
        self.refresh_stats()

    def open_shop(self):
        if self.in_combat:
            self.log("You cannot shop during an active duel.")
            return
        self.shop_coins_var.set(f"Coins: {self.coins}")
        self.refresh_shop_gear_list()
        self.hide_all_screens()
        self.shop_frame.pack(fill=tk.BOTH, expand=True)

    def buy_health_salve(self):
        if self.in_combat:
            return
        if self.coins < 10:
            messagebox.showinfo("Shop", "You do not have enough coins for that.")
            return
        if self.player.health >= self.player.max_health:
            messagebox.showinfo("Shop", "You are already at full health.")
            return

        self.coins -= 10
        heal_amount = min(12, self.player.max_health - self.player.health)
        self.player.health += heal_amount
        self.refresh_stats()
        if self._embedded_screen_visible(self.shop_frame):
            self.shop_coins_var.set(f"Coins: {self.coins}")
        self.log(f"You buy a Health Salve and recover {heal_amount} HP.")

    def buy_iron_tonic(self):
        if self.in_combat:
            return
        if self.coins < 15:
            messagebox.showinfo("Shop", "You do not have enough coins for that.")
            return

        self.coins -= 15
        self.stat_bonuses["defense"] += 1
        self.apply_player_stats(heal_missing_max=True)
        self.refresh_stats()
        if self._embedded_screen_visible(self.shop_frame):
            self.shop_coins_var.set(f"Coins: {self.coins}")
        self.log("You drink an Iron Tonic and gain +1 Defense for this run.")

    def buy_equipment(self, item):
        if self.in_combat:
            return
        if self.coins < item["price"]:
            messagebox.showinfo("Shop", "You do not have enough coins for that.")
            return

        self.coins -= item["price"]
        self.add_to_inventory(item)
        self.log(f"You buy {item['name']} — added to inventory.")
        if self._embedded_screen_visible(self.shop_frame):
            self.shop_coins_var.set(f"Coins: {self.coins}")
        self.refresh_character_panel()

    def close_shop(self):
        if self.run_started:
            self.show_battle_screen()
            if self.in_preparation and not self.awaiting_reward:
                self.status_var.set("Ready to engage")
                self.phase_info_var.set(
                    "Preparation phase — Shop and Recruit are open. Strike first when you are ready."
                )
        else:
            self.show_main_menu()

    def show_game_over_screen(self):
        if self.game_over_window is not None and self.game_over_window.winfo_exists():
            self.game_over_window.lift()
            return

        self.game_over_window = tk.Toplevel(self.root)
        self.game_over_window.title("Game Over")
        self.game_over_window.geometry("320x180")
        self.game_over_window.transient(self.root)
        self.game_over_window.grab_set()
        self.game_over_window.configure(bg="#D2B48C")

        ttk.Label(self.game_over_window, text="Game Over", font=("Segoe UI", 16, "bold")).pack(pady=(12, 8))
        ttk.Label(
            self.game_over_window,
            text=f"You reached enemy level {self.enemy_level}.\nStart a new run to climb again.",
        ).pack(pady=(0, 10))
        ttk.Button(self.game_over_window, text="Start New Run", command=self.start_new_run).pack()

    def start_new_run(self):
        if self.game_over_window is not None and self.game_over_window.winfo_exists():
            self.game_over_window.destroy()
            self.game_over_window = None
        self.reset_run_state()
        self.run_started = True
        self.show_battle_screen()
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.delete(1.0, tk.END)
        self.log_box.configure(state=tk.DISABLED)
        self.log("A fresh run begins.")
        self.log("The arena is ready for another climb.")
        self.enter_preparation_phase(first_fight=True, announce_opponent=True)

    def refresh_stats(self):
        self.player_health_var.set(f"HP: {self.player.health} / {self.player.max_health}")
        self.enemy_health_var.set(f"HP: {self.enemy.health} / {self.enemy.max_health}")
        self.player_stats_var.set(f"Attack {self.player.attack}  Defense {self.player.defense}")
        self.player_equipment_var.set(self.equipment_summary_text())
        self.enemy_stats_var.set(f"Attack {self.enemy.attack}  Defense {self.enemy.defense}")
        self.enemy_banner_var.set(f"{self.enemy.enemy_type}  —  Level {self.enemy.level}")
        style_label = self.enemy.ai_style.replace("bruiser", "Bruiser").replace("tricky", "Tricky Skirmisher")
        style_label = style_label.replace("aggressive", "Aggressive Striker").replace("balanced", "Balanced Fighter")
        self.enemy_type_var.set(f"Type: {style_label}")
        self.progress_level_var.set(f"Level: {self.player_level}")
        self.progress_xp_var.set(f"XP: {self.player_xp} / {self.player_level * 10}")
        self.progress_coins_var.set(f"Coins: {self.coins}")
        self.progress_race_var.set(f"Race: {self.selected_race}")
        self.update_power_strike_button()
        self.player_bar["maximum"] = self.player.max_health
        self.player_bar["value"] = max(0, self.player.health)
        self.enemy_bar["maximum"] = self.enemy.max_health
        self.enemy_bar["value"] = max(0, self.enemy.health)
        self.refresh_character_panel()
        self.refresh_mercenary_panel()
        self.root.update_idletasks()

    def pick_enemy_theme(self, level):
        eligible = [theme for theme in self.enemy_themes if theme["min_level"] <= level]
        if level <= 2:
            pool = [theme for theme in eligible if theme["min_level"] <= 2]
        elif level <= 4:
            pool = [theme for theme in eligible if theme["min_level"] <= 4]
        else:
            pool = eligible
        return random.choice(pool or eligible)

    def make_enemy(self, level):
        theme = self.pick_enemy_theme(level)
        attack = max(1, 6 + level + theme["attack_mod"])
        defense = max(0, 2 + (level - 1) // 2 + theme["defense_mod"])
        health = max(8, 24 + level * 5 + theme["health_mod"])
        return Combatant(
            f"{theme['name']} (Lv {level})",
            attack,
            defense,
            health,
            level=level,
            flavor=theme["flavor"],
            ai_style=theme["ai_style"],
            enemy_type=theme["name"],
        )

    def show_level_up_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Level Up")
        dialog.geometry("320x160")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text=f"You reached level {self.player_level}!", font=("Segoe UI", 12, "bold")).pack(
            pady=(12, 6)
        )
        ttk.Label(dialog, text="Choose one stat to strengthen:").pack(pady=(0, 10))

        def choose(stat):
            if stat == "attack":
                self.stat_bonuses["attack"] += 1
                self.log("You sharpen your blade and gain +1 Attack.")
            elif stat == "defense":
                self.stat_bonuses["defense"] += 1
                self.log("You fortify your guard and gain +1 Defense.")
            else:
                self.stat_bonuses["health"] += 5
                self.log("You harden your body and gain +5 Max Health.")
            self.apply_player_stats(heal_missing_max=True)
            self.refresh_stats()
            dialog.destroy()

        button_row = ttk.Frame(dialog)
        button_row.pack()
        ttk.Button(button_row, text="Attack +1", command=lambda: choose("attack")).pack(side=tk.LEFT, padx=4)
        ttk.Button(button_row, text="Defense +1", command=lambda: choose("defense")).pack(side=tk.LEFT, padx=4)
        ttk.Button(button_row, text="Health +5", command=lambda: choose("health")).pack(side=tk.LEFT, padx=4)

    def check_level_up(self):
        while self.player_xp >= self.player_level * 10:
            self.player_xp -= self.player_level * 10
            self.player_level += 1
            self.stat_bonuses["health"] += 2
            self.apply_player_stats(heal_missing_max=True)
            self.log(f"\nLevel up! You are now level {self.player_level} (+2 Max HP).")
            self.show_level_up_dialog()
            self.refresh_stats()

    def build_reward_options(self):
        pool = [
            ("Sharpened Steel", "+2 Attack", "attack", 2),
            ("Reinforced Mail", "+1 Defense", "defense", 1),
            ("Vitality Charm", "+10 Max HP and heal 10", "health", 10),
            ("Lucky Purse", "+8 coins", "coins", 8),
            ("Healing Draught", "Restore 15 HP", "heal", 15),
            ("Ambush Tactics", "Next foe starts wounded", "wound", 0),
        ]
        return random.sample(pool, 3)

    def show_victory_reward_dialog(self, options):
        dialog = tk.Toplevel(self.root)
        dialog.title("Victory Reward")
        dialog.geometry("380x220")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(dialog, text="Choose your reward", font=("Segoe UI", 12, "bold")).pack(pady=(12, 6))
        ttk.Label(dialog, text="Each victory shapes your run differently.").pack(pady=(0, 10))

        def apply_reward(option):
            label, detail, key, value = option
            if key == "attack":
                self.stat_bonuses["attack"] += value
                self.log(f"Reward: {label} — {detail}.")
            elif key == "defense":
                self.stat_bonuses["defense"] += value
                self.log(f"Reward: {label} — {detail}.")
            elif key == "health":
                self.stat_bonuses["health"] += value
                self.log(f"Reward: {label} — {detail}.")
            elif key == "coins":
                self.coins += value
                self.log(f"Reward: {label} — {detail}.")
            elif key == "heal":
                healed = min(value, self.player.max_health - self.player.health)
                self.player.health += healed
                self.log(f"Reward: {label} — you recover {healed} HP.")
            elif key == "wound":
                self.next_enemy_wounded = True
                self.log(f"Reward: {label} — {detail}.")
            if key in {"attack", "defense", "health"}:
                self.apply_player_stats(heal_missing_max=True)
            self.awaiting_reward = False
            self.refresh_stats()
            dialog.destroy()
            self.maybe_offer_loot_drop()

        for option in options:
            label, detail, _, _ = option
            ttk.Button(
                dialog, text=f"{label}: {detail}", command=lambda opt=option: apply_reward(opt)
            ).pack(fill=tk.X, padx=40, pady=4)

    def take_turn(self, player_action):
        if self.awaiting_first_strike:
            self.begin_combat()
        if not self.in_combat:
            return
        if player_action == "power" and self.power_strike_cooldown > 0:
            return

        enemy_action = self.enemy_choice(player_action)
        action_names = {"swing": "swing", "block": "block", "power": "power strike"}
        self.log(f"\nYou choose to {action_names[player_action]}.")
        self.log(f"{self.enemy.enemy_type} chooses to {enemy_action}.")

        if player_action == "power":
            self.resolve_power_strike(enemy_action)
            self.power_strike_cooldown = POWER_STRIKE_COOLDOWN
        elif player_action == "swing" and enemy_action == "swing":
            player_hits = self.compute_damage(self.player, self.enemy)
            enemy_hits = self.compute_damage(self.enemy, self.player)
            if self._player_damage_reduction_next:
                enemy_hits = max(1, enemy_hits - 3)
                self._player_damage_reduction_next = False
                self.log("Shield Wall softens the enemy riposte!")
            self.enemy.health -= player_hits
            self.player.health -= enemy_hits
            self.log(f"Your blade lands for {player_hits} damage.")
            self.log(f"The enemy ripostes for {enemy_hits} damage.")
        elif player_action == "swing" and enemy_action == "block":
            player_hits = self.compute_damage(self.player, self.enemy, blocked=True)
            self.enemy.health -= player_hits
            self.log(f"Your strike slips through for {player_hits} damage.")
            self.log("The enemy braces and softens the blow.")
        elif player_action == "block" and enemy_action == "swing":
            enemy_hits = self.compute_damage(self.enemy, self.player, blocked=True)
            if self._player_damage_reduction_next:
                enemy_hits = max(1, enemy_hits - 2)
                self._player_damage_reduction_next = False
                self.log("Shield Wall further reduces the blow!")
            self.player.health -= enemy_hits
            self.log(f"The enemy lunges for {enemy_hits} damage.")
            self.log("You raise your guard and take less punishment.")
        else:
            self.player.health -= STALEMATE_CHIP_DAMAGE
            self.enemy.health -= STALEMATE_CHIP_DAMAGE
            self.log("Both warriors hold their ground — a tense stalemate chips away resolve.")
            self.log(f"Each fighter takes {STALEMATE_CHIP_DAMAGE} wear-and-tear damage.")

        if self.power_strike_cooldown > 0 and player_action != "power":
            self.power_strike_cooldown -= 1

        if self.enemy.health > 0 and self.player.health > 0:
            self.resolve_mercenary_turns()

        self.refresh_stats()

        if self.enemy.health <= 0:
            self.finish_match(victory=True)
        elif self.player.health <= 0:
            self.finish_match(victory=False)
        else:
            self.status_var.set("Another exchange begins.")

    def resolve_power_strike(self, enemy_action):
        power_hits = self.compute_power_damage(self.player, self.enemy, enemy_action == "block")
        self.enemy.health -= power_hits
        self.log(f"You unleash a crushing blow for {power_hits} damage!")

        if enemy_action == "swing":
            enemy_hits = self.compute_damage(self.enemy, self.player)
            if self._player_damage_reduction_next:
                enemy_hits = max(1, enemy_hits - 3)
                self._player_damage_reduction_next = False
                self.log("Shield Wall absorbs part of the counterattack!")
            self.player.health -= enemy_hits
            self.log(f"You are wide open — the enemy punishes you for {enemy_hits} damage!")
        elif enemy_action == "block":
            self.log("The enemy braces, but your power still breaks through.")
        else:
            self.player.health -= STALEMATE_CHIP_DAMAGE
            self.log("You overextend while the enemy holds back, taking 1 wear-and-tear damage.")

    def enemy_choice(self, player_action=None):
        if player_action == "power":
            return random.choice(["swing", "swing", "block"])
        if self.enemy.health <= 8:
            return random.choice(["block", "block", "swing"])
        if self.player.health <= 10:
            return random.choice(["swing", "swing", "block"])

        style = self.enemy.ai_style
        if style == "aggressive":
            return random.choice(["swing", "swing", "swing", "block"])
        if style == "tricky":
            return random.choice(["block", "block", "swing", "block"])
        if style == "bruiser":
            return random.choice(["swing", "swing", "block", "block"])
        return random.choice(["swing", "swing", "block"])

    def compute_damage(self, attacker, defender, blocked=False):
        base = max(1, attacker.attack - defender.defense)
        if blocked:
            return max(1, base - BLOCK_DAMAGE_REDUCTION)
        return base

    def compute_power_damage(self, attacker, defender, enemy_blocked):
        base = max(1, attacker.attack - defender.defense) + POWER_STRIKE_BONUS
        if enemy_blocked:
            return max(1, base - BLOCK_DAMAGE_REDUCTION // 2)
        return base

    def apply_rest_heal(self):
        if self.player.health < self.player.max_health:
            healed = min(REST_HEAL_BETWEEN_FIGHTS, self.player.max_health - self.player.health)
            self.player.health += healed
            self.log(f"You catch your breath and recover {healed} HP.")
        self.apply_mercenary_rest_heal()

    def finish_match(self, victory):
        if victory:
            xp_mult = float(self.battle_bonuses.get("xp_multiplier", 1.0))
            coin_bonus = int(self.battle_bonuses.get("coin_bonus", 0))
            xp_gain = max(1, int(self.enemy.level * xp_mult))
            coin_gain = 5 + coin_bonus
            self.player_xp += xp_gain
            self.coins += coin_gain
            remaining_hp = self.player.health
            self.log(
                f"\nVictory over {self.enemy.enemy_type}! You gain {xp_gain} XP and {coin_gain} coins. "
                f"You remain at {remaining_hp}/{self.player.max_health} HP."
            )
            self.check_level_up()
            self.apply_rest_heal()
            self.refresh_recruitment_pool()
            self.enemy_level += 1
            self.enemy = self.make_enemy(self.enemy_level)
            self.awaiting_reward = True
            self.enter_preparation_phase()
            self.log(f"A stronger challenger awaits: {self.enemy.enemy_type}.")
            reward_options = self.build_reward_options()
            self.show_victory_reward_dialog(reward_options)
        else:
            self.cancel_scheduled_fight()
            self.in_combat = False
            self.in_preparation = False
            self.awaiting_first_strike = False
            self.set_action_buttons_for_phase()
            self.play_again_btn.configure(state=tk.NORMAL)
            self.shop_btn.configure(state=tk.DISABLED)
            self.recruit_btn.configure(state=tk.DISABLED)
            self.character_btn.configure(state=tk.DISABLED)
            self.main_menu_btn.configure(state=tk.NORMAL)
            self.update_save_run_buttons()
            self.status_var.set("Defeat: your warrior falls.")
            self.log("\nDefeat! Your warrior is brought down.")
            if self.active_mercenaries or self.fallen_mercenaries:
                self.log("Your mercenaries scatter — hire anew on the next run.")
            self.show_game_over_screen()


    # --- Custom content, admin tools, stat reset, and loot drops ---

    def load_custom_content(self):
        """Load admin-created items, mercenaries, enemies, and battle bonuses."""
        if not os.path.exists(self.custom_content_path):
            return
        try:
            with open(self.custom_content_path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return
        custom_items = data.get("shop_items", [])
        custom_mercs = data.get("mercenaries", [])
        custom_enemies = data.get("enemies", [])
        removed_items = set(data.get("removed_shop_items", []))
        removed_enemies = set(data.get("removed_enemies", []))
        base_items = [item for item in SHOP_EQUIPMENT if item["id"] not in removed_items]
        base_enemies = [enemy for enemy in ENEMY_THEMES if enemy["name"] not in removed_enemies]
        self.shop_equipment = merge_custom_lists(base_items, custom_items)
        self.mercenary_templates = merge_custom_lists(MERCENARY_TEMPLATES, custom_mercs)
        self.enemy_themes = merge_custom_lists(base_enemies, custom_enemies, key="name")
        bonuses = data.get("battle_bonuses", {})
        self.battle_bonuses = {
            "xp_multiplier": float(bonuses.get("xp_multiplier", 1.0)),
            "coin_bonus": int(bonuses.get("coin_bonus", 0)),
        }

    def save_custom_content(
        self,
        custom_items,
        custom_mercs,
        custom_enemies,
        removed_shop_items=None,
        removed_enemies=None,
    ):
        """Persist admin additions to game_custom.json."""
        existing = self._load_custom_file_raw()
        payload = {
            "shop_items": custom_items,
            "mercenaries": custom_mercs,
            "enemies": custom_enemies,
            "removed_shop_items": (
                removed_shop_items
                if removed_shop_items is not None
                else existing.get("removed_shop_items", [])
            ),
            "removed_enemies": (
                removed_enemies if removed_enemies is not None else existing.get("removed_enemies", [])
            ),
            "battle_bonuses": self.battle_bonuses,
        }
        with open(self.custom_content_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        self.load_custom_content()

    def _load_custom_file_raw(self):
        if os.path.exists(self.custom_content_path):
            with open(self.custom_content_path, encoding="utf-8") as handle:
                return json.load(handle)
        return {}

    def on_menu_title_click(self, _event=None):
        """Hidden admin unlock: click the title three times."""
        self.title_click_count += 1
        if self.title_click_count >= ADMIN_CLICKS_REQUIRED:
            self.title_click_count = 0
            self.admin_unlocked = True
            self.update_admin_button_visibility()
            messagebox.showinfo("Admin Mode", "Admin Mode unlocked. Use the Admin Mode button on the menu.")

    def open_admin_panel(self):
        if not self.admin_unlocked:
            messagebox.showinfo("Admin Mode", "Admin Mode is locked.")
            return
        self.admin_xp_var.set(str(self.battle_bonuses.get("xp_multiplier", 1.0)))
        self.admin_coin_var.set(str(self.battle_bonuses.get("coin_bonus", 0)))
        self.hide_all_screens()
        self.admin_frame.pack(fill=tk.BOTH, expand=True)
        self.refresh_admin_lists()

    def _read_custom_file_lists(self):
        data = self._load_custom_file_raw()
        return {
            "custom_items": data.get("shop_items", []),
            "custom_mercs": data.get("mercenaries", []),
            "custom_enemies": data.get("enemies", []),
            "removed_shop_items": data.get("removed_shop_items", []),
            "removed_enemies": data.get("removed_enemies", []),
        }

    def open_reset_stats_dialog(self):
        """Spend coins to redistribute the original 15 stat points."""
        if self.in_combat:
            messagebox.showinfo("Reset Stats", "You cannot reset stats during combat.")
            return
        if self.coins < RESET_STAT_COST:
            messagebox.showinfo("Reset Stats", f"You need {RESET_STAT_COST} coins to reset stats.")
            return

        dialog = tk.Toplevel(self.character_window or self.root)
        dialog.title("Reset Stats")
        dialog.geometry("340x240")
        dialog.transient(self.root)
        dialog.grab_set()
        ttk.Label(
            dialog,
            text=f"Redistribute 15 points for {RESET_STAT_COST} coins.\nRace bonuses are kept.",
            wraplength=300,
        ).pack(pady=(10, 8))

        temp_attack = tk.IntVar(value=self.creation_attack_points)
        temp_defense = tk.IntVar(value=self.creation_defense_points)
        temp_health = tk.IntVar(value=self.creation_health_points)
        points_left = tk.IntVar(value=0)

        def refresh_points_label():
            left = 15 - temp_attack.get() - temp_defense.get() - temp_health.get()
            points_left.set(left)
            points_label.set(f"Points left: {left}")

        points_label = tk.StringVar()
        refresh_points_label()

        def adjust(stat, delta):
            left = points_left.get()
            if delta > 0 and left <= 0:
                return
            if stat == "attack" and temp_attack.get() + delta < 0:
                return
            if stat == "defense" and temp_defense.get() + delta < 0:
                return
            if stat == "health" and temp_health.get() + delta < 0:
                return
            if stat == "attack":
                temp_attack.set(temp_attack.get() + delta)
            elif stat == "defense":
                temp_defense.set(temp_defense.get() + delta)
            else:
                temp_health.set(temp_health.get() + delta)
            refresh_points_label()

        row = ttk.Frame(dialog)
        row.pack(pady=6)
        for idx, (label, var, stat) in enumerate(
            [("Attack", temp_attack, "attack"), ("Defense", temp_defense, "defense"), ("Health", temp_health, "health")]
        ):
            ttk.Label(row, text=label).grid(row=idx, column=0, padx=6)
            ttk.Label(row, textvariable=var, width=4).grid(row=idx, column=1)
            ttk.Button(row, text="-", width=3, command=lambda s=stat: adjust(s, -1)).grid(row=idx, column=2)
            ttk.Button(row, text="+", width=3, command=lambda s=stat: adjust(s, 1)).grid(row=idx, column=3)

        ttk.Label(dialog, textvariable=points_label, font=("Segoe UI", 10, "bold")).pack(pady=4)

        def confirm_reset():
            if points_left.get() != 0:
                messagebox.showinfo("Reset Stats", "Spend all 15 points before confirming.")
                return
            self.coins -= RESET_STAT_COST
            self.creation_attack_points = temp_attack.get()
            self.creation_defense_points = temp_defense.get()
            self.creation_health_points = temp_health.get()
            self.creation_points_left = 0
            self.apply_player_stats()
            self.player.health = min(self.player.health, self.player.max_health)
            self.log(f"You pay {RESET_STAT_COST} coins to reset and redistribute your stats.")
            self.refresh_stats()
            self.refresh_character_panel()
            dialog.destroy()

        ttk.Button(dialog, text="Confirm Reset", command=confirm_reset).pack(pady=8)

    def roll_loot_item(self):
        """Pick a random droppable item from the shop pool."""
        pool = [dict(item) for item in self.shop_equipment if item.get("slot")]
        if not pool:
            return None
        item = dict(random.choice(pool))
        item.setdefault("id", item["name"].lower().replace(" ", "_"))
        return item

    def item_sell_value(self, item):
        return max(3, int(item.get("price", 12) * 0.55))

    def maybe_offer_loot_drop(self):
        """Sometimes offer a loot item after the victory reward is chosen."""
        if random.random() < LOOT_DROP_CHANCE:
            item = self.roll_loot_item()
            if item:
                self.show_item_drop_dialog(item)
                return
        self.enter_preparation_phase(announce_opponent=True)

    def show_item_drop_dialog(self, item):
        dialog = tk.Toplevel(self.root)
        dialog.title("Item Drop")
        dialog.geometry("400x220")
        dialog.transient(self.root)
        dialog.grab_set()
        bits = []
        if item.get("attack"):
            bits.append(f"+{item['attack']} ATK")
        if item.get("defense"):
            bits.append(f"+{item['defense']} DEF")
        if item.get("health"):
            bits.append(f"+{item['health']} HP")
        detail = ", ".join(bits) if bits else "no bonus"
        sell_val = self.item_sell_value(item)
        ttk.Label(dialog, text="Loot Found!", font=("Segoe UI", 12, "bold")).pack(pady=(10, 4))
        ttk.Label(
            dialog,
            text=f"{item['name']} ({item['slot']}) — {detail}\nSell value: {sell_val} coins",
            wraplength=360,
        ).pack(pady=(0, 10))

        def finish_loot():
            dialog.destroy()
            self.enter_preparation_phase(announce_opponent=True)

        def equip_loot():
            self.equip_item(item)
            self.log(f"Loot equipped: {item['name']}.")
            finish_loot()

        def sell_loot():
            self.coins += sell_val
            self.log(f"You sell {item['name']} for {sell_val} coins.")
            self.refresh_stats()
            finish_loot()

        def stash_loot():
            self.add_to_inventory(item)
            self.log(f"Stashed {item['name']} in inventory.")
            finish_loot()

        def destroy_loot():
            self.log(f"You discard {item['name']}.")
            finish_loot()

        btn_row = ttk.Frame(dialog)
        btn_row.pack(pady=6)
        ttk.Button(btn_row, text="Equip", command=equip_loot, width=10).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Inventory", command=stash_loot, width=10).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text=f"Sell ({sell_val})", command=sell_loot, width=12).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Destroy", command=destroy_loot, width=10).pack(side=tk.LEFT, padx=4)


if __name__ == "__main__":
    root = tk.Tk()
    BattleApp(root)
    root.mainloop()