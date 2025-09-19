#!/usr/bin/env python3
"""
Estimate which Bible books are likely available based on verse count
Uses the Bible structure to calculate book boundaries
"""

def get_bible_books_with_verse_counts():
    """Return list of Bible books with approximate verse counts"""
    # Approximate verse counts for each Bible book (rounded)
    old_testament = [
        ("Genesis", 1533),
        ("Exodus", 1213), 
        ("Leviticus", 859),
        ("Numbers", 1288),
        ("Deuteronomy", 959),
        ("Joshua", 658),
        ("Judges", 618),
        ("Ruth", 85),
        ("1 Samuel", 810),
        ("2 Samuel", 695),
        ("1 Kings", 816),
        ("2 Kings", 719),
        ("1 Chronicles", 943),
        ("2 Chronicles", 822),
        ("Ezra", 280),
        ("Nehemiah", 406),
        ("Esther", 167),
        ("Job", 1070),
        ("Psalms", 2461),
        ("Proverbs", 915),
        ("Ecclesiastes", 222),
        ("Song of Songs", 117),
        ("Isaiah", 1292),
        ("Jeremiah", 1364),
        ("Lamentations", 154),
        ("Ezekiel", 1273),
        ("Daniel", 357),
        ("Hosea", 197),
        ("Joel", 73),
        ("Amos", 146),
        ("Obadiah", 21),
        ("Jonah", 48),
        ("Micah", 105),
        ("Nahum", 47),
        ("Habakkuk", 56),
        ("Zephaniah", 53),
        ("Haggai", 38),
        ("Zechariah", 211),
        ("Malachi", 55)
    ]
    
    new_testament = [
        ("Matthew", 1071),
        ("Mark", 678), 
        ("Luke", 1151),
        ("John", 879),
        ("Acts", 1007),
        ("Romans", 433),
        ("1 Corinthians", 437),
        ("2 Corinthians", 257),
        ("Galatians", 149),
        ("Ephesians", 155),
        ("Philippians", 104),
        ("Colossians", 95),
        ("1 Thessalonians", 89),
        ("2 Thessalonians", 47),
        ("1 Timothy", 113),
        ("2 Timothy", 83),
        ("Titus", 46),
        ("Philemon", 25),
        ("Hebrews", 303),
        ("James", 108),
        ("1 Peter", 105),
        ("2 Peter", 61),
        ("1 John", 105),
        ("2 John", 13),
        ("3 John", 14),
        ("Jude", 25),
        ("Revelation", 404)
    ]
    
    return old_testament + new_testament

def estimate_available_books(current_verse_count):
    """Estimate which books are available based on current verse count"""
    
    books = get_bible_books_with_verse_counts()
    total_verses = sum(count for _, count in books)
    
    print(f"📊 Estimating available books for {current_verse_count:,} verses")
    print(f"🎯 Total Bible verses: {total_verses:,}")
    print(f"📈 Current progress: {(current_verse_count/total_verses)*100:.1f}%")
    print("\n" + "="*60)
    
    # Calculate cumulative totals
    cumulative = 0
    available_books = []
    partial_books = []
    
    for book_name, verse_count in books:
        if cumulative + verse_count <= current_verse_count:
            # Full book is available
            available_books.append(book_name)
            cumulative += verse_count
        elif cumulative < current_verse_count:
            # Partial book is available
            remaining_verses = current_verse_count - cumulative
            percentage = (remaining_verses / verse_count) * 100
            partial_books.append((book_name, remaining_verses, verse_count, percentage))
            cumulative = current_verse_count
            break
        else:
            break
    
    print("✅ FULLY AVAILABLE BOOKS:")
    print("-" * 30)
    
    if not available_books:
        print("   None yet - upload just starting")
    else:
        # Group by testament
        ot_books = []
        nt_books = []
        
        old_testament_names = [book for book, _ in get_bible_books_with_verse_counts()[:39]]
        
        for book in available_books:
            if book in old_testament_names:
                ot_books.append(book)
            else:
                nt_books.append(book)
        
        if ot_books:
            print("   📜 Old Testament:")
            for book in ot_books:
                print(f"      • {book}")
        
        if nt_books:
            print("   ✝️  New Testament:")
            for book in nt_books:
                print(f"      • {book}")
    
    if partial_books:
        print(f"\n⏳ PARTIALLY AVAILABLE:")
        print("-" * 30)
        for book_name, available, total, percentage in partial_books:
            print(f"   • {book_name}: {available:,}/{total:,} verses ({percentage:.1f}%)")
    
    print(f"\n📚 Summary:")
    print(f"   • Complete books: {len(available_books)}")
    print(f"   • Partial books: {len(partial_books)}")
    
    if available_books or partial_books:
        print(f"\n🔍 You can search for verses from:")
        searchable_books = available_books + [book for book, _, _, _ in partial_books]
        for book in searchable_books[:10]:  # Show first 10
            print(f"   • {book}")
        if len(searchable_books) > 10:
            print(f"   • ... and {len(searchable_books) - 10} more books")

def main():
    print("🔍 Bible Books Availability Estimator")
    print("="*60)
    
    # Based on your last known progress
    last_known_count = 550
    
    print(f"📊 Using last known verse count: {last_known_count:,}")
    print("(This is an estimate based on your upload progress)")
    print()
    
    estimate_available_books(last_known_count)
    
    print("\n" + "="*60)
    print("💡 To get the exact current count:")
    print("   1. Check your Render dashboard for service status") 
    print("   2. Set PINECONE_API_KEY and run: python3 check_progress.py")
    print("   3. Or wait for your service to come back online")

if __name__ == "__main__":
    main()