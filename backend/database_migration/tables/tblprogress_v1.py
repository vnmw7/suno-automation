TABLE_NAME = "tblprogress_v1"


def create_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE {TABLE_NAME} (
                pg1_id bigserial primary key,
                pg1_created_at timestamptz default now(),
                pg1_song_struct_id bigint references song_structure_tbl(id),
                pg1_style text,
                pg1_lyrics text,
                pg1_song_id varchar,
                pg1_status smallint,
                pg1_reviews smallint,
                pg1_updated_at timestamptz default now()
            );
        """
        )
