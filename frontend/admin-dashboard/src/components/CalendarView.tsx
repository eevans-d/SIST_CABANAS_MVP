import { useState } from 'react';
import { DayPicker } from 'react-day-picker';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { useCalendarAvailability } from '../hooks/useCalendar';
import 'react-day-picker/style.css';

interface CalendarViewProps {
  accommodationId?: number;
}

const CalendarView = ({ accommodationId }: CalendarViewProps) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const currentMonth = currentDate.getMonth() + 1;
  const currentYear = currentDate.getFullYear();

  const { data, isLoading, error } = useCalendarAvailability(
    currentMonth,
    currentYear,
    accommodationId
  );

  // Agrupar disponibilidad por estado para colorear días
  const getModifiers = () => {
    if (!data?.accommodations || data.accommodations.length === 0) {
      return {
        available: [],
        preReserved: [],
        confirmed: [],
        blocked: [],
      };
    }

    const availability = data.accommodations[0]?.availability || [];

    return {
      available: availability
        .filter(a => a.status === 'available')
        .map(a => new Date(a.date)),
      preReserved: availability
        .filter(a => a.status === 'pre_reserved')
        .map(a => new Date(a.date)),
      confirmed: availability
        .filter(a => a.status === 'confirmed')
        .map(a => new Date(a.date)),
      blocked: availability
        .filter(a => a.status === 'blocked')
        .map(a => new Date(a.date)),
    };
  };

  const modifiers = getModifiers();

  const modifiersStyles = {
    available: { backgroundColor: '#10b981', color: 'white' },
    preReserved: { backgroundColor: '#f59e0b', color: 'white' },
    confirmed: { backgroundColor: '#3b82f6', color: 'white' },
    blocked: { backgroundColor: '#ef4444', color: 'white' },
  };

  const handleMonthChange = (date: Date) => {
    setCurrentDate(date);
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600">Error al cargar el calendario</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header con selector de alojamiento */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-2">
          Calendario de Disponibilidad
        </h2>
        <p className="text-sm text-gray-600">
          {format(currentDate, "MMMM 'de' yyyy", { locale: es })}
        </p>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      )}

      {/* Calendario */}
      {!isLoading && (
        <div className="calendar-container">
          <DayPicker
            locale={es}
            month={currentDate}
            onMonthChange={handleMonthChange}
            modifiers={modifiers}
            modifiersStyles={modifiersStyles}
            className="mx-auto"
            classNames={{
              root: 'rdp-custom',
              month_caption: 'flex justify-center items-center h-10 font-semibold text-lg',
              months: 'flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0',
              month_grid: 'w-full border-collapse space-y-1',
              weekdays: 'flex',
              weekday: 'text-gray-500 rounded-md w-9 font-normal text-[0.8rem]',
              week: 'flex w-full mt-2',
              day: 'h-9 w-9 text-center text-sm p-0 relative',
              day_button: 'h-9 w-9 p-0 font-normal rounded-md hover:bg-gray-100',
              day_today: 'bg-gray-100 font-bold',
              day_outside: 'text-gray-400',
              day_disabled: 'text-gray-300',
              day_hidden: 'invisible',
            }}
          />
        </div>
      )}

      {/* Leyenda */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Leyenda:</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-emerald-500"></div>
            <span className="text-sm text-gray-600">Disponible</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-amber-500"></div>
            <span className="text-sm text-gray-600">Pre-reservado</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-blue-500"></div>
            <span className="text-sm text-gray-600">Confirmado</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-red-500"></div>
            <span className="text-sm text-gray-600">Bloqueado</span>
          </div>
        </div>
      </div>

      {/* Información de reservas para el mes */}
      {data && data.accommodations.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Estadísticas del mes:
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {data.accommodations.map(acc => {
              const confirmed = acc.availability.filter(a => a.status === 'confirmed').length;
              const preReserved = acc.availability.filter(a => a.status === 'pre_reserved').length;

              return (
                <div key={acc.id} className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-500 mb-1">{acc.name}</p>
                  <p className="text-lg font-semibold text-gray-800">
                    {confirmed + preReserved} días
                  </p>
                  <p className="text-xs text-gray-500">reservados</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default CalendarView;
