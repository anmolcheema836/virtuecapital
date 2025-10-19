# process_pdfs.py

import os
import re
from PyPDF2 import PdfReader, PdfWriter

def extract_header_text(page):
    """
    Extracts text from the top portion of a PDF page to be used as the header.
    This function extracts all text and then uses a visitor function to identify
    the text with the highest vertical position.

    Args:
        page: A PyPDF2 PageObject.

    Returns:
        A string containing the extracted header text, or None if no text is found.
    """
    highest_y = 0
    header_text = ""
    
    # Visitor function to capture text and its vertical position
    def visitor_body(text, cm, tm, fontDict, fontSize):
        nonlocal highest_y, header_text
        y = tm[5]
        if y > highest_y:
            highest_y = y
            header_text = text.strip()

    page.extract_text(visitor_text=visitor_body)
    
    return header_text if header_text else None

def sanitize_filename(filename):
    """
    Removes characters that are invalid for Windows filenames.

    Args:
        filename: The string to be sanitized.

    Returns:
        A sanitized string suitable for use as a filename.
    """
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def process_pdfs_in_folder(folder_path='.'):
    """
    Processes all PDF files in a given folder to rename them based on
    their header text and correct the orientation of landscape pages.

    Args:
        folder_path: The path to the folder containing the PDFs.
                     Defaults to the current directory.
    """
    # Create a sub-directory for processed files to avoid overwriting originals
    output_folder = os.path.join(folder_path, 'processed')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created directory: {output_folder}")

    # Iterate over all files in the specified directory
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.pdf'):
            input_pdf_path = os.path.join(folder_path, filename)
            print(f"\nProcessing: {filename}")

            try:
                # Open the PDF file
                reader = PdfReader(input_pdf_path)
                writer = PdfWriter()
                
                # --- 1. RENAME BASED ON HEADER ---
                # Get the first page to extract the header
                first_page = reader.pages[0]
                
                # Extract the header text
                header_text = extract_header_text(first_page)
                
                if header_text:
                    # Sanitize the extracted text to create a valid filename
                    sanitized_header = sanitize_filename(header_text)
                    new_filename = f"{sanitized_header}.pdf"
                    print(f"  - Extracted header: '{header_text}' -> New filename: '{new_filename}'")
                else:
                    # If no header is found, use the original filename
                    new_filename = filename
                    print("  - Could not determine header. Using original filename.")
                
                output_pdf_path = os.path.join(output_folder, new_filename)

                # Handle filename conflicts
                counter = 1
                while os.path.exists(output_pdf_path):
                    name, ext = os.path.splitext(new_filename)
                    output_pdf_path = os.path.join(output_folder, f"{name}_{counter}{ext}")
                    counter += 1


                # --- 2. CORRECT PAGE ORIENTATION ---
                rotated_pages = 0
                # Iterate through all pages in the PDF
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    
                    # Check if the page is in landscape orientation (width > height)
                    if page.mediabox.width > page.mediabox.height:
                        # Rotate the page 90 degrees clockwise to make it portrait
                        page.rotate(90)
                        rotated_pages += 1
                    
                    # Add the (potentially rotated) page to the writer object
                    writer.add_page(page)

                if rotated_pages > 0:
                    print(f"  - Rotated {rotated_pages} landscape page(s) to portrait.")
                else:
                    print("  - No landscape pages found to rotate.")

                # --- SAVE THE NEW PDF ---
                # Write the changes to a new PDF file in the 'processed' directory
                with open(output_pdf_path, 'wb') as output_file:
                    writer.write(output_file)
                
                print(f"  - Saved processed file to: {output_pdf_path}")

            except Exception as e:
                print(f"  - An error occurred while processing {filename}: {e}")

if __name__ == '__main__':
    # Get the directory where the script is located
    current_directory = os.path.dirname(os.path.realpath(__file__))
    print(f"Starting PDF processing in: {current_directory}\n")
    process_pdfs_in_folder(current_directory)
    print("\nBatch processing complete.")