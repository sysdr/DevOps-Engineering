import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BuildsList = () => {
  const [builds, setBuilds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBuilds();
  }, []);

  const fetchBuilds = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/metrics/trends');
      if (response.data.build_times) {
        setBuilds(response.data.build_times);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching builds:', error);
      setLoading(false);
    }
  };

  const triggerTestBuild = async () => {
    try {
      const buildId = `test-${Date.now()}`;
      await axios.post('http://localhost:8000/api/builds/start', {
        build_id: buildId,
        pipeline_name: 'test-pipeline'
      });
      
      // Simulate build completion after 10 seconds
      setTimeout(async () => {
        await axios.post(`http://localhost:8000/api/builds/${buildId}/finish`, {
          success: Math.random() > 0.1 // 90% success rate
        });
        fetchBuilds();
      }, 10000);
      
    } catch (error) {
      console.error('Error triggering build:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Build History</h2>
        <button
          onClick={triggerTestBuild}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          Trigger Test Build
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Build ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {builds.map((build, index) => (
                <tr key={build.build_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {build.build_id}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {build.duration.toFixed(1)}s
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {new Date(build.timestamp * 1000).toLocaleString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      build.duration < 30 
                        ? 'bg-green-100 text-green-800'
                        : build.duration < 60
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {build.duration < 30 ? 'Fast' : build.duration < 60 ? 'Average' : 'Slow'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default BuildsList;
