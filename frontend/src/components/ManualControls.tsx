import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface ManualControlData {
  x: number; // steering -1 to 1
  y: number; // throttle 0 to 1
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
    `${active ? 'bg-blue-600 text-white hover:bg-blue-500' : 'bg-gray-700 text-gray-200 hover:bg-gray-600'}`;

  return (
    <div
      className="flex w-full max-w-xl flex-col items-center space-y-6"
      style={{ touchAction: 'manipulation' }}
    >
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
          <span className="w-10 text-left text-xs text-gray-400">0%</span>
          <input
            type="range"
            min={0}
            max={100}
            value={throttle}
            onChange={handleThrottleChange}
            className="h-2 flex-1 cursor-pointer appearance-none rounded-lg bg-gray-700"
          />
          <span className="w-12 text-right text-xs text-gray-400">100%</span>
        </div>
        <div className="mt-2 text-xs text-gray-400 text-center">
          {throttle > 0 && `Avançando (${throttle}%)`}
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

        <div className="flex w-full flex-wrap items-center justify-center gap-4">
          <Button
            variant="outline"
            size="lg"
            className={`${steeringButtonClass(steering === -1)} min-w-[4.5rem] flex-1 sm:flex-none`}
            onClick={() => handleSteeringChange(-1)}
          >
            <ChevronLeft className="w-5 h-5" />
          </Button>

          <Button
            variant="outline"
            size="lg"
            className={`${steeringButtonClass(steering === 0)} min-w-[4.5rem] flex-1 sm:flex-none`}
            onClick={() => handleSteeringChange(0)}
          >
            <Square className="w-4 h-4" />
          </Button>

          <Button
            variant="outline"
            size="lg"
            className={`${steeringButtonClass(steering === 1)} min-w-[4.5rem] flex-1 sm:flex-none`}
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
