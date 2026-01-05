'use client';

import React, { useEffect, useState } from 'react';
import { timelineApi } from '@/lib/api';
import { Calendar, CheckCircle, Circle, Clock, ArrowRight, ChevronDown, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function TimelinePage() {
  const [currentPhase, setCurrentPhase] = useState<any>(null);
  const [milestones, setMilestones] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [readinessData, setReadinessData] = useState<any>(null);
  const [showTransitionModal, setShowTransitionModal] = useState(false);
  const [expandedPhases, setExpandedPhases] = useState<{[key: number]: boolean}>({});

  useEffect(() => {
    loadTimeline();
  }, []);

  const loadTimeline = async () => {
    try {
      const [phaseRes, milestonesRes] = await Promise.all([
        timelineApi.getCurrentPhase(),
        timelineApi.getMilestones(),
      ]);

      setCurrentPhase(phaseRes.data);
      setMilestones(milestonesRes.data || []);

      // Set current phase as expanded by default
      const currentPhaseNum = parseInt(phaseRes.data?.phase?.replace('phase', '') || '1');
      setExpandedPhases({ [currentPhaseNum]: true });

      // Load readiness data
      await loadReadiness();

      setLoading(false);
    } catch (error) {
      console.error('Error loading timeline:', error);
      setLoading(false);
    }
  };

  const loadReadiness = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/phase-transition/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (res.ok) {
        const data = await res.json();
        console.log('Readiness data loaded:', data);
        setReadinessData(data);
      } else {
        console.error('Failed to load readiness data:', res.status, res.statusText);
        const errorText = await res.text();
        console.error('Error response:', errorText);
      }
    } catch (error) {
      console.error('Error loading readiness:', error);
    }
  };

  const handleTransition = async () => {
    if (!readinessData || !readinessData.can_transition) return;

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/phase-transition/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          to_phase: readinessData.next_phase,
          decision: 'go',
          readiness_score: readinessData.readiness_score,
          notes: 'Manual phase transition via UI',
        }),
      });

      if (res.ok) {
        alert('Successfully transitioned to next phase!');
        setShowTransitionModal(false);
        await loadTimeline();
      } else {
        alert('Failed to transition phase');
      }
    } catch (error) {
      console.error('Error transitioning phase:', error);
      alert('Failed to transition phase');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Loading timeline...</div>
      </div>
    );
  }

  const allPhases = [
    {
      phase: 1,
      name: 'Credibility Pilot',
      timeline: 'Months 0-2',
      objective: 'Build trust, validate product-market fit, refine messaging',
      keyMetric: 'NPS ≥ 8',
      weeks: [
        { week: 1, title: 'Foundation', focus: 'LinkedIn optimization, initial connects' },
        { week: 2, title: 'Foundation', focus: 'LinkedIn optimization, initial connects' },
        { week: 3, title: 'Active Outreach', focus: 'Personalized outreach to engaged connections' },
        { week: 4, title: 'Active Outreach', focus: 'Personalized outreach to engaged connections' },
        { week: 5, title: 'Conversion & Onboarding', focus: 'Demos, onboarding, referral requests' },
        { week: 6, title: 'Conversion & Onboarding', focus: 'Demos, onboarding, referral requests' },
        { week: 7, title: 'Scale & Validate', focus: 'Support existing pilots, pursue referrals' },
        { week: 8, title: 'Scale & Validate', focus: 'Support existing pilots, pursue referrals' },
      ],
      deliverables: ['10-15 pilot counselors', 'NPS ≥ 8', '10+ organic referrals'],
    },
    {
      phase: 2,
      name: 'Firm Distribution',
      timeline: 'Months 2-4',
      objective: 'Scale usage through established counseling firms',
      keyMetric: 'Renewal ≥ 80%',
      weeks: [
        { week: 1, title: 'Firm Research', focus: 'Identify target firms, research decision makers' },
        { week: 2, title: 'Firm Research', focus: 'Prepare partnership pitch deck and pricing' },
        { week: 3, title: 'Partnership Outreach', focus: 'Reach out to firms, conduct demos' },
        { week: 4, title: 'Partnership Outreach', focus: 'Negotiate agreements, set up referrals' },
        { week: 5, title: 'Firm Onboarding', focus: 'Onboard partner firms, train counselors' },
        { week: 6, title: 'Firm Onboarding', focus: 'Student onboarding through firms' },
        { week: 7, title: 'Growth & Iteration', focus: 'Monitor metrics, collect feedback' },
        { week: 8, title: 'Growth & Iteration', focus: 'Achieve targets, document success stories' },
      ],
      deliverables: ['3-5 partner firms', '50+ students per firm', 'Renewal intent ≥ 80%'],
    },
    {
      phase: 3,
      name: 'Student Activation',
      timeline: 'Months 4-6',
      objective: 'Drive direct student engagement within firm ecosystem',
      keyMetric: 'WAR ≥ 60%',
      weeks: [
        { week: 1, title: 'Platform Enhancement', focus: 'Launch student dashboard and features' },
        { week: 2, title: 'Platform Enhancement', focus: 'Deploy clustering, task management' },
        { week: 3, title: 'Student Activation', focus: 'Drive activation via counselor invites' },
        { week: 4, title: 'Student Activation', focus: 'Monitor time-to-first-value, optimize onboarding' },
        { week: 5, title: 'Engagement Optimization', focus: 'Track weekly active rate, feature adoption' },
        { week: 6, title: 'Engagement Optimization', focus: 'Deploy NPS survey, iterate on friction' },
        { week: 7, title: 'Validation', focus: 'Achieve 60%+ weekly active rate' },
        { week: 8, title: 'Validation', focus: 'Collect testimonials, prepare for Phase 4' },
      ],
      deliverables: ['Student dashboard', 'Weekly active rate ≥ 60%', 'Student NPS ≥ 7'],
    },
    {
      phase: 4,
      name: 'Direct Growth',
      timeline: 'Month 6+',
      objective: 'Platform expansion to consumer market',
      keyMetric: 'Conversion ≥ 5%',
      weeks: [
        { week: 1, title: 'Public Launch', focus: 'Launch signup flow and pricing tiers' },
        { week: 2, title: 'Public Launch', focus: 'Deploy counselor marketplace, referral program' },
        { week: 3, title: 'Marketing Campaigns', focus: 'Begin content marketing, drive traffic' },
        { week: 4, title: 'Marketing Campaigns', focus: 'Monitor conversion, engage on social' },
        { week: 5, title: 'Growth & Optimization', focus: 'Optimize CAC, expand content' },
        { week: 6, title: 'Growth & Optimization', focus: 'Build school counselor partnerships' },
        { week: 7, title: 'Scale', focus: 'Scale to 500+ monthly signups' },
        { week: 8, title: 'Scale', focus: 'Maintain retention, continuous iteration' },
      ],
      deliverables: ['Public signup', '500+ monthly signups', 'Paid conversion ≥ 5%', '70%+ 12-mo retention'],
    },
  ];

  const currentPhaseNum = parseInt(currentPhase?.phase?.replace('phase', '') || '1');
  const phase1Weeks = allPhases[0].weeks;

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
            <h1 className="text-3xl font-bold text-gray-900">Timeline & Milestones</h1>
            <p className="text-gray-600 mt-1">
              Track phase progress and key deadlines for Phase 1 launch
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Current Phase Status */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {currentPhase?.phase?.replace('phase', 'Phase ')} - Week {currentPhase?.week_number}
              </h2>
              <p className="text-gray-600 mt-1">
                {currentPhase?.week_start_date && currentPhase?.week_end_date
                  ? `${new Date(currentPhase.week_start_date).toLocaleDateString()} to ${new Date(currentPhase.week_end_date).toLocaleDateString()}`
                  : 'Dates not available'}
              </p>
            </div>
            <div
              className={`px-4 py-2 rounded-full text-sm font-semibold ${
                currentPhase?.on_schedule
                  ? 'bg-green-100 text-green-800'
                  : 'bg-orange-100 text-orange-800'
              }`}
            >
              {currentPhase?.on_schedule ? '✓ On Track' : '⚠ Needs Attention'}
            </div>
          </div>

          {currentPhase?.blockers && currentPhase.blockers.length > 0 && (
            <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
              <h3 className="font-semibold text-orange-900 mb-2">Current Blockers:</h3>
              <ul className="space-y-1">
                {currentPhase.blockers.map((blocker: string, idx: number) => (
                  <li key={idx} className="text-orange-800 text-sm">
                    • {blocker}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {readinessData && readinessData.current_phase !== 'phase4' && (
            <div className="mt-4">
              <button
                onClick={() => setShowTransitionModal(true)}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
              >
                <ArrowRight className="w-5 h-5" />
                Evaluate Phase Transition
              </button>
            </div>
          )}
        </div>

        {/* Phase Transition Modal */}
        {showTransitionModal && readinessData && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6">
                <h2 className="text-2xl font-bold">Phase Transition Readiness</h2>
                <p className="text-purple-100 mt-1">
                  {readinessData.current_phase} → {readinessData.next_phase}
                </p>
              </div>

              <div className="p-6">
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">Readiness Score</h3>
                    <span className={`text-3xl font-bold ${
                      readinessData.readiness_score >= 80 ? 'text-green-600' :
                      readinessData.readiness_score >= 60 ? 'text-orange-600' : 'text-red-600'
                    }`}>
                      {readinessData.readiness_score.toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div
                      className={`h-4 rounded-full transition-all ${
                        readinessData.readiness_score >= 80 ? 'bg-green-600' :
                        readinessData.readiness_score >= 60 ? 'bg-orange-600' : 'bg-red-600'
                      }`}
                      style={{ width: `${readinessData.readiness_score}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    Recommendation: <span className="font-semibold">{readinessData.recommendation}</span>
                  </p>
                </div>

                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Success Criteria</h3>
                  <div className="space-y-3">
                    {Object.entries(readinessData.criteria).map(([key, criterion]: [string, any]) => (
                      <div key={key} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                        {criterion.met ? (
                          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                        ) : (
                          <Circle className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{criterion.description}</div>
                          <div className="text-sm text-gray-600 mt-1">
                            Current: <span className="font-semibold">{criterion.current}</span> |
                            Target: <span className="font-semibold">{criterion.target}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-gray-600 mt-3">
                    {readinessData.criteria_met} of {readinessData.total_criteria} criteria met
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setShowTransitionModal(false)}
                    className="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleTransition}
                    disabled={!readinessData.can_transition}
                    className={`flex-1 px-4 py-2 rounded-lg transition-colors flex items-center justify-center gap-2 ${
                      readinessData.can_transition
                        ? 'bg-purple-600 text-white hover:bg-purple-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    <ArrowRight className="w-5 h-5" />
                    Proceed to Next Phase
                  </button>
                </div>

                {!readinessData.can_transition && (
                  <p className="text-sm text-orange-600 mt-3 text-center">
                    Readiness score must be at least 70% to transition
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* All Phases Overview */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <Calendar className="w-6 h-6 text-blue-600" />
            Complete GTM Roadmap
          </h2>

          <div className="grid md:grid-cols-2 gap-4">
            {allPhases.map((phase) => {
              const isCurrentPhase = phase.phase === currentPhaseNum;
              const isPastPhase = phase.phase < currentPhaseNum;

              return (
                <div
                  key={phase.phase}
                  className={`p-5 rounded-lg border-2 transition-all ${
                    isCurrentPhase
                      ? 'border-blue-500 bg-blue-50'
                      : isPastPhase
                      ? 'border-green-200 bg-green-50'
                      : 'border-gray-200 bg-white'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-bold text-gray-900">
                        Phase {phase.phase}: {phase.name}
                      </h3>
                      <p className="text-sm text-gray-600">{phase.timeline}</p>
                    </div>
                    {isCurrentPhase && (
                      <span className="text-xs font-semibold text-blue-600 bg-blue-100 px-2 py-1 rounded">
                        CURRENT
                      </span>
                    )}
                    {isPastPhase && <CheckCircle className="w-5 h-5 text-green-600" />}
                  </div>
                  <p className="text-sm text-gray-700 mb-2">
                    <span className="font-semibold">Objective:</span> {phase.objective}
                  </p>
                  <p className="text-sm text-purple-700 font-semibold mb-2">
                    🎯 {phase.keyMetric}
                  </p>
                  {phase.deliverables && (
                    <div className="text-sm text-gray-600">
                      <span className="font-semibold">Key Deliverables:</span>
                      <ul className="list-disc ml-4 mt-1">
                        {phase.deliverables.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Detailed Week-by-Week Timelines for All Phases */}
        {allPhases.map((phaseData) => {
          const isExpanded = expandedPhases[phaseData.phase] || false;
          const toggleExpanded = () => {
            setExpandedPhases(prev => ({
              ...prev,
              [phaseData.phase]: !prev[phaseData.phase]
            }));
          };

          return (
            <div key={phaseData.phase} className="bg-white rounded-lg shadow p-6 mb-6">
              <button
                onClick={toggleExpanded}
                className="w-full flex items-center justify-between text-left mb-4"
              >
                <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <Clock className="w-6 h-6 text-blue-600" />
                  Phase {phaseData.phase}: {phaseData.name} - 8-Week Timeline
                </h2>
                <ChevronDown className={`w-6 h-6 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
              </button>

              {isExpanded && (
                <div className="space-y-4">
                  {phaseData.weeks?.map((weekData) => {
                    const isCurrentWeek = phaseData.phase === currentPhaseNum && weekData.week === currentPhase?.week_number;
                    const isPast = phaseData.phase < currentPhaseNum ||
                                   (phaseData.phase === currentPhaseNum && weekData.week < (currentPhase?.week_number || 1));

                    return (
                      <div
                        key={weekData.week}
                        className={`relative flex items-start gap-4 p-4 rounded-lg border-2 transition-all ${
                          isCurrentWeek
                            ? 'border-blue-500 bg-blue-50'
                            : isPast
                            ? 'border-green-200 bg-green-50'
                            : 'border-gray-200 bg-white'
                        }`}
                      >
                        <div className="flex-shrink-0">
                          {isPast ? (
                            <CheckCircle className="w-6 h-6 text-green-600" />
                          ) : isCurrentWeek ? (
                            <Clock className="w-6 h-6 text-blue-600" />
                          ) : (
                            <Circle className="w-6 h-6 text-gray-400" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h3 className="font-semibold text-gray-900">
                              Week {weekData.week}: {weekData.title}
                            </h3>
                            {isCurrentWeek && (
                              <span className="text-xs font-semibold text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                CURRENT WEEK
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mt-1">Focus: {weekData.focus}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {/* Milestones */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-purple-600" />
            Key Milestones
          </h2>

          {milestones.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600">No milestones defined yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {milestones.map((milestone) => (
                <div
                  key={milestone.id}
                  className="flex items-start gap-4 p-4 rounded-lg border border-gray-200 hover:border-purple-300 transition-colors"
                >
                  <div className="flex-shrink-0">
                    {milestone.completed ? (
                      <CheckCircle className="w-6 h-6 text-green-600" />
                    ) : (
                      <Circle className="w-6 h-6 text-gray-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{milestone.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{milestone.description}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span>Due: {milestone.target_date}</span>
                      {milestone.completed && milestone.completed_date && (
                        <span className="text-green-600">
                          Completed: {milestone.completed_date}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
