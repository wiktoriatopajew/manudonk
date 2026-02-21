"""
Fix product titles in shopify.csv
Replace "Full Manual Set – ..." with "Workshop Repair Service Manual"
"""
import csv
import re

def fix_title(title):
    """
    Remove 'Full Manual Set' and everything after it, replace with 'Workshop Repair Service Manual'
    """
    if not title or 'Full Manual Set' not in title:
        return title
    
    # Extract the part before "Full Manual Set"
    # Remove any trailing spaces and separators (-, –, —)
    parts = re.split(r'\s+Full Manual Set', title, maxsplit=1)
    base_title = parts[0].strip()
    
    # Remove trailing separators if any
    base_title = re.sub(r'\s*[-–—]\s*$', '', base_title)
    
    # Add new ending
    new_title = f"{base_title} Workshop Repair Service Manual"
    
    return new_title


def main():
    input_file = 'shopify.csv'
    output_file = 'shopify_fixed.csv'
    
    print("🔧 Starting to fix product titles...")
    
    count = 0
    fixed_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # Process each row
        for row_num, row in enumerate(reader):
            if row_num == 0:
                # Header row - write as is
                writer.writerow(row)
                continue
            
            count += 1
            
            # Check if this row has a title (column index 1)
            if len(row) > 1 and row[1]:
                original_title = row[1]
                fixed_title = fix_title(original_title)
                
                if original_title != fixed_title:
                    row[1] = fixed_title
                    fixed_count += 1
                    
                    if fixed_count <= 10:  # Show first 10 changes
                        print(f"\n✓ Changed:")
                        print(f"  FROM: {original_title}")
                        print(f"  TO:   {fixed_title}")
            
            writer.writerow(row)
    
    print(f"\n✅ Done!")
    print(f"📊 Processed {count} rows")
    print(f"🔄 Fixed {fixed_count} titles")
    print(f"💾 Output saved to: {output_file}")


if __name__ == "__main__":
    main()
