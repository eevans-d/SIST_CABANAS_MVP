import CalendarView from '../../components/CalendarView';

const CalendarPage = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Calendario</h1>
        <p className="mt-2 text-sm text-gray-600">
          Visualiza la disponibilidad de tus alojamientos por mes
        </p>
      </div>

      <CalendarView />
    </div>
  );
};

export default CalendarPage;
