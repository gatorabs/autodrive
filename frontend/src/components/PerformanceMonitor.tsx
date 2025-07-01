interface PerformanceMonitorProps {
  fps: number;
  frameTime: number;
}

const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({ fps, frameTime }) => {
  const isError = fps === 0;

  const statusColor = isError ? "bg-red-500" : "bg-green-400";
  const textColorFps = isError ? "text-red-400" : "text-green-400";
  const textColorMs = isError ? "text-red-400" : "text-yellow-400";

  return (
    <div className="bg-gray-800 px-4 py-2 rounded-md flex items-center space-x-4">
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 ${statusColor} rounded-full animate-pulse`}></div>
        <span className="text-sm text-gray-300">FPS:</span>
        <span className={`text-sm font-mono ${textColorFps}`}>{fps}</span>
      </div>
      <div className="w-px h-4 bg-gray-600"></div>
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-300">MS:</span>
        <span className={`text-sm font-mono ${textColorMs}`}>{frameTime}</span>
      </div>
    </div>
  );
};

export default PerformanceMonitor;
