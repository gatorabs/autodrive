import React, { useState, useRef, useEffect } from 'react';

interface JoystickData {
  x: number; // -1 to 1 (left to right)
  y: number; // -1 to 1 (down to up)
}

interface VirtualJoystickProps {
  onJoystickMove: (data: JoystickData) => void;
  size?: number;
}

const VirtualJoystick: React.FC<VirtualJoystickProps> = ({
  onJoystickMove,
  size = 120,
}) => {
  const [isActive, setIsActive] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const joystickRef = useRef<HTMLDivElement>(null);
  const knobRef = useRef<HTMLDivElement>(null);

  const maxDistance = size / 2 - 20; // Leave some padding

  const handleStart = (clientX: number, clientY: number) => {
    setIsActive(true);
    handleMove(clientX, clientY);
  };

  const handleMove = (clientX: number, clientY: number) => {
    if (!isActive || !joystickRef.current) return;

    const rect = joystickRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    let deltaX = clientX - centerX;
    let deltaY = clientY - centerY;

    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    if (distance > maxDistance) {
      deltaX = (deltaX / distance) * maxDistance;
      deltaY = (deltaY / distance) * maxDistance;
    }

    setPosition({ x: deltaX, y: deltaY });

    // Normalize to -1 to 1 range
    const normalizedX = deltaX / maxDistance;
    const normalizedY = -deltaY / maxDistance; // Invert Y for intuitive up/down

    onJoystickMove({ x: normalizedX, y: normalizedY });
  };

  const handleEnd = () => {
    setIsActive(false);
    setPosition({ x: 0, y: 0 });
    onJoystickMove({ x: 0, y: 0 });
  };

  // Mouse events
  const handleMouseDown = (e: React.MouseEvent) => {
    handleStart(e.clientX, e.clientY);
  };

  const handleMouseMove = (e: MouseEvent) => {
    handleMove(e.clientX, e.clientY);
  };

  const handleMouseUp = () => {
    handleEnd();
  };

  // Touch events
  const handleTouchStart = (e: React.TouchEvent) => {
    e.preventDefault();
    const touch = e.touches[0];
    handleStart(touch.clientX, touch.clientY);
  };

  const handleTouchMove = (e: TouchEvent) => {
    e.preventDefault();
    const touch = e.touches[0];
    handleMove(touch.clientX, touch.clientY);
  };

  const handleTouchEnd = (e: TouchEvent) => {
    e.preventDefault();
    handleEnd();
  };

  useEffect(() => {
    if (isActive) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.addEventListener('touchmove', handleTouchMove);
      document.addEventListener('touchend', handleTouchEnd);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [isActive]);

  return (
    <div className="flex flex-col items-center space-y-4">
      <div
        ref={joystickRef}
        className="relative bg-gray-700 rounded-full border-4 border-gray-600 select-none"
        style={{ width: size, height: size }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        {/* Base circle with grid pattern */}
        <div className="absolute inset-2 rounded-full border border-gray-500 opacity-30">
          <div className="absolute top-1/2 left-0 right-0 h-px bg-gray-500 opacity-50"></div>
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-500 opacity-50"></div>
        </div>
        
        {/* Movable knob */}
        <div
          ref={knobRef}
          className={`absolute w-8 h-8 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full shadow-lg transition-all duration-75 ${
            isActive ? 'scale-110 shadow-blue-400/50' : ''
          }`}
          style={{
            left: `calc(50% + ${position.x}px - 16px)`,
            top: `calc(50% + ${position.y}px - 16px)`,
          }}
        >
          <div className="absolute inset-1 bg-white rounded-full opacity-30"></div>
        </div>
      </div>
      
      {/* Direction indicators */}
      <div className="flex flex-col items-center text-xs text-gray-400">
        <div className="text-center">
          <div>X: {position.x.toFixed(0)}px</div>
          <div>Y: {position.y.toFixed(0)}px</div>
        </div>
      </div>
    </div>
  );
};

export default VirtualJoystick;