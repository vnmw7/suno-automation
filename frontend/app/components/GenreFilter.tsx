// app/components/GenreFilter.tsx

interface GenreFilterProps {
  genres: string[];
  selectedGenre: string | null;
  onSelectGenre: (genre: string) => void;
}

export default function GenreFilter({
  genres,
  selectedGenre,
  onSelectGenre,
}: GenreFilterProps) {
  return (
    <div>
      <h3 className="text-md font-semibold mb-2 text-slate-600">Genre</h3>
      <div className="space-y-1.5">
        {genres.map((genre) => (
          <button
            key={genre}
            onClick={() => onSelectGenre(genre)}
            className={`w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors
              ${
                selectedGenre === genre
                  ? "bg-sky-600 text-white font-medium"
                  : "bg-slate-100 hover:bg-slate-200 text-slate-700"
              }`}
          >
            {genre}
          </button>
        ))}
      </div>
    </div>
  );
}
