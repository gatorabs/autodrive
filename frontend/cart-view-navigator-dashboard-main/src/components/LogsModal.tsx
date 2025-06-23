
import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileText, Trash2, Download, Filter } from 'lucide-react';
import { LogEntry } from '../hooks/useLogs';

interface LogsModalProps {
  logs: LogEntry[];
  onClearLogs: () => void;
}

const LogsModal = ({ logs, onClearLogs }: LogsModalProps) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');

  const getTypeColor = (type: LogEntry['type']) => {
    switch (type) {
      case 'success': return 'bg-green-500';
      case 'warning': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      case 'info': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getCategoryIcon = (category: LogEntry['category']) => {
    switch (category) {
      case 'motor': return '⚙️';
      case 'can': return '🔌';
      case 'camera': return '📷';
      case 'system': return '💻';
      case 'navigation': return '🧭';
      default: return '📝';
    }
  };

  const filteredLogs = logs.filter(log => {
    const categoryMatch = selectedCategory === 'all' || log.category === selectedCategory;
    const typeMatch = selectedType === 'all' || log.type === selectedType;
    return categoryMatch && typeMatch;
  });

  const exportLogs = () => {
    const logData = filteredLogs.map(log => ({
      timestamp: log.timestamp.toISOString(),
      type: log.type,
      category: log.category,
      message: log.message,
      details: log.details
    }));
    
    const blob = new Blob([JSON.stringify(logData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vehicle-logs-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <div className="px-3 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors duration-100 cursor-pointer flex items-center justify-center">
          <FileText className="h-6 w-6" />
        </div>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] bg-gray-900 text-white border-gray-700">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Logs do Sistema ({logs.length})</span>
            </span>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={exportLogs}>
                <Download className="h-4 w-4 mr-1" />
                Exportar
              </Button>
              <Button variant="destructive" size="sm" onClick={onClearLogs}>
                <Trash2 className="h-4 w-4 mr-1" />
                Limpar
              </Button>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Filtros */}
          <div className="flex items-center space-x-4 p-3 bg-gray-800 rounded-lg">
            <Filter className="h-4 w-4" />
            <div className="flex items-center space-x-2">
              <span className="text-sm">Categoria:</span>
              <select 
                value={selectedCategory} 
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="bg-gray-700 text-white rounded px-2 py-1 text-sm"
              >
                <option value="all">Todas</option>
                <option value="motor">Motor</option>
                <option value="can">CAN</option>
                <option value="camera">Câmera</option>
                <option value="system">Sistema</option>
                <option value="navigation">Navegação</option>
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm">Tipo:</span>
              <select 
                value={selectedType} 
                onChange={(e) => setSelectedType(e.target.value)}
                className="bg-gray-700 text-white rounded px-2 py-1 text-sm"
              >
                <option value="all">Todos</option>
                <option value="info">Info</option>
                <option value="success">Sucesso</option>
                <option value="warning">Aviso</option>
                <option value="error">Erro</option>
              </select>
            </div>
            <Badge variant="secondary">{filteredLogs.length} logs</Badge>
          </div>

          {/* Lista de logs */}
          <ScrollArea className="h-96 bg-gray-800 rounded-lg p-4">
            <div className="space-y-2">
              {filteredLogs.length === 0 ? (
                <div className="text-center text-gray-400 py-8">
                  Nenhum log encontrado
                </div>
              ) : (
                filteredLogs.map((log) => (
                  <div key={log.id} className="border border-gray-700 rounded-lg p-3 bg-gray-750">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3 flex-1">
                        <span className="text-lg">{getCategoryIcon(log.category)}</span>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <Badge 
                              className={`${getTypeColor(log.type)} text-white text-xs px-2 py-1`}
                            >
                              {log.type.toUpperCase()}
                            </Badge>
                            <span className="text-xs text-gray-400 capitalize">
                              {log.category}
                            </span>
                            <span className="text-xs text-gray-500">
                              {log.timestamp.toLocaleString('pt-BR')}
                            </span>
                          </div>
                          <div className="text-sm text-white">{log.message}</div>
                          {log.details && (
                            <div className="text-xs text-gray-400 mt-1 font-mono">
                              {log.details}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default LogsModal;