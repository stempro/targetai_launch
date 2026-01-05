'use client';

import { useEffect, useState } from 'react';
import { metricsApi } from '@/lib/api';
import { BarChart3, TrendingUp, Target, Calendar, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const res = await metricsApi.getCurrent();
      setMetrics(res.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading metrics:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Loading metrics...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Metrics & Analytics</h1>
            <p className="text-gray-600 mt-1">
              Deep dive into performance metrics and track Phase 1 progress
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Current Phase Metrics */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            Phase 1 Current Metrics
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Pilots Onboarded"
              value={metrics?.total_pilots_onboarded || 0}
              target={`${metrics?.phase1_targets?.pilots_onboarded_min}-${metrics?.phase1_targets?.pilots_onboarded_max}`}
              icon={<Target className="w-6 h-6" />}
              color="blue"
            />
            <MetricCard
              title="NPS Score"
              value={metrics?.current_nps?.toFixed(1) || 'N/A'}
              target={`≥${metrics?.phase1_targets?.nps_target}`}
              icon={<TrendingUp className="w-6 h-6" />}
              color="green"
            />
            <MetricCard
              title="Weekly Active Rate"
              value={`${metrics?.current_weekly_active_rate || 0}%`}
              target={`≥${metrics?.phase1_targets?.weekly_active_rate_target}%`}
              icon={<BarChart3 className="w-6 h-6" />}
              color="purple"
            />
            <MetricCard
              title="Referrals"
              value={metrics?.total_referrals || 0}
              target={`≥${metrics?.phase1_targets?.referrals_target}`}
              icon={<Target className="w-6 h-6" />}
              color="orange"
            />
          </div>
        </div>

        {/* Detailed Metrics */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Engagement Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Engagement Metrics</h3>
            <div className="space-y-4">
              <MetricRow label="Active Users (Week 4)" value={metrics?.week4_active_users || 0} />
              <MetricRow label="Engagement Rate" value={`${metrics?.current_weekly_active_rate || 0}%`} />
              <MetricRow label="Session Frequency" value={metrics?.avg_sessions_per_week?.toFixed(1) || 'N/A'} />
            </div>
          </div>

          {/* Conversion Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversion Metrics</h3>
            <div className="space-y-4">
              <MetricRow label="Demo to Pilot Rate" value={`${metrics?.demo_to_pilot_conversion_rate || 0}%`} />
              <MetricRow label="Referral Rate" value={`${metrics?.referral_rate || 0}%`} />
              <MetricRow label="Churn Rate" value={`${metrics?.churn_rate || 0}%`} />
            </div>
          </div>
        </div>

        {/* Phase 1 Targets */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-purple-600" />
            Phase 1 Success Criteria
          </h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-700 mb-3">Primary Goals</h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex justify-between">
                  <span>Pilots Onboarded:</span>
                  <span className="font-semibold">
                    {metrics?.phase1_targets?.pilots_onboarded_min}-{metrics?.phase1_targets?.pilots_onboarded_max}
                  </span>
                </li>
                <li className="flex justify-between">
                  <span>NPS Score:</span>
                  <span className="font-semibold">≥{metrics?.phase1_targets?.nps_target}</span>
                </li>
                <li className="flex justify-between">
                  <span>Weekly Active Rate:</span>
                  <span className="font-semibold">≥{metrics?.phase1_targets?.weekly_active_rate_target}%</span>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-3">Secondary Goals</h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex justify-between">
                  <span>Referrals:</span>
                  <span className="font-semibold">≥{metrics?.phase1_targets?.referrals_target}</span>
                </li>
                <li className="flex justify-between">
                  <span>Features Validated:</span>
                  <span className="font-semibold">≥{metrics?.phase1_targets?.features_validated_min}</span>
                </li>
                <li className="flex justify-between">
                  <span>Avg Sessions/Week:</span>
                  <span className="font-semibold">≥{metrics?.phase1_targets?.avg_sessions_per_week_target}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function MetricCard({
  title,
  value,
  target,
  icon,
  color,
}: {
  title: string;
  value: string | number;
  target: string;
  icon: React.ReactNode;
  color: string;
}) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
          {icon}
        </div>
      </div>
      <h3 className="text-gray-600 text-sm font-medium">{title}</h3>
      <div className="mt-2">
        <div className="text-3xl font-bold text-gray-900">{value}</div>
        <div className="text-sm text-gray-500 mt-1">Target: {target}</div>
      </div>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
      <span className="text-gray-600">{label}</span>
      <span className="font-semibold text-gray-900">{value}</span>
    </div>
  );
}
