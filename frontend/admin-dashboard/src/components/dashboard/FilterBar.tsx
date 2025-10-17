import React, { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { StatusFilter } from './StatusFilter';
import { DateRangeFilter } from './DateRangeFilter';

export interface FilterState {
  statuses: string[];
  startDate?: string;
  endDate?: string;
}

interface FilterBarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  isLoading?: boolean;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onFiltersChange,
  isLoading = false,
}) => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Sincronizar filtros con URL params al montar
  useEffect(() => {
    const statusesParam = searchParams.get('statuses');
    const startDateParam = searchParams.get('start_date');
    const endDateParam = searchParams.get('end_date');

    const urlFilters: FilterState = {
      statuses: statusesParam ? statusesParam.split(',') : [],
      startDate: startDateParam || undefined,
      endDate: endDateParam || undefined,
    };

    // Solo actualizar si hay diferencias con los filtros actuales
    const hasChanges =
      JSON.stringify(filters.statuses.sort()) !== JSON.stringify(urlFilters.statuses.sort()) ||
      filters.startDate !== urlFilters.startDate ||
      filters.endDate !== urlFilters.endDate;

    if (hasChanges) {
      onFiltersChange(urlFilters);
    }
  }, []); // Solo al montar

  // Actualizar URL cuando cambian los filtros
  useEffect(() => {
    const newParams = new URLSearchParams();

    if (filters.statuses.length > 0) {
      newParams.set('statuses', filters.statuses.join(','));
    }

    if (filters.startDate) {
      newParams.set('start_date', filters.startDate);
    }

    if (filters.endDate) {
      newParams.set('end_date', filters.endDate);
    }

    // Solo actualizar si hay cambios
    const currentParamsString = searchParams.toString();
    const newParamsString = newParams.toString();

    if (currentParamsString !== newParamsString) {
      setSearchParams(newParams);
    }
  }, [filters, searchParams, setSearchParams]);

  const handleStatusesChange = (statuses: string[]) => {
    onFiltersChange({
      ...filters,
      statuses,
    });
  };

  const handleStartDateChange = (startDate: string) => {
    onFiltersChange({
      ...filters,
      startDate: startDate || undefined,
    });
  };

  const handleEndDateChange = (endDate: string) => {
    onFiltersChange({
      ...filters,
      endDate: endDate || undefined,
    });
  };

  const clearAllFilters = () => {
    onFiltersChange({
      statuses: [],
      startDate: undefined,
      endDate: undefined,
    });
  };

  const hasActiveFilters =
    filters.statuses.length > 0 ||
    filters.startDate ||
    filters.endDate;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          Filtros
        </h3>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearAllFilters}
            disabled={isLoading}
            className="text-sm text-red-600 hover:text-red-800 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Limpiar todos
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Status Filter */}
        <div>
          <StatusFilter
            value={filters.statuses}
            onChange={handleStatusesChange}
          />
        </div>

        {/* Date Range Filter */}
        <div>
          <DateRangeFilter
            startDate={filters.startDate}
            endDate={filters.endDate}
            onStartDateChange={handleStartDateChange}
            onEndDateChange={handleEndDateChange}
          />
        </div>
      </div>

      {/* Indicador de filtros activos */}
      {hasActiveFilters && (
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="flex flex-wrap gap-2">
            {filters.statuses.length > 0 && (
              <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                {filters.statuses.length === 1
                  ? `Estado: ${filters.statuses[0]}`
                  : `${filters.statuses.length} estados`
                }
              </span>
            )}

            {(filters.startDate || filters.endDate) && (
              <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                {filters.startDate && filters.endDate
                  ? `${formatDateBadge(filters.startDate)} - ${formatDateBadge(filters.endDate)}`
                  : filters.startDate
                  ? `Desde ${formatDateBadge(filters.startDate)}`
                  : `Hasta ${formatDateBadge(filters.endDate!)}`
                }
              </span>
            )}
          </div>
        </div>
      )}

      {isLoading && (
        <div className="mt-3 flex items-center text-sm text-gray-500">
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Aplicando filtros...
        </div>
      )}
    </div>
  );
};

// Helper para formatear fecha en badges
const formatDateBadge = (dateString: string): string => {
  const date = new Date(dateString + 'T00:00:00');
  return date.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
  });
};
