#!/usr/bin/env python

import argparse
import os
import glob
import textwrap
import torch
import h5py
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm
from arrangement_puzzle.seating_puzzle import load_puzzle_from_disk
from llama_tools.run_llama import generate_response, run_model_generate_with_hidden_states, process_hidden_states
from llama_tools.io import save_hidden_states_to_disk

def main():
    parser = argparse.ArgumentParser(description="Process seating puzzles and save hidden states.")
    parser.add_argument(
        "--puzzle_dir",
        type=str,
        default="/path/to/puzzle_dir",
        help="Directory containing puzzle JSON files."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="/data_volume/adam/seating-puzzles/llama-activations/2/self_output_2",
        help="Directory to save hidden states and output files."
    )
    parser.add_argument(
        "--puzzle_ids",
        type=int,
        nargs="*",
        default=None,
        help="Space-separated list of puzzle IDs to process (e.g. --puzzle_ids 9065 9066). If omitted, process all JSONs."
    )
    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        help="Path or name of the Hugging Face model to use."
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda:0",
        help="Device for inference (e.g., 'cpu', 'cuda:0', 'cuda:1')."
    )
    
    args = parser.parse_args()
    
    puzzle_dir = args.puzzle_dir
    output_dir = args.output_dir
    puzzle_ids = args.puzzle_ids
    model_name = args.model_name
    device_str = args.device

    # Determine device
    device = torch.device(device_str if torch.cuda.is_available() or device_str == "cpu" else "cpu")
    print(f"Using device: {device}")

    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    model = model.to(device)
    model.eval()
    
    # If puzzle_ids is not provided, we'll process all .json puzzle files in puzzle_dir.
    if not puzzle_ids:
        # Grabs all JSON files in puzzle_dir and extracts numeric IDs from filenames
        puzzle_paths = glob.glob(os.path.join(puzzle_dir, "*.json"))
        puzzle_ids = [
            int(os.path.basename(path).split(".json")[0]) 
            for path in puzzle_paths
        ]
        puzzle_ids.sort()  # If you want them in ascending order
    
    # Make sure output_dir exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Loop over each puzzle ID
    for i in tqdm(puzzle_ids):
        puzzle_path = os.path.join(puzzle_dir, f"{i}.json")
        if not os.path.exists(puzzle_path):
            print(f"Puzzle file not found: {puzzle_path}")
            continue
        
        clues, arrangement, namecolormapping = load_puzzle_from_disk(puzzle_path)
        
        # Prepare a base instruction string with example puzzles
        # (You can move this string to a separate file if you prefer.)
        input_str = textwrap.dedent("""
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
        """)
        
        # Append the new puzzle data to the instruction
        input_str += "\n\nPuzzle:\n"
        input_str += str(namecolormapping) + "\n\n"
        input_str += "Clues:\n"
        for clue in clues:
            input_str += str(clue) + "\n"
        input_str += "\nSolution:\n"
        
        tokenized_input = tokenizer(input_str, return_tensors="pt").to(device)

        # generate model output
        output = generate_response(input_str, model, tokenizer, max_length = len(tokenized_input['input_ids'][0]) + 384, device=device)

        # generate hidden states for that output
        response, hidden_states, _ = run_model_generate_with_hidden_states(output, model, tokenizer, device, top_k=1, max_length=1)

        hidden_states_tensor = torch.stack(hidden_states, dim=1) # shape: batch_size, num_layers, sequence_length, hidden_size

        # remove prompt since that will be constant
        hidden_states_tensor = hidden_states_tensor[:,:,len(tokenized_input['input_ids'][0]):,:]
        
        # Prepare output paths
        puzzle_output_dir = os.path.join(output_dir, str(i))
        os.makedirs(puzzle_output_dir, exist_ok=True)
        
        hidden_states_path = os.path.join(puzzle_output_dir, "hidden_states.h5")
        with h5py.File(hidden_states_path, "w") as f:
            f.create_dataset(
                "tensor_data", 
                data=hidden_states_tensor.cpu().numpy(), 
                chunks=True
            )
        
        # Save the final text output (the chain-of-thought or final answer from the model)
        input_text_path = os.path.join(puzzle_output_dir, "input.txt")
        with open(input_text_path, 'w', encoding="utf-8") as f:
            f.write(input_str)

        response_text_path = os.path.join(puzzle_output_dir, "response.txt")
        with open(response_text_path, 'w', encoding="utf-8") as f:
            f.write(response)

if __name__ == "__main__":
    main()