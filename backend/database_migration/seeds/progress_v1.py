from datetime import datetime


def get_seeds(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM song_structure_tbl LIMIT 1")
        song_struct_id = cur.fetchone()[0]

    seeds = [
        {
            "pg1_song_struct_id": song_struct_id,
            "pg1_style": "Gospel",
            "pg1_lyrics": "In the beginning, God created the heavens and the earth.",
            "pg1_song_id": "song123",
            "pg1_status": 1,
            "pg1_reviews": 0,
            "pg1_updated_at": datetime.now(),
        },
        {
            "pg1_song_struct_id": song_struct_id,
            "pg1_style": "Choir",
            "pg1_lyrics": "The Lord is my shepherd, I shall not want.",
            "pg1_song_id": "song456",
            "pg1_status": 1,
            "pg1_reviews": 1,
            "pg1_updated_at": datetime.now(),
        },
    ]
    return seeds


def insert_seeds(conn):
    seeds = get_seeds(conn)
    with conn.cursor() as cur:
        for seed in seeds:
            cur.execute(
                """
                INSERT INTO tblprogress_v1 (pg1_song_struct_id, pg1_style, pg1_lyrics, pg1_song_id, pg1_status, pg1_reviews, pg1_updated_at)
                VALUES (%(pg1_song_struct_id)s, %(pg1_style)s, %(pg1_lyrics)s, %(pg1_song_id)s, %(pg1_status)s, %(pg1_reviews)s, %(pg1_updated_at)s)
            """,
                seed,
            )
    conn.commit()
