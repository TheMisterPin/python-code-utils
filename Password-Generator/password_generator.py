import random
import string


def generate_password(min_length, numbers=True, special_characters=True):
    letters = string.ascii_letters
    numbers = string.digits
    special_characters = string.punctuation

    characters = letters
    if numbers:
        characters += numbers
    if special_characters:
        characters += special_characters

    pwd = ''

    meets_criteria = False
    has_number = False
    has_special_character = False
    while not meets_criteria or len(pwd) < min_length:
        new_char = random.choice(characters)
        pwd += new_char

        if new_char in numbers:
            has_number = True
        elif new_char in special_characters:
            has_special_character = True

        meets_criteria = True
        if numbers:
            meets_criteria = has_number
        if special_characters:
            meets_criteria = meets_criteria and has_special_character

    return pwd


min_lenght = int(input("Enter the minimum length of the password: "))

has_numbers = input(
    "Do you want numbers in your password? (yes/no): ").lower() == 'yes'
has_special_characters = input(
    "Do you want special characters in your password? (yes/no): ").lower() == 'yes'

pwd = generate_password(min_lenght, has_numbers, has_special_characters)
print("Your new password is:", pwd)
