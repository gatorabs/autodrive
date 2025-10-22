import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import PerformanceMonitor from '@/components/PerformanceMonitor';
import ManualControls, { ManualControlData } from '@/components/ManualControls';
import DisableManualModeModal from '@/components/DisableManualModeModal';
import { endpoints } from '@/config/api';

const ManualMode = () => {
    const navigate = useNavigate();
    const [controlData, setControlData] = useState<ManualControlData>({ x: 0, y: 0 });
    const [fps, setFps] = useState(0);
    const [frameTime, setFrameTime] = useState(0);

    const [isExitModalOpen, setIsExitModalOpen] = useState(false);

    const handleBackConfirm = async () => {
        setIsExitModalOpen(false);
        try {
            await fetch(endpoints.manualMode, {
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

    const handleControlChange = useCallback((data: ManualControlData) => {
        setControlData(data);
        fetch(endpoints.manualControls, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).catch(err => console.error('Erro ao enviar controles manuais:', err));
    }, []);

    useEffect(() => {
        const interval = setInterval(() => {
            fetch(endpoints.carInfo)
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
                })
                .catch(() => {
                    setFps(0);
                    setFrameTime(0);
                });
        }, 500);

        return () => clearInterval(interval);
    }, [navigate]);

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

                        <PerformanceMonitor fps={fps} frameTime={frameTime} />
                    </div>
                </header>

                {/* Main Content */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-gray-800 rounded-lg p-6">
                        <h3 className="text-lg font-semibold mb-4 text-center">Controles</h3>

                        <div className="flex flex-col items-center space-y-4">
                            <ManualControls onControlChange={handleControlChange} />

                            <div className="text-sm text-gray-400 text-center w-full">
                                <div className="grid grid-cols-2 gap-4 mt-4">
                                    <div>
                                        <div className="font-semibold text-white">Direção</div>
                                        <div>{controlData.x > 0.1 ? 'Direita' : controlData.x < -0.1 ? 'Esquerda' : 'Centro'}</div>
                                    </div>
                                    <div>
                                        <div className="font-semibold text-white">Velocidade</div>
                                        <div>{controlData.y > 0.1 ? 'Frente' : 'Parado'}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div className="bg-gray-800 rounded-lg p-6">
                            <h3 className="text-lg font-semibold mb-4">Status do Veículo</h3>

                            <div className="space-y-3">
                                <div className="flex justify-between items-center">
                                    <span className="text-gray-400">Modo:</span>
                                    <span className="text-orange-300 font-semibold">Manual</span>
                                </div>

                                <div className="flex justify-between items-center">
                                    <span className="text-gray-400">Velocidade:</span>
                                    <span className="text-white">{(controlData.y * 100).toFixed(0)}%</span>
                                </div>

                                <div className="flex justify-between items-center">
                                    <span className="text-gray-400">Direção:</span>
                                    <span className="text-white">{(controlData.x * 45).toFixed(0)}°</span>
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
