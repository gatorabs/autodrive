import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileText, Trash2, Download, Filter, Cpu, MemoryStick, HardDrive } from 'lucide-react';
import { LogEntry } from '@/hooks/useLogs';

interface ProcessInfo {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_mb: number;
  io_mb: number;
  priority: string;
}

interface SystemInfo {
  process_count: number;
  processes: ProcessInfo[];
  system_cpu: number;
  total_ram_mb: number;
}

interface LogsModalProps {
  logs: LogEntry[];
  onClearLogs: () => void;
}

const LogsModal = ({ logs, onClearLogs }: LogsModalProps) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [systemInfo, setSystemInfo] = useState<SystemInfo>({
    process_count: 0,
    processes: [],
    system_cpu: 0,
    total_ram_mb: 0,
  });

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'HIGH': return 'bg-red-500';
      case 'ABOVE_NORMAL': return 'bg-orange-500';
      case 'NORMAL': return 'bg-green-500';
      case 'BELOW_NORMAL': return 'bg-blue-500';
      case 'IDLE': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  const formatBytes = (mb: number) => {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb.toFixed(1)} MB`;
  };

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

  const fetchProcesses = () => {
    fetch('http://192.168.15.12:5000/api/v2/python-processes')
      .then(res => res.json())
      .then(data => setSystemInfo(data))
      .catch(err => console.error('Error fetching processes:', err));
  };

  useEffect(() => {
    fetchProcesses();
    const interval = setInterval(fetchProcesses, 5000);
    return () => clearInterval(interval);
  }, []);

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

  const totalProcessCpu = systemInfo.processes
    .reduce((acc, proc) => acc + proc.cpu_percent, 0);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <div className="px-3 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors duration-100 cursor-pointer flex items-center justify-center">
          <FileText className="h-6 w-6" />
        </div>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] bg-gray-900 text-white overflow-hidden flex flex-col border-gray-700">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Logs do Sistema ({logs.length})</span>
            </span>
            <div className="flex items-center space-x-2">
              <Button variant="default" size="sm" onClick={exportLogs}>
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

        <Tabs defaultValue="logs" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-gray-800">
            <TabsTrigger value="logs" className="data-[state=active]:bg-gray-700">
              <FileText className="h-4 w-4 mr-2" />
              Logs
            </TabsTrigger>
            <TabsTrigger value="processes" className="data-[state=active]:bg-gray-700">
              <Cpu className="h-4 w-4 mr-2" />
              Processos
            </TabsTrigger>
          </TabsList>

          <TabsContent value="logs" className="space-y-4 mt-4">
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
            <ScrollArea className="h-80 bg-gray-800 rounded-lg p-4">
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
          </TabsContent>

          <TabsContent value="processes" className="space-y-4 mt-4">
            {/* Informações do sistema */}
            <div className="p-3 bg-gray-800 rounded-lg">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-blue-400">{systemInfo.process_count}</div>
                  <div className="text-xs text-gray-400">Processos Python</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-400">{totalProcessCpu.toFixed(1)}%</div>
                  <div className="text-xs text-gray-400">CPU Total</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-purple-400">{formatBytes(systemInfo.total_ram_mb)}</div>
                  <div className="text-xs text-gray-400">RAM Total</div>
                </div>
              </div>
            </div>

            {/* Lista de processos */}
            <ScrollArea className="h-80 bg-gray-800 rounded-lg p-4">
              <div className="space-y-2">
                {systemInfo.processes.map((process) => (
                  <div key={process.pid} className="border border-gray-700 rounded-lg p-3 bg-gray-750">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <div className="text-sm font-mono text-blue-400">PID: {process.pid}</div>
                        <Badge 
                          className={`${getPriorityColor(process.priority)} text-white text-xs px-2 py-1`}
                        >
                          {process.priority}
                        </Badge>
                      </div>
                      <div className="text-xs text-gray-400">{process.name}</div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="flex items-center space-x-2">
                        <Cpu className="h-4 w-4 text-blue-400" />
                        <span>CPU: {process.cpu_percent.toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <MemoryStick className="h-4 w-4 text-green-400" />
                        <span>RAM: {formatBytes(process.memory_mb)}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <HardDrive className="h-4 w-4 text-purple-400" />
                        <span>I/O: {formatBytes(process.io_mb)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default LogsModal;