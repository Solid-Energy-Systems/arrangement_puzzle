import re

from arrangement_puzzle.seating_puzzle import get_position_names, Arrangement, NameColorMapping


def normalize_arrangement(arrangement_str):
    """
    Normalize the arrangement string by removing whitespace and converting to lowercase.
    """
    return re.sub(r'\s+', '', arrangement_str).lower()

def extract_final_arrangement(decoded_output, target_occurrence=4):
    """
    Extract the line immediately following the specified occurrence of "Final Arrangement:".
    
    Args:
        decoded_output (str): The complete output from the model.
        target_occurrence (int): The occurrence of "Final Arrangement:" to target.
        
    Returns:
        str or None: The extracted arrangement string if found; otherwise, None.
    """
    # Find all start indices of "Final Arrangement:"
    pattern = r'Final Arrangement:'
    matches = list(re.finditer(pattern, decoded_output))
    
    if len(matches) < target_occurrence:
        # Not enough occurrences found
        return None
    
    # Get the start index of the target occurrence
    target_match = matches[target_occurrence - 1]  # Zero-based indexing
    start_index = target_match.end()
    
    # Extract the substring starting from the end of the target match
    substring = decoded_output[start_index:]
    
    # Split the substring into lines
    lines = substring.strip().split('\n')
    
    if not lines:
        return None
    
    # Return the first non-empty line
    for line in lines:
        stripped_line = line.strip()
        if stripped_line:
            return stripped_line
    
    return None

def analyze_llm_output(input_string, correct_arrangement, name_color_mapping, tokenizer, puzzle_pos=4):
    """
    Analyzes the LLM's output to categorize tokens and verify the correctness of the final answer.

    Parameters:
    - input_string (str): The combined prompt and LLM output.
    - correct_arrangement (Arrangement): The correct arrangement for verification.
    - name_color_mapping (NameColorMapping): The mapping from labels to actual names and colors.
    - tokenizer: The tokenizer to use for tokenizing the input string.
    - puzzle_pos (int): The position of the LLM's puzzle in the input string (default: 4).

    Returns:
    - token_dict (dict): A dictionary mapping token indices to their categories.
    - final_answer_correct (bool): Whether the LLM's final answer is correct.
    """

    # Step 1: Identify all "Puzzle:" positions
    puzzle_matches = list(re.finditer(r'^Puzzle:', input_string, re.MULTILINE))
    if len(puzzle_matches) < puzzle_pos:
        raise ValueError("The input string does not contain at least four 'Puzzle:' instances.")

    # The fourth "Puzzle:" marks the start of the LLM's puzzle
    llm_puzzle_start = puzzle_matches[puzzle_pos-1].start()

    # Extract the LLM's puzzle and everything after it
    llm_puzzle_and_after = input_string[llm_puzzle_start:]

    # Now, within llm_puzzle_and_after, find "Final answer:" to determine the end of the LLM's solution
    final_answer_match = re.search(r'^Final answer:', llm_puzzle_and_after, re.MULTILINE)
    if not final_answer_match:
        raise ValueError("The LLM's puzzle does not contain a 'Final answer:' section.")

    # The end of the LLM's solution is either the start of the next 'Puzzle:' or the end of the input
    next_puzzle_match = re.search(r'^Puzzle:', llm_puzzle_and_after[final_answer_match.end():], re.MULTILINE)
    if next_puzzle_match:
        llm_solution_end = final_answer_match.end() + next_puzzle_match.start()
    else:
        llm_solution_end = len(llm_puzzle_and_after)

    # Extract the LLM's solution including the final answer text
    llm_solution = llm_puzzle_and_after[:llm_solution_end]

    # Extract the "Final answer:" lines
    final_answer_text = llm_puzzle_and_after[final_answer_match.end():]

    # Split the LLM's solution into lines
    solution_lines = llm_solution.splitlines()

    # Identify sections within the LLM's puzzle
    section_indices = {}
    for i, line in enumerate(solution_lines):
        if line.startswith('Puzzle:'):
            section_indices['puzzle_start'] = i
        elif line.startswith('Clues:'):
            section_indices['clues_start'] = i
        elif line.startswith('Solution:'):
            section_indices['solution_start'] = i
        elif line.startswith('Final answer:'):
            section_indices['final_answer_start'] = i

    # Extract clues from the LLM's 'Clues:' section
    clues_start_index = section_indices['clues_start'] + 1
    clues_end_index = section_indices['solution_start']
    llm_clues_list = [line.strip() for line in solution_lines[clues_start_index:clues_end_index] if line.strip()]

    # Verify that all necessary sections are present
    required_sections = ['puzzle_start', 'clues_start', 'solution_start', 'final_answer_start']
    for section in required_sections:
        if section not in section_indices:
            raise ValueError(f"The LLM's puzzle is missing the '{section.replace('_', ' ')}' section.")

    # Categorize each line within the LLM's puzzle
    line_categories = ['unknown'] * len(solution_lines)
    for i in range(len(solution_lines)):
        if i < section_indices['clues_start']:
            line_categories[i] = 'puzzle'
        elif section_indices['clues_start'] <= i < section_indices['solution_start']:
            line_categories[i] = 'clues'
        elif section_indices['solution_start'] <= i < section_indices['final_answer_start']:
            if solution_lines[i].startswith('Solution:'):
                line_categories[i] = 'solution'
            elif solution_lines[i].startswith('Applying clue:'):
                line_categories[i] = 'solution_clue'
            else:
                line_categories[i] = 'solution_detail'
        elif i >= section_indices['final_answer_start']:
            line_categories[i] = 'final_answer'

    # Build line start positions for mapping
    line_start_positions = []
    cumulative_length = llm_puzzle_start  # Start from the start of the LLM's puzzle
    for line in solution_lines:
        line_start_positions.append(cumulative_length)
        cumulative_length += len(line) + 1  # +1 for newline character

    # Define regex patterns to parse phrases within the lines
    patterns = [
        # Person is at position (with negation)
        (re.compile(r'\b(\w+)\s+(is|must be|cannot be|can\'t be)\s+(?:at|in)\s+position\s+([\w\s]+)\b', re.IGNORECASE),
         lambda m: [('person_at_position', m.group(1), m.group(3).strip(), m.group(2).lower() in ['cannot be', "can't be"], m.start(), m.end())]),
        # Person is wearing color at position (with negation)
        (re.compile(r'\b(\w+)\s+(is|must be|cannot be|can\'t be)\s+wearing\s+(\w+)\s+(?:at|in)\s+position\s+([\w\s]+)\b', re.IGNORECASE),
         lambda m: [('person_wearing_color', m.group(1), m.group(3), m.group(4).strip(), m.group(2).lower() in ['cannot be', "can't be"], m.start(), m.end())]),
        # Person is wearing color (with negation)
        (re.compile(r'\b(\w+)\s+(is|must be|cannot be|can\'t be)\s+wearing\s+(\w+)\b', re.IGNORECASE),
         lambda m: [('person_wearing_color_simple', m.group(1), m.group(3), m.group(2).lower() in ['cannot be', "can't be"], m.start(), m.end())]),
        # Color is at position (with negation)
        (re.compile(r'\b(?:the person|someone)\s+wearing\s+(\w+)\s+(is|must be|cannot be|can\'t be)\s+(?:at|in)\s+position\s+([\w\s]+)\b', re.IGNORECASE),
         lambda m: [('color_at_position', m.group(1), m.group(3).strip(), m.group(2).lower() in ['cannot be', "can't be"], m.start(), m.end())]),
        # Position must have the person wearing color (with negation)
        (re.compile(r'\bposition\s+([\w\s]+)\s+(must have|has|cannot have|can\'t have)\s+(?:someone|the person)\s+wearing\s+(\w+)\b', re.IGNORECASE),
         lambda m: [('position_has_color', m.group(1).strip(), m.group(3), m.group(2).lower() in ['cannot have', "can't have"], m.start(), m.end())]),
        # Position must have person (with negation)
        (re.compile(r'\bposition\s+([\w\s]+)\s+(must have|has|cannot have|can\'t have)\s+(\w+)\b', re.IGNORECASE),
         lambda m: [('position_has_person', m.group(1).strip(), m.group(3), m.group(2).lower() in ['cannot have', "can't have"], m.start(), m.end())]),
        # Immediately left of (with negation)
        (re.compile(r'\b(\w+)\s+(is|must be|cannot be|can\'t be)\s+immediately\s+to\s+the\s+left\s+of\s+(\w+)\b', re.IGNORECASE),
         lambda m: [('immediately_left_of', m.group(1), m.group(3), m.group(2).lower() in ['cannot be', "can't be"], m.start(), m.end())]),
        # Immediately right of (with negation)
        (re.compile(r'\b(\w+)\s+(is|must be|cannot be|can\'t be)\s+immediately\s+to\s+the\s+right\s+of\s+(\w+)\b', re.IGNORECASE),
         lambda m: [('immediately_right_of', m.group(1), m.group(3), m.group(2).lower() in ['cannot be', "can't be"], m.start(), m.end())]),
        # Applying clue
        (re.compile(r'^Applying clue:\s+(.*)$'),
         lambda m: [('clue', m.group(1), False, m.start(), m.end())]),
        # Add more patterns as needed
    ]

    def parse_line(line):
        """
        Parses a line and extracts relevant facts based on predefined patterns.
        Returns a list of facts with their positions within the line.
        Each fact is a tuple: (fact_type, fact_data, is_negated, start, end)
        """
        facts = []
        for pattern, action in patterns:
            for match in pattern.finditer(line):
                extracted_facts = action(match)
                if extracted_facts:
                    facts.extend(extracted_facts)
        return facts

    # Build reverse mappings from NameColorMapping
    # Maps actual names to labels
    name_to_label = {v: k for k, v in name_color_mapping.people_mapping.items()}
    # Maps actual color names (lowercased) to color numbers
    color_to_number = {v.lower(): k for k, v in name_color_mapping.color_mapping.items()}

    def check_fact(fact_type, fact_data, is_negated, correct_arrangement, llm_clues_list):
        """
        Checks whether a parsed fact is correct based on the correct_arrangement and NameColorMapping.
        """
        positions = get_position_names(len(correct_arrangement.people))
        positions = [pos.lower() for pos in positions]
        result = None  # Initialize result as None (unable to determine)

        if fact_type == 'clue':
            clue_text = fact_data[0].strip()
            is_clue_hallucination = clue_text not in llm_clues_list
            if is_clue_hallucination:
                return 'clue_hallucination'  # The clue does not exist
            else:
                return True  # Valid clue
        elif fact_type == 'person_at_position':
            person_name, position = fact_data[0], fact_data[1].lower()
            person_label = name_to_label.get(person_name)
            if person_label and position in positions:
                position_index = positions.index(position)
                expected_person_label = correct_arrangement.people[position_index]
                result = (expected_person_label == person_label)
        elif fact_type == 'person_wearing_color':
            person_name, color_name, position = fact_data[0], fact_data[1].lower(), fact_data[2].lower()
            person_label = name_to_label.get(person_name)
            color_number = color_to_number.get(color_name)
            if person_label and color_number and position in positions:
                position_index = positions.index(position)
                expected_person_label = correct_arrangement.people[position_index]
                expected_color_number = correct_arrangement.mapping.get(person_label)
                expected_position_label = correct_arrangement.people[position_index]
                result = (expected_color_number == color_number and expected_person_label == person_label)
        elif fact_type == 'person_wearing_color_simple':
            person_name, color_name = fact_data[0], fact_data[1].lower()
            person_label = name_to_label.get(person_name)
            color_number = color_to_number.get(color_name)
            if person_label and color_number:
                expected_color_number = correct_arrangement.mapping.get(person_label)
                result = (expected_color_number == color_number)
        elif fact_type == 'color_at_position':
            color_name, position = fact_data[0].lower(), fact_data[1].lower()
            color_number = color_to_number.get(color_name)
            if color_number and position in positions:
                position_index = positions.index(position)
                person_label = correct_arrangement.people[position_index]
                expected_color_number = correct_arrangement.mapping.get(person_label)
                result = (expected_color_number == color_number)
        elif fact_type == 'position_has_person':
            position, person_name = fact_data[0].lower(), fact_data[1]
            person_label = name_to_label.get(person_name)
            if person_label and position in positions:
                position_index = positions.index(position)
                expected_person_label = correct_arrangement.people[position_index]
                result = (expected_person_label == person_label)
        elif fact_type == 'position_has_color':
            position, color_name = fact_data[0].lower(), fact_data[1].lower()
            color_number = color_to_number.get(color_name)
            if color_number and position in positions:
                position_index = positions.index(position)
                person_label = correct_arrangement.people[position_index]
                expected_color_number = correct_arrangement.mapping.get(person_label)
                result = (expected_color_number == color_number)
        elif fact_type == 'immediately_left_of':
            person1_name, person2_name = fact_data[0], fact_data[1]
            person1_label = name_to_label.get(person1_name)
            person2_label = name_to_label.get(person2_name)
            if person1_label and person2_label:
                try:
                    index1 = correct_arrangement.people.index(person1_label)
                    index2 = correct_arrangement.people.index(person2_label)
                    result = (index1 + 1 == index2)
                except ValueError:
                    result = False
        elif fact_type == 'immediately_right_of':
            person1_name, person2_name = fact_data[0], fact_data[1]
            person1_label = name_to_label.get(person1_name)
            person2_label = name_to_label.get(person2_name)
            if person1_label and person2_label:
                try:
                    index1 = correct_arrangement.people.index(person1_label)
                    index2 = correct_arrangement.people.index(person2_label)
                    result = (index1 - 1 == index2)
                except ValueError:
                    result = False

        if result is None:
            return None  # Unable to determine
        else:
            return not result if is_negated else result

    # List to store facts with their positions and correctness
    fact_spans = []

    for i, line in enumerate(solution_lines):
        category = line_categories[i]
        line_start_pos = line_start_positions[i]
        if category in ['solution_detail', 'solution_clue']:
            # Attempt to parse and categorize
            facts = parse_line(line)
            if facts:
                for fact in facts:
                    fact_type = fact[0]
                    fact_data = fact[1:-3]  # Exclude is_negated, start, and end positions
                    is_negated = fact[-3]
                    fact_start_in_line = fact[-2]
                    fact_end_in_line = fact[-1]
                    fact_start = line_start_pos + fact_start_in_line
                    fact_end = line_start_pos + fact_end_in_line
                    is_correct = check_fact(fact_type, fact_data, is_negated, correct_arrangement, llm_clues_list)
                    # Store the fact with its span and correctness
                    if is_correct == 'clue_hallucination':
                        category = 'clue_hallucination'
                    elif is_correct is True:
                        category = 'solution_correct'
                    elif is_correct is False:
                        category = 'solution_incorrect'
                    else:
                        category = 'solution_unknown'

                    fact_spans.append({
                        'start': fact_start,
                        'end': fact_end,
                        'correctness': is_correct,
                        'category': category
                    })
        else:
            # For other categories, process as needed
            pass

    # Function to decide token category based on overlapping facts
    def decide_token_category(overlapping_categories, line_category):
        if 'clue_hallucination' in overlapping_categories:
            return 'clue_hallucination'
        elif 'solution_incorrect' in overlapping_categories:
            return 'solution_incorrect'
        elif 'solution_correct' in overlapping_categories:
            return 'solution_correct'
        elif 'solution_unknown' in overlapping_categories:
            return 'solution_unknown'
        else:
            return line_category

    # Tokenize the input string with offsets
    encoded = tokenizer(input_string, return_offsets_mapping=True, add_special_tokens=False)
    token_dict = {}
    for idx, (start, end) in enumerate(encoded['offset_mapping']):
        if start < llm_puzzle_start:
            # Tokens before the LLM's puzzle are part of the prompt
            token_dict[idx] = 'prompt'
        elif llm_puzzle_start <= start < llm_puzzle_start + len(llm_solution):
            # Tokens within the LLM's solution (including final answer)
            token_pos_in_solution = start - llm_puzzle_start
            # Determine which line this token belongs to
            line_index = None
            for j in range(len(line_start_positions)):
                line_start = line_start_positions[j]
                if line_start <= start < line_start_positions[j] + len(solution_lines[j]) + 1:
                    line_index = j
                    break
            if line_index is not None:
                line_category = line_categories[line_index]
                # Get overlapping facts
                overlapping_categories = []
                for fact in fact_spans:
                    if start < fact['end'] and end > fact['start']:
                        overlapping_categories.append(fact['category'])
                token_category = decide_token_category(overlapping_categories, line_category)
                token_dict[idx] = token_category
            else:
                token_dict[idx] = 'unknown'
        else:
            # Tokens after the LLM's solution
            token_dict[idx] = 'after'

    # Step 4: Check if the final answer is correct
    # Parse the final answer text
    final_answer_lines = final_answer_text.strip().split('\n')
    final_answer_mapping = {}

    # Pattern to match entries like "Name (Color color_name, position position_name)"
    pattern = re.compile(r'(\w+)\s+\(Color\s+(\w+),\s+position\s+([\w\s]+)\)', re.IGNORECASE)

    for line in final_answer_lines:
        matches = pattern.findall(line)
        for match in matches:
            person_name, color_name, position_name = match
            final_answer_mapping[person_name] = {
                'color': color_name.lower(),
                'position': position_name.lower().strip()
            }

    # Verify the final answer against the correct arrangement
    final_answer_correct = True

    # Build the expected order of names and positions from the correct arrangement
    expected_positions = get_position_names(len(correct_arrangement.people))
    expected_positions = [pos.lower() for pos in expected_positions]
    expected_person_data = {}

    for person_label, position_name in zip(correct_arrangement.people, expected_positions):
        person_name = name_color_mapping.people_mapping[person_label]
        expected_color_number = correct_arrangement.mapping.get(person_label)
        expected_color_name = name_color_mapping.color_mapping.get(expected_color_number).lower()
        expected_person_data[person_name] = {
            'color': expected_color_name,
            'position': position_name
        }

    # Check that all expected persons are present
    expected_persons_set = set(expected_person_data.keys())
    final_answer_persons_set = set(final_answer_mapping.keys())

    if expected_persons_set != final_answer_persons_set:
        final_answer_correct = False
    else:
        # Now, check for each person
        for person_name in expected_persons_set:
            expected_data = expected_person_data[person_name]
            answer_data = final_answer_mapping[person_name]

            # Check color
            if answer_data['color'] != expected_data['color']:
                final_answer_correct = False
                break

            # Check position
            if answer_data['position'] != expected_data['position']:
                final_answer_correct = False
                break

    return token_dict, final_answer_correct