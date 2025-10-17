import React, { useState, useRef, useEffect } from 'react';
import type { ReservationStatus } from '../../types';

interface StatusFilterProps {
  value: string[];
  onChange: (statuses: string[]) => void;
}

const STATUS_OPTIONS: { value: ReservationStatus; label: string; color: string }[] = [
  { value: 'pending', label: 'Pendiente', color: 'bg-gray-100 text-gray-800' },
  { value: 'pre_reserved', label: 'Pre-Reserva', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'confirmed', label: 'Confirmada', color: 'bg-green-100 text-green-800' },
  { value: 'checked_in', label: 'Check-in', color: 'bg-blue-100 text-blue-800' },
  { value: 'checked_out', label: 'Check-out', color: 'bg-purple-100 text-purple-800' },
  { value: 'cancelled', label: 'Cancelada', color: 'bg-red-100 text-red-800' },
  { value: 'expired', label: 'Expirada', color: 'bg-gray-100 text-gray-500' },
];

export const StatusFilter: React.FC<StatusFilterProps> = ({ value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleStatus = (status: string) => {
    if (value.includes(status)) {
      onChange(value.filter(s => s !== status));
    } else {
      onChange([...value, status]);
    }
  };

  const clearAll = () => {
    onChange([]);
  };

  const selectedCount = value.length;

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Estado
      </label>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="relative w-full bg-white border border-gray-300 rounded-md shadow-sm pl-3 pr-10 py-2 text-left cursor-pointer focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
      >
        <span className="block truncate">
          {selectedCount === 0
            ? 'Todos los estados'
            : selectedCount === 1
            ? STATUS_OPTIONS.find(opt => opt.value === value[0])?.label
            : `${selectedCount} estados seleccionados`
          }
        </span>
        <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
          {/* Header con "Limpiar todo" */}
          {selectedCount > 0 && (
            <div className="px-3 py-2 border-b border-gray-100">
              <button
                type="button"
                onClick={clearAll}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Limpiar selección
              </button>
            </div>
          )}

          {/* Opciones */}
          {STATUS_OPTIONS.map((option) => {
            const isSelected = value.includes(option.value);

            return (
              <div
                key={option.value}
                onClick={() => toggleStatus(option.value)}
                className="cursor-pointer select-none relative py-2 pl-3 pr-9 hover:bg-gray-50"
              >
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => {}} // Manejado por onClick del div
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-3"
                  />
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded-full ${option.color}`}
                  >
                    {option.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
