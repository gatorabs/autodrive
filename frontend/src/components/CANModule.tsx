
import { CheckCircle, XCircle } from "lucide-react";

interface CANModuleProps {
  name: string;
  connected: boolean;
}

const CANModule = ({ name, connected }: CANModuleProps) => {
  return (
    <div className={`flex items-center justify-between p-3 rounded-lg ${connected ? 'bg-green-900/20' : 'bg-red-900/20'}`}>
      <div className="flex items-center">
        <div className={`w-2 h-2 rounded-full mr-3 ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
        <span>{name}</span>
      </div>
      <div className="flex items-center">
        {connected ? (
          <>
            <CheckCircle className="w-4 h-4 mr-1 text-green-500" />
            <span className="text-green-500 text-sm">Conectado</span>
          </>
        ) : (
          <>
            <XCircle className="w-4 h-4 mr-1 text-red-500" />
            <span className="text-red-500 text-sm">Desconectado</span>
          </>
        )}
      </div>
    </div>
  );
};

export default CANModule;
