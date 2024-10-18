from arrangement_puzzle.seating_puzzle import *
from arrangement_puzzle.solve_puzzle import *
import random
import os
import shutil
from tqdm import tqdm
random.seed(42)


def test_trials():
    n_trials = 100
    save_dir = "/tmp/seating_puzzles"
    os.makedirs(save_dir, exist_ok=True)

    for n in range(2,6):
        n_success = 0
        n_fail = 0
        print(f"Running trials for n={n}")
        for trial in tqdm(range(n_trials)):
            if run_one_trial(n, trial, save_dir):
                n_success += 1
            else:
                n_fail += 1
        print(f"Success: {n_success}, Fail: {n_fail}, Fraction: {n_success / n_trials}")
    shutil.rmtree(save_dir)


def run_one_trial(n, trial, save_dir):
    mapping = NameColorMapping(n)
    generated_clues = generate_clues(n, mapping)
    unique_clues = filter_duplicate_clues(generated_clues)
    necessary_clues = filter_unnecessary_clues(unique_clues, n, mapping)
    consistent_arrangements = generate_consistent_arrangements(necessary_clues, n, mapping)

    assert len(consistent_arrangements) == 1, f"Expected 1 consistent arrangement, got {len(consistent_arrangements)}"
    save_puzzle_to_disk(necessary_clues, consistent_arrangements[0], mapping, f"{save_dir}/{n}_{trial}.json")
    necessary_clues_2, consistent_arrangements_2, mapping_2 = load_puzzle_from_disk(f"{save_dir}/{n}_{trial}.json")
    assert len(necessary_clues) == len(necessary_clues_2), f"Clue length mismatch during puzzle saving and loading. Expected {len(necessary_clues)}, got {len(necessary_clues_2)}"
    for i in range(len(necessary_clues)):
        assert str(necessary_clues[i]) == str(necessary_clues_2[i]), f"Clue mismatch during puzzle saving and loading. Expected {necessary_clues[i]}, got {necessary_clues_2[i]}"
    assert str(consistent_arrangements[0]) == str(consistent_arrangements_2), f"Arrangement mismatch during puzzle saving and loading. Expected {consistent_arrangements}, got {consistent_arrangements_2}"
    assert str(mapping) == str(mapping_2), f"NameColorMapping mismatch during puzzle saving and loading. Expected {mapping}, got {mapping_2}"

    parsed_arrangement = parse_arrangement(str(consistent_arrangements[0]), mapping)
    assert str(parsed_arrangement) == str(consistent_arrangements[0]), f"Arrangement string parse error. Expected {consistent_arrangements[0]}, got {parsed_arrangement}"
    reasoning_chain, arrangement = solve_puzzle(necessary_clues, n, mapping)
    if arrangement is None:
        return False
    assert str(arrangement) == str(consistent_arrangements[0]), f"Incorrect puzzle solve. Expected {consistent_arrangements[0]}, got {arrangement}"
    return True

if __name__ == "__main__":
    test_trials()