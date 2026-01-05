'use client';

import { useEffect, useState } from 'react';
import { counselorsApi } from '@/lib/api';
import { Users, Search, Filter, Plus, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function CounselorsPage() {
  const [counselors, setCounselors] = useState<any[]>([]);
  const [pipelineStats, setPipelineStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStage, setFilterStage] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newCounselor, setNewCounselor] = useState({
    name: '',
    email: '',
    linkedin_url: '',
    firm: '',
    location: '',
    specialization: '',
  });

  useEffect(() => {
    loadCounselors();
  }, []);

  const loadCounselors = async () => {
    try {
      const [counselorsRes, statsRes] = await Promise.all([
        counselorsApi.getAll(),
        counselorsApi.getPipelineStats(),
      ]);

      setCounselors(counselorsRes.data);
      setPipelineStats(statsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading counselors:', error);
      setLoading(false);
    }
  };

  const handleAddCounselor = async () => {
    try {
      await counselorsApi.create(newCounselor);
      setShowAddModal(false);
      setNewCounselor({
        name: '',
        email: '',
        linkedin_url: '',
        firm: '',
        location: '',
        specialization: '',
      });
      await loadCounselors();
    } catch (error) {
      console.error('Error adding counselor:', error);
      alert('Failed to add counselor');
    }
  };

  const filteredCounselors = counselors.filter((c) => {
    const matchesSearch =
      c.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.school?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStage = filterStage === 'all' || c.stage === filterStage;

    return matchesSearch && matchesStage;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Loading counselors...</div>
      </div>
    );
  }

  const stages = ['target', 'connected', 'discovery', 'demo_scheduled', 'demo_completed', 'pilot', 'active', 'advocate', 'churned'];

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
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Counselor Pipeline</h1>
              <p className="text-gray-600 mt-1">
                Manage your counselor prospects and track pipeline progress
              </p>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Add Counselor
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Pipeline Stats */}
        {pipelineStats && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Pipeline Overview</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(pipelineStats.by_stage).map(([stage, count]) => (
                <div key={stage} className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">{count as number}</div>
                  <div className="text-sm text-gray-600 capitalize mt-1">
                    {stage.replace('_', ' ')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by name, email, or school..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="text-gray-400 w-5 h-5" />
              <select
                value={filterStage}
                onChange={(e) => setFilterStage(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Stages</option>
                {stages.map((stage) => (
                  <option key={stage} value={stage}>
                    {stage.replace('_', ' ').charAt(0).toUpperCase() + stage.replace('_', ' ').slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Counselors List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-600" />
              Counselors ({filteredCounselors.length})
            </h2>
          </div>

          {filteredCounselors.length === 0 ? (
            <div className="p-12 text-center">
              <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No counselors found</h3>
              <p className="text-gray-600 mb-4">
                {searchTerm || filterStage !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Get started by adding your first counselor prospect'}
              </p>
              <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                Add First Counselor
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      School
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stage
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Priority
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Contact
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredCounselors.map((counselor) => (
                    <tr key={counselor.id} className="hover:bg-gray-50 cursor-pointer">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{counselor.name}</div>
                        <div className="text-sm text-gray-500">{counselor.email}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {counselor.school || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800 capitalize">
                          {counselor.stage?.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {counselor.priority_score || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {counselor.last_contact_date
                          ? new Date(counselor.last_contact_date).toLocaleDateString()
                          : 'Never'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Add Counselor Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="bg-blue-600 text-white p-4 rounded-t-lg">
              <h2 className="text-xl font-bold">Add New Counselor</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  type="text"
                  value={newCounselor.name}
                  onChange={(e) => setNewCounselor({ ...newCounselor, name: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="John Doe"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input
                  type="email"
                  value={newCounselor.email}
                  onChange={(e) => setNewCounselor({ ...newCounselor, email: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="john@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">LinkedIn URL</label>
                <input
                  type="url"
                  value={newCounselor.linkedin_url}
                  onChange={(e) => setNewCounselor({ ...newCounselor, linkedin_url: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://linkedin.com/in/..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Firm</label>
                <input
                  type="text"
                  value={newCounselor.firm}
                  onChange={(e) => setNewCounselor({ ...newCounselor, firm: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="ABC Counseling"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={newCounselor.location}
                  onChange={(e) => setNewCounselor({ ...newCounselor, location: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="New York, NY"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Specialization</label>
                <input
                  type="text"
                  value={newCounselor.specialization}
                  onChange={(e) => setNewCounselor({ ...newCounselor, specialization: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="College admissions"
                />
              </div>
            </div>
            <div className="p-4 bg-gray-50 rounded-b-lg flex gap-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddCounselor}
                disabled={!newCounselor.name || !newCounselor.email}
                className={`flex-1 px-4 py-2 rounded-lg transition-colors ${
                  newCounselor.name && newCounselor.email
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                Add Counselor
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
