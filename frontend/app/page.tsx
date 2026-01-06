'use client';

import { useEffect, useState } from 'react';
import { metricsApi, counselorsApi, timelineApi } from '@/lib/api';
import { BarChart3, Users, TrendingUp, Calendar, Target, AlertCircle, MessageCircle, ChevronDown, ChevronUp, BookMarked, Trash2, LogOut } from 'lucide-react';
import { useActivityChat } from '@/contexts/ActivityChatContext';
import Modal from '@/components/Modal';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [currentPhase, setCurrentPhase] = useState<any>(null);
  const [pipelineStats, setPipelineStats] = useState<any>(null);
  const [agentInsights, setAgentInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [metricsExpanded, setMetricsExpanded] = useState(false);
  const { openChat, isAnchored } = useActivityChat();
  const router = useRouter();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [metricsRes, phaseRes, statsRes] = await Promise.all([
        metricsApi.getCurrent(),
        timelineApi.getCurrentPhase(),
        counselorsApi.getPipelineStats(),
      ]);

      setMetrics(metricsRes.data);
      setCurrentPhase(phaseRes.data);
      setPipelineStats(statsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setLoading(false);
    }
  };

  const runInsightsAgent = async () => {
    try {
      const { agentsApi } = await import('@/lib/api');
      const res = await agentsApi.runMetricsInsights('overview');
      setAgentInsights(res.data);
    } catch (error) {
      console.error('Error running insights agent:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
      router.push('/login');
      router.refresh();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div
      className={`min-h-screen bg-gray-50 transition-all duration-300 ${
        isAnchored ? 'md:mr-[600px] max-md:mb-[50vh]' : ''
      }`}
    >
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">TargetAI Launch Manager</h1>
              <p className="text-gray-600 mt-1">
                {currentPhase
                  ? `Phase ${currentPhase.phase.replace('phase', '')} - Week ${currentPhase.week_number}`
                  : 'Not initialized'}
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={runInsightsAgent}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
              >
                Get AI Insights
              </button>
              <button
                onClick={handleLogout}
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors flex items-center gap-2"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Weekly Action Plan */}
        {currentPhase && (
          <WeeklyActionPlan
            week={currentPhase.week_number}
            phase={currentPhase.phase}
            onTrack={currentPhase.on_schedule}
            onAiChat={openChat}
          />
        )}

        {/* Key Metrics & Pipeline Stats - Collapsible */}
        <div className="bg-white rounded-lg shadow mb-8">
          <button
            onClick={() => setMetricsExpanded(!metricsExpanded)}
            className="w-full p-6 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <h2 className="text-xl font-semibold text-gray-900">Key Metrics & Pipeline</h2>
            {metricsExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-600" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-600" />
            )}
          </button>
          {metricsExpanded && (
            <div className="px-6 pb-6 space-y-6">
              {/* Key Metrics Cards - Phase Aware */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {currentPhase?.phase === 'phase1' && (
                  <>
                    <MetricCard
                      title="Pilots Onboarded"
                      value={metrics?.total_pilots_onboarded || 0}
                      target={`${metrics?.phase1_targets?.pilots_onboarded_min}-${metrics?.phase1_targets?.pilots_onboarded_max}`}
                      icon={<Users className="w-6 h-6" />}
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
                      title="Weekly Active"
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
                  </>
                )}
                {currentPhase?.phase === 'phase2' && (
                  <>
                    <MetricCard
                      title="Partner Firms"
                      value={metrics?.partner_firms || 0}
                      target={`${metrics?.phase2_targets?.partner_firms_min}-${metrics?.phase2_targets?.partner_firms_max}`}
                      icon={<Users className="w-6 h-6" />}
                      color="blue"
                    />
                    <MetricCard
                      title="Total Students"
                      value={metrics?.total_students || 0}
                      target={`≥${metrics?.phase2_targets?.total_students_target}`}
                      icon={<TrendingUp className="w-6 h-6" />}
                      color="green"
                    />
                    <MetricCard
                      title="Students/Firm"
                      value={metrics?.partner_firms > 0 ? Math.round((metrics?.total_students || 0) / metrics.partner_firms) : 0}
                      target={`≥${metrics?.phase2_targets?.students_per_firm_target}`}
                      icon={<BarChart3 className="w-6 h-6" />}
                      color="purple"
                    />
                    <MetricCard
                      title="Renewal Intent"
                      value={`${metrics?.current_renewal_intent || 0}%`}
                      target={`≥${metrics?.phase2_targets?.renewal_intent_target}%`}
                      icon={<Target className="w-6 h-6" />}
                      color="orange"
                    />
                  </>
                )}
                {currentPhase?.phase === 'phase3' && (
                  <>
                    <MetricCard
                      title="Active Students"
                      value={metrics?.active_students || 0}
                      target="Monitor"
                      icon={<Users className="w-6 h-6" />}
                      color="blue"
                    />
                    <MetricCard
                      title="Weekly Active Rate"
                      value={`${metrics?.current_weekly_active_rate || 0}%`}
                      target={`≥${metrics?.phase3_targets?.weekly_active_rate_target}%`}
                      icon={<TrendingUp className="w-6 h-6" />}
                      color="green"
                    />
                    <MetricCard
                      title="Student NPS"
                      value={metrics?.current_nps?.toFixed(1) || 'N/A'}
                      target={`≥${metrics?.phase3_targets?.student_nps_target}`}
                      icon={<BarChart3 className="w-6 h-6" />}
                      color="purple"
                    />
                    <MetricCard
                      title="Feature Adoption"
                      value={`${metrics?.current_feature_adoption_rate || 0}%`}
                      target={`≥${metrics?.phase3_targets?.feature_adoption_rate_target}%`}
                      icon={<Target className="w-6 h-6" />}
                      color="orange"
                    />
                  </>
                )}
                {currentPhase?.phase === 'phase4' && (
                  <>
                    <MetricCard
                      title="Monthly Signups"
                      value={metrics?.monthly_signups || 0}
                      target={`≥${metrics?.phase4_targets?.monthly_signups_target}`}
                      icon={<Users className="w-6 h-6" />}
                      color="blue"
                    />
                    <MetricCard
                      title="Paid Conversion"
                      value={`${metrics?.current_paid_conversion_rate || 0}%`}
                      target={`≥${metrics?.phase4_targets?.paid_conversion_rate_target}%`}
                      icon={<TrendingUp className="w-6 h-6" />}
                      color="green"
                    />
                    <MetricCard
                      title="MRR"
                      value={`$${metrics?.mrr?.toFixed(0) || 0}`}
                      target="Monitor"
                      icon={<BarChart3 className="w-6 h-6" />}
                      color="purple"
                    />
                    <MetricCard
                      title="12-mo Retention"
                      value={`${metrics?.current_retention_12mo || 0}%`}
                      target={`≥${metrics?.phase4_targets?.retention_12mo_target}%`}
                      icon={<Target className="w-6 h-6" />}
                      color="orange"
                    />
                  </>
                )}
              </div>

              {/* Pipeline Stats */}
              {pipelineStats && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Counselor Pipeline</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(pipelineStats.by_stage).map(([stage, count]) => (
                      <div key={stage} className="text-center">
                        <div className="text-2xl font-bold text-gray-900">{count as number}</div>
                        <div className="text-sm text-gray-600 capitalize">{stage.replace('_', ' ')}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* AI Insights */}
        {agentInsights && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 mb-8">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-6 h-6 text-purple-600 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-purple-900 mb-2">
                  AI Insights & Recommendations
                </h3>
                <div className="text-gray-700 whitespace-pre-wrap">
                  {agentInsights.output.insights}
                </div>
                {agentInsights.recommendations.length > 0 && (
                  <div className="mt-4">
                    <div className="font-semibold text-purple-900 mb-2">
                      Recommended Actions:
                    </div>
                    <ul className="space-y-1">
                      {agentInsights.recommendations.map((rec: string, i: number) => (
                        <li key={i} className="text-gray-700">
                          • {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <QuickActionCard
            title="Weekly Log"
            description="Track your weekly progress and activities"
            href="/weekly-log"
            icon={<Calendar className="w-8 h-8" />}
          />
          <QuickActionCard
            title="View Counselors"
            description="Manage your counselor pipeline"
            href="/counselors"
            icon={<Users className="w-8 h-8" />}
          />
          <QuickActionCard
            title="Metrics & Analytics"
            description="Deep dive into performance metrics"
            href="/metrics"
            icon={<BarChart3 className="w-8 h-8" />}
          />
          <QuickActionCard
            title="Timeline & Milestones"
            description="Track phase progress and deadlines"
            href="/timeline"
            icon={<Calendar className="w-8 h-8" />}
          />
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
    <div className="bg-white rounded-lg shadow p-6">
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

function QuickActionCard({
  title,
  description,
  href,
  icon,
}: {
  title: string;
  description: string;
  href: string;
  icon: React.ReactNode;
}) {
  return (
    <a
      href={href}
      className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
    >
      <div className="flex items-center gap-4">
        <div className="text-gray-600">{icon}</div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600 mt-1">{description}</p>
        </div>
      </div>
    </a>
  );
}

function DeleteConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className="relative bg-white rounded-lg shadow-2xl max-w-md w-full mx-4 transform transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-red-200">
          <h3 className="text-lg font-semibold text-gray-900">Confirm Delete</h3>
        </div>

        {/* Body */}
        <div className="px-6 py-4 bg-red-50 border-t border-b border-red-200">
          <p className="text-red-800 text-sm">
            Are you sure you want to delete this saved tip? This action cannot be undone.
          </p>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-6 py-2 rounded-lg transition-colors font-medium"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg transition-colors font-medium"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

function SavedTips({ taskId }: { taskId: string }) {
  const [tips, setTips] = useState<any[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [deleteModalState, setDeleteModalState] = useState<{
    isOpen: boolean;
    tipIndex: number | null;
  }>({
    isOpen: false,
    tipIndex: null,
  });
  const [successModal, setSuccessModal] = useState<{
    isOpen: boolean;
    message: string;
  }>({
    isOpen: false,
    message: '',
  });

  const loadTips = async () => {
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/chat/activity/tips/${taskId}`);
      if (response.ok) {
        const data = await response.json();
        setTips(data.tips || []);
      }
    } catch (error) {
      console.error('Error loading tips:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (index: number) => {
    setDeleteModalState({
      isOpen: true,
      tipIndex: index,
    });
  };

  const handleConfirmDelete = async () => {
    if (deleteModalState.tipIndex === null) return;

    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${API_BASE_URL}/api/chat/activity/tips/${taskId}/${deleteModalState.tipIndex}`,
        {
          method: 'DELETE',
        }
      );

      if (response.ok) {
        setDeleteModalState({ isOpen: false, tipIndex: null });
        setSuccessModal({
          isOpen: true,
          message: 'Tip deleted successfully!',
        });
        await loadTips(); // Reload tips
      }
    } catch (error) {
      console.error('Error deleting tip:', error);
      alert('Failed to delete tip. Please try again.');
    }
  };

  useEffect(() => {
    loadTips();

    // Refresh tips every 5 seconds when chat is open
    const interval = setInterval(() => {
      loadTips();
    }, 5000);

    return () => clearInterval(interval);
  }, [taskId]);

  if (loading) {
    return null;
  }

  if (tips.length === 0) {
    return null;
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  return (
    <div className="ml-5 pl-4 border-l-2 border-purple-200">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700 font-medium"
      >
        <BookMarked className="w-4 h-4" />
        <span>Saved Tips ({tips.length})</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
      </button>
      {isExpanded && (
        <div className="mt-2 space-y-3">
          {tips.map((tip, idx) => (
            <div key={idx} className="bg-purple-50 rounded-lg p-3 border border-purple-100 relative group">
              <button
                onClick={() => handleDeleteClick(idx)}
                className="absolute top-2 right-2 p-1 text-red-500 hover:text-red-700 hover:bg-red-100 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                title="Delete this tip"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <div className="text-xs text-purple-600 font-medium mb-1">
                {formatTimestamp(tip.timestamp)}
              </div>
              <div className="text-sm text-gray-700 whitespace-pre-wrap pr-8">
                {tip.content}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={deleteModalState.isOpen}
        onClose={() => setDeleteModalState({ isOpen: false, tipIndex: null })}
        onConfirm={handleConfirmDelete}
      />

      {/* Success Modal */}
      <Modal
        isOpen={successModal.isOpen}
        onClose={() => setSuccessModal({ isOpen: false, message: '' })}
        title="Success"
        message={successModal.message}
        type="success"
      />
    </div>
  );
}

function WeeklyActionPlan({
  week,
  phase,
  onTrack,
  onAiChat,
}: {
  week: number;
  phase: string;
  onTrack: boolean;
  onAiChat: (task: string, taskId: string) => void;
}) {
  const getWeeklyActivities = (weekNum: number) => {
    if (weekNum <= 2) {
      return {
        title: 'Week 1-2: Foundation',
        focus: 'LinkedIn profile optimization, initial connects',
        activities: [
          { task: 'Optimize LinkedIn profile with counselor-focused positioning', done: false },
          { task: 'Build target list of 50 counselors matching selection criteria', done: false },
          { task: 'Send 20 connection requests with personalized notes', done: false },
          { task: 'Engage with 10 counselor posts (meaningful comments)', done: false },
          { task: 'Draft and publish first LinkedIn thought leadership post', done: false },
          { task: 'Prepare demo environment with realistic sample data', done: false },
        ],
        targets: {
          connections: 40,
          posts: 1,
          demos: 0,
        },
      };
    } else if (weekNum <= 4) {
      return {
        title: 'Week 3-4: Active Outreach',
        focus: 'Personalized outreach to engaged connections',
        activities: [
          { task: 'Send 15 personalized DMs to engaged connections', done: false },
          { task: 'Schedule 8-10 discovery calls', done: false },
          { task: 'Conduct discovery calls using provided script', done: false },
          { task: 'Score candidates using rubric', done: false },
          { task: 'Convert qualified leads to demo sessions', done: false },
          { task: 'Publish second thought leadership post', done: false },
        ],
        targets: {
          dms: 15,
          calls: '8-10',
          demos: '8-10',
        },
      };
    } else if (weekNum <= 6) {
      return {
        title: 'Week 5-6: Conversion & Onboarding',
        focus: 'Demos, onboarding, referral requests',
        activities: [
          { task: 'Conduct demo sessions for qualified candidates', done: false },
          { task: 'Complete hands-on setup for committed pilots', done: false },
          { task: 'Execute Week 1 check-in calls with new pilots', done: false },
          { task: 'Ask each pilot for 2-3 referrals', done: false },
          { task: 'Document feedback and feature requests', done: false },
          { task: 'Continue outreach via referrals', done: false },
        ],
        targets: {
          pilots: '5-8',
          referrals: '10+',
          checkIns: 'All new pilots',
        },
      };
    } else {
      return {
        title: 'Week 7-8: Scale & Validate',
        focus: 'Support existing pilots, pursue referrals',
        activities: [
          { task: 'Reach 10-15 active pilot counselors', done: false },
          { task: 'Conduct bi-weekly check-ins with all pilots', done: false },
          { task: 'Deploy Week 4 NPS survey', done: false },
          { task: 'Analyze feedback themes and prioritize fixes', done: false },
          { task: 'Identify 3-5 potential advocate counselors', done: false },
          { task: 'Begin Phase 2 planning with validated learnings', done: false },
        ],
        targets: {
          activePilots: '10-15',
          nps: '≥8',
          advocates: '3-5',
        },
      };
    }
  };

  const weekData = getWeeklyActivities(week);

  return (
    <div className="mb-8">
      <div className={`rounded-lg shadow-lg p-6 ${onTrack ? 'bg-gradient-to-r from-blue-50 to-purple-50' : 'bg-gradient-to-r from-orange-50 to-red-50'}`}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{weekData.title}</h2>
            <p className="text-gray-600 mt-1">Focus: {weekData.focus}</p>
          </div>
          <div className={`px-4 py-2 rounded-full text-sm font-semibold ${onTrack ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}`}>
            {onTrack ? '✓ On Track' : '⚠ Needs Attention'}
          </div>
        </div>

        <div className="grid md:grid-cols-[2fr,1fr] gap-6">
          {/* Activities Checklist */}
          <div className="bg-white rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-600" />
              This Week's Activities
            </h3>
            <ul className="space-y-4">
              {weekData.activities.map((activity, idx) => {
                const taskId = `week${week}_${idx}`;
                return (
                  <li key={idx} className="space-y-2" data-task-id={taskId}>
                    <div className="flex items-start gap-3 text-lg group">
                      <span className={`mt-2 w-2 h-2 rounded-full flex-shrink-0 ${
                        activity.done ? 'bg-green-500' : 'bg-blue-500'
                      }`} />
                      <span className={`flex-1 ${activity.done ? 'line-through text-gray-500' : 'text-gray-700'}`}>
                        {activity.task}
                      </span>
                      <button
                        onClick={() => onAiChat(activity.task, taskId)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-purple-100 rounded text-purple-600"
                        title="Get AI recommendation"
                      >
                        <MessageCircle className="w-5 h-5" />
                      </button>
                    </div>
                    <SavedTips taskId={taskId} />
                  </li>
                );
              })}
            </ul>
          </div>

          {/* Weekly Targets */}
          <div className="bg-white rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-600" />
              Weekly Targets
            </h3>
            <div className="space-y-3">
              {Object.entries(weekData.targets).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center">
                  <span className="text-lg text-gray-600 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}:</span>
                  <span className="text-lg font-semibold text-gray-900">{value}</span>
                </div>
              ))}
            </div>

            {week >= 3 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500 mb-2">Quick Actions:</p>
                <div className="flex gap-2">
                  <button className="flex-1 bg-blue-600 text-white text-xs py-2 px-3 rounded hover:bg-blue-700">
                    Log Activity
                  </button>
                  <button className="flex-1 bg-purple-600 text-white text-xs py-2 px-3 rounded hover:bg-purple-700">
                    Add Counselor
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
