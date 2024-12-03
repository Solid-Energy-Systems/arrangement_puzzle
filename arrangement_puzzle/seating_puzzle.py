import itertools
import random
import json
import re

def save_puzzle_to_disk(clues, arrangement, namecolormapping, file_name="puzzle.json"):
    """
    Saves the puzzle configuration to a JSON file on disk.

    Args:
        clues (list): A list of Clue objects defining the puzzle's rules.
        arrangement (Arrangement): The current arrangement of people and colors.
        namecolormapping (NameColorMapping): The mapping of labels to names and colors.
        file_name (str): The name of the file to save the puzzle. Defaults to "puzzle.json".

    Returns:
        None
    """
    # Prepare the data for serialization
    data = {
        "clues": [
            {
                "clue_type": clue.clue_type,
                "property_x": clue.property_x,
                "property_y": clue.property_y,
                "property_z": clue.property_z,
                "color": clue.color,
                "negation": clue.negation
            } for clue in clues
        ],
        "arrangement": {
            "people": arrangement.people,
            "colors": arrangement.colors,
            "mapping": arrangement.mapping
        },
        "namecolormapping": {
            "people_mapping": namecolormapping.people_mapping,
            "color_mapping": namecolormapping.color_mapping
        }
    }

    # Save the data as JSON to disk
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

def load_puzzle_from_disk(file_name="puzzle.json"):
    """
    Loads the puzzle configuration from a JSON file on disk.

    Args:
        file_name (str): The name of the file to load the puzzle from. Defaults to "puzzle.json".

    Returns:
        tuple: A tuple containing the list of Clue objects, Arrangement, and NameColorMapping.
    """
    # Helper function to cast entries to int if they represent an integer
    def try_cast_int(value):
        try:
            return int(value)
        except:
            return value

    # Load the puzzle data from JSON
    with open(file_name, "r") as f:
        data = json.load(f)

    # Recreate the NameColorMapping object
    namecolormapping = NameColorMapping(len(data["namecolormapping"]["people_mapping"]))
    namecolormapping.people_mapping = data["namecolormapping"]["people_mapping"]
    namecolormapping.color_mapping = {int(k): v for k, v in data["namecolormapping"]["color_mapping"].items()}

    # Recreate the Arrangement object, ensuring any string integers are cast to int
    arrangement = Arrangement(
        people=[p for p in data["arrangement"]["people"]],
        colors=[c for c in data["arrangement"]["colors"]],
        mapping=namecolormapping
    )

    # Recreate the Clue objects, casting any integer-like strings to int
    clues = [
        Clue(
            clue_type=clue_data["clue_type"],
            property_x=try_cast_int(clue_data["property_x"]),
            property_y=try_cast_int(clue_data["property_y"]),
            property_z=try_cast_int(clue_data["property_z"]),
            color=try_cast_int(clue_data["color"]),
            negation=bool(clue_data["negation"]),
            mapping=namecolormapping
        ) for clue_data in data["clues"]
    ]

    return clues, arrangement, namecolormapping



random.seed(42)

colors_list = [
    "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown", "black", "white",
    "cyan", "magenta", "lime", "indigo", "violet", "gold", "silver", "turquoise", "teal", "lavender",
    "beige", "maroon", "olive", "coral", "navy", "peach", "mint", "chocolate", "salmon", "plum",
    "crimson", "amber", "ivory", "khaki", "fuchsia", "ruby", "sapphire", "emerald", "charcoal", "aqua",
    "rose", "jade", "lilac", "slate", "mustard", "sand", "bronze", "copper", "steel", "graphite"
]

names_list = {
    'A': ['Alice', 'Aaron', 'Ava', 'Andrew', 'Amelia', 'Alex', 'Aidan', 'Abigail', 'Amber', 'Arthur'],
    'B': ['Ben', 'Bella', 'Brandon', 'Brooke', 'Blake', 'Brianna', 'Bryan', 'Bethany', 'Beatrice', 'Bradley'],
    'C': ['Chris', 'Catherine', 'Caleb', 'Charlotte', 'Cameron', 'Clara', 'Connor', 'Candice', 'Cole', 'Chloe'],
    'D': ['David', 'Diana', 'Daniel', 'Daisy', 'Dylan', 'Derek', 'Dominic', 'Deborah', 'Dakota', 'Delilah'],
    'E': ['Ethan', 'Emma', 'Evan', 'Elena', 'Edward', 'Ella', 'Eli', 'Erin', 'Eleanor', 'Ezra'],
    'F': ['Felix', 'Fiona', 'Finn', 'Faith', 'Frederick', 'Frances', 'Franklin', 'Flora', 'Farah', 'Fernando'],
    'G': ['George', 'Grace', 'Gabriel', 'Gloria', 'Gavin', 'Genevieve', 'Gregory', 'Giselle', 'Gordon', 'Gemma'],
    'H': ['Henry', 'Hannah', 'Hugo', 'Hazel', 'Harry', 'Harper', 'Holden', 'Heather', 'Hudson', 'Hope'],
    'I': ['Isaac', 'Isabella', 'Ian', 'Ivy', 'Iris', 'Ivan', 'Isla', 'Indigo', 'Irene', 'Imogen'],
    'J': ['Jack', 'Julia', 'James', 'Jessica', 'Jacob', 'Jasmine', 'Joshua', 'Jade', 'Joseph', 'Joy'],
    'K': ['Kevin', 'Katherine', 'Kyle', 'Kayla', 'Keith', 'Kendra', 'Kenneth', 'Kimberly', 'Kurt', 'Kiera'],
    'L': ['Liam', 'Lily', 'Logan', 'Laura', 'Lucas', 'Lucy', 'Louis', 'Leah', 'Leon', 'Luna'],
    'M': ['Michael', 'Mia', 'Matthew', 'Megan', 'Max', 'Molly', 'Mason', 'Madeline', 'Marcus', 'Melanie'],
    'N': ['Nathan', 'Natalie', 'Noah', 'Nina', 'Nicholas', 'Nora', 'Neil', 'Naomi', 'Nolan', 'Nicole'],
    'O': ['Oliver', 'Olivia', 'Owen', 'Ophelia', 'Oscar', 'Odette', 'Omar', 'Octavia', 'Orlando', 'Orla'],
    'P': ['Peter', 'Penelope', 'Patrick', 'Phoebe', 'Paul', 'Paige', 'Preston', 'Piper', 'Philip', 'Polly'],
    'Q': ['Quinn', 'Quincy', 'Quentin', 'Queenie', 'Quinlan', 'Quiana', 'Quade', 'Quorra', 'Quill', 'Quiana'],
    'R': ['Ryan', 'Rachel', 'Robert', 'Rebecca', 'Riley', 'Ruth', 'Raymond', 'Rosie', 'Richard', 'Ruby'],
    'S': ['Samuel', 'Sophia', 'Steven', 'Sarah', 'Simon', 'Samantha', 'Scott', 'Scarlett', 'Sebastian', 'Sienna'],
    'T': ['Thomas', 'Tara', 'Theodore', 'Taylor', 'Toby', 'Tessa', 'Tyler', 'Tabitha', 'Tristan', 'Tina'],
    'U': ['Ulysses', 'Uma', 'Ulric', 'Unity', 'Ursula', 'Ulrich', 'Uriel', 'Una', 'Usman', 'Urbana'],
    'V': ['Victor', 'Violet', 'Vincent', 'Vanessa', 'Vivian', 'Vince', 'Valerie', 'Valentino', 'Veronica', 'Vera'],
    'W': ['William', 'Wendy', 'Wyatt', 'Willow', 'Wesley', 'Whitney', 'Walter', 'Willa', 'Warren', 'Winona'],
    'X': ['Xander', 'Xena', 'Xavier', 'Ximena', 'Xanthia', 'Xylon', 'Xia', 'Xerxes', 'Xaviera', 'Xoe'],
    'Y': ['Yasmin', 'Yara', 'Yosef', 'Yvonne', 'Yuri', 'Yolanda', 'Yael', 'Yvette', 'Yasir', 'Yasmina'],
    'Z': ['Zachary', 'Zara', 'Zane', 'Zoey', 'Zoe', 'Zach', 'Zelda', 'Zina', 'Zeke', 'Zahara']
}


class NameColorMapping:
    def __init__(self, n):
        # Create local copies of the global lists to avoid modifying them
        local_names_list = {key: names[:] for key, names in names_list.items()}  # Copy names_list dictionary
        local_colors_list = colors_list[:]  # Copy colors_list

        # Generate the mappings without modifying global variables
        self.people_mapping = {chr(ord('A') + i): random.choice(local_names_list[chr(ord('A') + i)]) for i in range(n)}
        self.color_mapping = {i + 1: local_colors_list.pop(random.randint(0, len(local_colors_list) - 1)) for i in range(n)}

    def __str__(self):
        people = ', '.join(list(self.people_mapping.values())[:-1]) + ' and ' + list(self.people_mapping.values())[-1]
        colors = ', '.join(list(self.color_mapping.values())[:-1]) + ' and ' + list(self.color_mapping.values())[-1]
        return f"{people} are sitting in a row on {len(self.people_mapping)} chairs. They are wearing shirts with colors {colors}. Each of them is wearing a different color."

def get_position_names(num_people):
    """
    Returns a list of position names based on the number of people.

    Args:
        num_people (int): The number of people in the arrangement.

    Returns:
        list: A list of position names.
    """
    if num_people == 2:
        return ['left', 'right']
    elif num_people == 3:
        return ['left', 'middle', 'right']
    elif num_people == 4:
        return ['far left', 'middle left', 'middle right', 'far right']
    elif num_people == 5:
        return ['far left', 'left', 'middle', 'right', 'far right']
    elif num_people == 6:
        return ['far left', 'just left of center', 'left of center', 'right of center', 'just right of center', 'far right']
    else:
        raise ValueError("Unsupported number of people")


class Arrangement:
    def __init__(self, people, colors, mapping):
        self.people = people  # List of people represented by labels
        self.colors = colors  # List of unique colors represented by numbers
        self.mapping = {p: c for p, c in zip(people, colors)}  # Map people to colors
        self.name_color_mapping = mapping  # Map labels to actual names and colors

    def __str__(self):
        position_names = get_position_names(len(self.people))
        output = []
        for person_label, position_name in zip(self.people, position_names):
            person_name = self.name_color_mapping.people_mapping[person_label]
            color_name = self.name_color_mapping.color_mapping[self.mapping[person_label]]
            output.append(f'{person_name} (Color {color_name}, position {position_name})')
        return ', '.join(output)



def parse_arrangement(arrangement_str, name_color_mapping):
    """
    Parses an arrangement string into an Arrangement object.

    Args:
        arrangement_str (str): The arrangement string, e.g., 'Aaron (Color turquoise), Ben (Color copper)'
        name_color_mapping (NameColorMapping): An object containing mappings for names and colors.

    Returns:
        Arrangement: The parsed arrangement.
    """
    # Remove extra whitespace
    arrangement_str = arrangement_str.strip()

    # regex pattern to capture color names instead of numbers
    pattern = r'(\w+) \(Color (\w+)\)'
    matches = re.findall(pattern, arrangement_str)

    if not matches:
        print("No matches found. Please check the input string and regex pattern.")
        return None

    # Extract the people and colors
    people = []
    colors = []
    for name, color_name in matches:
        # Find the corresponding key for the name using the people_mapping
        key_found = False
        for key, value in name_color_mapping.people_mapping.items():
            if value == name:
                people.append(key)
                key_found = True
                break
        if not key_found:
            print(f"Name '{name}' not found in people_mapping.")
            return None

        # Map color name to color number
        key_found = False
        for key, value in name_color_mapping.color_mapping.items():
            if value == color_name:
                colors.append(key)
                key_found = True
                break
        
        if not key_found:
            print(f"Color '{color_name}' not found in color_mapping.")
            return None
        
    # Create and return the Arrangement
    return Arrangement(people, colors, name_color_mapping)


def format_reference(reference, mapping):
    """
    Formats a reference to a person or color based on the mapping.

    Args:
        reference (int or str): A reference to a person or color.
        mapping (NameColorMapping): The mapping object to interpret references.

    Returns:
        str: A formatted string representation of the reference.
    """
    if isinstance(reference, int):
        return f"the person wearing {mapping.color_mapping[reference]}"
    return mapping.people_mapping[reference]

class Clue:
    def __init__(self, clue_type, property_x, property_y=None, property_z=None, color=None, negation=False, mapping=None):
        self.clue_type = clue_type  # Type of clue (e.g., "wearing", "immediate_left", "left_of", "between", "far_left", "end")
        self.property_x = property_x
        self.property_y = property_y
        self.property_z = property_z
        self.color = color
        self.negation = negation
        self.name_color_mapping = mapping

    def __str__(self):
        def person_or_color(reference):
            return format_reference(reference, self.name_color_mapping)

        description = ""
        if self.clue_type == "wearing":
            description = f"{self.name_color_mapping.people_mapping[self.property_x]} is {'not ' if self.negation else ''}wearing {self.name_color_mapping.color_mapping[self.color]}."
        elif self.clue_type == "immediate_left":
            description = f"{person_or_color(self.property_x)} is {'not ' if self.negation else ''}immediately to the left of {person_or_color(self.property_y)}."
        elif self.clue_type == "immediate_right":
            description = f"{person_or_color(self.property_x)} is {'not ' if self.negation else ''}immediately to the right of {person_or_color(self.property_y)}."
        elif self.clue_type == "left_of":
            description = f"{person_or_color(self.property_x)} is {'not ' if self.negation else ''}somewhere to the left of {person_or_color(self.property_y)}."
        elif self.clue_type == "right_of":
            description = f"{person_or_color(self.property_x)} is {'not ' if self.negation else ''}somewhere to the right of {person_or_color(self.property_y)}."
        elif self.clue_type == "between":
            description = f"{person_or_color(self.property_x)} is {'not ' if self.negation else ''}somewhere in between {person_or_color(self.property_y)} and {person_or_color(self.property_z)}."
        elif self.clue_type == "far_left":
            description = f"{person_or_color(self.property_x)} is {'not ' if self.negation else ''}sitting on the far left."
        elif self.clue_type == "far_right":
            description = f"{person_or_color(self.property_x)} is {'not ' if self.negation else ''}sitting on the far right."
        elif self.clue_type == "end":
            description = f"{person_or_color(self.property_x)} is {'not ' if self.negation else ''}sitting on the end."
        return description[0].upper() + description[1:]

    def is_consistent(self, arrangement):
        try:
            person_x = self.property_x if isinstance(self.property_x, str) else [p for p, c in arrangement.mapping.items() if c == self.property_x][0]
            person_y = self.property_y if isinstance(self.property_y, str) else [p for p, c in arrangement.mapping.items() if c == self.property_y][0] if self.property_y else None
            person_z = self.property_z if isinstance(self.property_z, str) else [p for p, c in arrangement.mapping.items() if c == self.property_z][0] if self.property_z else None

            if self.clue_type == "wearing":
                result = (arrangement.mapping[person_x] == self.color) != self.negation
            elif self.clue_type == "immediate_left":
                index_x = arrangement.people.index(person_x)
                index_y = arrangement.people.index(person_y)
                result = (index_x == index_y - 1) != self.negation
            elif self.clue_type == "immediate_right":
                index_x = arrangement.people.index(person_x)
                index_y = arrangement.people.index(person_y)
                result = (index_x == index_y + 1) != self.negation
            elif self.clue_type == "left_of":
                index_x = arrangement.people.index(person_x)
                index_y = arrangement.people.index(person_y)
                result = (index_x < index_y) != self.negation
            elif self.clue_type == "right_of":
                index_x = arrangement.people.index(person_x)
                index_y = arrangement.people.index(person_y)
                result = (index_x > index_y) != self.negation
            elif self.clue_type == "between":
                index_x = arrangement.people.index(person_x)
                index_y = arrangement.people.index(person_y)
                index_z = arrangement.people.index(person_z)
                result = ((index_y < index_x < index_z) or (index_z < index_x < index_y)) != self.negation
            elif self.clue_type == "far_left":
                result = (arrangement.people.index(person_x) == 0) != self.negation
            elif self.clue_type == "far_right":
                result = (arrangement.people.index(person_x) == len(arrangement.people) - 1) != self.negation
            elif self.clue_type == "end":
                result = (arrangement.people.index(person_x) in [0, len(arrangement.people) - 1]) != self.negation
            else:
                result = True
            return result
        except ValueError as e:
            print(f"Error during evaluation: {e}")
            return False


def generate_random_arrangement(n, mapping):
    """
    Generates a random arrangement of people and colors.

    Args:
        n (int): The number of people and colors.
        mapping (NameColorMapping): The mapping of names and colors.

    Returns:
        Arrangement: A randomly generated arrangement.
    """
    people = random.sample([chr(ord('A') + i) for i in range(n)], n)
    colors = random.sample(range(1, n + 1), n)
    arrangement = Arrangement(people, colors, mapping)
    return arrangement

def generate_all_arrangements(n, mapping):
    """
    Generates all possible arrangements of people and colors.

    Args:
        n (int): The number of people and colors.
        mapping (NameColorMapping): The mapping of names and colors.

    Yields:
        Arrangement: Each possible arrangement.
    """
    people_permutations = itertools.permutations([chr(ord('A') + i) for i in range(n)])
    for people in people_permutations:
        color_permutations = itertools.permutations(range(1, n + 1))
        for colors in color_permutations:
            arrangement = Arrangement(list(people), list(colors), mapping)
            yield arrangement

def is_valid_arrangement(arrangement, clues):
    """
    Checks if an arrangement satisfies all given clues.

    Args:
        arrangement (Arrangement): The arrangement to validate.
        clues (list): A list of Clue objects defining the puzzle's rules.

    Returns:
        bool: True if the arrangement is valid, False otherwise.
    """
    result = all(clue.is_consistent(arrangement) for clue in clues)
    return result

def generate_consistent_arrangements(clues, n, mapping):
    """
    Generates all arrangements that are consistent with the given clues.

    Args:
        clues (list): A list of Clue objects.
        n (int): The number of people and colors.
        mapping (NameColorMapping): The mapping of names and colors.

    Returns:
        list: A list of consistent arrangements.
    """
    consistent_arrangements = [arr for arr in generate_all_arrangements(n, mapping) if is_valid_arrangement(arr, clues)]
    return consistent_arrangements

def generate_clues(n, mapping):
    """
    Generates clues to create a puzzle with a unique solution.

    Args:
        n (int): The number of people and colors.
        mapping (NameColorMapping): The mapping of names and colors.

    Returns:
        list: A list of Clue objects.
    """
    def random_property():
        return random.choice([chr(ord('A') + i) for i in range(n)] + list(range(1, n + 1)))

    all_clues = [
        lambda: Clue("wearing", random.choice([chr(ord('A') + i) for i in range(n)]), color=random.randint(1, n), mapping=mapping),
        lambda: Clue("immediate_left", random_property(), property_y=random_property(), mapping=mapping),
        lambda: Clue("immediate_right", random_property(), property_y=random_property(), mapping=mapping),
        lambda: Clue("left_of", random_property(), property_y=random_property(), mapping=mapping),
        lambda: Clue("right_of", random_property(), property_y=random_property(), mapping=mapping),
        lambda: Clue("between", random_property(), property_y=random_property(), property_z=random_property(), mapping=mapping),
        lambda: Clue("far_left", random_property(), mapping=mapping),
        lambda: Clue("far_right", random_property(), mapping=mapping),
        lambda: Clue("end", random_property(), mapping=mapping)
    ]
    consistent_arrangements = list(generate_all_arrangements(n, mapping))
    clues = []

    while len(consistent_arrangements) > 1:
        while True:
            new_clue = random.choice(all_clues)()
            new_clue.negation = random.choice([True, False])
            filtered_arrangements = [arr for arr in consistent_arrangements if new_clue.is_consistent(arr)]
            if len(filtered_arrangements) > 0:
                break
        clues.append(new_clue)
        consistent_arrangements = filtered_arrangements
        
    return clues

def filter_duplicate_clues(clues):
    """
    Filters out duplicate clues from a list of clues.

    Args:
        clues (list): A list of Clue objects.

    Returns:
        list: A list of unique clues.
    """
    unique_clues = []
    for clue in clues:
        if clue not in unique_clues:
            unique_clues.append(clue)
    return unique_clues

def filter_unnecessary_clues(clues, n, mapping):
    """
    Filters out unnecessary clues that do not contribute to a unique solution.

    Args:
        clues (list): A list of Clue objects.
        n (int): The number of people and colors.
        mapping (NameColorMapping): The mapping of names and colors.

    Returns:
        list: A list of necessary clues.
    """
    filtered_clues = clues[:]
    for clue in clues:
        temp_clues = filtered_clues[:]
        temp_clues.remove(clue)
        consistent_arrangements = generate_consistent_arrangements(temp_clues, n, mapping)
        if len(consistent_arrangements) == 1:
            filtered_clues.remove(clue)
    return filtered_clues


if __name__ == "__main__":
    # Example usage:
    n = 5  # Number of people (<= 26)
    mapping = NameColorMapping(n)
    arrangement = generate_random_arrangement(n, mapping)
    print("Random Arrangement:")
    print(arrangement)

    # Example clues
    generated_clues = generate_clues(n, mapping)
    print("\nGenerated Clues:")
    for clue in generated_clues:
        print(clue)

    print("\nFiltering duplicate clues:")
    unique_clues = filter_duplicate_clues(generated_clues)
    for clue in unique_clues:
        print(clue)

    print("\nFiltering unnecessary clues:")
    necessary_clues = filter_unnecessary_clues(unique_clues, n, mapping)
    print(mapping)
    for clue in necessary_clues:
        print(clue)

    print("\nGenerating all consistent arrangements:")
    consistent_arrangements = generate_consistent_arrangements(necessary_clues, n, mapping)
    for i, arr in enumerate(consistent_arrangements):
        print(f"Arrangement {i + 1}: {arr}")

    # save_puzzle_to_disk(necessary_clues, consistent_arrangements[0], mapping, "puzzle.json")

