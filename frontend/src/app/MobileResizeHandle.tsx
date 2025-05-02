"use client";

import { useRef, useCallback, useLayoutEffect } from "react";

interface MobileResizeHandleProps {
  onResize: (delta: number) => void;
}

const MobileResizeHandle: React.FC<MobileResizeHandleProps> = ({
  onResize,
}) => {
  const handleRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const startY = useRef(0);

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    isDragging.current = true;
    startY.current = e.clientY;
    document.body.style.cursor = "row-resize";
    document.addEventListener(
      "pointermove",
      handlePointerMove as unknown as EventListener
    );
    document.addEventListener(
      "pointerup",
      handlePointerUp as unknown as EventListener
    );
    e.preventDefault();
  }, []);

  const handlePointerMove = useCallback(
    (e: PointerEvent) => {
      if (!isDragging.current) return;
      const delta = e.clientY - startY.current;
      onResize(delta);
      startY.current = e.clientY;
    },
    [onResize]
  );

  const handlePointerUp = useCallback(() => {
    isDragging.current = false;
    document.body.style.cursor = "";
    document.removeEventListener(
      "pointermove",
      handlePointerMove as unknown as EventListener
    );
    document.removeEventListener(
      "pointerup",
      handlePointerUp as unknown as EventListener
    );
  }, [handlePointerMove]);

  useLayoutEffect(() => {
    const handle = handleRef.current;
    if (handle) {
      handle.addEventListener(
        "pointerdown",
        handlePointerDown as unknown as EventListener
      );
      return () => {
        handle.removeEventListener(
          "pointerdown",
          handlePointerDown as unknown as EventListener
        );
        document.removeEventListener(
          "pointermove",
          handlePointerMove as unknown as EventListener
        );
        document.removeEventListener(
          "pointerup",
          handlePointerUp as unknown as EventListener
        );
      };
    }
  }, [handlePointerDown, handlePointerMove, handlePointerUp]);

  return (
    <div
      ref={handleRef}
      className="h-2 flex items-center justify-center my-1 touch-none cursor-row-resize"
    >
      <div className="w-12 h-1 rounded-full bg-border/50 hover:bg-primary/60 transition-colors" />
    </div>
  );
};

export default MobileResizeHandle;
