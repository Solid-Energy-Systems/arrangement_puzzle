#!/usr/bin/env python

import argparse
import os
import torch
import h5py
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM

# Assume these helper functions are imported or defined in the same file.
from arrangement_puzzle.solve_puzzle import solve_puzzle
from arrangement_puzzle.seating_puzzle import load_puzzle_from_disk

prompt = """
The following are example puzzles. Your objective is to figure out where everyone is sitting, and what color shirts they are wearing.
Note that the same clue can reference the same person multiple times.
For instance, the clue "The person wearing red is not sitting to the right of Adam" could be satisfied by Adam wearing red.

Puzzle:
Andrew and Bethany are sitting in a row on 2 chairs. They are wearing shirts with colors emerald and turquoise. Each of them is wearing a different color.

Clues:
Andrew is not immediately to the left of the person wearing turquoise.
Andrew is immediately to the left of Bethany.

Solution:
Applying clue: Andrew is not immediately to the left of the person wearing turquoise.
This clue does not give us additional useful information right now.
Applying clue: Andrew is immediately to the left of Bethany.
Because Bethany is at one of positions left or right, Andrew must be in position left.
Because Andrew is at position left, Bethany must be in position right.
Andrew cannot be at position right because they are at position left.
Position right must have Bethany because they're the only person left.
Could not determine a unique arrangement yet. Iterating through clues again.
Applying clue: Andrew is not immediately to the left of the person wearing turquoise.
Because Andrew is at position left, the person wearing turquoise must be in position left.
Bethany is wearing one of emerald or turquoise, and they are at position right which contains someone wearing emerald.
Therefore, Bethany must be wearing emerald at position right.
Emerald cannot be worn by someone at position left because it is worn by someone at position right.
Position left must have someone wearing turquoise because it's the only color left.
Emerald is worn by one of Andrew or Bethany, and it is at position right which contains Bethany.
Therefore, position right must have Bethany wearing emerald.
Applying clue: Andrew is immediately to the left of Bethany.
This clue does not give us additional useful information right now.
All positions have been determined.

Final answer:
Andrew (Color turquoise, position left), Bethany (Color emerald, position right)


Puzzle:
Aidan and Bradley are sitting in a row on 2 chairs. They are wearing shirts with colors orange and peach. Each of them is wearing a different color.

Clues:
The person wearing orange is not immediately to the left of the person wearing peach.
Aidan is sitting on the far right.

Solution:
Applying clue: The person wearing orange is not immediately to the left of the person wearing peach.
Because the person wearing peach is at one of positions left or right, the person wearing orange must be in position right.
Because the person wearing orange is at position right, the person wearing peach must be in position left.
Peach cannot be worn by someone at position right because it is worn by someone at position left.
Position right must have someone wearing orange because it's the only color left.
Applying clue: Aidan is sitting on the far right.
Aidan must be at position right.
Bradley cannot be at position right because they are at position left.
Position right must have Aidan because they're the only person left.
Bradley is wearing one of orange or peach, and they are at position left which contains someone wearing peach.
Therefore, Bradley must be wearing peach at position left.
Peach is worn by one of Aidan or Bradley, and it is at position left which contains Bradley.
Therefore, position left must have Bradley wearing peach.
Aidan is wearing one of orange or peach, and they are at position right which contains someone wearing orange.
Therefore, Aidan must be wearing orange at position right.
Orange is worn by one of Aidan or Bradley, and it is at position right which contains Aidan.
Therefore, position right must have Aidan wearing orange.
All positions have been determined.

Final answer:
Bradley (Color peach, position left), Aidan (Color orange, position right)


Puzzle:
Alice and Bella are sitting in a row on 2 chairs. They are wearing shirts with colors coral and lavender. Each of them is wearing a different color.

Clues:
Alice is not somewhere to the left of Bella.
The person wearing lavender is not immediately to the left of Alice.

Solution:
Applying clue: Alice is not somewhere to the left of Bella.
Because Bella is at one of positions left or right, Alice must be in position right.
Because Alice is at position right, Bella must be in position left.
Bella cannot be at position right because they are at position left.
Position right must have Alice because they're the only person left.
Applying clue: The person wearing lavender is not immediately to the left of Alice.
Because Alice is at position right, the person wearing lavender must be in position right.
Bella is wearing one of coral or lavender, and they are at position left which contains someone wearing coral.
Therefore, Bella must be wearing coral at position left.
Coral cannot be worn by someone at position right because it is worn by someone at position left.
Position right must have someone wearing lavender because it's the only color left.
Coral is worn by one of Alice or Bella, and it is at position left which contains Bella.
Therefore, position left must have Bella wearing coral.
Alice is wearing one of coral or lavender, and they are at position right which contains someone wearing lavender.
Therefore, Alice must be wearing lavender at position right.
Lavender is worn by one of Alice or Bella, and it is at position right which contains Alice.
Therefore, position right must have Alice wearing lavender.
All positions have been determined.

Final answer:
Bella (Color coral, position left), Alice (Color lavender, position right)
"""

def main():
    parser = argparse.ArgumentParser(description="Generate and save hidden states for puzzle solutions.")
    
    parser.add_argument(
        "--puzzle_dir",
        type=str,
        default="/path/to/puzzles",
        help="Directory where puzzle JSON files are located."
    )
    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        help="Path or identifier of a Hugging Face causal LM (e.g., gpt2, EleutherAI/gpt-neo-2.7B)."
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda:0",
        help="Compute device (e.g., 'cpu', 'cuda:0', 'cuda:1')."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="/data_volume/adam/seating-puzzles/llama-activations/2/correct_hidden_prompt",
        help="Directory to store the hidden state HDF5 files and input texts."
    )
    parser.add_argument(
        "--max_puzzles",
        type=int,
        default=10000,
        help="Number of puzzles to attempt from 0 to max_puzzles-1."
    )
    
    args = parser.parse_args()

    puzzle_dir = args.puzzle_dir
    model_name = args.model_name
    device_str = args.device
    output_dir = args.output_dir
    max_puzzles = args.max_puzzles

    # Determine the actual device
    device = torch.device(device_str if torch.cuda.is_available() or device_str == "cpu" else "cpu")
    print(f"Using device: {device}")

    # 1. Load the model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.to(device)
    model.eval()

    # 2. Tokenize the prompt once (move to GPU if applicable)
    prompt_tokens = tokenizer(prompt, return_tensors="pt").to(device)

    # 3. Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # 4. Process puzzles in the range [0, max_puzzles)
    for i in tqdm(range(max_puzzles)):
        puzzle_path = os.path.join(puzzle_dir, f"{i}.json")
        
        # If the file doesn't exist, skip
        if not os.path.isfile(puzzle_path):
            continue
        
        # Load puzzle data
        clues, arrangement, namecolormapping = load_puzzle_from_disk(puzzle_path)
        
        # Solve puzzle (assumed to be a function you have available)
        reasoning_chain, arrangement_solved = solve_puzzle(clues, 2, namecolormapping)

        # Check for arrangement mismatch
        if str(arrangement) != str(arrangement_solved):
            print(f"Arrangement mismatch for puzzle {i}, skipping...")
            continue
        
        # Build the text input that follows the prompt
        input_str = "\n\nPuzzle:\n"
        input_str += str(namecolormapping) + "\n\n"
        input_str += "Clues:\n"
        for clue in clues:
            input_str += str(clue) + "\n"
        input_str += "\nSolution:\n"
        for step in reasoning_chain:
            input_str += step + "\n"
        input_str += "\nFinal answer:\n"
        input_str += str(arrangement_solved)

        # Replace numeric positions with textual "left" / "right"
        input_str = input_str.replace("0", "left")
        input_str = input_str.replace("1", "right")

        # 5. Tokenize the puzzle content and append to prompt tokens
        input_str_tokens = tokenizer(input_str, return_tensors="pt").to(device)

        # Concatenate prompt tokens + puzzle tokens
        # Skip the first token of the new puzzle tokens (common approach to avoid double BOS tokens)
        all_tokens = torch.cat(
            [prompt_tokens["input_ids"], input_str_tokens["input_ids"][:, 1:]], 
            dim=1
        )
        all_tokens_mask = torch.cat(
            [prompt_tokens["attention_mask"], input_str_tokens["attention_mask"][:, 1:]], 
            dim=1
        )

        # 6. Generate hidden states with no gradient
        with torch.no_grad():
            outputs = model(
                input_ids=all_tokens,
                attention_mask=all_tokens_mask,
                output_hidden_states=True
            )

        # 7. Stack hidden states: shape => [batch, num_layers, seq_len, hidden_dim]
        # Then remove the prompt portion from the sequence dimension
        # Here outputs.hidden_states is a tuple of length num_layers, each shape = [batch, seq_len, hidden_dim]
        stacked_hidden_states = torch.stack(outputs.hidden_states, dim=1)
        # stacked_hidden_states shape => [batch=1, num_layers, seq_len, hidden_dim]
        # We only want from prompt_tokens['input_ids'].shape[1]: onward
        stacked_hidden_states = stacked_hidden_states[0, :, prompt_tokens["input_ids"].shape[1]:, :]

        # 8. Save hidden states to HDF5
        puzzle_output_dir = os.path.join(output_dir, str(i))
        os.makedirs(puzzle_output_dir, exist_ok=True)
        h5_file_path = os.path.join(puzzle_output_dir, "hidden_states.h5")

        with h5py.File(h5_file_path, "w") as f:
            f.create_dataset(
                "tensor_data", 
                data=stacked_hidden_states.cpu().numpy(), 
                chunks=True
            )

        # 9. Save the input text
        text_file_path = os.path.join(puzzle_output_dir, "input.txt")
        with open(text_file_path, "w", encoding="utf-8") as file:
            file.write(input_str)


if __name__ == "__main__":
    main()