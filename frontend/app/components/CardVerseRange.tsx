import { useState } from 'react';
import { generateSong as callGenerateSongAPI } from '../lib/api';

interface VerseRangeCardProps {
  range: string;
  bookName: string;
  chapter: number;
  lyrics?: string;
  style?: string;
}

const VerseRangeCard = ({ range, bookName, chapter, lyrics = '', style = 'Contemporary Christian' }: VerseRangeCardProps) => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateSong = async () => {
    setIsLoading(true);
    setMessage(null);
    setError(null);    try {
      const title = `${bookName} ${chapter}:${range}`;      const requestPayload = {
        strBookName: bookName,
        intBookChapter: chapter,
        strVerseRange: range,
        strStyle: style,
        strTitle: title,
      };
      
      console.log('Sending request payload:', requestPayload);
      
      const result = await callGenerateSongAPI(requestPayload);

      if (result.success) {
        setMessage('Song generated successfully!');
        console.log('Song generation result:', result.result);
      } else {
        setError(result.error || result.message || 'Failed to generate song');
      }
    } catch (err) {
      setError('An unexpected error occurred');
      console.error('Error generating song:', err);
    } finally {
      setIsLoading(false);
    }
  };  return (
    <div className="p-2 bg-sky-50 border border-sky-200 rounded-md text-xs text-slate-700 shadow-sm">
      <div className="flex justify-between items-center">
        <span>Verses: {range}</span>
        <button
          className={`ml-2 px-2 py-1 text-white rounded text-xs transition-colors ${
            isLoading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-green-500 hover:bg-green-600'
          }`}
          onClick={handleGenerateSong}
          disabled={isLoading}
        >
          {isLoading ? 'Generating...' : 'Generate Song'}
        </button>
      </div>
      
      {message && (
        <div className="mt-2 p-2 bg-green-100 border border-green-300 rounded text-green-700">
          {message}
        </div>
      )}
      
      {error && (
        <div className="mt-2 p-2 bg-red-100 border border-red-300 rounded text-red-700">
          {error}
        </div>
      )}
    </div>
  );
};

export default VerseRangeCard;
