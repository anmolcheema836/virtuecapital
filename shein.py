import string
import random

def generate_unique_codes(num_codes: int) -> set:
    """
    Generates a specified number of unique codes based on a fixed pattern.

    Pattern: 'SV4' prefix followed by 12 random alphanumeric characters.
    
    Args:
        num_codes: The number of unique codes to generate.

    Returns:
        A set containing the unique generated codes.
    """
    # Define the constant prefix for the code
    prefix = "SV4"
    
    # Define the character set for the random part (uppercase letters + digits)
    # Excludes potentially confusing characters like 'O' vs '0' or 'I' vs '1' if desired,
    # but for this script, we'll use all standard uppercase and digits.
    alphanumeric_chars = string.ascii_uppercase + string.digits
    
    # Use a set to automatically handle uniqueness.
    # A set cannot contain duplicate items.
    unique_codes = set()
    
    print(f"Generating {num_codes} unique codes...")
    
    # Loop until the set has the desired number of unique codes
    while len(unique_codes) < num_codes:
        # Generate the random 12-character part
        random_part = ''.join(random.choices(alphanumeric_chars, k=12))
        
        # Assemble the full code
        new_code = prefix + random_part
        
        # Add the new code to the set. If it's a duplicate, the set's size won't change.
        unique_codes.add(new_code)
        
    print("Generation complete.")
    return unique_codes

# --- Main execution block ---
if __name__ == "__main__":
    # ==================================================================
    # ==  FILL IN THE NUMBER OF CODES YOU WANT TO GENERATE HERE  ==
    # ==================================================================
    number_of_codes_to_generate = 100000  # <--- CHANGE THIS VALUE
    # ==================================================================

    # Generate the codes by calling the function
    generated_codes = generate_unique_codes(number_of_codes_to_generate)
    
    # Define the output filename
    output_filename = "generated_codes.txt"
    
    try:
        # Write the generated codes to the output file, one code per line
        with open(output_filename, "w") as f:
            for code in sorted(list(generated_codes)):  # Sort the list before writing
                f.write(code + "\n")
        print(f"Successfully saved {len(generated_codes)} codes to '{output_filename}'")
    except IOError as e:
        print(f"Error: Could not write to file '{output_filename}'. Reason: {e}")