"""Headless playtest: run several fights with mercenaries hired."""
import json
import random
import tkinter as tk

from battle_gui import BattleApp, Mercenary, mercenary_hire_cost


def fight_one_battle(app, max_turns=80):
    """Fight the current enemy until victory or defeat."""
    app.cancel_scheduled_fight()
    # Combat begins on the first take_turn call during preparation.
    turns = 0
    while app.in_combat and turns < max_turns:
        turns += 1
        if app.player.health <= app.player.max_health * 0.35:
            action = "block"
        elif app.power_strike_cooldown <= 0 and random.random() < 0.2:
            action = "power"
        else:
            action = "swing"
        app.take_turn(action)
        app.root.update()
    if app.player.health <= 0:
        return "defeat", turns
    if not app.in_combat and app.player.alive():
        return "victory", turns
    return "timeout", turns


def run_mercenary_playtest(seed=7):
    random.seed(seed)
    with open("player_build.json", encoding="utf-8") as handle:
        build = json.load(handle)

    root = tk.Tk()
    root.withdraw()
    app = BattleApp(root)

    app.selected_race = build.get("race", "Human")
    app.creation_attack_points = build["attack"]
    app.creation_defense_points = build["defense"]
    app.creation_health_points = build["health"]
    app.creation_points_left = 0
    app.confirm_character_creation()

    def auto_reward(options):
        label, detail, key, value = options[0]
        if key == "attack":
            app.stat_bonuses["attack"] += value
        elif key == "defense":
            app.stat_bonuses["defense"] += value
        elif key == "health":
            app.stat_bonuses["health"] += value
        elif key == "coins":
            app.coins += value
        elif key == "heal":
            app.player.health += min(value, app.player.max_health - app.player.health)
        elif key == "wound":
            app.next_enemy_wounded = True
        if key in {"attack", "defense", "health"}:
            app.apply_player_stats(heal_missing_max=True)
        app.awaiting_reward = False
        app.refresh_stats()
        app.enter_preparation_phase(announce_opponent=True)

    app.show_victory_reward_dialog = auto_reward
    app.show_level_up_dialog = lambda: None
    app.root.update()

    # Hire two mercenaries from the recruitment pool.
    hired = []
    for template in list(app.recruitment_pool)[:2]:
        cost = mercenary_hire_cost(template)
        app.coins = max(app.coins, cost)
        app.hire_mercenary(template)
        hired.append(template["name"])
    app.root.update()

    results = []
    for battle in range(5):
        if not app.player.alive():
            break
        outcome, turns = fight_one_battle(app)
        merc_status = [
            f"{m.name}:{m.health}/{m.max_health}{' (fallen)' if m.fallen else ''}"
            for m in app.active_mercenaries + app.fallen_mercenaries
        ]
        results.append(
            {
                "battle": battle + 1,
                "outcome": outcome,
                "turns": turns,
                "player_hp": app.player.health,
                "enemy_level": app.enemy_level,
                "coins": app.coins,
                "mercenaries": merc_status,
            }
        )
        if outcome != "victory":
            break
        app.cancel_scheduled_fight()
        app.root.update_idletasks()

    root.destroy()
    return hired, results


def run_gauntlet(seed):
    """Chain fights until defeat; returns summary stats."""
    random.seed(seed)
    with open("player_build.json", encoding="utf-8") as handle:
        build = json.load(handle)

    root = tk.Tk()
    root.withdraw()
    app = BattleApp(root)
    app.selected_race = build.get("race", "Human")
    app.creation_attack_points = build["attack"]
    app.creation_defense_points = build["defense"]
    app.creation_health_points = build["health"]
    app.creation_points_left = 0

    def auto_reward(options):
        key, value = options[0][2], options[0][3]
        if key == "attack":
            app.stat_bonuses["attack"] += value
        elif key == "defense":
            app.stat_bonuses["defense"] += value
        elif key == "health":
            app.stat_bonuses["health"] += value
        elif key == "coins":
            app.coins += value
        elif key == "heal":
            app.player.health += min(value, app.player.max_health - app.player.health)
        elif key == "wound":
            app.next_enemy_wounded = True
        if key in {"attack", "defense", "health"}:
            app.apply_player_stats(heal_missing_max=True)
        app.awaiting_reward = False
        app.refresh_stats()
        app.enter_preparation_phase(announce_opponent=True)

    app.show_victory_reward_dialog = auto_reward
    app.show_level_up_dialog = lambda: None
    app.confirm_character_creation()

    hired = []
    for template in list(app.recruitment_pool)[:2]:
        app.coins = max(app.coins, mercenary_hire_cost(template))
        app.hire_mercenary(template)
        hired.append(template["name"])

    app.cancel_scheduled_fight()
    app.begin_next_fight()
    turns = 0
    while app.player.alive() and turns < 250:
        turns += 1

        if app.player.health < app.player.max_health * 0.35:
            action = "block"
        elif app.power_strike_cooldown <= 0 and random.random() < 0.15:
            action = "power"
        else:
            action = "swing"
        app.take_turn(action)
        root.update()

    summary = {
        "seed": seed,
        "hired": hired,
        "wins": app.enemy_level - 1,
        "turns": turns,
        "coins": app.coins,
        "living": [m.name for m in app.active_mercenaries if m.alive()],
        "fallen": [m.name for m in app.fallen_mercenaries],
    }
    root.destroy()
    return summary


if __name__ == "__main__":
    print("=== MERCENARY PLAYTEST (single run) ===")
    hired, results = run_mercenary_playtest()
    print(f"Hired: {', '.join(hired)}")
    for row in results:
        print(
            f"  Battle {row['battle']}: {row['outcome']} in {row['turns']} turns | "
            f"player HP {row['player_hp']} | foe Lv {row['enemy_level']} | "
            f"coins {row['coins']} | party: {row['mercenaries']}"
        )

    print("\n=== MERCENARY GAUNTLET (5 seeds) ===")
    for seed in (7, 13, 42, 99, 2026):
        row = run_gauntlet(seed)
        print(
            f"  seed {row['seed']}: hired {row['hired']} | wins {row['wins']} | "
            f"turns {row['turns']} | coins {row['coins']} | "
            f"living {row['living']} | fallen {row['fallen']}"
        )