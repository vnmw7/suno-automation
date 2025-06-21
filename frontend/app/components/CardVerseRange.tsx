import { useState } from "react";
import ModalSongs from "./ModalSongs";

interface VerseRangeCardProps {
  range: string;
  bookName: string;
  chapter: number;
  lyrics?: string;
  style?: string;
}

const VerseRangeCard = ({
  range,
  bookName,
  chapter,
  style = "Contemporary Christian",
}: VerseRangeCardProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleCardClick = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };
  return (
    <>
      <button
        className="w-full p-2 bg-sky-50 border border-sky-200 rounded-md text-xs text-slate-700 shadow-sm cursor-pointer hover:bg-sky-100 transition-colors text-left"
        onClick={handleCardClick}
      >
        <div className="flex justify-between items-center">
          <span>Verses: {range}</span>
          <span className="text-blue-600 text-xs">Click to generate song</span>
        </div>
      </button>

      <ModalSongs
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        range={range}
        bookName={bookName}
        chapter={chapter}
        style={style}
      />
    </>
  );
};

export default VerseRangeCard;
