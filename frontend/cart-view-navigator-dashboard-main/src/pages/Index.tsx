import { useEffect, useState } from "react";
import CameraFeed from "@/components/CameraFeed";
import MotorStatus from "@/components/MotorStatus";
import CANModule from "@/components/CANModule";
import TurnSignal from "@/components/TurnSignal";
import { toast } from "sonner";

const Index = () => {
  const [servoAngle, setServoAngle] = useState(0);
  const [motorRPM, setMotorRPM] = useState(0);
  const [canModules, setCanModules] = useState([
    { id: 1, name: "Módulo Principal", connected: false },
    { id: 2, name: "Módulo Sensor", connected: false },
    { id: 3, name: "Módulo Motor", connected: false },
  ]);
  const [turnSignals, setTurnSignals] = useState({ left: false, right: false });
  const [previousRunning, setPreviousRunning] = useState(false);
  const [systemRunning, setSystemRunning] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      fetch("http://192.168.15.12:5000/api/car_info")
        .then(res => res.json())
        .then(data => {
          setServoAngle(data.car_info.direction);
          setSystemRunning(data.running);
          setMotorRPM(data.car_info.speed);
        })
        .catch(err => {
          console.error("Erro ao obter direção:", err);
          setSystemRunning(false);
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


  // Simulação de dados em tempo real
  useEffect(() => {
    const interval = setInterval(() => {
      // Simular RPM do motor entre 0 e 3000
      
      //const newRPM = Math.floor(Math.random() * 3000);
      //setMotorRPM(newRPM);

      // Simular mudança aleatória de estados dos módulos CAN
      //const updatedModules = canModules.map(module => ({
      //  ...module,
      //  connected: Math.random() > 0.2 // 80% de chance de estar conectado
      //}));
      //setCanModules(updatedModules);

      // Simular os sinais de seta (piscar)
      if (Math.random() > 0.7) {
        const newSignals = { ...turnSignals };
        if (Math.random() > 0.5) {
          newSignals.left = !newSignals.left;
        } else {
          newSignals.right = !newSignals.right;
        }
        setTurnSignals(newSignals);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [canModules, turnSignals]);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto p-4">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-center">Mercedes-Benz</h1>
          <div className="flex justify-between items-center mt-2">
            <div className={`px-4 py-2 rounded-md ${systemRunning ? "bg-gray-800 px-4 py-2 rounded-md" : "bg-gray-800 px-4 py-2 rounded-md"}`}>
              <span className={systemRunning ? "text-green-400" : "text-red-400"}>
                ● {systemRunning ? "Sistema Ativo" : "Sistema Inativo"}
              </span>
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
                currentValue={servoAngle + 90}  // Converter para escala 0-180
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
