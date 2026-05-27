import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ManualModeDialogProps {
  open: boolean;
  mode: "enable" | "disable";
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
}

export function ManualModeDialog({ open, mode, onOpenChange, onConfirm }: ManualModeDialogProps) {
  const enabling = mode === "enable";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-white/10 bg-slate-950 text-white">
        <DialogHeader>
          <div className="flex items-start gap-3">
            <div className="rounded-2xl bg-amber-400/15 p-3 text-amber-300">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <DialogTitle className="text-xl">
                {enabling ? "Enable Manual Mode" : "Disable Manual Mode"}
              </DialogTitle>
              <DialogDescription className="mt-2 text-slate-300">
                {enabling
                  ? "Manual control temporarily pauses autonomous control and lets you drive speed and steering directly."
                  : "Autonomous control will take over steering and speed again."}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="border-white/10 bg-slate-900 text-slate-200">
            Cancel
          </Button>
          <Button onClick={onConfirm} className="bg-blue-500 text-white hover:bg-blue-400">
            {enabling ? "Enable Manual Mode" : "Return To Dashboard"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
