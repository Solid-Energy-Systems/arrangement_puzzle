from arrangement_puzzle.seating_puzzle import *
from tqdm import tqdm

def initialize_possibilities(n, mapping):
    """
    Initializes the possible positions, people, and colors for the puzzle to the set of all possible values.

    Args:
        n (int): The number of people/colors.
        mapping (NameColorMapping): A mapping of names to labels and colors.

    Returns:
        tuple: Three dictionaries representing possible positions for:
            - positions_possibilities: Dict of positions and possible people/colors.
            - people_possibilities: Dict of people and their possible positions/colors.
            - colors_possibilities: Dict of colors and their possible positions/people.
    """
    # Initialize possibilities for each position
    positions_possibilities = {}
    for pos in range(n):
        positions_possibilities[pos] = {
            'people': set([chr(ord('A') + i) for i in range(n)]),
            'colors': set(range(1, n + 1))
        }
    # Initialize possibilities for each person
    people_possibilities = {}
    for person in [chr(ord('A') + i) for i in range(n)]:
        people_possibilities[person] = {
            'positions': set(range(n)),
            'colors': set(range(1, n + 1))
        }
    # Initialize possibilities for each color
    colors_possibilities = {}
    for color in range(1, n + 1):
        colors_possibilities[color] = {
            'positions': set(range(n)),
            'people': set([chr(ord('A') + i) for i in range(n)])
        }
    return positions_possibilities, people_possibilities, colors_possibilities



def apply_wearing_clue(clue, positions_possibilities, people_possibilities, colors_possibilities, reasoning_chain, mapping):
    """
    Applies a 'wearing' clue to update possibilities based on the clue.

    Args:
        clue (Clue): The clue object to apply.
        positions_possibilities (dict): Possible positions for each person and color.
        people_possibilities (dict): Possible positions/colors for each person.
        colors_possibilities (dict): Possible positions/people for each color.
        reasoning_chain (list): Logs of reasoning steps.
        mapping (NameColorMapping): Mapping of names and colors.

    Returns:
        bool: True if the possibilities were modified, False otherwise.
    """
    person = clue.property_x
    color = clue.color
    modified = False  # Initialize modified to False

    person = clue.property_x
    color = clue.color

    if not clue.negation:
        # Update person's possible colors
        old_person_colors = people_possibilities[person]['colors'].copy()
        people_possibilities[person]['colors'].intersection_update({color})
        if people_possibilities[person]['colors'] != old_person_colors:
            modified = True

        # Update color's possible people
        old_color_people = colors_possibilities[color]['people'].copy()
        colors_possibilities[color]['people'].intersection_update({person})
        if colors_possibilities[color]['people'] != old_color_people:
            modified = True
    else:
        # Remove color from person's possible colors
        old_person_colors = people_possibilities[person]['colors'].copy()
        people_possibilities[person]['colors'].discard(color)
        if people_possibilities[person]['colors'] != old_person_colors:
            modified = True

        # Remove person from color's possible people
        old_color_people = colors_possibilities[color]['people'].copy()
        colors_possibilities[color]['people'].discard(person)
        if colors_possibilities[color]['people'] != old_color_people:
            modified = True

    return modified

def negate_invalid_pairs(invalid_pairs, x_positions, y_positions):
    """
    Removes invalid pairs of positions for negation clues.

    Args:
        invalid_pairs (set): Set of invalid (x, y) pairs.
        x_positions (set): Possible x positions.
        y_positions (set): Possible y positions.

    Returns:
        list: Valid pairs of (x, y) positions.
    """
    valid_pairs = []

    for x in x_positions:
        for y in y_positions:
            if (x, y) not in invalid_pairs:
                valid_pairs.append((x, y))
    
    return valid_pairs

def negate_invalid_triples(invalid_triples, x_positions, y_positions, z_positions):
    """
    Removes invalid triples of positions for negation clues.

    Args:
        invalid_triples (set): Set of invalid (x, y, z) triples.
        x_positions (set): Possible x positions.
        y_positions (set): Possible y positions.
        z_positions (set): Possible z positions.

    Returns:
        list: Valid triples of (x, y, z) positions.
    """
    valid_triples = []

    for x in x_positions:
        for y in y_positions:
            for z in z_positions:
                if (x, y, z) not in invalid_triples:
                    valid_triples.append((x, y, z))
    
    return valid_triples

def can_be_equal(property_x, property_y, people_possibilities, reasoning_chain, mapping):
    """
    Determines whether two properties (person or color) can be the same.

    Args:
        property_x (int or str): The first property (person or color).
        property_y (int or str): The second property (person or color).
        people_possibilities (dict): Possibilities for each person.
        reasoning_chain (list): Logs of reasoning steps.
        mapping (NameColorMapping): Mapping of names and colors.

    Returns:
        bool: True if the properties can be the same, False otherwise.
    """
    if isinstance(property_x, int) and isinstance(property_y, int) and property_x != property_y:
        return False
    if isinstance(property_x, str) and isinstance(property_y, str) and property_x != property_y:
        return False
    if isinstance(property_x, str) and isinstance(property_y, int):
        for color in people_possibilities[property_x]['colors']:
            if color == property_y:
                return True
        reasoning_chain.append(f"We know that {format_reference(property_x, mapping)} is not wearing {format_reference(property_y, mapping)}.")
        return False
    if isinstance(property_x, int) and isinstance(property_y, str):
        for color in people_possibilities[property_y]['colors']:
            if color == property_x:
                return True
        reasoning_chain.append(f"We know that {format_reference(property_y, mapping)} is not wearing {format_reference(property_x, mapping)}.")
        return False

def apply_position_clue(clue, positions_possibilities, people_possibilities, colors_possibilities, reasoning_chain, mapping):
    """
    Applies a position-related clue to update possibilities.

    Args:
        clue (Clue): The clue object to apply.
        positions_possibilities (dict): Possible positions for each person and color.
        people_possibilities (dict): Possible positions/colors for each person.
        colors_possibilities (dict): Possible positions/people for each color.
        reasoning_chain (list): Logs of reasoning steps.
        mapping (NameColorMapping): Mapping of names and colors.

    Returns:
        bool: True if the possibilities were modified, False otherwise.
    """
    n = len(positions_possibilities)

    def get_possible_positions(entity):
        if isinstance(entity, str):
            return people_possibilities[entity]['positions']
        elif isinstance(entity, int):
            return colors_possibilities[entity]['positions']

    x_positions = get_possible_positions(clue.property_x)
    y_positions = get_possible_positions(clue.property_y)
    changed = False


    if clue.clue_type == "immediate_left":
        # Generate all possible pairs
        possible_pairs = set((x, x + 1) for x in range(n - 1))
        # Filter pairs based on current possible positions
        valid_pairs = set((x, y) for x, y in possible_pairs if x in x_positions and y in y_positions)

        if clue.negation:
            possible_equal = can_be_equal(clue.property_x, clue.property_y, people_possibilities, reasoning_chain, mapping)
            valid_pairs = negate_invalid_pairs(valid_pairs, x_positions, y_positions)
            if not possible_equal:
                valid_pairs = set((x, y) for x, y in valid_pairs if x != y)

        # Update positions to only include positions where the clue can be satisfied
        valid_x = set(x for x, _ in valid_pairs)
        if valid_x != x_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_y, mapping)} is at {set_to_str('position', y_positions)}, {format_reference(clue.property_x, mapping)} must be in {set_to_str('position', valid_x)}.")
            x_positions.intersection_update(valid_x)
            changed = True

        valid_y = set(y for _, y in valid_pairs)

        if valid_y != y_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_x, mapping)} is at {set_to_str('position', x_positions)}, {format_reference(clue.property_y, mapping)} must be in {set_to_str('position', valid_y)}.")
            y_positions.intersection_update(valid_y)
            changed = True
    elif clue.clue_type == "immediate_right":
        # Similar logic for immediate_right
        possible_pairs = set((x, x - 1) for x in range(1, n))
        valid_pairs = set((x, y) for x, y in possible_pairs if x in x_positions and y in y_positions)

        if clue.negation:
            possible_equal = can_be_equal(clue.property_x, clue.property_y, people_possibilities, reasoning_chain, mapping)
            valid_pairs = negate_invalid_pairs(valid_pairs, x_positions, y_positions)
            if not possible_equal:
                valid_pairs = set((x, y) for x, y in valid_pairs if x != y)

        valid_x = set(x for x, _ in valid_pairs)
        if valid_x != x_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_y, mapping)} is at {set_to_str('position', y_positions)}, {format_reference(clue.property_x, mapping)} must be in {set_to_str('position', valid_x)}.")
            x_positions.intersection_update(valid_x)
            changed = True

        valid_y = set(y for _, y in valid_pairs)
        if valid_y != y_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_x, mapping)} is at {set_to_str('position', x_positions)}, {format_reference(clue.property_y, mapping)} must be in {set_to_str('position', valid_y)}.")
            y_positions.intersection_update(valid_y)
            changed = True
    elif clue.clue_type == "right_of":
        # Generate all possible pairs where x > y
        possible_pairs = set((x, y) for x in x_positions for y in y_positions if x > y)

        if clue.negation:
            possible_equal = can_be_equal(clue.property_x, clue.property_y, people_possibilities, reasoning_chain, mapping)
            possible_pairs = negate_invalid_pairs(possible_pairs, x_positions, y_positions)
            if not possible_equal:
                possible_pairs = set((x, y) for x, y in possible_pairs if x != y)

        valid_x = set(x for x, _ in possible_pairs)
        if valid_x != x_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_y, mapping)} is at {set_to_str('position', y_positions)}, {format_reference(clue.property_x, mapping)} must be in {set_to_str('position', valid_x)}.")
            x_positions.intersection_update(valid_x)
            changed = True

        valid_y = set(y for _, y in possible_pairs)
        if valid_y != y_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_x, mapping)} is at {set_to_str('position', x_positions)}, {format_reference(clue.property_y, mapping)} must be in {set_to_str('position', valid_y)}.")
            y_positions.intersection_update(valid_y)
            changed = True
    elif clue.clue_type == "left_of":
        # Generate all possible pairs where x < y
        possible_pairs = set((x, y) for x in x_positions for y in y_positions if x < y)

        if clue.negation:
            possible_equal = can_be_equal(clue.property_x, clue.property_y, people_possibilities, reasoning_chain, mapping)
            possible_pairs = negate_invalid_pairs(possible_pairs, x_positions, y_positions)
            if not possible_equal:
                possible_pairs = set((x, y) for x, y in possible_pairs if x != y)

        valid_x = set(x for x, _ in possible_pairs)
        if valid_x != x_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_y, mapping)} is at {set_to_str('position', y_positions)}, {format_reference(clue.property_x, mapping)} must be in {set_to_str('position', valid_x)}.")
            x_positions.intersection_update(valid_x)
            changed = True
        
        valid_y = set(y for _, y in possible_pairs)
        if valid_y != y_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_x, mapping)} is at {set_to_str('position', x_positions)}, {format_reference(clue.property_y, mapping)} must be in {set_to_str('position', valid_y)}.")
            y_positions.intersection_update(valid_y)
            changed = True
    elif clue.clue_type == "between":
        z_positions = get_possible_positions(clue.property_z)
        possible_triples = set((x, y, z) for x in x_positions for y in y_positions for z in z_positions if (y < x < z) or (z < x < y))

        if clue.negation:
            possible_equal_xy = can_be_equal(clue.property_x, clue.property_y, people_possibilities, reasoning_chain, mapping)
            possible_equal_yz = can_be_equal(clue.property_y, clue.property_z, people_possibilities, reasoning_chain, mapping)
            possible_equal_xz = can_be_equal(clue.property_x, clue.property_z, people_possibilities, reasoning_chain, mapping)
            possible_triples = negate_invalid_triples(possible_triples, x_positions, y_positions, z_positions)
            if not possible_equal_xy:
                possible_triples = set((x, y, z) for x, y, z in possible_triples if x != y)
            if not possible_equal_yz:
                possible_triples = set((x, y, z) for x, y, z in possible_triples if y != z)
            if not possible_equal_xz:
                possible_triples = set((x, y, z) for x, y, z in possible_triples if x != z)
        else:
            person = None
            color = None
            if isinstance(clue.property_y, str) and isinstance(clue.property_z, int):
                person = clue.property_y
                color = clue.property_z
            elif isinstance(clue.property_y, int) and isinstance(clue.property_z, str):
                person = clue.property_z
                color = clue.property_y
            if person is not None:
                old_person_colors = people_possibilities[person]['colors'].copy()
                people_possibilities[person]['colors'].discard(color)
                if people_possibilities[person]['colors'] != old_person_colors:
                    reasoning_chain.append(f"{format_reference(person, mapping)} cannot be wearing {format_reference(color, mapping)} because {format_reference(clue.property_y, mapping)} is between them.")
                    changed = True

                # Remove person from color's possible people
                old_color_people = colors_possibilities[color]['people'].copy()
                colors_possibilities[color]['people'].discard(person)
                if colors_possibilities[color]['people'] != old_color_people:
                    changed = True

        valid_x = set(x for x, _, _ in possible_triples)
        if valid_x != x_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_y, mapping)} is at {set_to_str('position', y_positions)} and {format_reference(clue.property_z, mapping)} is in {set_to_str('position', z_positions)}, {format_reference(clue.property_x, mapping)} must be in {set_to_str('position', valid_x)}.")
            x_positions.intersection_update(valid_x)
            changed = True
        
        valid_y = set(y for _, y, _ in possible_triples)
        if valid_y != y_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_x, mapping)} is at {set_to_str('position', x_positions)} and {format_reference(clue.property_z, mapping)} is in {set_to_str('position', z_positions)}, {format_reference(clue.property_y, mapping)} must be in {set_to_str('position', valid_y)}.")
            y_positions.intersection_update(valid_y)
            changed = True
        
        valid_z = set(z for _, _, z in possible_triples)
        if valid_z != z_positions:
            reasoning_chain.append(f"Because {format_reference(clue.property_x, mapping)} is at {set_to_str('position', x_positions)} and {format_reference(clue.property_y, mapping)} is in {set_to_str('position', y_positions)}, {format_reference(clue.property_z, mapping)} must be in {set_to_str('position', valid_z)}.")
            z_positions.intersection_update(valid_z)
            changed = True
    else:
        reasoning_chain.append(f"Clue type '{clue.clue_type}' not fully implemented.")

    return changed

def capitalize_first_letter(str):
    """
    Capitalizes the first letter of a string.

    Args:
        string (str): The input string.

    Returns:
        str: The string with the first letter capitalized.
    """
    return str[0].upper() + str[1:]

def apply_end_clue(clue, positions_possibilities, people_possibilities, colors_possibilities, reasoning_chain, mapping):
    """
    Applies a clue related to an entity being at the far left, far right, or an end.

    Args:
        clue (Clue): The clue object to apply.
        positions_possibilities (dict): Possible positions for each person and color.
        people_possibilities (dict): Possible positions/colors for each person.
        colors_possibilities (dict): Possible positions/people for each color.
        reasoning_chain (list): Logs of reasoning steps.
        mapping (NameColorMapping): Mapping of names and colors.

    Returns:
        bool: True if the possibilities were modified, False otherwise.
    """
    n = len(positions_possibilities)
    pos_far_left = 0
    pos_far_right = n - 1
    positions = set()
    if clue.clue_type == "far_left":
        positions.add(pos_far_left)
    elif clue.clue_type == "far_right":
        positions.add(pos_far_right)
    elif clue.clue_type == "end":
        positions.update([pos_far_left, pos_far_right])

    entity = clue.property_x

    modified = False  # Initialize modified to False

    if clue.negation:
        # Remove positions from entity's possible positions
        if isinstance(entity, str):
            old_positions = people_possibilities[entity]['positions'].copy()
            people_possibilities[entity]['positions'].difference_update(positions)
            if people_possibilities[entity]['positions'] != old_positions:
                reasoning_chain.append(f"{capitalize_first_letter(format_reference(entity, mapping))} cannot be at {set_to_str('position', positions)}.")
                modified = True
        elif isinstance(entity, int):
            old_positions = colors_possibilities[entity]['positions'].copy()
            colors_possibilities[entity]['positions'].difference_update(positions)
            if colors_possibilities[entity]['positions'] != old_positions:
                reasoning_chain.append(f"{capitalize_first_letter(format_reference(entity, mapping))} cannot be at {set_to_str('position', positions)}.")
                modified = True
    else:
        # Restrict entity's possible positions
        if isinstance(entity, str):
            old_positions = people_possibilities[entity]['positions'].copy()
            people_possibilities[entity]['positions'].intersection_update(positions)
            if people_possibilities[entity]['positions'] != old_positions:
                reasoning_chain.append(f"{capitalize_first_letter(format_reference(entity, mapping))} must be at {set_to_str('position', positions)}.")
                modified = True
        elif isinstance(entity, int):
            old_positions = colors_possibilities[entity]['positions'].copy()
            colors_possibilities[entity]['positions'].intersection_update(positions)
            if colors_possibilities[entity]['positions'] != old_positions:
                reasoning_chain.append(f"{capitalize_first_letter(format_reference(entity, mapping))} must be at {set_to_str('position', positions)}.")
                modified = True
    return modified

def set_to_str(substring, s):
    """
    Converts a set to a human-readable string format.

    Args:
        substring (str): Prefix to describe the type of set.
        s (set): The set to convert.

    Returns:
        str: A formatted string representation of the set.
    """
    if len(s) == 0:
        return "none of the {substring}"
    elif len(s) == 1:
        return f"{substring}{' ' if substring else ''}{next(iter(s))}"
    else:
        return f"one of {substring}{'s ' if substring else ''}{', '.join(str(x) for x in sorted(s)[:-1])} or {sorted(s)[-1]}" 

def propagate_constraints(positions_possibilities, people_possibilities, colors_possibilities, reasoning_chain, mapping):
    """
    Propagates constraints to reduce possibilities based on existing reasoning.

    Args:
        positions_possibilities (dict): Possible positions for each person and color.
        people_possibilities (dict): Possible positions/colors for each person.
        colors_possibilities (dict): Possible positions/people for each color.
        reasoning_chain (list): Logs of reasoning steps.
        mapping (NameColorMapping): Mapping of names and colors.

    Returns:
        None
    """
    changed = True
    while changed:
        changed = False
        # For each position
        for pos in positions_possibilities:
            for person in positions_possibilities[pos]['people'].copy():
                if pos not in people_possibilities[person]['positions']:
                    positions_possibilities[pos]['people'].discard(person)
                    changed = True
            for color in positions_possibilities[pos]['colors'].copy():
                if pos not in colors_possibilities[color]['positions']:
                    positions_possibilities[pos]['colors'].discard(color)
                    changed = True
            # If position has only one possible person
            if len(positions_possibilities[pos]['people']) == 1:
                person = next(iter(positions_possibilities[pos]['people']))
                people_possibilities[person]['positions'] = {pos}
                
                # Remove this person from other positions
                for other_pos in positions_possibilities:
                    if other_pos != pos:
                        len_other_pos = len(positions_possibilities[other_pos]['people'])
                        positions_possibilities[other_pos]['people'].discard(person)
                        len_people = len(people_possibilities[person]['positions'])
                        people_possibilities[person]['positions'].discard(other_pos)
                        if len_people > len(people_possibilities[person]['positions']) or len_other_pos > len(positions_possibilities[other_pos]['people']):
                            reasoning_chain.append(f"{mapping.people_mapping[person]} cannot be at position {other_pos} because they are at position {pos}.")
                            changed = True
                        if len_other_pos > 1 and len(positions_possibilities[other_pos]['people']) == 1:
                            reasoning_chain.append(f"Position {other_pos} must have {mapping.people_mapping[next(iter(positions_possibilities[other_pos]['people']))]} because they're the only person left.")
                            people_possibilities[next(iter(positions_possibilities[other_pos]['people']))]['positions'] = {other_pos}

                if positions_possibilities[pos]['colors'] != people_possibilities[person]['colors']:
                    reasoning_chain.append(f"{mapping.people_mapping[person]} is wearing {set_to_str('', [mapping.color_mapping[c] for c in people_possibilities[person]['colors']])}, and they are at position {pos} which contains someone wearing {set_to_str('', [mapping.color_mapping[c] for c in positions_possibilities[pos]['colors']])}.")
                    positions_possibilities[pos]['colors'].intersection_update(people_possibilities[person]['colors'])
                    people_possibilities[person]['colors'].intersection_update(positions_possibilities[pos]['colors'])
                    reasoning_chain.append(f"Therefore, {mapping.people_mapping[person]} must be wearing {set_to_str('', [mapping.color_mapping[c] for c in positions_possibilities[pos]['colors']])} at position {pos}.")
                    changed = True

            # If position has only one possible color
            if len(positions_possibilities[pos]['colors']) == 1:
                color = next(iter(positions_possibilities[pos]['colors']))
                colors_possibilities[color]['positions'] = {pos}
                
                # Remove this color from other positions
                for other_pos in positions_possibilities:
                    if other_pos != pos:
                        len_other_pos = len(positions_possibilities[other_pos]['colors'])
                        positions_possibilities[other_pos]['colors'].discard(color)
                        len_colors = len(colors_possibilities[color]['positions'])
                        colors_possibilities[color]['positions'].discard(other_pos)

                        if len_colors > len(colors_possibilities[color]['positions']) or len_other_pos > len(positions_possibilities[other_pos]['colors']):
                            reasoning_chain.append(f"{mapping.color_mapping[color].capitalize()} cannot be worn by someone at position {other_pos} because it is worn by someone at position {pos}.")
                            changed = True

                        if len_other_pos > 1 and len(positions_possibilities[other_pos]['colors']) == 1:
                            reasoning_chain.append(f"Position {other_pos} must have someone wearing {mapping.color_mapping[next(iter(positions_possibilities[other_pos]['colors']))]} because it's the only color left.")
                            colors_possibilities[next(iter(positions_possibilities[other_pos]['colors']))]['positions'] = {other_pos}

                if positions_possibilities[pos]['people'] != colors_possibilities[color]['people']:
                    reasoning_chain.append(f"{mapping.color_mapping[color].capitalize()} is worn by {set_to_str('', [mapping.people_mapping[p] for p in colors_possibilities[color]['people']])}, and it is at position {pos} which contains {set_to_str('', [mapping.people_mapping[p] for p in positions_possibilities[pos]['people']])}.")
                    positions_possibilities[pos]['people'].intersection_update(colors_possibilities[color]['people'])
                    colors_possibilities[color]['people'].intersection_update(positions_possibilities[pos]['people'])
                    reasoning_chain.append(f"Therefore, position {pos} must have {set_to_str('', [mapping.people_mapping[p] for p in colors_possibilities[color]['people']])} wearing {mapping.color_mapping[color]}.")
                    changed = True

        # For each person
        for person in people_possibilities:
            for pos in people_possibilities[person]['positions'].copy():
                if person not in positions_possibilities[pos]['people']:
                    people_possibilities[person]['positions'].discard(pos)
                    changed = True
            for color in people_possibilities[person]['colors'].copy():
                if person not in colors_possibilities[color]['people']:
                    people_possibilities[person]['colors'].discard(color)
                    changed = True
            # If person has only one possible position
            if len(people_possibilities[person]['positions']) == 1:
                pos = next(iter(people_possibilities[person]['positions']))
                positions_possibilities[pos]['people'] = {person}
                
                # Remove other people from this position
                for other_person in people_possibilities:
                    if other_person != person:
                        len_positions = len(positions_possibilities[pos]['people'])
                        positions_possibilities[pos]['people'].discard(other_person)
                        len_other_person = len(people_possibilities[other_person]['positions'])
                        people_possibilities[other_person]['positions'].discard(pos)
                        if len_positions > len(positions_possibilities[pos]['people']) or len_other_person > len(people_possibilities[other_person]['positions']):
                            reasoning_chain.append(f"Position {pos} cannot have {mapping.people_mapping[other_person]} because it has {mapping.people_mapping[person]}.")
                            changed = True
                        if len_other_person > 1 and len(people_possibilities[other_person]['positions']) == 1:
                            reasoning_chain.append(f"{mapping.people_mapping[other_person]} must be at position {next(iter(people_possibilities[other_person]['positions']))} because it's the only position left.")
                            positions_possibilities[next(iter(people_possibilities[other_person]['positions']))]['people'] = {other_person}

            # If person has only one possible color
            if len(people_possibilities[person]['colors']) == 1:
                color = next(iter(people_possibilities[person]['colors']))
                colors_possibilities[color]['people'] = {person}
                
                # Remove this color from other people's possibilities
                for other_person in people_possibilities:
                    if other_person != person and color in people_possibilities[other_person]['colors']:
                        len_other_person = len(people_possibilities[other_person]['colors'])
                        people_possibilities[other_person]['colors'].discard(color)
                        len_colors = len(colors_possibilities[color]['people'])
                        colors_possibilities[color]['people'].discard(other_person)
                        if len_colors > len(colors_possibilities[color]['people']) or len_other_person > len(people_possibilities[other_person]['colors']):
                            reasoning_chain.append(f"{mapping.people_mapping[other_person]} cannot be wearing {mapping.color_mapping[color]} because {mapping.people_mapping[person]} is wearing it.")
                            changed = True
                        if len_other_person > 1 and len(people_possibilities[other_person]['colors']) == 1:
                            reasoning_chain.append(f"{mapping.people_mapping[other_person]} must be wearing {mapping.color_mapping[next(iter(people_possibilities[other_person]['colors']))]} because it's the only color left.")
                            colors_possibilities[next(iter(people_possibilities[other_person]['colors']))]['people'] = {other_person}


                if people_possibilities[person]['positions'] != colors_possibilities[color]['positions']:
                    reasoning_chain.append(f"{mapping.people_mapping[person]} is at {set_to_str('position', people_possibilities[person]['positions'])}, and they are wearing {mapping.color_mapping[color]} which is at {set_to_str('position', colors_possibilities[color]['positions'])}.")
                    people_possibilities[person]['positions'].intersection_update(colors_possibilities[color]['positions'])
                    colors_possibilities[color]['positions'].intersection_update(people_possibilities[person]['positions'])
                    reasoning_chain.append(f"Therefore, {mapping.people_mapping[person]} must be at {set_to_str('position', people_possibilities[person]['positions'])} wearing {mapping.color_mapping[color]}.")
                    changed = True

        # For each color
        for color in colors_possibilities:
            for pos in colors_possibilities[color]['positions'].copy():
                if color not in positions_possibilities[pos]['colors']:
                    colors_possibilities[color]['positions'].discard(pos)
                    changed = True
            for person in colors_possibilities[color]['people'].copy():
                if color not in people_possibilities[person]['colors']:
                    colors_possibilities[color]['people'].discard(person)
                    changed = True
            # If color has only one possible position
            if len(colors_possibilities[color]['positions']) == 1:
                pos = next(iter(colors_possibilities[color]['positions']))
                positions_possibilities[pos]['colors'] = {color}
                
                # Remove other colors from this position
                for other_color in colors_possibilities:
                    if other_color != color:
                        len_positions = len(positions_possibilities[pos]['colors'])
                        positions_possibilities[pos]['colors'].discard(other_color)
                        len_other_color = len(colors_possibilities[other_color]['positions'])
                        colors_possibilities[other_color]['positions'].discard(pos)
                        if len_positions > len(positions_possibilities[pos]['colors']) or len_other_color > len(colors_possibilities[other_color]['positions']):
                            changed = True
                            reasoning_chain.append(f"Position {pos} cannot have a person wearing {mapping.color_mapping[other_color]} because it has someone wearing {mapping.color_mapping[color]}.")
                        if len_other_color > 1 and len(colors_possibilities[other_color]['positions']) == 1:
                            reasoning_chain.append(f"{mapping.color_mapping[other_color].capitalize()} must be worn by someone at position {next(iter(colors_possibilities[other_color]['positions']))} because it's the only possible position left for that color.")
                            positions_possibilities[next(iter(colors_possibilities[other_color]['positions']))]['colors'] = {other_color}


            # If color has only one possible person
            if len(colors_possibilities[color]['people']) == 1:
                person = next(iter(colors_possibilities[color]['people']))
                people_possibilities[person]['colors'] = {color}
                
                # Remove this person from other colors' possibilities
                for other_color in colors_possibilities:
                    if other_color != color:
                        len_other_color = len(colors_possibilities[other_color]['people'])
                        colors_possibilities[other_color]['people'].discard(person)
                        len_people = len(people_possibilities[person]['colors'])
                        people_possibilities[person]['colors'].discard(other_color)
                        if len_people > len(people_possibilities[person]['colors']) or len_other_color > len(colors_possibilities[other_color]['people']):
                            changed = True
                            reasoning_chain.append(f"{mapping.people_mapping[person]} cannot be wearing {mapping.color_mapping[other_color]} because they are wearing {mapping.color_mapping[color]}.")
                        if len_other_color > 1 and len(colors_possibilities[other_color]['people']) == 1:
                            reasoning_chain.append(f"{mapping.color_mapping[other_color].capitalize()} must be worn by {mapping.people_mapping[next(iter(colors_possibilities[other_color]['people']))]} because it's the only person left.")
                            people_possibilities[next(iter(colors_possibilities[other_color]['people']))]['colors'] = {other_color}

def apply_clue(clue, positions_possibilities, people_possibilities, colors_possibilities, reasoning_chain, mapping):
    """
    Applies a generic clue to update possibilities.

    Args:
        clue (Clue): The clue object to apply.
        positions_possibilities (dict): Possible positions for each person and color.
        people_possibilities (dict): Possible positions/colors for each person.
        colors_possibilities (dict): Possible positions/people for each color.
        reasoning_chain (list): Logs of reasoning steps.
        mapping (NameColorMapping): Mapping of names and colors.

    Returns:
        bool: True if the possibilities were modified, False otherwise.
    """
    modified = False
    if clue.clue_type == "wearing":
        modified = apply_wearing_clue(clue, positions_possibilities, people_possibilities, colors_possibilities, reasoning_chain, mapping)
    elif clue.clue_type in ["immediate_left", "immediate_right", "left_of", "right_of", "between"]:
        modified = apply_position_clue(clue, positions_possibilities, people_possibilities, colors_possibilities, reasoning_chain, mapping)
    elif clue.clue_type in ["far_left", "far_right", "end"]:
        modified = apply_end_clue(clue, positions_possibilities, people_possibilities, colors_possibilities, reasoning_chain, mapping)
    else:
        reasoning_chain.append(f"Unknown clue type: {clue.clue_type}")

    return modified


def solve_puzzle(clues, n, mapping):
    """
    Solves the puzzle based on the provided clues.

    Args:
        clues (list): List of Clue objects.
        n (int): The number of people/colors.
        mapping (NameColorMapping): Mapping of names and colors.

    Returns:
        tuple: A reasoning chain (list) and the final arrangement (Arrangement).
    """
    positions_possibilities, people_possibilities, colors_possibilities = initialize_possibilities(n, mapping)
    reasoning_chain = []

    max_attempts = 10
    # Apply clues one by one
    for i in range(max_attempts):
        for clue in clues:
            reasoning_chain.append(f"Applying clue: {clue}")
            modified = apply_clue(clue, positions_possibilities, people_possibilities, colors_possibilities, reasoning_chain, mapping)
            if not modified:
                reasoning_chain.append(f"This clue does not give us additional useful information right now.")
            # After applying each clue, propagate constraints
            propagate_constraints(positions_possibilities, people_possibilities, colors_possibilities, reasoning_chain, mapping)
        # After all clues are applied, check if we have a unique solution
        # If for each position, there is only one possible person and one possible color
        # Then we have a solution

        arrangement = None
        if all(len(positions_possibilities[pos]['people']) == 1 and len(positions_possibilities[pos]['colors']) == 1 for pos in positions_possibilities):
            # Construct the arrangement
            people = [next(iter(positions_possibilities[pos]['people'])) for pos in sorted(positions_possibilities)]
            colors = [next(iter(positions_possibilities[pos]['colors'])) for pos in sorted(positions_possibilities)]
            arrangement = Arrangement(people, colors, mapping)
            reasoning_chain.append("All positions have been determined.")
            break
        else:
            reasoning_chain.append("Could not determine a unique arrangement yet. Iterating through clues again.")
            # reasoning_chain.append("Positions possibiilities:")
            # for pos in positions_possibilities:
            #     reasoning_chain.append(f"Position {pos}: {positions_possibilities[pos]}")
            # reasoning_chain.append("People possibiilities:")
            # for person in people_possibilities:
            #     reasoning_chain.append(f"{mapping.people_mapping[person]}: {people_possibilities[person]}")
            # reasoning_chain.append("Colors possibiilities:")
            # for color in colors_possibilities:
            #     reasoning_chain.append(f"Color {mapping.color_mapping[color]}: {colors_possibilities[color]}")
            # if i < max_attempts - 1:
            #     reasoning_chain.append("Iterating through clues again.")

    return reasoning_chain, arrangement

if __name__ == "__main__":
    random.seed(42)
    

    for n in [2]:#range(2, 7):
        n_trials = 4
        for trial in range(n_trials):
            mapping = NameColorMapping(n)
            # arrangement = generate_random_arrangement(n, mapping)
            # print("Random Arrangement:")
            # print(arrangement)

            # Example clues
            generated_clues = generate_clues(n, mapping)
            # print("\nGenerated Clues:")
            # for clue in generated_clues:
            #     print(clue)

            # print("\nFiltering duplicate clues:")
            unique_clues = filter_duplicate_clues(generated_clues)
            # for clue in unique_clues:
            #     print(clue)

            # print("\nFiltering unnecessary clues:")
            necessary_clues = filter_unnecessary_clues(unique_clues, n, mapping)
            print("Puzzle:")
            print(mapping)
            print("\nClues:")
            for clue in necessary_clues:
                print(clue)

            # print("\nGenerating all consistent arrangements:")
            consistent_arrangements = generate_consistent_arrangements(necessary_clues, n, mapping)
            # for i, arr in enumerate(consistent_arrangements):
            #     print(f"Arrangement {i + 1}: {arr}")


            clues = necessary_clues

            # Define clues based on your puzzle
            # clues = [
            #     Clue("end", property_x=mapping.color_mapping_inv['steel'], mapping=mapping),  # The person wearing steel is sitting on the end.
            #     Clue("right_of", property_x='A', property_y='C', mapping=mapping),  # Aaron is somewhere to the right of Cameron.
            #     Clue("far_left", property_x=mapping.color_mapping_inv['black'], mapping=mapping),  # The person wearing black is sitting on the far left.
            #     Clue("right_of", property_x='C', property_y='D', mapping=mapping),  # Cameron is somewhere to the right of Daisy.
            #     Clue("right_of", property_x='A', property_y=mapping.color_mapping_inv['pink'], mapping=mapping),  # Aaron is somewhere to the right of the person wearing pink.
            #     Clue("far_left", property_x='B', mapping=mapping),  # Ben is sitting on the far left.
            #     Clue("end", property_x='E', mapping=mapping),  # Elena is sitting on the end.
            #     Clue("immediate_right", property_x=mapping.color_mapping_inv['sand'], property_y='D', mapping=mapping)  # The person wearing sand is immediately to the right of Daisy.
            # ]

            # print("Solving the puzzle...")
            reasoning_chain, arrangement = solve_puzzle(clues, n, mapping)

            # print("Reasoning Chain:")
            print("\nSolution:")
            for step in reasoning_chain:
                print(step)

            print("\nFinal Arrangement:")
            print(arrangement)
            # if arrangement:
            #     print("Success")
            # else:
            #     print(mapping)
            #     for clue in necessary_clues:
            #         print(clue)
            #     for i, arr in enumerate(consistent_arrangements):
            #         print(f"Arrangement {i + 1}: {arr}")
            #     for step in reasoning_chain:
            #         print(step)
            #     raise ValueError("No unique arrangement could be determined.")
            print("\n\n")
            