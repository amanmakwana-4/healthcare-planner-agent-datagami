import React, { useState, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import InputForm from '../components/InputForm';
import SummaryCard from '../components/SummaryCard';
import HospitalCard from '../components/HospitalCard';
import DoctorCard from '../components/DoctorCard';
import PlanSection from '../components/PlanSection';
import SkeletonLoader from '../components/Loader';
import { generateHealthcarePlan } from '../services/api';
import { AlertCircle, RotateCcw } from 'lucide-react';

const confidenceClassMap = {
  'Exact GPS': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  'City-level': 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  'Fallback Web': 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
};

const confidenceClass = (value) => confidenceClassMap[value] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';

const Home = () => {
  const [inputs, setInputs] = useState(null);
  const resultsRef = useRef(null);

  const {
    data: result,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: inputs
      ? ['healthcarePlan', inputs.topic, inputs.location, inputs.locationMode, inputs.latitude, inputs.longitude]
      : [],
    queryFn: () => generateHealthcarePlan(inputs),
    enabled: !!inputs,
    staleTime: 1000 * 60 * 60, // 1 hour
    gcTime: 1000 * 60 * 60 * 2, // 2 hours
  });

  const handleSubmit = (payload) => {
    setInputs(payload);
  };

  const hasDoctorsInsideHospitals =
    !!result?.hospitals?.some(
      (hospital) => Array.isArray(hospital.specialistDoctors) && hospital.specialistDoctors.length > 0
    );

  // Scroll to results when data arrives
  useEffect(() => {
    if (result && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [result]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Input Section */}
      <div className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950">
        <InputForm onSubmit={handleSubmit} isLoading={isLoading} />
      </div>

      {/* Results Section */}
      {(isLoading || error || result) && (
        <div
          ref={resultsRef}
          className="w-full max-w-3xl mx-auto px-4 py-8 md:py-12"
        >
          {/* Loading State */}
          {isLoading && (
            <div className="space-y-6">
              <SkeletonLoader type="summary" />
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Nearby Hospitals
                </h2>
                <SkeletonLoader count={3} type="card" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Recommended Doctors
                </h2>
                <SkeletonLoader count={3} type="card" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Your Healthcare Plan
                </h2>
                <SkeletonLoader type="text" count={6} />
              </div>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-300 dark:border-red-800 rounded-2xl p-6 md:p-8 text-center animate-fadeIn">
              <AlertCircle className="w-12 h-12 text-red-600 dark:text-red-400 mx-auto mb-4" />
              <h2 className="text-lg md:text-xl font-semibold text-red-900 dark:text-red-200 mb-2">
                Something went wrong
              </h2>
              <p className="text-red-800 dark:text-red-300 mb-6 leading-relaxed">
                {error?.message || 'Failed to generate healthcare plan. Please try again.'}
              </p>
              <button
                onClick={() => refetch()}
                className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 active:scale-95 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200"
              >
                <RotateCcw className="w-5 h-5" />
                Try Again
              </button>
            </div>
          )}

          {/* Results State */}
          {result && !isLoading && (
            <div className="space-y-8 pb-8">
              {result.location_confidence && (
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                    Location Confidence
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${confidenceClass(result.location_confidence.overall)}`}>
                      Overall: {result.location_confidence.overall}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${confidenceClass(result.location_confidence.hospitals)}`}>
                      Hospitals: {result.location_confidence.hospitals}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${confidenceClass(result.location_confidence.doctors)}`}>
                      Doctors: {result.location_confidence.doctors}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
                    Area: {result.location_confidence.location}
                  </p>
                </div>
              )}

              {/* Summary Card */}
              {result.summary && <SummaryCard summary={result.summary} />}

              {/* Hospitals Section */}
              {result.hospitals && result.hospitals.length > 0 && (
                <div>
                  <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-4">
                    🏥 Nearby Hospitals
                  </h2>
                  <div className="space-y-3">
                    {result.hospitals.map((hospital, idx) => (
                      <HospitalCard key={idx} hospital={hospital} index={idx} />
                    ))}
                  </div>
                </div>
              )}

              {/* Doctors Section */}
              {result.doctors && result.doctors.length > 0 && !hasDoctorsInsideHospitals && (
                <div>
                  <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-4">
                    👨‍⚕️ Recommended Doctors
                  </h2>
                  <div className="space-y-3">
                    {result.doctors.map((doctor, idx) => (
                      <DoctorCard key={idx} doctor={doctor} index={idx} />
                    ))}
                  </div>
                </div>
              )}

              {/* Plan Section */}
              {result.plan && <PlanSection plan={result.plan} />}

              {/* New Search CTA */}
              <div className="text-center py-6">
                <button
                  onClick={() => setInputs(null)}
                  className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-semibold transition-colors duration-200"
                >
                  ← Start a New Search
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Home;
