import React, { useEffect, useState } from "react";

interface CameraFeedProps {
  label: string;
  systemRunning: boolean
}

const keyMap: Record<string, string> = {
  Fasor: "NORMAL_FRAME",
  Filtros: "EDGES_FRAME",
  "Detecção de Objetos": "OBJECT_FRAME",
};

const CameraFeed: React.FC<CameraFeedProps> = ({ label }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [imgKey, setImgKey] = useState(0); // forçar reload do <img>

  const key = keyMap[label];
  const streamUrl = `http://192.40.226.220:5000/video_feed/${key}`;

  // Verificação periódica da disponibilidade do stream
  useEffect(() => {
    const interval = setInterval(() => {
      const testImg = new Image();
      testImg.src = streamUrl + `?check=${Date.now()}`; // Bypass cache
      testImg.onload = () => {
        if (hasError) {
          setHasError(false);
          setIsLoading(true); // Recarregar visivelmente
          setImgKey(prev => prev + 1); // Força <img> a recarregar
        }
      };
      testImg.onerror = () => {
        if (!hasError) {
          setHasError(true);
          setIsLoading(false);
        }
      };
    }, 3000); // a cada 5s

    return () => clearInterval(interval);
  }, [streamUrl, hasError]);
  
  // Inicializar estados ao mudar label
  useEffect(() => {
    setIsLoading(true);
    setHasError(false);
    setImgKey(prev => prev + 1);
  }, [label]);

  if (!key) {
    return (
      <div className="bg-red-800 text-white p-4 rounded-lg">
        <h3 className="text-lg font-semibold">Erro</h3>
        <p>Chave de câmera inválida para: {label}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="bg-gray-700 px-3 py-2 border-b border-gray-600">
        <div className="flex justify-between items-center">
          <span>{label}</span>
          {isLoading ? (
            <span className="animate-pulse text-yellow-400">●</span>
          ) : hasError ? (
            <span className="text-red-500">●</span>
          ) : (
            <span className="text-green-400">●</span>
          )}
        </div>
      </div>

      <div className="aspect-video bg-black/50 relative">
        {isLoading && !hasError && (
          <div className="absolute inset-0 flex items-center justify-center z-10 bg-black/60">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
          </div>
        )}

        {hasError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-red-400 bg-black/70 z-10">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>Erro na transmissão</span>
          </div>
        ) : (
          <img
            key={imgKey}
            src={`${streamUrl}?refresh=${imgKey}`} 
            alt={`Feed da câmera - ${label}`}
            className="w-full h-full object-contain"
            onLoad={() => setIsLoading(false)}
            onError={() => {
              setHasError(true);
              setIsLoading(false);
            }}
          />
        )}

        {!hasError && (
          <>
            <div className="absolute top-0 right-0 text-xs text-gray-400 m-2 z-20">
              {new Date().toLocaleTimeString()}
            </div>
            <div className="absolute inset-0 grid grid-cols-3 grid-rows-3 opacity-10 z-0 pointer-events-none">
              {[...Array(9)].map((_, i) => (
                <div key={i} className="border border-gray-600" />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default CameraFeed;
