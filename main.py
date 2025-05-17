from utils.llm_chat_utils import create_song_structure, get_verse_ranges

book_name = "Genesis"
book_chapter = 1

prompt = f"Split {book_name} {book_chapter} in Christian NIV Bible into 2 sections of similar size which stand alone. If the chapter is between 30 and 45 verses long, split into 3 sections instead, and if the chapter is less than 15 verses, split into one section instead. If the chapter is between 45 and 60 verses long, split into 4 sections instead. If the chapter is over 60 verses long, split into 5 sections instead. give the range of versus separated by commas. Provide the output as numbers in oneline, nothing extra like explanations. Do not iclude the thinking and thought process to save output tokens."

verse_ranges = get_verse_ranges(prompt)
print(f"Verse ranges: {verse_ranges}")

prompt = f"Outline {book_name} {book_chapter}:{verse_ranges[0]} in the bible as a song structure of 4-6 naturally segmented verses, choruses or bridges. Don't write out the text. Never split one verse across stanzas. Never reuse verses. Give no introduction, conclusion or explanation, simply give scripture ranges separated by commas. For each, Label your stanzas inside brackets[] followed by a colon : and followed by only verse range like 5-14, each separated by comma in a single line. give nothing else. example: [Chorus]:18-28,[Bridge]:29-35"

song_structure = create_song_structure(prompt)
print(f"Song structure: {song_structure}")
