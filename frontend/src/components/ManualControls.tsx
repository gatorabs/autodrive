import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface ManualControlData {
  x: number; // steering -1 to 1
  y: number; // throttle -1 to 1
}

interface ManualControlsProps {
  onControlChange: (data: ManualControlData) => void;
}

const ManualControls: React.FC<ManualControlsProps> = ({ onControlChange }) => {
  const [steering, setSteering] = useState(0);
  const [throttle, setThrottle] = useState(0);

  useEffect(() => {
    onControlChange({ x: steering, y: throttle / 100 });
  }, [steering, throttle, onControlChange]);

  const handleThrottleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setThrottle(Number(event.target.value));
  };

  const handleSteeringChange = (value: number) => {
    setSteering(value);
  };

  const resetThrottle = () => setThrottle(0);
  const resetSteering = () => setSteering(0);

  const steeringButtonClass = (active: boolean) =>
    `w-16 ${active ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-gray-700 text-gray-200 hover:bg-gray-600'}`;

  return (
    <div className="flex flex-col items-center space-y-6 w-full">
      <div className="w-full">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold text-white">Acelerador</span>
          <button
            type="button"
            onClick={resetThrottle}
            className="text-xs text-blue-300 hover:text-blue-200"
          >
            Resetar
          </button>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-xs text-gray-400 w-8 text-left">Ré</span>
          <input
            type="range"
            min={-100}
            max={100}
            value={throttle}
            onChange={handleThrottleChange}
            className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
          />
          <span className="text-xs text-gray-400 w-12 text-right">Frente</span>
        </div>
        <div className="mt-2 text-xs text-gray-400 text-center">
          {throttle > 0 && `Avançando (${throttle}%)`}
          {throttle < 0 && `Recuando (${Math.abs(throttle)}%)`}
          {throttle === 0 && 'Parado'}
        </div>
      </div>

      <div className="w-full">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold text-white">Direção</span>
          <button
            type="button"
            onClick={resetSteering}
            className="text-xs text-blue-300 hover:text-blue-200"
          >
            Centralizar
          </button>
        </div>

        <div className="flex items-center justify-center space-x-4">
          <Button
            variant="outline"
            size="lg"
            className={steeringButtonClass(steering === -1)}
            onClick={() => handleSteeringChange(-1)}
          >
            <ChevronLeft className="w-5 h-5" />
          </Button>

          <Button
            variant="outline"
            size="lg"
            className={steeringButtonClass(steering === 0)}
            onClick={() => handleSteeringChange(0)}
          >
            <Square className="w-4 h-4" />
          </Button>

          <Button
            variant="outline"
            size="lg"
            className={steeringButtonClass(steering === 1)}
            onClick={() => handleSteeringChange(1)}
          >
            <ChevronRight className="w-5 h-5" />
          </Button>
        </div>
        <div className="mt-2 text-xs text-gray-400 text-center">
          {steering === 0 && 'Centro'}
          {steering === -1 && 'Virando para a esquerda'}
          {steering === 1 && 'Virando para a direita'}
        </div>
      </div>
    </div>
  );
};

export default ManualControls;
