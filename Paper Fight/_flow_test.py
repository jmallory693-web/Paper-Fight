"""Verify preparation phase, first-strike combat, creation screen, and save/load run."""
import json
import os
import tkinter as tk

import battle_gui
from battle_gui import BattleApp


def mock_dialogs():
    battle_gui.messagebox.showinfo = lambda *args, **kwargs: None
    battle_gui.messagebox.askyesno = lambda *args, **kwargs: True
    battle_gui.messagebox.askyesnocancel = lambda *args, **kwargs: True


def test_creation_screen(app, root):
    app.start_new_build()
    root.update()
    creation_visible = bool(app.creation_frame.winfo_manager())
    menu_hidden = not app.menu_frame.winfo_manager()
    no_popup = not any(isinstance(w, tk.Toplevel) for w in root.winfo_children())
    return creation_visible and menu_hidden and no_popup


def test_preparation_and_first_strike(app, root):
    app.creation_attack_points = 5
    app.creation_defense_points = 5
    app.creation_health_points = 5
    app.creation_points_left = 0
    app.confirm_character_creation()
    root.update()
    prep_ok = app.in_preparation and app.awaiting_first_strike and not app.in_combat
    shop_ok = str(app.shop_btn.cget("state")) == "normal"
    swing_ok = str(app.swing_btn.cget("state")) == "normal"
    no_timer = app.fight_timer_id is None
    app.take_turn("swing")
    root.update()
    combat_ok = app.in_combat and not app.awaiting_first_strike
    return prep_ok, shop_ok, swing_ok, no_timer, combat_ok


def test_save_load_roundtrip(app, root, path):
    app.run_started = True
    app.build_active = True
    app.coins = 42
    app.player_level = 3
    app.player_xp = 7
    app.enemy_level = 4
    app.active_mercenaries = []
    app.fallen_mercenaries = []
    app.refresh_recruitment_pool()
    if app.recruitment_pool:
        tpl = app.recruitment_pool[0]
        app.coins = max(app.coins, 100)
        app.hire_mercenary(tpl)
    app.coins = 42
    app.save_run_to_file = lambda: None  # avoid messagebox path
    data = app.build_run_save_data()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    app2 = BattleApp(root)
    app2.run_save_path = path
    app2.load_run_from_file = BattleApp.load_run_from_file.__get__(app2, BattleApp)
    battle_gui.messagebox.showinfo = lambda *a, **k: None
    app2.load_run_from_file()
    root.update()
    return (
        app2.coins == 42,
        app2.player_level == 3,
        app2.enemy_level == 4,
        app2.in_preparation and app2.awaiting_first_strike,
        len(app2.active_mercenaries) == len(data["run"]["active_mercenaries"]),
    )


def test_footer_save_and_main_menu(app, root, run_path):
    app.run_save_path = run_path
    app.creation_attack_points = 5
    app.creation_defense_points = 5
    app.creation_health_points = 5
    app.creation_points_left = 0
    app.confirm_character_creation()
    root.update()
    footer_enabled = str(app.save_run_footer_btn.cget("state")) == "normal"
    app.coins = 77
    saved = app.save_run_to_file(show_message=False)
    root.update()
    with open(app.run_save_path, encoding="utf-8") as handle:
        data = json.load(handle)
    coins_saved = data["run"]["coins"] == 77

    battle_gui.messagebox.askyesnocancel = lambda *a, **k: True
    app.return_to_main_menu()
    root.update()
    on_menu = bool(app.menu_frame.winfo_manager())

    return footer_enabled, saved, coins_saved, on_menu


def main():
    mock_dialogs()
    root = tk.Tk()
    root.withdraw()
    app = BattleApp(root)

    results = []
    results.append(("creation is in-game screen", test_creation_screen(app, root)))

    # Fresh app for run flow after creation consumed the first app state.
    root.destroy()
    root = tk.Tk()
    root.withdraw()
    app = BattleApp(root)
    mock_dialogs()

    run_path = os.path.join(os.path.dirname(__file__), "_test_run_save.json")
    footer_ok, saved_ok, coins_ok, menu_ok = test_footer_save_and_main_menu(app, root, run_path)
    results.append(("footer save run enabled", footer_ok))
    results.append(("footer save run writes file", saved_ok))
    results.append(("footer save run coins correct", coins_ok))
    results.append(("main menu yes saves and exits", menu_ok))

    root.destroy()
    root = tk.Tk()
    root.withdraw()
    app = BattleApp(root)
    mock_dialogs()

    prep, shop, swing, no_timer, combat = test_preparation_and_first_strike(app, root)
    results.append(("preparation phase active", prep))
    results.append(("shop enabled in preparation", shop))
    results.append(("swing enabled before combat", swing))
    results.append(("no auto fight timer", no_timer))
    results.append(("first strike starts combat", combat))

    try:
        coins_ok, lvl_ok, enemy_ok, prep_ok, merc_ok = test_save_load_roundtrip(app, root, run_path)
        results.append(("save/load coins", coins_ok))
        results.append(("save/load level", lvl_ok))
        results.append(("save/load enemy level", enemy_ok))
        results.append(("load resumes preparation", prep_ok))
        results.append(("save/load mercenaries", merc_ok))
    finally:
        if os.path.exists(run_path):
            os.remove(run_path)

    print("=== FLOW TEST ===")
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    root.destroy()
    ok_all = all(ok for _, ok in results)
    print(f"\nOverall: {'PASS' if ok_all else 'FAIL'}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())