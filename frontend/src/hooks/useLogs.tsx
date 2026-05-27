import { useState, useEffect, useCallback } from 'react';

export interface LogEntry {
  id: string;
  timestamp: Date;
  type: 'info' | 'warning' | 'error' | 'success';
  category: 'motor' | 'can' | 'camera' | 'system' | 'navigation';
  message: string;
  details?: string;
}

export const useLogs = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = useCallback((
    type: LogEntry['type'],
    category: LogEntry['category'],
    message: string,
    details?: string
  ) => {
    const newLog: LogEntry = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      type,
      category,
      message,
      details
    };
    
    setLogs(prev => {
      const updated = [newLog, ...prev];
      if (updated.length > 150) {
        return updated.slice(0, 150);
      }
      return updated;
    });
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  const getLogsByCategory = useCallback((category: LogEntry['category']) => {
    return logs.filter(log => log.category === category);
  }, [logs]);

  const getLogsByType = useCallback((type: LogEntry['type']) => {
    return logs.filter(log => log.type === type);
  }, [logs]);

  useEffect(() => {
    // Log inicial do sistema
    addLog('success', 'system', 'Sistema inicializado com sucesso', 'Dashboard do veículo autônomo carregado');
  }, [addLog]);

  return {
    logs,
    addLog,
    clearLogs,
    getLogsByCategory,
    getLogsByType,
    totalLogs: logs.length
  };
};
