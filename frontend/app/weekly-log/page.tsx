'use client';

import { useEffect, useState } from 'react';
import { weeklyLogsApi, timelineApi } from '@/lib/api';
import { CheckCircle, Circle, Save, Calendar, TrendingUp, AlertCircle, Copy, Download, MessageCircle } from 'lucide-react';
import { useActivityChat } from '@/contexts/ActivityChatContext';

export default function WeeklyLogPage() {
  const [weeklyLog, setWeeklyLog] = useState<any>(null);
  const [currentPhase, setCurrentPhase] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { openChat } = useActivityChat();

  useEffect(() => {
    loadWeeklyLog();
  }, []);

  const loadWeeklyLog = async () => {
    try {
      const phaseRes = await timelineApi.getCurrentPhase();
      setCurrentPhase(phaseRes.data);

      const logRes = await weeklyLogsApi.getCurrent(
        phaseRes.data.phase,
        phaseRes.data.week_number
      );
      setWeeklyLog(logRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading weekly log:', error);
      setLoading(false);
    }
  };

  const toggleActivity = (taskId: string) => {
    if (!weeklyLog) return;

    const updated = {
      ...weeklyLog,
      activities: weeklyLog.activities.map((act: any) =>
        act.task_id === taskId
          ? {
              ...act,
              completed: !act.completed,
              completed_at: !act.completed ? new Date().toISOString() : null,
            }
          : act
      ),
    };
    setWeeklyLog(updated);
  };

  const updateMetric = (field: string, value: number) => {
    setWeeklyLog({ ...weeklyLog, [field]: value });
  };

  const addItem = (field: 'wins' | 'challenges' | 'learnings', value: string) => {
    if (!value.trim()) return;
    setWeeklyLog({
      ...weeklyLog,
      [field]: [...(weeklyLog[field] || []), value],
    });
  };

  const removeItem = (field: 'wins' | 'challenges' | 'learnings', index: number) => {
    setWeeklyLog({
      ...weeklyLog,
      [field]: weeklyLog[field].filter((_: any, i: number) => i !== index),
    });
  };

  const saveLog = async () => {
    if (!weeklyLog || !currentPhase) return;

    setSaving(true);
    try {
      await weeklyLogsApi.updateLog(
        currentPhase.phase,
        currentPhase.week_number,
        weeklyLog
      );
      alert('Weekly log saved successfully!');
    } catch (error) {
      console.error('Error saving log:', error);
      alert('Failed to save log');
    } finally {
      setSaving(false);
    }
  };

  const submitLog = async () => {
    if (!weeklyLog || !currentPhase) return;

    setSaving(true);
    try {
      await weeklyLogsApi.updateLog(
        currentPhase.phase,
        currentPhase.week_number,
        { ...weeklyLog, submitted: true }
      );
      alert('Weekly log submitted!');
      loadWeeklyLog();
    } catch (error) {
      console.error('Error submitting log:', error);
      alert('Failed to submit log');
    } finally {
      setSaving(false);
    }
  };

  const generateLogText = () => {
    if (!weeklyLog || !currentPhase) return '';

    const completedActivities = weeklyLog.activities?.filter((a: any) => a.completed) || [];
    const pendingActivities = weeklyLog.activities?.filter((a: any) => !a.completed) || [];

    let text = `# Weekly Log - ${currentPhase.phase.replace('phase', 'Phase ')} Week ${currentPhase.week_number}\n\n`;
    text += `📅 ${weeklyLog.week_start_date} to ${weeklyLog.week_end_date}\n\n`;

    text += `## 📊 Weekly Metrics\n`;
    text += `- Connections Made: ${weeklyLog.connections_made || 0}\n`;
    text += `- DMs Sent: ${weeklyLog.dms_sent || 0}\n`;
    text += `- Discovery Calls: ${weeklyLog.discovery_calls || 0}\n`;
    text += `- Demos Completed: ${weeklyLog.demos_completed || 0}\n`;
    text += `- Pilots Onboarded: ${weeklyLog.pilots_onboarded_this_week || 0}\n`;
    text += `- Referrals Received: ${weeklyLog.referrals_received || 0}\n\n`;

    text += `## ✅ Completed Activities (${completedActivities.length}/${weeklyLog.activities?.length || 0})\n`;
    completedActivities.forEach((act: any) => {
      text += `- [x] ${act.task_description}\n`;
    });
    text += `\n`;

    if (pendingActivities.length > 0) {
      text += `## ⏳ Pending Activities (${pendingActivities.length})\n`;
      pendingActivities.forEach((act: any) => {
        text += `- [ ] ${act.task_description}\n`;
      });
      text += `\n`;
    }

    if (weeklyLog.wins?.length > 0) {
      text += `## 🎉 Wins\n`;
      weeklyLog.wins.forEach((win: string) => {
        text += `- ${win}\n`;
      });
      text += `\n`;
    }

    if (weeklyLog.challenges?.length > 0) {
      text += `## ⚠️ Challenges\n`;
      weeklyLog.challenges.forEach((challenge: string) => {
        text += `- ${challenge}\n`;
      });
      text += `\n`;
    }

    if (weeklyLog.learnings?.length > 0) {
      text += `## 💡 Learnings\n`;
      weeklyLog.learnings.forEach((learning: string) => {
        text += `- ${learning}\n`;
      });
      text += `\n`;
    }

    if (weeklyLog.next_week_focus) {
      text += `## 🎯 Next Week's Focus\n`;
      text += `${weeklyLog.next_week_focus}\n\n`;
    }

    text += `---\n`;
    text += `Generated with TargetAI Launch Manager\n`;

    return text;
  };

  const copyToClipboard = async () => {
    const text = generateLogText();
    try {
      await navigator.clipboard.writeText(text);
      alert('Weekly log copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy:', error);
      alert('Failed to copy to clipboard');
    }
  };

  const downloadAsMarkdown = () => {
    const text = generateLogText();
    const blob = new Blob([text], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `week-${currentPhase?.week_number}-log.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Loading weekly log...</div>
      </div>
    );
  }

  const completedCount = weeklyLog?.activities?.filter((a: any) => a.completed).length || 0;
  const totalCount = weeklyLog?.activities?.length || 0;
  const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Weekly Log</h1>
              <p className="text-gray-600 mt-1">
                {currentPhase?.phase.replace('phase', 'Phase ')} - Week {currentPhase?.week_number}
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={copyToClipboard}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
              >
                <Copy className="w-4 h-4" />
                Copy
              </button>
              <button
                onClick={downloadAsMarkdown}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
              <button
                onClick={saveLog}
                disabled={saving}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Saving...' : 'Save Draft'}
              </button>
              {!weeklyLog?.submitted && (
                <button
                  onClick={submitLog}
                  disabled={saving}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Submit Week
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Progress Bar */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-lg font-semibold text-gray-900">Weekly Progress</h2>
            <span className="text-sm text-gray-600">
              {completedCount} of {totalCount} completed
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Activities Checklist */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-600" />
              Activities Checklist
            </h2>
            <ul className="space-y-3">
              {weeklyLog?.activities?.map((activity: any) => (
                <li
                  key={activity.task_id}
                  className="flex items-start gap-3 p-3 rounded hover:bg-gray-50 group"
                >
                  <div
                    className="flex items-start gap-3 flex-1 cursor-pointer"
                    onClick={() => toggleActivity(activity.task_id)}
                  >
                    {activity.completed ? (
                      <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    ) : (
                      <Circle className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                    )}
                    <span
                      className={`flex-1 ${
                        activity.completed ? 'line-through text-gray-500' : 'text-gray-700'
                      }`}
                    >
                      {activity.task_description}
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      openChat(activity.task_description, activity.task_id);
                    }}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-purple-100 rounded text-purple-600"
                    title="Get AI assistance"
                  >
                    <MessageCircle className="w-4 h-4" />
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Weekly Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-purple-600" />
              Weekly Metrics
            </h2>
            <div className="space-y-4">
              {/* Phase 1 Metrics */}
              {currentPhase?.phase === 'phase1' && (
                <>
                  <MetricInput
                    label="Connections Made"
                    value={weeklyLog?.connections_made || 0}
                    onChange={(v) => updateMetric('connections_made', v)}
                  />
                  <MetricInput
                    label="DMs Sent"
                    value={weeklyLog?.dms_sent || 0}
                    onChange={(v) => updateMetric('dms_sent', v)}
                  />
                  <MetricInput
                    label="Discovery Calls"
                    value={weeklyLog?.discovery_calls || 0}
                    onChange={(v) => updateMetric('discovery_calls', v)}
                  />
                  <MetricInput
                    label="Demos Completed"
                    value={weeklyLog?.demos_completed || 0}
                    onChange={(v) => updateMetric('demos_completed', v)}
                  />
                  <MetricInput
                    label="Pilots Onboarded"
                    value={weeklyLog?.pilots_onboarded_this_week || 0}
                    onChange={(v) => updateMetric('pilots_onboarded_this_week', v)}
                  />
                  <MetricInput
                    label="Referrals Received"
                    value={weeklyLog?.referrals_received || 0}
                    onChange={(v) => updateMetric('referrals_received', v)}
                  />
                </>
              )}

              {/* Phase 2 Metrics */}
              {currentPhase?.phase === 'phase2' && (
                <>
                  <MetricInput
                    label="Firms Contacted"
                    value={weeklyLog?.firms_contacted || 0}
                    onChange={(v) => updateMetric('firms_contacted', v)}
                  />
                  <MetricInput
                    label="Partnership Agreements Signed"
                    value={weeklyLog?.partnership_agreements_signed || 0}
                    onChange={(v) => updateMetric('partnership_agreements_signed', v)}
                  />
                  <MetricInput
                    label="Students Onboarded"
                    value={weeklyLog?.students_onboarded_this_week || 0}
                    onChange={(v) => updateMetric('students_onboarded_this_week', v)}
                  />
                  <MetricInput
                    label="Firm Demos Completed"
                    value={weeklyLog?.firm_demos_completed || 0}
                    onChange={(v) => updateMetric('firm_demos_completed', v)}
                  />
                </>
              )}

              {/* Phase 3 Metrics */}
              {currentPhase?.phase === 'phase3' && (
                <>
                  <MetricInput
                    label="Active Students This Week"
                    value={weeklyLog?.active_students_this_week || 0}
                    onChange={(v) => updateMetric('active_students_this_week', v)}
                  />
                  <MetricInput
                    label="Student Sessions"
                    value={weeklyLog?.student_sessions || 0}
                    onChange={(v) => updateMetric('student_sessions', v)}
                  />
                  <MetricInput
                    label="Feature Adoption Events"
                    value={weeklyLog?.feature_adoption_events || 0}
                    onChange={(v) => updateMetric('feature_adoption_events', v)}
                  />
                  <MetricInput
                    label="Student Feedback Collected"
                    value={weeklyLog?.student_feedback_collected || 0}
                    onChange={(v) => updateMetric('student_feedback_collected', v)}
                  />
                </>
              )}

              {/* Phase 4 Metrics */}
              {currentPhase?.phase === 'phase4' && (
                <>
                  <MetricInput
                    label="New Signups"
                    value={weeklyLog?.new_signups || 0}
                    onChange={(v) => updateMetric('new_signups', v)}
                  />
                  <MetricInput
                    label="Paid Conversions"
                    value={weeklyLog?.paid_conversions || 0}
                    onChange={(v) => updateMetric('paid_conversions', v)}
                  />
                  <MetricInput
                    label="Churn Count"
                    value={weeklyLog?.churn_count || 0}
                    onChange={(v) => updateMetric('churn_count', v)}
                  />
                  <MetricInput
                    label="Marketing Spend ($)"
                    value={weeklyLog?.marketing_spend || 0}
                    onChange={(v) => updateMetric('marketing_spend', v)}
                    isDecimal
                  />
                  <MetricInput
                    label="Revenue This Week ($)"
                    value={weeklyLog?.revenue_this_week || 0}
                    onChange={(v) => updateMetric('revenue_this_week', v)}
                    isDecimal
                  />
                </>
              )}
            </div>
          </div>
        </div>

        {/* Reflections */}
        <div className="grid lg:grid-cols-3 gap-6 mt-6">
          <ReflectionSection
            title="Wins 🎉"
            items={weeklyLog?.wins || []}
            placeholder="What went well this week?"
            onAdd={(value) => addItem('wins', value)}
            onRemove={(index) => removeItem('wins', index)}
            color="green"
          />
          <ReflectionSection
            title="Challenges ⚠️"
            items={weeklyLog?.challenges || []}
            placeholder="What was difficult?"
            onAdd={(value) => addItem('challenges', value)}
            onRemove={(index) => removeItem('challenges', index)}
            color="orange"
          />
          <ReflectionSection
            title="Learnings 💡"
            items={weeklyLog?.learnings || []}
            placeholder="What did you learn?"
            onAdd={(value) => addItem('learnings', value)}
            onRemove={(index) => removeItem('learnings', index)}
            color="blue"
          />
        </div>

        {/* Next Week Focus */}
        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Next Week's Focus</h2>
          <textarea
            value={weeklyLog?.next_week_focus || ''}
            onChange={(e) => setWeeklyLog({ ...weeklyLog, next_week_focus: e.target.value })}
            placeholder="What will you focus on next week?"
            className="w-full p-3 border border-gray-300 rounded-lg resize-none"
            rows={3}
          />
        </div>

        {/* Export Preview */}
        <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-6 mt-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-700">📋 Export Preview</h2>
            <p className="text-sm text-gray-500">This is what will be copied/downloaded</p>
          </div>
          <pre className="bg-white p-4 rounded border border-gray-300 text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap">
            {generateLogText()}
          </pre>
        </div>
      </main>
    </div>
  );
}

function MetricInput({
  label,
  value,
  onChange,
  isDecimal = false,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  isDecimal?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(isDecimal ? parseFloat(e.target.value) || 0 : parseInt(e.target.value) || 0)}
        min="0"
        step={isDecimal ? "0.01" : "1"}
        className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-center"
      />
    </div>
  );
}

function ReflectionSection({
  title,
  items,
  placeholder,
  onAdd,
  onRemove,
  color,
}: {
  title: string;
  items: string[];
  placeholder: string;
  onAdd: (value: string) => void;
  onRemove: (index: number) => void;
  color: 'green' | 'orange' | 'blue';
}) {
  const [newItem, setNewItem] = useState('');

  const handleAdd = () => {
    onAdd(newItem);
    setNewItem('');
  };

  const colorClasses = {
    green: 'bg-green-50 border-green-200',
    orange: 'bg-orange-50 border-orange-200',
    blue: 'bg-blue-50 border-blue-200',
  };

  return (
    <div className={`rounded-lg border-2 p-6 ${colorClasses[color]}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <ul className="space-y-2 mb-4">
        {items.map((item, index) => (
          <li key={index} className="flex items-start gap-2 text-sm">
            <span className="flex-1 text-gray-700">• {item}</span>
            <button
              onClick={() => onRemove(index)}
              className="text-red-600 hover:text-red-800 text-xs"
            >
              ×
            </button>
          </li>
        ))}
      </ul>
      <div className="flex gap-2">
        <input
          type="text"
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAdd()}
          placeholder={placeholder}
          className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
        />
        <button
          onClick={handleAdd}
          className="bg-gray-600 text-white px-3 py-2 rounded hover:bg-gray-700 text-sm"
        >
          +
        </button>
      </div>
    </div>
  );
}
