interface MotorStatusProps {
  title: string;
  value: string;
  color: string;
  icon: "rotate" | "gauge";
  maxValue: number;
  currentValue: number;
}

const MotorStatus = ({ title, value, color, icon, maxValue, currentValue }: MotorStatusProps) => {
  
  const percentage = (currentValue / maxValue) * 100;
  const servoRotationAngle = icon === "rotate" ? currentValue - 0 : 180;
  const isMotorRunning = icon === "gauge" && currentValue > 0;

  const spinDuration = isMotorRunning
    ? 5 - (4.8 * (currentValue / maxValue)) // De 5s até 0.2s
    : 0;

  return (
    <div className="bg-gray-700 p-4 rounded-lg">
      <div className="flex items-center mb-2">
        {icon === "rotate" ? (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" style={{ color }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" style={{ color }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
          </svg>
        )}
        <h3 className="text-md font-medium">{title}</h3>
      </div>
      
      <div className="flex justify-between items-center mb-1">
        <span className="text-xl font-bold">{value}</span>
        <span className="text-xs text-gray-400">Máx: {icon === "rotate" ? "180°" : `${maxValue} RPM`}</span>
      </div>

      {/* Visualização do Servo Motor */}
      {icon === "rotate" && (
        <div className="flex justify-center my-4">
          <div className="relative">
            {/* Base do servo */}
            <div className="w-16 h-12 bg-gray-600 rounded-lg border-2 border-gray-500 flex items-center justify-center">
              {/* Eixo central */}
              <div className="w-3 h-3 bg-gray-400 rounded-full relative">
                {/* Braço do servo */}
                <div 
                  className="absolute w-8 h-1 bg-orange-500 rounded-full transition-transform duration-1000 ease-out"
                  style={{ 
                    left: 'calc(50% - 4px)',
                    top: '50%',
                    transform: `translateY(-50%) rotate(${servoRotationAngle}deg)`,
                    transformOrigin: '4px 50%'
                  }}
                >
                  {/* Ponta do braço */}
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-orange-400 rounded-full"></div>
                </div>
              </div>
            </div>
            {/* Indicador de posição */}
            <div className="text-center mt-2">
              <span className="text-xs text-gray-400">
                {currentValue === 90 ? "Centro" : currentValue > 90 ? "Direita" : "Esquerda"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Visualização do Motor DC */}
      {icon === "gauge" && (
        <div className="flex justify-center my-4">
          <div className="relative flex flex-col items-center">
            {/* Base do motor */}
            <div className="w-16 h-12 bg-gray-600 rounded-lg border-2 border-gray-500 flex items-center justify-center">
              {/* Rotor central */}
              <div 
                className="w-8 h-8 border-4 border-yellow-500 rounded-full relative"
                style={{
                  animation: isMotorRunning ? `spin ${spinDuration}s linear infinite` : "none"
                }}
              >
                {/* Indicador de rotação */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1 h-2 bg-yellow-400 rounded-full"></div>
              </div>
            </div>
            {/* Indicador de status */}
            <div className="mt-2 text-center">
              <span className="text-xs text-gray-400 inline-block w-24">
                {isMotorRunning ? "Movimentando" : "Parado"}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="w-full bg-gray-600 rounded-full h-2.5">
        <div 
          className="h-2.5 rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${percentage}%`, backgroundColor: color }}
        ></div>
      </div>
    </div>
  );
};

export default MotorStatus;