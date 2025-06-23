
import React, { createContext, useContext, ReactNode } from 'react';
import { useLogs, LogEntry } from '../hooks/useLogs';

interface LogsContextType {
  logs: LogEntry[];
  addLog: (type: LogEntry['type'], category: LogEntry['category'], message: string, details?: string) => void;
  clearLogs: () => void;
  getLogsByCategory: (category: LogEntry['category']) => LogEntry[];
  getLogsByType: (type: LogEntry['type']) => LogEntry[];
  totalLogs: number;
}

const LogsContext = createContext<LogsContextType | undefined>(undefined);

export const LogsProvider = ({ children }: { children: ReactNode }) => {
  const logsData = useLogs();

  return (
    <LogsContext.Provider value={logsData}>
      {children}
    </LogsContext.Provider>
  );
};

export const useLogsContext = () => {
  const context = useContext(LogsContext);
  if (context === undefined) {
    throw new Error('useLogsContext must be used within a LogsProvider');
  }
  return context;
};