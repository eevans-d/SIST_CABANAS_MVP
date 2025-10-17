export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>

      {/* Placeholder para KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Reservas</h3>
          <p className="text-3xl font-bold text-gray-900">--</p>
          <p className="text-sm text-gray-600 mt-2">Cargando...</p>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Huéspedes</h3>
          <p className="text-3xl font-bold text-gray-900">--</p>
          <p className="text-sm text-gray-600 mt-2">Cargando...</p>
        </div>

        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Ingresos del Mes</h3>
          <p className="text-3xl font-bold text-gray-900">$--</p>
          <p className="text-sm text-gray-600 mt-2">Cargando...</p>
        </div>
      </div>

      {/* Placeholder para tabla de reservas */}
      <div className="card">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Reservas Recientes</h3>
        <div className="text-center text-gray-500 py-8">
          Tabla de reservas en construcción...
        </div>
      </div>
    </div>
  );
}
