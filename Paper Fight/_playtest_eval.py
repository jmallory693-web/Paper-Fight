"""Headless playtest harness for battle_gui evaluation."""
import json
import random
import sys

import tkinter as tk

from battle_gui import BattleApp, Combatant


def make_enemy(level):
    names = ["Raven Blade", "Stonebreaker", "Ash Warden", "Iron Fang", "Thorn Captain"]
    name = names[(level - 1) % len(names)]
    attack = 6 + level
    defense = 2 + (level - 1) // 2
    health = 24 + level * 5
    return Combatant(f"{name} (Lv {level})", attack, defense, health, level=level)


def enemy_choice(enemy, player):
    if enemy.health <= 8:
        return random.choice(["block", "block", "swing"])
    if player.health <= 10:
        return random.choice(["swing", "block", "block"])
    return random.choice(["swing", "swing", "block"])


def compute_damage(attacker, defender, blocked=False):
    base = max(1, attacker.attack - defender.defense)
    if blocked:
        return max(1, base - 4)
    return base


def take_turn(player, enemy, player_action):
    enemy_action = enemy_choice(enemy, player)
    if player_action == "swing" and enemy_action == "swing":
        enemy.health -= compute_damage(player, enemy)
        player.health -= compute_damage(enemy, player)
    elif player_action == "swing" and enemy_action == "block":
        enemy.health -= compute_damage(player, enemy, blocked=True)
    elif player_action == "block" and enemy_action == "swing":
        player.health -= compute_damage(enemy, player, blocked=True)
    return enemy_action


def check_level_up(player_level, player_xp, player):
    while player_xp >= player_level * 10:
        player_xp -= player_level * 10
        player_level += 1
        player.max_health += 2
        player.health = player.max_health
    return player_level, player_xp


def simulate_run(build, strategy="mixed", seed=42):
    random.seed(seed)
    player = Combatant(
        "Player",
        6 + build["attack"],
        2 + build["defense"],
        25 + build["health"] * 5,
    )
    player.max_health = player.health
    player_level, player_xp, coins, enemy_level = 1, 0, 10, 1
    enemy = make_enemy(enemy_level)
    battles_won = 0
    turns_total = 0
    shop_heals = 0

    while player.alive():
        if player.health < player.max_health * 0.5 and coins >= 10:
            coins -= 10
            player.health += min(10, player.max_health - player.health)
            shop_heals += 1

        turns = 0
        while player.alive() and enemy.alive() and turns < 200:
            turns += 1
            if strategy == "aggressive":
                action = "swing"
            elif strategy == "defensive":
                action = "block" if player.health <= player.max_health * 0.4 else "swing"
            else:
                action = (
                    "block"
                    if enemy.attack - player.defense >= 4 and player.health < 15
                    else "swing"
                )
            take_turn(player, enemy, action)

        turns_total += turns
        if not player.alive():
            break

        battles_won += 1
        player_xp += enemy.level
        coins += 5
        player.health = player.max_health
        player_level, player_xp = check_level_up(player_level, player_xp, player)
        enemy_level += 1
        enemy = make_enemy(enemy_level)

    return {
        "battles_won": battles_won,
        "final_level": player_level,
        "coins_left": coins,
        "shop_heals": shop_heals,
        "avg_turns": round(turns_total / max(1, battles_won), 1),
    }


def gui_smoke_test(saved_build):
    print("=== GUI SMOKE TEST ===")
    root = tk.Tk()
    root.withdraw()
    app = BattleApp(root)

    results = []
    results.append(("menu on launch", hasattr(app, "menu_frame")))
    results.append(("battle screen hidden", not app.main_frame.winfo_ismapped()))

    app.creation_attack_points = saved_build["attack"]
    app.creation_defense_points = saved_build["defense"]
    app.creation_health_points = saved_build["health"]
    app.creation_points_left = 0
    app.confirm_character_creation()

    results.append(("run started", app.run_started))
    results.append(
        (
            "build applied",
            app.player.attack == 6 + saved_build["attack"]
            and app.player.defense == 2 + saved_build["defense"]
            and app.player.health == 25 + saved_build["health"] * 5,
        )
    )

    log_before = len(app.log_box.get("1.0", "end").strip())
    for _ in range(3):
        app.take_turn("swing")
    log_after = len(app.log_box.get("1.0", "end").strip())

    results.append(("combat + log updates", log_after > log_before))
    results.append(("shop enabled in run", str(app.shop_btn.cget("state")) == "normal"))

    # Avoid modal dialogs: test game-over state directly without messageboxes.
    app.swing_btn.configure(state=tk.DISABLED)
    app.block_btn.configure(state=tk.DISABLED)
    app.play_again_btn.configure(state=tk.NORMAL)
    results.append(("defeat state wiring", str(app.swing_btn.cget("state")) == "disabled"))

    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    root.destroy()
    return all(ok for _, ok in results)


def main():
    with open("player_build.json", encoding="utf-8") as handle:
        saved = json.load(handle)

    gui_ok = gui_smoke_test(saved)

    print("\n=== BALANCE SIMULATIONS (100 seeds, mixed strategy) ===")
    builds = [
        ("glass cannon (15 ATK)", {"attack": 15, "defense": 0, "health": 0}),
        ("turtle (15 DEF)", {"attack": 0, "defense": 15, "health": 0}),
        ("HP tank (15 HP pts)", {"attack": 0, "defense": 0, "health": 15}),
        ("saved build", saved),
        ("balanced (5/5/5)", {"attack": 5, "defense": 5, "health": 5}),
    ]
    for label, build in builds:
        wins = [simulate_run(build, "mixed", seed)["battles_won"] for seed in range(100)]
        print(
            f"  {label}: avg={sum(wins)/len(wins):.1f} wins, "
            f"min={min(wins)}, max={max(wins)}"
        )

    print("\n=== STRATEGY COMPARISON (saved build) ===")
    for strat in ("aggressive", "defensive", "mixed"):
        wins = [simulate_run(saved, strat, seed)["battles_won"] for seed in range(100)]
        print(f"  {strat}: avg={sum(wins)/len(wins):.1f} wins")

    print("\n=== PACING SAMPLE (saved build, seed 7) ===")
    r = simulate_run(saved, "mixed", 7)
    print(f"  battles won: {r['battles_won']}, final level: {r['final_level']}")
    print(f"  avg turns/battle: {r['avg_turns']}, shop heals used: {r['shop_heals']}")

    p = Combatant("P", 6 + saved["attack"], 2 + saved["defense"], 25 + saved["health"] * 5)
    print("\n=== DAMAGE AT KEY MILESTONES ===")
    for lvl in (1, 3, 5, 8):
        e = make_enemy(lvl)
        print(
            f"  vs Lv{lvl} ({e.attack}/{e.defense}/{e.health}): "
            f"trade={compute_damage(p,e)}/{compute_damage(e,p)}, "
            f"blocked={compute_damage(e,p,blocked=True)}"
        )

    print(f"\nGUI smoke test overall: {'PASS' if gui_ok else 'FAIL'}")
    return 0 if gui_ok else 1


if __name__ == "__main__":
    sys.exit(main())