from arrangement_puzzle.seating_puzzle import save_puzzle_to_disk, NameColorMapping, Arrangement, Clue, generate_clues, filter_duplicate_clues, filter_unnecessary_clues, generate_consistent_arrangements
import os
from tqdm import tqdm
import random

root_dir = "/data_volume/adam/seating-puzzles"
n_iters = 10000

for n in range(2, 7):
    for iter in tqdm(range(n_iters)):
        savedir = os.path.join(root_dir, str(n))
        os.makedirs(savedir, exist_ok=True)
        filepath = os.path.join(savedir, f"{iter}.json")
        
        # Check if the file already exists
        if os.path.exists(filepath):
            continue  # Skip the rest of the loop if the file exists
        
        name_color_mapping = NameColorMapping(n)
        generated_clues = generate_clues(n, name_color_mapping)
        unique_clues = filter_duplicate_clues(generated_clues)
        necessary_clues = filter_unnecessary_clues(unique_clues, n, name_color_mapping)
        consistent_arrangements = generate_consistent_arrangements(necessary_clues, n, name_color_mapping)

        assert len(consistent_arrangements) == 1
        
        save_puzzle_to_disk(necessary_clues, consistent_arrangements[0], name_color_mapping, filepath)
