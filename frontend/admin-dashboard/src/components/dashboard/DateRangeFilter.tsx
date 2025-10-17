import React from 'react';

interface DateRangeFilterProps {
  startDate?: string;
  endDate?: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
}

export const DateRangeFilter: React.FC<DateRangeFilterProps> = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
}) => {
  // Obtener fecha mínima (hoy) y máxima (1 año en el futuro)
  const today = new Date().toISOString().split('T')[0];
  const maxDate = new Date();
  maxDate.setFullYear(maxDate.getFullYear() + 1);
  const maxDateString = maxDate.toISOString().split('T')[0];

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onStartDateChange(e.target.value);

    // Si la fecha de fin es anterior a la nueva fecha de inicio, limpiarla
    if (endDate && e.target.value > endDate) {
      onEndDateChange('');
    }
  };

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onEndDateChange(e.target.value);
  };

  const clearDates = () => {
    onStartDateChange('');
    onEndDateChange('');
  };

  const hasDateFilter = startDate || endDate;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          Rango de Fechas
        </label>
        {hasDateFilter && (
          <button
            type="button"
            onClick={clearDates}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
          >
            Limpiar
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Fecha desde */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Check-in desde
          </label>
          <input
            type="date"
            value={startDate || ''}
            onChange={handleStartDateChange}
            min={today}
            max={maxDateString}
            className="block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            placeholder="dd/mm/yyyy"
          />
        </div>

        {/* Fecha hasta */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Check-in hasta
          </label>
          <input
            type="date"
            value={endDate || ''}
            onChange={handleEndDateChange}
            min={startDate || today}
            max={maxDateString}
            className="block w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            placeholder="dd/mm/yyyy"
          />
        </div>
      </div>

      {/* Feedback visual del rango seleccionado */}
      {startDate || endDate ? (
        <div className="text-xs text-gray-600 bg-blue-50 px-2 py-1 rounded">
          {startDate && endDate
            ? `Desde ${formatDateForDisplay(startDate)} hasta ${formatDateForDisplay(endDate)}`
            : startDate
            ? `Desde ${formatDateForDisplay(startDate)} en adelante`
            : `Hasta ${formatDateForDisplay(endDate!)}`
          }
        </div>
      ) : null}
    </div>
  );
};

// Helper para formatear fecha en formato dd/mm/yyyy
const formatDateForDisplay = (dateString: string): string => {
  const date = new Date(dateString + 'T00:00:00');
  return date.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};
