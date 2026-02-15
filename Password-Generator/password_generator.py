#!/usr/bin/env python3
import argparse
import os
import random
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.gui_helpers import FieldSpec, build_form


def generate_password(min_length: int, numbers: bool = True, special_characters: bool = True) -> str:
    letters = string.ascii_letters
    digits = string.digits
    specials = string.punctuation

    characters = letters
    if numbers:
        characters += digits
    if special_characters:
        characters += specials

    pwd = ""

    meets_criteria = False
    has_number = False
    has_special_character = False
    while not meets_criteria or len(pwd) < min_length:
        new_char = random.choice(characters)
        pwd += new_char

        if new_char in digits:
            has_number = True
        elif new_char in specials:
            has_special_character = True

        meets_criteria = True
        if numbers:
            meets_criteria = has_number
        if special_characters:
            meets_criteria = meets_criteria and has_special_character

    return pwd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a random password.")
    parser.add_argument("--length", type=int, default=12, help="Minimum password length.")
    parser.add_argument("--numbers", action="store_true", default=True, help="Include numbers.")
    parser.add_argument("--no-numbers", action="store_false", dest="numbers", help="Exclude numbers.")
    parser.add_argument(
        "--special",
        action="store_true",
        default=True,
        help="Include special characters.",
    )
    parser.add_argument(
        "--no-special",
        action="store_false",
        dest="special",
        help="Exclude special characters.",
    )
    parser.add_argument("--gui", action="store_true", help="Launch the GUI.")
    parser.add_argument("--cli", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def should_launch_gui() -> bool:
    return "--cli" not in sys.argv and ("--gui" in sys.argv or len(sys.argv) == 1)


def launch_gui() -> None:
    fields = [
        FieldSpec(key="length", label="Minimum length", field_type="text", default="12", required=True),
        FieldSpec(key="numbers", label="Include numbers", field_type="bool", default=True),
        FieldSpec(key="special", label="Include special characters", field_type="bool", default=True),
    ]

    def on_submit(values, output_widget):
        try:
            length = int(values["length"])
        except ValueError:
            if output_widget:
                output_widget.insert("end", "Please enter a valid number for length.\n")
            return

        password = generate_password(length, values["numbers"], values["special"])
        if output_widget:
            output_widget.insert("end", password + "\n")
        else:
            print(password)

    build_form("Password Generator", fields, on_submit, submit_label="Generate")


def main() -> None:
    if should_launch_gui():
        launch_gui()
        return

    args = parse_args()
    password = generate_password(args.length, args.numbers, args.special)
    print("Your new password is:", password)


if __name__ == "__main__":
    main()
