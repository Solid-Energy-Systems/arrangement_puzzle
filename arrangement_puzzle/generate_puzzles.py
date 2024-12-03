from arrangement_puzzle.seating_puzzle import (
    save_puzzle_to_disk, NameColorMapping, Arrangement, Clue,
    generate_clues, filter_duplicate_clues, filter_unnecessary_clues,
    generate_consistent_arrangements
)
import os
from tqdm import tqdm
import random
import argparse

def main(root_dir, n_iters, min_n, max_n):
    """
    Generate seating puzzles and save them to the specified directory.

    Args:
        root_dir (str): The root directory to save puzzles.
        n_iters (int): Number of iterations per group size.
        min_n (int): Minimum number of people/colors.
        max_n (int): Maximum number of people/colors.
    """
    for n in range(min_n, max_n + 1):
        for iter in tqdm(range(n_iters), desc=f"Generating puzzles for {n} people"):
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

if __name__ == "__main__":
    # Define argument parser
    parser = argparse.ArgumentParser(description="Generate seating puzzles and save them to disk.")
    parser.add_argument(
        "root_dir",
        type=str,
        help="Root directory to save the puzzles."
    )
    parser.add_argument(
        "--n_iters", 
        type=int, 
        default=10000, 
        help="Number of puzzles to generate per group size."
    )
    parser.add_argument(
        "--min_n", 
        type=int, 
        default=2, 
        help="Minimum number of people/colors."
    )
    parser.add_argument(
        "--max_n", 
        type=int, 
        default=6, 
        help="Maximum number of people/colors."
    )

    # Parse arguments
    args = parser.parse_args()

    # Call main function with parsed arguments
    main(root_dir=args.root_dir, n_iters=args.n_iters, min_n=args.min_n, max_n=args.max_n)