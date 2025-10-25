import ocrmypdf
import subprocess
import os

# Input and output files
input_pdf = "NTPC.PDF"
readable_pdf = "NTPC_readable.pdf"
output_txt = "NTPC.txt"

# Step 1: Convert PDF into searchable/readable PDF using OCR
# If the PDF is already text-based, OCR will not harm it
ocrmypdf.ocr(input_pdf, readable_pdf, deskew=True, force_ocr=False)

print(f"Readable PDF saved as: {readable_pdf}")

# Step 2: Extract text from the readable PDF using pdftotext
# Make sure pdftotext is installed and in PATH
subprocess.run(["pdftotext", "-layout", readable_pdf, output_txt], check=True)

print(f"Extracted text saved as: {output_txt}")
