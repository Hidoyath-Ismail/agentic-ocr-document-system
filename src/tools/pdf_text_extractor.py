from pypdf import PdfReader # Importing PdfReader from pypdf to read PDF files
from pathlib import Path # Importing Path from pathlib to handle file paths


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF using pypdf (best-effort)."""
    reader = PdfReader(pdf_path) # Loads the PDF file
    pages_text = [] # List to hold text from each page

    for page in reader.pages:
        text = page.extract_text() or "" # Extract text from each page
        pages_text.append(text) # Append the extracted text to the list

    return "\n".join(pages_text).strip() # Join all pages' text with newlines


if __name__ == "__main__": # For testing the function
    sample_pdf = Path("data/uploads/Receipt-2398-4319.pdf") # Path to a sample PDF file
    text = extract_text_from_pdf(str(sample_pdf)) # Extract text from the sample PDF
    print(f"Extracted text length: {len(text)}") # Print the length of the extracted text
    print(text[:500]) # Print the first 500 characters of the extracted text
