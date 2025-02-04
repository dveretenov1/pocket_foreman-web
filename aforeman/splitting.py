import os
from PyPDF2 import PdfReader, PdfWriter
import math

def get_pdf_size(pdf_path):
    """Get PDF file size in MB"""
    return os.path.getsize(pdf_path) / (1024 * 1024)

def split_pdf_by_size(input_pdf, max_size_mb):
    """
    Split PDF into multiple files based on maximum size in MB
    Returns: List of output PDF paths
    """
    # Get input PDF size and reader
    input_size = get_pdf_size(input_pdf)
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    
    # Calculate number of splits needed
    num_splits = math.ceil(input_size / max_size_mb)
    pages_per_split = math.ceil(total_pages / num_splits)
    
    output_files = []
    
    # Create splits
    for split_num in range(num_splits):
        writer = PdfWriter()
        
        # Calculate page range for this split
        start_page = split_num * pages_per_split
        end_page = min((split_num + 1) * pages_per_split, total_pages)
        
        # Add pages to this split
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        
        # Save split PDF
        output_path = f"{os.path.splitext(input_pdf)[0]}_part{split_num + 1}.pdf"
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        output_files.append(output_path)
        
        # Verify split size
        split_size = get_pdf_size(output_path)
        print(f"Split {split_num + 1} size: {split_size:.2f} MB")
    
    return output_files

def main():
    # Example usage
    input_pdf = "Mechanical Only.pdf"  # Replace with your PDF path
    max_size_mb = 5  # Maximum size per split in MB
    
    try:
        print(f"Original PDF size: {get_pdf_size(input_pdf):.2f} MB")
        output_files = split_pdf_by_size(input_pdf, max_size_mb)
        print("\nSplit complete!")
        print("Output files:", output_files)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()