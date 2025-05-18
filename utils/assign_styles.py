import os

import pandas as pd


def separate_books():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file_path = os.path.join(
        base_dir, "data", "bible_song_styles", "song_variation_map.csv"
    )

    df_all = pd.read_csv(csv_file_path, header=None, dtype=str).fillna("")

    style_dataframes = {}

    # Positive Style (first row)
    positive_style_name = df_all.iloc[0, 0]
    positive_style_descriptions = (
        df_all.iloc[0, 1:].replace("", pd.NA).dropna().tolist()
    )
    if positive_style_descriptions:
        style_dataframes[positive_style_name] = pd.DataFrame(
            [positive_style_descriptions],
            columns=[f"Style_{i+1}" for i in range(len(positive_style_descriptions))],
        )
    else:
        style_dataframes[positive_style_name] = pd.DataFrame()

    # Negative Style (second row)
    negative_style_name = df_all.iloc[1, 0]
    negative_style_descriptions = (
        df_all.iloc[1, 1:].replace("", pd.NA).dropna().tolist()
    )
    if negative_style_descriptions:
        style_dataframes[negative_style_name] = pd.DataFrame(
            [negative_style_descriptions],
            columns=[f"Style_{i+1}" for i in range(len(negative_style_descriptions))],
        )
    else:
        style_dataframes[negative_style_name] = pd.DataFrame()

    df_books_raw = df_all.iloc[2:].copy()
    df_books_raw.reset_index(drop=True, inplace=True)

    bible_book_dataframes = {}

    if not df_books_raw.empty:
        df_books_raw["ActualBook"] = df_books_raw.iloc[:, 0].replace("", pd.NA).ffill()

        for book_name, group_df in df_books_raw.groupby("ActualBook"):
            book_specific_df = group_df.iloc[:, 1:-1].copy()

            num_chapter_cols = book_specific_df.shape[1]
            book_specific_df.columns = [f"Style_{i+1}" for i in range(num_chapter_cols)]

            book_specific_df.reset_index(drop=True, inplace=True)

            book_specific_df = book_specific_df.fillna("")

            bible_book_dataframes[book_name] = book_specific_df

    return style_dataframes, bible_book_dataframes


# style_dataframes, bible_book_dataframes = separate_books()

# print("--- Style DataFrames ---")
# for name, df_style in style_dataframes.items():
#     print(f"\n--- DataFrame for: {name} ---")
#     print(df_style)

# print("\n\n--- Bible Book DataFrames ---")

# for name, book_df in bible_book_dataframes.items():
#     print(f"\n--- DataFrame for: {name} ---")
#     print(book_df.head())


def get_style_by_chapter(book_name, chapter_number, tone):
    style_dataframes, bible_book_dataframes = separate_books()

    if book_name not in bible_book_dataframes:
        print(f"Book {book_name} not found.")
        return None

    df = bible_book_dataframes[book_name]

    chapter_to_find_str = str(chapter_number)
    column_name = ""

    for column in df.columns:
        if chapter_to_find_str in df[column].values:
            column_name = column
            break

    if column_name != "":

        if tone == 0:
            df_styles = style_dataframes["Negative Style"]

        if tone == 1:
            df_styles = style_dataframes["Positive Style"]

        style = df_styles[column_name].values[0]
        style = style.split(",") if isinstance(style, str) else style
        style = [s.strip() for s in style if s.strip()]

    return style
