import { useEffect, useState, useRef } from "react";
import CameraFeed from "@/components/CameraFeed";
import MotorStatus from "@/components/MotorStatus";
import CANModule from "@/components/CANModule";
import TurnSignal from "@/components/TurnSignal";
import { toast } from "sonner";
import ManualModeModal from "@/components/ManualModeModal";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Cog } from "lucide-react";
import PerformanceMonitor from "@/components/PerformanceMonitor";
import LogsModal from "@/components/LogsModal";
import { useLogsContext } from "@/contexts/LogsContext";
import { endpoints } from "@/config/api";
const RIGHT_SIGNAL_THRESH = 100;
const LEFT_SIGNAL_THRESH = 80;

const Index = () => {
  const [servoAngle, setServoAngle] = useState(0);
  const [motorRPM, setMotorRPM] = useState(0);
  const [fps, setFps] = useState(0);
  const [isManualModeModalOpen, setIsManualModeModalOpen] = useState(false);
  const [frameTime, setFrameTime] = useState(0);
  const [canModules, setCanModules] = useState([
    { id: 1, name: "Módulo Principal", connected: false },
    { id: 2, name: "Módulo Sensor", connected: false },
    { id: 3, name: "Módulo Motor", connected: false },
  ]);
  const [turnSignals, setTurnSignals] = useState({ left: false, right: false });
  const [previousRunning, setPreviousRunning] = useState(false);
  const [systemRunning, setSystemRunning] = useState(false);
  const [previousRPM, setPreviousRPM] = useState(null);
  const [previousDirection, setPreviousDirection] = useState(null);
  const [connectionError, setConnectionError] = useState(false);
  const { logs, addLog, clearLogs } = useLogsContext();
  const [logsModalOpen, setLogsModalOpen] = useState(false);
  const connectionErrorRef = useRef(false);
  const navigate = useNavigate();

  const handleManualModeConfirm = async () => {
    setIsManualModeModalOpen(false);
    try {
      await fetch(endpoints.manualMode, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: true })
      });
    } catch (err) {
      console.error('Erro ao ativar modo manual:', err);
    }
    navigate('/manual-mode');
  };

  const rightSignalThresh = 100;
  const leftSignalThresh = 80;

  useEffect(() => {
  const interval = setInterval(() => {
    fetch(endpoints.carInfo)
      .then(res => res.json())
      .then(data => {
        if (data.manual_mode && data.webview) {
          navigate('/manual-mode');
          return;
        }
        const speed = data.car_info.CAR_SPEED_DATA;
        const running = data.running;
        const direction = data.car_info.CAR_DIRECTION_DATA;
        const enrich = (base: string) => {
          if (logsModalOpen && data.time_info) {
            return `${base} | FPS: ${data.time_info.fps} | FrameTime: ${data.time_info.total_processing_time}ms`;
          }
          return base;
        }; 
        setServoAngle(direction);
        setSystemRunning(running);
        setMotorRPM(speed);
        
        if (connectionErrorRef.current) {
          connectionErrorRef.current = false;
          setConnectionError(false);
          addLog('success', 'system', 'Conexão restabelecida', enrich('Veículo voltou a responder.'));
        }

        if (previousRunning !== running) {
          if (running) {
            addLog('success', 'system', 'Sistema ativado', enrich('O veículo autônomo está ativo.'));
          } else {
            addLog('warning', 'system', 'Sistema desativado', enrich('O veículo autônomo foi desativado.'));
          }
          setPreviousRunning(running);
        }

        // Verifica e loga somente se houve alteração no RPM
        if (previousRPM !== speed) {
          if (speed > 0) {
            addLog('success', 'motor', 'Motor DC rodando', enrich(`RPM: ${speed}`));
          } else if (speed === 0) {
            addLog('warning', 'motor', 'Motor DC parado', enrich('RPM: 0'));
          } else if (speed < 0) {
            addLog('error', 'motor', 'Motor DC em valor negativo inesperado', enrich(`RPM: ${speed}`));
          }
          setPreviousRPM(speed);
        }

        // Verifica e loga somente se houve alteração na direção do servo
        if (previousDirection !== direction) {
          addLog('info', 'navigation', 'Direção alterada', `Servo ângulo: ${direction}°`);
          setPreviousDirection(direction);
        }

        // Lógica dos sinais direcionais
        if (direction === 90) {
          setTurnSignals({ left: false, right: false });
        } else if (direction > rightSignalThresh) {
          setTurnSignals({ left: false, right: true });
        } else if (direction < leftSignalThresh) {
          setTurnSignals({ left: true, right: false });
        }

        // Atualização de métricas adicionais
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

        if (!connectionErrorRef.current) {
          addLog(
            'error',
            'system',
            'Falha de comunicação',
            'Não foi possível obter dados do veículo. Verifique se o servidor está ativo.'
          );
          connectionErrorRef.current = true;
          setConnectionError(true);
        }
      });
  }, 500);

    return () => clearInterval(interval);
  }, [previousRPM, previousRunning, previousDirection, addLog, logsModalOpen, navigate]);

  useEffect(() => {
    if (!previousRunning && systemRunning) {
      toast.success("Dashboard conectado ao veículo autônomo", {
        position: "top-right",
      });
    }
    setPreviousRunning(systemRunning);
  }, [previousRunning, systemRunning]);

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
              <LogsModal
                logs={logs}
                onClearLogs={clearLogs}
                open={logsModalOpen}
                onOpenChange={setLogsModalOpen}
              />
              <div
                onClick={() => setIsManualModeModalOpen(true)}
                className="px-3 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors duration-100 cursor-pointer flex items-center justify-center"
              >
                <Cog className="h-6 w-6" />
              </div>
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
      <ManualModeModal
        isOpen={isManualModeModalOpen}
        onClose={() => setIsManualModeModalOpen(false)}
        onConfirm={handleManualModeConfirm}
      />
    </div>
  );
};

export default Index;
