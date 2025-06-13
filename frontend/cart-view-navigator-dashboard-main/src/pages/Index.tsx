import { useEffect, useState } from "react";
import CameraFeed from "@/components/CameraFeed";
import MotorStatus from "@/components/MotorStatus";
import CANModule from "@/components/CANModule";
import TurnSignal from "@/components/TurnSignal";
import { toast } from "sonner";
import PerformanceMonitor from "@/components/PerformanceMonitor";

const Index = () => {
  const [servoAngle, setServoAngle] = useState(0);
  const [motorRPM, setMotorRPM] = useState(0);
  const [fps, setFps] = useState(0);
  const [frameTime, setFrameTime] = useState(0);
  const [canModules, setCanModules] = useState([
    { id: 1, name: "Módulo Principal", connected: false },
    { id: 2, name: "Módulo Sensor", connected: false },
    { id: 3, name: "Módulo Motor", connected: false },
  ]);
  const [turnSignals, setTurnSignals] = useState({ left: false, right: false });
  const [previousRunning, setPreviousRunning] = useState(false);
  const [systemRunning, setSystemRunning] = useState(false);
  
  var rightSignalThresh = 100;
  var leftSignalThresh = 80;

  useEffect(() => {
    const interval = setInterval(() => {
      fetch("http://192.168.15.12:5000/api/car_info")
        .then(res => res.json())
        .then(data => {
          setServoAngle(data.car_info.direction);
          setSystemRunning(data.running);
          setMotorRPM(data.car_info.speed);

          if (data.car_info.direction == 90) {
            setTurnSignals({ left: false, right: false });
          } else if (data.car_info.direction > rightSignalThresh) {
            setTurnSignals({ left: false, right: true });
          } else if (data.car_info.direction < leftSignalThresh){
            setTurnSignals({ left: true, right: false });
          }

          if (data.time_info) {
            setFps(data.time_info.fps);
            setFrameTime(data.time_info.total_processing_time);
          }
        })
        .catch(err => {
          console.error("Erro ao obter direção:", err);
          setSystemRunning(false);
          setTurnSignals({ left: false, right: false });
          setFps(0);
          setFrameTime(0);
        });
    }, 500);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!previousRunning && systemRunning) {
      toast.success("Dashboard conectado ao veículo autônomo", {
        position: "top-right",
      });
    }
    setPreviousRunning(systemRunning);
  }, [systemRunning]);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto p-4">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-center"></h1>
          <div className="flex justify-between items-center mt-2">
            <div className="flex items-center space-x-4">
              <div className={`px-4 py-2 rounded-md bg-gray-800`}>
                <span className={systemRunning ? "text-green-400" : "text-red-400"}>
                  ● {systemRunning ? "Sistema Ativo" : "Sistema Inativo"}
                </span>
              </div>
              <PerformanceMonitor fps={fps} frameTime={frameTime} />
            </div>
            <div className="flex space-x-4">
              <TurnSignal direction="left" active={turnSignals.left} />
              <TurnSignal direction="right" active={turnSignals.right} />
            </div>
          </div>
        </header>

        {/* Câmeras - Apenas 3 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <CameraFeed label="Fasor" systemRunning={systemRunning} />
          <CameraFeed label="Filtros" systemRunning={systemRunning} />
          <CameraFeed label="Detecção de Objetos" systemRunning={systemRunning} />
        </div>

        {/* Painel de informações */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold mb-4 border-b border-gray-700 pb-2">Status do Motor</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <MotorStatus
                title="Servo Motor"
                value={`${servoAngle}°`}
                color="#f97316"
                icon="rotate"
                maxValue={180}
                currentValue={servoAngle}  // Converter para escala 0-180
              />
              <MotorStatus
                title="Motor DC"
                value={`${motorRPM} PWM`}
                color="#eab308"
                icon="gauge"
                maxValue={255}
                currentValue={motorRPM}
              />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold mb-4 border-b border-gray-700 pb-2">Rede CAN</h2>
            <div className="space-y-3">
              {canModules.map((module) => (
                <CANModule
                  key={module.id}
                  name={module.name}
                  connected={module.connected}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
