ai_prompts = {
    "gen_song_struct": """
                        Make a song structure using the Book of {strBookName} chapter {intBookChapter}, strictly from verses {strVerseRange} in the Bible only. The song will have 4-6 (or more if applicable) naturally segmented based on the Bible verse contents. Strictly do not overlap nor reuse the verses in each segment. Strictly the output should be in json format: {{'stanza label': 'bible verse range number only', 'stanza label': 'bible verse range number only'}}. Do not provide any explanation only the json output.

                        Here are the core building blocks. 
                        1. Verse
                        Purpose: To tell the story, set the scene, and provide details. Each verse typically has different lyrics that move the narrative forward.
                        Musical Feel: Often less intense or energetic than the chorus. The melody is usually consistent from one verse to the next, but the words change.
                        2. Chorus
                        Purpose: To state the main idea or theme of the song. It's the big, memorable payoff that listeners wait for.
                        Musical Feel: Usually the most energetic, "biggest," and catchiest part of the song. The lyrics and melody are almost always identical (or very similar) each time the chorus appears. The song's title is often found here.
                        3. Bridge
                        Purpose: To provide a contrast and a break from the verse-chorus-verse-chorus repetition. It introduces a new perspective, a shift in emotion, or a musical "detour" before returning to the final chorus.
                        Musical Feel: It feels different from the rest of the song, often using a new chord progression, melody, and lyrical theme. It builds tension that is released by the final chorus.
                        4. Intro (Introduction)
                        Purpose: To set the mood, key, and tempo of the song. It grabs the listener's attention and prepares them for what's to come.
                        Musical Feel: Can be anything from a simple instrumental riff, a drum fill, a vocal "ad-lib," or a unique soundscape.
                        5. Outro (or Coda)
                        Purpose: To bring the song to a conclusion. It's the opposite of the intro.
                        Musical Feel: Can be a fade-out, where the music gradually gets quieter; a hard stop on a final chord; or a new section that winds the song down. The term Coda is a more formal label (from classical music) for a unique ending section.
                        6. Pre-Chorus (or Lift)
                        Purpose: A short section that builds anticipation right before the chorus. It acts as a ramp-up, creating tension that the chorus releases.
                        Musical Feel: It feels like it's climbing or accelerating. The lyrics and melody are typically the same each time it appears.
                        7. Post-Chorus
                        Purpose: A section that comes immediately after a chorus to either extend the energy or provide a brief cooldown before the next verse begins.
                        Musical Feel: Often features a simple, repetitive vocal hook (like "oohs" and "aahs") or an instrumental riff. A famous example is the "Rah rah ah-ah-ah!" part in Lady Gaga's "Bad Romance."
                        8. Hook
                        Purpose: This is less of a structural section and more of a functional element. The hook is the single most catchy, memorable part of a song—the part that gets "stuck in your head."
                        Where it's found: The hook is often the main line of the chorus, but it can also be an instrumental riff (like the synth in Van Halen's "Jump") or a short vocal phrase.
                        9. Refrain
                        Purpose: A line or phrase that repeats, but unlike a full chorus, it's usually part of another section (most often the verse).
                        Distinction from Chorus: A chorus is its own distinct, standalone section. A refrain is a smaller, repeated part within a section. For example, at the end of each verse in Bob Dylan's "Blowin' in the Wind," the line "The answer, my friend, is blowin' in the wind" serves as a refrain.
                        10. Solo / Instrumental Break
                        Purpose: A section that showcases a particular instrument (e.g., guitar, saxophone, piano, synth). It provides a break from the vocals and adds instrumental flavor.
                        Musical Feel: Often played over the chord progression of a verse or chorus.
                        11. Middle 8
                        Purpose: This is essentially another name for a Bridge. It gets its name from often being eight bars long and appearing in the middle of the song. The term is very common in UK pop music.
                        12. Breakdown
                        Purpose: A section where the arrangement is stripped back, often leaving only the rhythm section (drums and bass) or just a single element. It lowers the energy to create dynamic contrast before building it back up.
                        Common in: Electronic, Metal, and Hard Rock music.

                        Putting It All Together: Common Structures
                        Using these labels, songs are often assembled into common structures.
                        Verse-Chorus-Verse-Chorus (A simple, repetitive form)
                        Verse-Chorus-Verse-Chorus-Bridge-Chorus (The most common structure in pop music)
                        Verse-Pre-Chorus-Chorus-Verse-Pre-Chorus-Chorus-Bridge-Chorus-Outro (A more developed, dynamic structure)
                        AABA (Common in older pop and jazz):
                        A: Verse
                        A: Verse
                        B: Bridge
                        A: Verse
                        """
}