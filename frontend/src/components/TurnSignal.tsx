
import { useEffect, useState } from 'react';

interface TurnSignalProps {
  direction: "left" | "right";
  active: boolean;
}

const TurnSignal = ({ direction, active }: TurnSignalProps) => {
  const [blinking, setBlinking] = useState(false);
  
  useEffect(() => {
    if (!active) {
      setBlinking(false);
      return;
    }
    
    const interval = setInterval(() => {
      setBlinking(prev => !prev);
    }, 500);
    
    return () => clearInterval(interval);
  }, [active]);
  
  return (
    <div className={`
      px-3 py-2 rounded-lg
      ${active ? (blinking ? 'bg-yellow-500' : 'bg-yellow-900/30') : 'bg-gray-700'} 
      transition-colors duration-100
    `}>
      {direction === "left" ? (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
        </svg>
      )}
    </div>
  );
};

export default TurnSignal;
