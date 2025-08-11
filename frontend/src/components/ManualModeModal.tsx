import React from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Zap, AlertTriangle } from 'lucide-react';

interface ManualModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

const ManualModeModal: React.FC<ManualModeModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-gray-800 border-gray-700 text-white">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/20 rounded-full">
              <AlertTriangle className="h-6 w-6 text-orange-400" />
            </div>
            <div>
              <DialogTitle className="text-xl font-bold">
                Ativar Modo Manual
              </DialogTitle>
              <DialogDescription className="text-gray-300 mt-1">
                Você está prestes a ativar o controle manual do veículo
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        
        <div className="py-4">
          <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="h-4 w-4 text-orange-400" />
              <span className="font-semibold text-orange-300">Atenção</span>
            </div>
            <p className="text-sm text-gray-300">
              O modo manual desativará temporariamente o sistema autônomo. 
              Você terá controle total sobre a direção e velocidade do veículo.
            </p>
          </div>
        </div>

        <DialogFooter className="flex gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            className="bg-gray-700 text-gray-300 hover:bg-gray-700"
          >
            Cancelar
          </Button>
          <Button
            onClick={onConfirm}
            className="bg-orange-500 hover:bg-orange-600 text-white"
          >
            Sim, Ativar Modo Manual
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ManualModeModal;