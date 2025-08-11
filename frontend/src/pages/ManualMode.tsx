import React, { useState, useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import PerformanceMonitor from '@/components/PerformanceMonitor';
import VirtualJoystick from '@/components/VirtualJoystick';
import DisableManualModeModal from '@/components/DisableManualModeModal';

const ManualMode = () => {
    const navigate = useNavigate();
    const [joystickData, setJoystickData] = useState({ x: 0, y: 0 });
    const [fps, setFps] = useState(0);
    const [frameTime, setFrameTime] = useState(0);
    const [isRunning, setIsRunning] = useState(true);

    const [isLoading, setIsLoading] = useState(true);
    const [hasError, setHasError] = useState(false);
    const [imgKey, setImgKey] = useState(0);
    const [isExitModalOpen, setIsExitModalOpen] = useState(false);
    const streamUrl = 'http://192.168.15.12:5000/video_feed/TAB2_FRAME';

    const handleBackConfirm = async () => {
        setIsExitModalOpen(false);
        try {
            await fetch('http://192.168.15.12:5000/api/v2/manual-mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ active: false })
            });
        } catch (err) {
            console.error('Erro ao desativar modo manual:', err);
        }
        navigate('/');
    };
    const handleBack = () => setIsExitModalOpen(true);

    const handleJoystickMove = (data: { x: number; y: number }) => {
        setJoystickData(data);
        fetch('http://192.168.15.12:5000/api/v2/manual-controls', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).catch(err => console.error('Erro ao enviar joystick:', err));
    };

    useEffect(() => {
        const interval = setInterval(() => {
            fetch('http://192.168.15.12:5000/api/car-info')
                .then(res => res.json())
                .then(data => {
                    if (!data.manual_mode && data.webview) {
                        navigate('/');
                        return;
                    }
                    if (data.time_info) {
                        setFps(data.time_info.fps);
                        setFrameTime(data.time_info.total_processing_time);
                    }
                    if (typeof data.running === 'boolean') {
                        setIsRunning(data.running);
                    }
                })
                .catch(() => {
                    setFps(0);
                    setFrameTime(0);
                    setIsRunning(false);
                });
        }, 500);

        return () => clearInterval(interval);
    }, [navigate]);

    useEffect(() => {
        const checkInterval = setInterval(() => {
            const testImg = new Image();
            testImg.src = streamUrl + `?check=${Date.now()}`;
            testImg.onload = () => {
                if (hasError) {
                    setHasError(false);
                    setIsLoading(true);
                    setImgKey(prev => prev + 1);
                }
            };
            testImg.onerror = () => {
                if (!hasError) {
                    setHasError(true);
                    setIsLoading(false);
                }
            };
        }, 3000);

        return () => clearInterval(checkInterval);
    }, [streamUrl, hasError]);

    useEffect(() => {
        setIsLoading(true);
        setHasError(false);
        setImgKey(prev => prev + 1);
    }, []);

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
                                onClick={handleBack}
                                className="bg-gray-700 text-gray-300 hover:bg-gray-700"
                            >
                                <ArrowLeft className="h-4 w-4 mr-2" />
                                Voltar
                            </Button>
                        </div>

                        <div className="flex items-center space-x-4">
                            <div className="bg-orange-500/20 border border-orange-500/30 px-4 py-2 rounded-md">
                                <span className={isRunning ? 'text-orange-300' : 'text-red-400'}>
                                    ● {isRunning ? 'Modo Manual Ativo' : 'Sistema Inativo'}
                                </span>                            </div>
                            <PerformanceMonitor fps={fps} frameTime={frameTime} />
                        </div>
                    </div>
                </header>

                {/* Main Content */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Camera Feed */}
                    <div className="lg:col-span-2 h-full">
                        <div className="bg-gray-800 rounded-lg overflow-hidden h-full flex flex-col">
                            <div className="bg-gray-700 px-4 py-2 border-b border-gray-600">
                                <h3 className="font-semibold flex items-center">
                                    <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                                    Câmera Frontal - Visão Principal
                                </h3>
                            </div>

                            <div className="bg-gray-900 relative flex-1 flex items-center justify-center">
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
                                        alt="Feed da câmera frontal"
                                        className="absolute inset-0 w-full h-full object-cover"
                                        onLoad={() => setIsLoading(false)}
                                        onError={() => {
                                            setHasError(true);
                                            setIsLoading(false);
                                        }}
                                    />
                                )}

                                {!hasError && (
                                    <>
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
                                    </>
                                )}
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
                    </div>
                </div>
            </div>
            <DisableManualModeModal
                isOpen={isExitModalOpen}
                onClose={() => setIsExitModalOpen(false)}
                onConfirm={handleBackConfirm}
            />
        </div>
    );
};

export default ManualMode;
