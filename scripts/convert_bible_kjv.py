#!/usr/bin/env python3
"""
Convert Bible data from aruljohn/Bible-kjv format to verse-checker API format.
This script processes all Bible books and creates a comprehensive dataset.
"""

import json
import os
from pathlib import Path

def convert_bible_kjv_to_api_format(bible_kjv_dir, output_file):
    """
    Convert Bible-kjv repository format to verse-checker API format.
    
    Args:
        bible_kjv_dir (Path): Path to the Bible-kjv repository
        output_file (Path): Output file for the converted data
    """
    
    verses = []
    total_verses = 0
    
    # Get all JSON files (exclude Books.json and other non-book files)
    json_files = [f for f in os.listdir(bible_kjv_dir) if f.endswith('.json') and f != 'Books.json']
    json_files.sort()  # Sort alphabetically
    
    print(f"📚 Processing {len(json_files)} Bible books...")
    
    for json_file in json_files:
        book_name = json_file.replace('.json', '')
        
        # Handle special naming conventions
        if book_name.startswith('1') or book_name.startswith('2') or book_name.startswith('3'):
            # Add space for books like "1Corinthians" -> "1 Corinthians"
            book_name = book_name[0] + ' ' + book_name[1:]
        elif book_name == 'SongofSolomon':
            book_name = 'Song of Solomon'
        
        file_path = os.path.join(bible_kjv_dir, json_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                book_data = json.load(f)
            
            book_verses = 0
            
            # Process chapters
            for chapter_data in book_data.get('chapters', []):
                chapter_num = int(chapter_data['chapter'])
                
                # Process verses
                for verse_data in chapter_data.get('verses', []):
                    verse_num = int(verse_data['verse'])
                    verse_text = verse_data['text']
                    
                    # Convert to our API format
                    verse_entry = {
                        "book": book_name,
                        "chapter": chapter_num,
                        "verse": verse_num,
                        "text": verse_text
                    }
                    
                    verses.append(verse_entry)
                    book_verses += 1
            
            total_verses += book_verses
            print(f"  ✅ {book_name}: {book_verses} verses")
            
        except Exception as e:
            print(f"  ❌ Error processing {json_file}: {e}")
    
    # Save the converted data
    print(f"\n💾 Saving {total_verses} verses to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(verses, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully converted {total_verses} Bible verses!")
    print(f"📊 Coverage: {len(json_files)} books")
    print(f"📁 Output file: {output_file}")
    
    return total_verses

def main():
    """Main function to convert Bible data."""
    
    # Paths
    bible_kjv_dir = Path("/Users/sharo2/downloads/Bible-kjv")
    data_dir = Path("/Users/sharo2/downloads/verse-checker/data")
    output_file = data_dir / "bible_complete.json"
    
    # Check if Bible-kjv directory exists
    if not bible_kjv_dir.exists():
        print(f"❌ Bible-kjv directory not found: {bible_kjv_dir}")
        print("Please make sure you've cloned the Bible-kjv repository.")
        return
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    print("🔄 Converting Bible-kjv data to verse-checker API format...")
    print(f"📁 Source: {bible_kjv_dir}")
    print(f"📁 Output: {output_file}")
    print()
    
    # Convert the data
    total_verses = convert_bible_kjv_to_api_format(bible_kjv_dir, output_file)
    
    print(f"\n🎉 Conversion complete!")
    print(f"📈 Your API will now have {total_verses} Bible verses for recognition!")
    print(f"\n📋 Next steps:")
    print(f"1. Replace data/bible.json with the new complete dataset:")
    print(f"   cp {output_file} {data_dir}/bible.json")
    print(f"2. Test locally to make sure it works")
    print(f"3. Commit and push to trigger a new deployment")

if __name__ == "__main__":
    main()