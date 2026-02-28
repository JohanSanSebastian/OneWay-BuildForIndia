import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts'

const TIP = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-earth-panel border border-white/5 rounded-xl p-3 shadow-lg flex flex-col gap-1 z-50 relative">
      <p className="text-slate-400 text-[11px] font-bold uppercase tracking-widest">{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} className="text-white text-sm font-semibold flex items-center gap-2">
          <span style={{ color: p.fill || p.stroke }}>●</span>
          <span>{p.name}:</span>
          <span>₹{(p.value || 0).toLocaleString()}</span>
        </p>
      ))}
    </div>
  )
}

/* Bar chart — divided into sections with different shades of amber/orange */
export function ServiceComparisonChart({ data }) {
  // Define shades of amber/orange from darkest (bottom) to lightest (top)
  const amberShades = [
    '#451a03', // very dark orange
    '#78350f',
    '#9a3412',
    '#c2410c',
    '#ea580c',
    '#f97316',
    '#fdba74', // lightest
  ]

  // The y-axis lines appear to be every 1000 units based on standard Recharts behavior
  const interval = 1000;

  // Find the maximum amount to know how many stacks we need
  const maxAmount = Math.max(...data.map(d => d.amount || 0));
  const numStacks = Math.ceil(maxAmount / interval) || 1;

  // Transform data to have separate keys for each segment
  const stackedData = data.map(item => {
    const amount = item.amount || 0;
    const transformed = { ...item };

    // Distribute amount into segment keys (segment0, segment1, etc.)
    let remainingAmount = amount;
    for (let i = 0; i < numStacks; i++) {
      if (remainingAmount > 0) {
        const segmentValue = Math.min(remainingAmount, interval);
        transformed[`segment${i}`] = segmentValue;
        remainingAmount -= segmentValue;
      } else {
        transformed[`segment${i}`] = 0;
      }
    }
    return transformed;
  });

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={stackedData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }} barCategoryGap="30%">
        <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
        <XAxis dataKey="service" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={40} tickFormatter={v => v >= 1000 ? `${v / 1000}k` : v} />
        <Tooltip content={<TIP />} cursor={{ fill: 'rgba(217,119,6,0.05)' }} />

        {/* Render stacked bars dynamically based on numStacks */}
        {/* Recharts stacks bottom-up in the order elements are declared */}
        {Array.from({ length: numStacks }).map((_, i) => (
          <Bar
            key={i}
            dataKey={`segment${i}`}
            stackId="a"
            fill={amberShades[Math.min(i, amberShades.length - 1)]}
            radius={[20, 20, 20, 20]}
            stroke="transparent"
            strokeWidth={0}
            barSize={20}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

/* Line chart — dynamic lines based on user accounts */
export function MonthlyTrendChart({ data, lines = [] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
        <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={40} tickFormatter={v => v >= 1000 ? `${v / 1000}k` : v} />
        <Tooltip content={<TIP />} />
        {lines.map(({ key, color, label, dash }) => (
          <Line key={key} type="monotone" dataKey={key} name={label} stroke={color}
            strokeWidth={2} dot={false} strokeDasharray={dash} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

/* Area line chart for billing history (used in HistoryModal) */
export function BillingLineChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={180}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="primary-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#d97706" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#d97706" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} width={40}
          tickFormatter={v => v >= 1000 ? `${v / 1000}k` : v} />
        <Tooltip content={<TIP />} />
        <Area type="monotone" dataKey="amount" name="Amount" stroke="#d97706"
          strokeWidth={2} fill="url(#primary-grad)" dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
