import React, { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import PerformanceMonitor from '@/components/PerformanceMonitor';
import VirtualJoystick from '@/components/VirtualJoystick';

const ManualMode = () => {
  const navigate = useNavigate();
  const [joystickData, setJoystickData] = useState({ x: 0, y: 0 });

  const handleJoystickMove = (data: { x: number; y: number }) => {
    setJoystickData(data);
    // Aqui você pode enviar os dados do joystick para o backend
    console.log('Joystick movement:', data);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto p-4">
        {/* Header */}
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/')}
                className="bg-gray-700 text-gray-300 hover:bg-gray-700"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Voltar
              </Button>
              <h1 className="text-3xl font-bold">Modo Manual</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="bg-orange-500/20 border border-orange-500/30 px-4 py-2 rounded-md">
                <span className="text-orange-300">● Modo Manual Ativo</span>
              </div>
              <PerformanceMonitor />
            </div>
          </div>
        </header>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Camera Feed */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <div className="bg-gray-700 px-4 py-2 border-b border-gray-600">
                <h3 className="font-semibold flex items-center">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                  Câmera Frontal - Visão Principal
                </h3>
              </div>
              
              <div className="aspect-video bg-gray-900 relative flex items-center justify-center">
                {/* Simulated camera feed */}
                <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900">
                  {/* Grid overlay for camera feed simulation */}
                  <div className="absolute inset-0 opacity-20">
                    <div className="grid grid-cols-8 grid-rows-6 h-full">
                      {Array.from({ length: 48 }).map((_, i) => (
                        <div key={i} className="border border-gray-600"></div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Camera info overlay */}
                  <div className="absolute top-4 left-4 bg-black/50 px-3 py-2 rounded text-sm">
                    <div>CAM-01 | 1920x1080 | 30fps</div>
                    <div className="text-green-400">MANUAL MODE</div>
                  </div>
                  
                  {/* Timestamp */}
                  <div className="absolute bottom-4 right-4 bg-black/50 px-3 py-2 rounded text-sm font-mono">
                    {new Date().toLocaleTimeString()}
                  </div>
                  
                  {/* Center crosshair */}
                  <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                    <div className="w-8 h-8 border-2 border-red-400 rounded-full opacity-60">
                      <div className="absolute top-1/2 left-1/2 w-2 h-2 bg-red-400 rounded-full transform -translate-x-1/2 -translate-y-1/2"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Control Panel */}
          <div className="space-y-6">
            {/* Joystick Control */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-center">Controles</h3>
              
              <div className="flex flex-col items-center space-y-4">
                <VirtualJoystick onJoystickMove={handleJoystickMove} />
                
                <div className="text-sm text-gray-400 text-center">
                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div>
                      <div className="font-semibold text-white">Direção</div>
                      <div>{joystickData.x > 0.1 ? 'Direita' : joystickData.x < -0.1 ? 'Esquerda' : 'Centro'}</div>
                    </div>
                    <div>
                      <div className="font-semibold text-white">Velocidade</div>
                      <div>{joystickData.y > 0.1 ? 'Frente' : joystickData.y < -0.1 ? 'Ré' : 'Parado'}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Status Panel */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Status do Veículo</h3>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Modo:</span>
                  <span className="text-orange-300 font-semibold">Manual</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Velocidade:</span>
                  <span className="text-white">{Math.abs(joystickData.y * 100).toFixed(0)}%</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Direção:</span>
                  <span className="text-white">{(joystickData.x * 45).toFixed(0)}°</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Sistema:</span>
                  <span className="text-green-400">Operacional</span>
                </div>
              </div>
            </div>

            {/* Emergency Controls */}
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
              <h4 className="text-red-300 font-semibold mb-2">Controles de Emergência</h4>
              <Button
                variant="destructive"
                className="w-full bg-red-600 hover:bg-red-700"
                onClick={() => {
                  setJoystickData({ x: 0, y: 0 });
                  // Aqui você pode adicionar lógica de parada de emergência
                }}
              >
                PARADA DE EMERGÊNCIA
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManualMode;