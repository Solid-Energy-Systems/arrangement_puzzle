import re
import random

def swap_attribute(reasoning_step, attribute1, attribute2):
    """
    Swaps occurrences of two attributes (`attribute1` and `attribute2`) in a reasoning step.

    This function replaces all occurrences of `attribute1` with `attribute2` and vice versa 
    within the given reasoning step, in a case-insensitive manner. It also returns a boolean 
    indicating whether any swap was performed.

    Args:
        reasoning_step (str): A single reasoning step as a string.
        attribute1 (str): The first attribute to be swapped.
        attribute2 (str): The second attribute to be swapped.

    Returns:
        tuple: 
            - str: The modified reasoning step with swapped attributes.
            - bool: True if any swaps were made, otherwise False.
    """
    # Create case-insensitive pattern for attributes
    pattern1 = re.compile(re.escape(attribute1), re.IGNORECASE)
    pattern2 = re.compile(re.escape(attribute2), re.IGNORECASE)
    
    # Check if there are any instances to swap
    swapped1 = bool(pattern1.search(reasoning_step))
    swapped2 = bool(pattern2.search(reasoning_step))
    
    # Swap the attributes
    reasoning_step = pattern1.sub('temp', reasoning_step)
    reasoning_step = pattern2.sub(attribute1, reasoning_step)
    reasoning_step = re.sub('temp', attribute2, reasoning_step, flags=re.IGNORECASE)
    
    # Return the modified reasoning_step and whether anything was swapped
    return reasoning_step, swapped1 or swapped2



def swap_attribute_chain(reasoning_chain, namecolormapping, n):
    """
    Randomly selects two attributes and swaps their occurrences in a reasoning chain.

    Depending on the type of attribute (position, color, or person), this function swaps 
    the selected attributes in all steps of the reasoning chain, except for steps that involve 
    reading clues. It returns the modified reasoning chain, the swapped attributes, and a 
    list indicating whether a swap was made for each reasoning step.

    Args:
        reasoning_chain (list of str): A sequence of reasoning steps.
        namecolormapping (NameColorMapping): An object containing mappings of people and colors.
        n (int): The number of positions or entities in the puzzle.

    Returns:
        tuple:
            - list of str: The modified reasoning chain with swapped attributes.
            - str: The first attribute that was swapped.
            - str: The second attribute that was swapped.
            - list of bool: A list where each element corresponds to a reasoning step, 
              indicating whether a swap was performed (True) or not (False).
    """
    # Decide what type of attribute to swap (position, color, person)
    attribute_type = random.choice(['position', 'color', 'person']) 

    # positions are encoded as numbers
    if attribute_type == 'position':
        attribute1 = str(random.randint(0, n - 1))
        attribute2 = str(random.randint(0, n - 1))
        while attribute1 == attribute2:
            attribute2 = str(random.randint(0, n - 1))
    elif attribute_type == 'color':
        attribute1 = random.choice(list(namecolormapping.color_mapping.values()))
        attribute2 = random.choice(list(namecolormapping.color_mapping.values()))
        while attribute1 == attribute2:
            attribute2 = random.choice(list(namecolormapping.color_mapping.values()))
    else:
        attribute1 = random.choice(list(namecolormapping.people_mapping.values()))
        attribute2 = random.choice(list(namecolormapping.people_mapping.values()))
        while attribute1 == attribute2:
            attribute2 = random.choice(list(namecolormapping.people_mapping.values()))
    

    swapped_chain = []
    was_swap = []
    for reasoning_step in reasoning_chain:
        # skip clue reading
        if 'Applying clue' in reasoning_step:
            swapped_chain.append(reasoning_step)
            was_swap.append(False)
            continue
        swapped_step, was_swap_step = swap_attribute(reasoning_step, attribute1, attribute2)
        was_swap.append(was_swap_step)
        swapped_chain.append(swapped_step)

    return swapped_chain, attribute1, attribute2, was_swap