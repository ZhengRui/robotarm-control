"use client";

import { useRef, useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { ChevronDown, Check } from "lucide-react";

interface BaseSelectProps {
  label?: string;
  disabled?: boolean;
  className?: string;
  width?: string;
  maxHeight?: string;
}

// Read-only select for displaying a selection without the ability to change
interface ReadOnlySelectProps extends BaseSelectProps {
  value: string;
  options: string[];
  placeholder?: string;
}

export const ReadOnlySelect = ({
  label,
  value,
  options,
  disabled = false,
  className,
  width = "120px",
  maxHeight = "160px",
  placeholder = "",
}: ReadOnlySelectProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div className={cn("relative", className)} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        style={{ boxSizing: "border-box", width }}
        className={cn(
          "inline-flex items-center justify-between rounded-md px-3 py-1.5 text-xs font-semibold h-7",
          "bg-black text-white border border-transparent outline-none focus:outline-none",
          isOpen ? "" : "",
          disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"
        )}
      >
        <span className="truncate">{value || placeholder}</span>
        <ChevronDown
          className={cn(
            "ml-1 size-3 transition-transform",
            isOpen ? "rotate-180" : ""
          )}
        />
      </button>

      {isOpen && !disabled && (
        <div
          className="absolute right-0 mt-1 z-50 bg-white rounded-md shadow-lg border border-gray-200 py-1 overflow-y-auto"
          style={{ width, maxHeight }}
        >
          {label && (
            <div className="px-3 py-1 border-b border-gray-100">
              <span className="text-xs font-semibold">{label}</span>
            </div>
          )}

          {options.map((option) => (
            <div
              key={option}
              className={cn(
                "px-3 py-1.5 text-xs cursor-default",
                option === value
                  ? "bg-primary/10 font-semibold text-primary"
                  : "hover:bg-gray-100 text-gray-400"
              )}
            >
              {option}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Multi-select component with ability to select multiple values
interface MultiSelectProps extends BaseSelectProps {
  selectedValues: string[];
  options: string[];
  onChange: (newValues: string[]) => void;
  placeholder?: string;
}

export const MultiSelect = ({
  label,
  selectedValues,
  options,
  onChange,
  disabled = false,
  className,
  width = "180px",
  maxHeight = "200px",
  placeholder = "Select options",
}: MultiSelectProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleToggleItem = (item: string) => {
    if (selectedValues.includes(item)) {
      onChange(selectedValues.filter((i) => i !== item));
    } else {
      onChange([...selectedValues, item]);
    }
  };

  const handleClearAll = () => {
    onChange([]);
  };

  return (
    <div className={cn("relative", className)} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        style={{ boxSizing: "border-box", width }}
        className={cn(
          "inline-flex items-center justify-between rounded-md px-3 py-1.5 text-xs font-semibold h-7",
          "border border-input bg-background outline-none focus:outline-none",
          isOpen ? "" : "",
          disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"
        )}
      >
        <span className="truncate">
          {selectedValues.length > 0
            ? `${selectedValues.length} queue${selectedValues.length > 1 ? "s" : ""} selected`
            : placeholder}
        </span>
        <ChevronDown
          className={cn(
            "ml-1 size-3 transition-transform",
            isOpen ? "rotate-180" : ""
          )}
        />
      </button>

      {isOpen && !disabled && (
        <div
          className="absolute right-0 mt-1 z-50 bg-white rounded-md shadow-lg border border-gray-200 py-1 overflow-y-auto"
          style={{ width: parseInt(width) + 40 + "px", maxHeight }}
        >
          <div className="px-3 py-1 border-b border-gray-100">
            <div className="flex justify-between items-center">
              <span className="text-xs font-semibold">{label}</span>
              {selectedValues.length > 0 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearAll();
                  }}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear All
                </button>
              )}
            </div>
          </div>

          {options.map((item) => (
            <div
              key={item}
              onClick={() => handleToggleItem(item)}
              className={cn(
                "px-3 py-1.5 text-xs cursor-pointer flex items-center justify-between",
                selectedValues.includes(item)
                  ? "bg-primary/5"
                  : "hover:bg-gray-100 text-gray-600"
              )}
            >
              <span
                className={selectedValues.includes(item) ? "font-medium" : ""}
              >
                {item}
              </span>
              {selectedValues.includes(item) && (
                <Check className="size-3 text-primary" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Tag component for displaying selected items
interface TagProps {
  label: string;
  onRemove?: () => void;
  className?: string;
}

export const Tag = ({ label, onRemove, className }: TagProps) => {
  return (
    <div
      className={cn(
        "inline-flex items-center justify-center gap-1 rounded-full px-3 py-1 text-xs font-semibold h-7",
        onRemove ? "bg-primary text-primary-foreground" : "bg-black text-white",
        className
      )}
    >
      {label}
      {onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="size-4 inline-flex items-center justify-center rounded-full hover:bg-primary-foreground/20"
        >
          <span className="sr-only">Remove</span>
          <svg
            width="8"
            height="8"
            viewBox="0 0 8 8"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M1 1L7 7M7 1L1 7"
              stroke="currentColor"
              strokeWidth="1.3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      )}
    </div>
  );
};

// Tags container component for displaying multiple tags
interface TagsContainerProps {
  children: React.ReactNode;
  className?: string;
}

export const TagsContainer = ({ children, className }: TagsContainerProps) => {
  return (
    <div className={cn("flex flex-wrap gap-2 mt-3 mb-2", className)}>
      {children}
    </div>
  );
};
