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
      <DialogContent className="border-border bg-background text-foreground">
        <DialogHeader>
          <div className="flex items-start gap-3">
            <div className="border border-warning/30 bg-warning-soft p-3 text-warning">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <DialogTitle className="font-display text-xl font-bold uppercase tracking-wide">
                {enabling ? "Enable Manual Mode" : "Disable Manual Mode"}
              </DialogTitle>
              <DialogDescription className="mt-2 text-muted-foreground">
                {enabling
                  ? "Manual control temporarily pauses autonomous control and lets you drive speed and steering directly."
                  : "Autonomous control will take over steering and speed again."}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="border-border bg-surface text-foreground">
            Cancel
          </Button>
          <Button onClick={onConfirm} className="bg-primary text-primary-foreground hover:bg-primary-hover">
            {enabling ? "Enable Manual Mode" : "Return To Dashboard"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
