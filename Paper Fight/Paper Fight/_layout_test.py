"""Verify battle_gui layouts fit within standard window sizes."""
import json
import tkinter as tk

from battle_gui import BattleApp


def widget_bottom(widget):
    return widget.winfo_y() + widget.winfo_height()


def widget_right(widget):
    return widget.winfo_x() + widget.winfo_width()


def fits_parent(parent, child, margin=2):
    parent.update_idletasks()
    child.update_idletasks()
    return (
        child.winfo_x() >= -margin
        and child.winfo_y() >= -margin
        and widget_right(child) <= parent.winfo_width() + margin
        and widget_bottom(child) <= parent.winfo_height() + margin
    )


def check_battle_layout(app):
    app.show_battle_screen()
    app.root.update_idletasks()
    checks = [
        ("main_frame", app.main_frame),
        ("player_card", app.player_card),
        ("merc_panel", app.merc_panel),
        ("enemy_card", app.enemy_card),
        ("swing_btn", app.swing_btn),
        ("log_box", app.log_box),
        ("footer play_again", app.play_again_btn),
    ]
    results = []
    for name, widget in checks:
        ok = fits_parent(app.main_frame, widget)
        results.append((name, ok, widget.winfo_y(), widget_bottom(widget)))
    return results


def main():
    with open("player_build.json", encoding="utf-8") as handle:
        build = json.load(handle)

    root = tk.Tk()
    app = BattleApp(root)
    root.geometry("900x640")
    root.update_idletasks()

    print("=== LAYOUT TEST @ 900x640 ===")
    print(f"Root size: {root.winfo_width()}x{root.winfo_height()}")

    menu_ok = fits_parent(root, app.menu_frame)
    print(f"  Menu frame fits: {'PASS' if menu_ok else 'FAIL'}")

    app.selected_race = build.get("race", "Human")
    app.creation_attack_points = build["attack"]
    app.creation_defense_points = build["defense"]
    app.creation_health_points = build["health"]
    app.creation_points_left = 0
    app.confirm_character_creation()
    root.update_idletasks()

    battle_checks = check_battle_layout(app)
    all_battle_ok = True
    main_bottom = 0
    for name, ok, y, bottom in battle_checks:
        main_bottom = max(main_bottom, bottom)
        if not ok:
            all_battle_ok = False
        print(f"  {name}: {'PASS' if ok else 'FAIL'} (y={y}, bottom={bottom})")

    print(f"  main_frame content height: {main_bottom} / {app.main_frame.winfo_height()}")
    print(f"  Battle layout overall: {'PASS' if all_battle_ok else 'FAIL'}")

    app.open_shop()
    root.update_idletasks()
    shop_ok = app.shop_window.winfo_height() <= 500 and app.shop_window.winfo_width() <= 450
    print(f"  Shop window compact: {'PASS' if shop_ok else 'FAIL'} ({app.shop_window.winfo_width()}x{app.shop_window.winfo_height()})")
    app.close_shop()

    app.open_recruit()
    root.update_idletasks()
    recruit_ok = app.recruit_window.winfo_height() <= 540 and app.recruit_window.winfo_width() <= 500
    print(f"  Recruit window compact: {'PASS' if recruit_ok else 'FAIL'} ({app.recruit_window.winfo_width()}x{app.recruit_window.winfo_height()})")
    app.close_recruit()

    app.start_new_build()
    root.update_idletasks()
    creation_ok = app.creation_frame.winfo_height() <= root.winfo_height()
    print(
        f"  Creation screen fits: {'PASS' if creation_ok else 'FAIL'} "
        f"({app.creation_frame.winfo_width()}x{app.creation_frame.winfo_height()})"
    )

    root.destroy()
    ok = menu_ok and all_battle_ok and shop_ok and recruit_ok and creation_ok
    print(f"\nOverall: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())