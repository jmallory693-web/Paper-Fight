import random
import sys


class Warrior:
    def __init__(self, name, attack, defense, health):
        self.name = name
        self.attack = attack
        self.defense = defense
        self.health = health

    def is_alive(self):
        return self.health > 0


def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def display_state(player, enemy):
    print(f"\n{player.name}: HP {player.health} | ATK {player.attack} | DEF {player.defense}")
    print(f"{enemy.name}: HP {enemy.health} | ATK {enemy.attack} | DEF {enemy.defense}")


def resolve_attack(attacker, defender, blocked=False):
    base_damage = max(1, attacker.attack - defender.defense)
    if blocked:
        damage = max(1, base_damage - 4)
        print(f"{defender.name} braces against the blow and reduces the impact.")
    else:
        damage = base_damage
    return damage


def player_turn(player, enemy):
    while True:
        action = input("Choose your action: swing or block: ").strip().lower()
        if action in {"swing", "block"}:
            return action
        print("Enter either 'swing' or 'block'.")


def enemy_turn(player, enemy):
    # The enemy is not perfect; it mixes attacks and blocks with a slight bias toward aggression.
    choices = ["swing", "swing", "swing", "block"]
    return random.choice(choices)


def combat_round(player, enemy, player_action, enemy_action):
    print(f"\n{player.name} chooses to {player_action}.")
    print(f"{enemy.name} chooses to {enemy_action}.")

    if player_action == "swing" and enemy_action == "swing":
        player_damage = resolve_attack(player, enemy)
        enemy_damage = resolve_attack(enemy, player)
        enemy.health -= player_damage
        player.health -= enemy_damage
        print(f"{player.name} strikes for {player_damage} damage!")
        print(f"{enemy.name} counters for {enemy_damage} damage!")

    elif player_action == "swing" and enemy_action == "block":
        player_damage = resolve_attack(player, enemy, blocked=True)
        enemy.health -= player_damage
        print(f"{player.name} lands a hit for {player_damage} damage!")
        print(f"{enemy.name} raises a guard to soften the blow.")

    elif player_action == "block" and enemy_action == "swing":
        enemy_damage = resolve_attack(enemy, player, blocked=True)
        player.health -= enemy_damage
        print(f"{enemy.name} lunges in for {enemy_damage} damage!")
        print(f"{player.name} holds the line and reduces the impact.")

    else:  # both block
        print("Both warriors brace themselves, wary of the next exchange.")


def play_game():
    print_header("The Arena of Ash and Iron")
    print("You stand before a fierce enemy warrior in a ruined coliseum.")

    player = Warrior("Player Warrior", 8, 3, 24)
    enemy = Warrior("Enemy Warrior", 7, 2, 26)

    while True:
        display_state(player, enemy)

        player_action = player_turn(player, enemy)
        enemy_action = enemy_turn(player, enemy)
        combat_round(player, enemy, player_action, enemy_action)

        if not enemy.is_alive():
            print_header("Victory")
            print(f"{player.name} stands triumphant over {enemy.name}!")
            break
        if not player.is_alive():
            print_header("Defeat")
            print(f"{enemy.name} has crushed {player.name}.")
            break

    again = input("\nPlay again? (y/n): ").strip().lower()
    if again == "y":
        play_game()
    else:
        print("\nThe arena falls silent. Farewell.")
        sys.exit(0)


if __name__ == "__main__":
    play_game()
