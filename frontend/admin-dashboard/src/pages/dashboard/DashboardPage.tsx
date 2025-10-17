import { StatsCard } from '../../components/dashboard/StatsCard';
import { useDashboardStats } from '../../hooks/useDashboardStats';

// Iconos SVG simples
const UsersIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
  </svg>
);

const CalendarIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const CashIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ClockIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ChartIcon = () => (
  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

export default function DashboardPage() {
  const { data: stats, isLoading, isError, error } = useDashboardStats();

  // Formatear moneda
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-900">Dashboard</h2>
        {stats?.last_updated && (
          <p className="text-sm text-gray-500">
            Actualizado: {new Date(stats.last_updated).toLocaleString('es-AR')}
          </p>
        )}
      </div>

      {/* Error state */}
      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-medium">Error al cargar estadísticas</p>
          <p className="text-red-600 text-sm mt-1">{error?.message || 'Error desconocido'}</p>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
        <StatsCard
          title="Total Reservas"
          value={stats?.total_reservations ?? '--'}
          icon={<CalendarIcon />}
          subtitle="Pre-reservas + Confirmadas"
          loading={isLoading}
        />

        <StatsCard
          title="Total Huéspedes"
          value={stats?.total_guests ?? '--'}
          icon={<UsersIcon />}
          subtitle="En reservas activas"
          loading={isLoading}
        />

        <StatsCard
          title="Ingresos del Mes"
          value={stats ? formatCurrency(stats.monthly_revenue) : '--'}
          icon={<CashIcon />}
          subtitle="Solo reservas confirmadas"
          loading={isLoading}
        />

        <StatsCard
          title="Pendientes"
          value={stats?.pending_confirmations ?? '--'}
          icon={<ClockIcon />}
          subtitle="Pre-reservas sin confirmar"
          loading={isLoading}
        />

        <StatsCard
          title="Ocupación"
          value={stats ? `${stats.avg_occupancy_rate}%` : '--'}
          icon={<ChartIcon />}
          subtitle="Promedio últimos 30 días"
          loading={isLoading}
        />
      </div>

      {/* Placeholder para tabla de reservas */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">Reservas Recientes</h3>
        <div className="text-center text-gray-500 py-8">
          Tabla de reservas en construcción...
        </div>
      </div>
    </div>
  );
}
