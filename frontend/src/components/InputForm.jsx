import React, { useState, useEffect } from 'react';
import { Search, AlertCircle, LocateFixed, MapPin } from 'lucide-react';

const InputForm = ({ onSubmit, isLoading }) => {
  const [topic, setTopic] = useState('');
  const [location, setLocation] = useState('');
  const [locationMode, setLocationMode] = useState('manual');
  const [geo, setGeo] = useState({ latitude: null, longitude: null, label: '' });
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);
  const [errors, setErrors] = useState({});
  const [locationStatus, setLocationStatus] = useState({ type: '', message: '' });

  const validateForm = () => {
    const newErrors = {};
    if (!topic.trim()) newErrors.topic = 'Please enter a symptom or disease';
    if (locationMode === 'manual' && !location.trim()) {
      newErrors.location = 'Please enter a location';
    }
    if (locationMode === 'current' && (!geo.latitude || !geo.longitude)) {
      newErrors.location = 'Please detect your current location first';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const reverseGeocode = async (latitude, longitude) => {
    const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`;
    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
    });
    if (!response.ok) return '';
    const data = await response.json();
    const address = data?.address || {};
    const city = address.city || address.town || address.village || address.county || '';
    const state = address.state || '';
    const country = address.country || '';
    return [city, state, country].filter(Boolean).join(', ');
  };

  const detectApproxLocationByIP = async () => {
    const response = await fetch('https://ipapi.co/json/', {
      headers: {
        Accept: 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error('Unable to detect approximate location');
    }
    const data = await response.json();
    const latitude = Number(data.latitude);
    const longitude = Number(data.longitude);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      throw new Error('Approximate location unavailable');
    }
    const label = [data.city, data.region, data.country_name].filter(Boolean).join(', ') || `Approx location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`;
    return { latitude, longitude, label };
  };

  const detectCurrentLocation = async () => {
    if (!navigator.geolocation) {
      setErrors((prev) => ({ ...prev, location: 'Geolocation is not supported in this browser' }));
      return;
    }

    setIsDetectingLocation(true);
    setErrors((prev) => ({ ...prev, location: '' }));
    setLocationStatus({ type: '', message: '' });

    if (!window.isSecureContext) {
      try {
        const approx = await detectApproxLocationByIP();
        setGeo(approx);
        setLocationStatus({
          type: 'info',
          message: 'Using approximate location because GPS prompt is unavailable on this page.',
        });
      } catch (e) {
        setErrors((prev) => ({ ...prev, location: 'GPS prompt unavailable here. Open via localhost/https and try again.' }));
      }
      setIsDetectingLocation(false);
      return;
    }

    try {
      if (navigator.permissions && navigator.permissions.query) {
        const permission = await navigator.permissions.query({ name: 'geolocation' });
        if (permission.state === 'denied') {
          try {
            const approx = await detectApproxLocationByIP();
            setGeo(approx);
            setLocationStatus({
              type: 'warning',
              message:
                'Using approximate location. GPS permission is denied in browser settings for this site.',
            });
          } catch (e) {
            setErrors((prev) => ({
              ...prev,
              location:
                'Location permission is denied in browser settings. Enable Location for this site and try again.',
            }));
          }
          setIsDetectingLocation(false);
          return;
        }
      }
    } catch (e) {
      // Ignore permissions API failures and continue with geolocation request.
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        let label = `Current location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`;
        try {
          const resolved = await reverseGeocode(latitude, longitude);
          if (resolved) label = resolved;
        } catch (e) {
          // Keep coordinate label when reverse geocoding fails.
        }
        setGeo({ latitude, longitude, label });
        setLocationStatus({ type: 'success', message: 'Using exact GPS location.' });
        setIsDetectingLocation(false);
      },
      (error) => {
        const fallback = async () => {
          try {
            const approx = await detectApproxLocationByIP();
            setGeo(approx);
            setLocationStatus({ type: 'info', message: 'Using approximate location (GPS unavailable).' });
          } catch (e) {
            let message = 'Unable to detect your location';
            if (error.code === 1) message = 'Location permission denied. Enable it in browser settings.';
            if (error.code === 2) message = 'Location unavailable';
            if (error.code === 3) message = 'Location request timed out';
            setErrors((prev) => ({ ...prev, location: message }));
          } finally {
            setIsDetectingLocation(false);
          }
        };
        fallback();
      },
      {
        enableHighAccuracy: true,
        timeout: 12000,
      }
    );
  };

  useEffect(() => {
    if (locationMode === 'current' && !geo.latitude && !isDetectingLocation) {
      detectCurrentLocation();
    }
    // Intentionally trigger once when entering current mode.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locationMode]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      if (locationMode === 'current') {
        onSubmit({
          topic: topic.trim(),
          location: geo.label,
          locationMode: 'current',
          latitude: geo.latitude,
          longitude: geo.longitude,
        });
      } else {
        onSubmit({
          topic: topic.trim(),
          location: location.trim(),
          locationMode: 'manual',
          latitude: null,
          longitude: null,
        });
      }
    }
  };

  const hasTopic = !!topic.trim();
  const hasManualLocation = !!location.trim();
  const hasCurrentLocation = !!geo.latitude && !!geo.longitude;
  const isValid = hasTopic && (locationMode === 'manual' ? hasManualLocation : hasCurrentLocation);

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-md mx-auto px-4 py-8 md:py-12"
    >
      {/* Heading */}
      <div className="mb-8 text-center md:text-left">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-2">
          Healthcare Assistant
        </h1>
        <p className="text-gray-600 dark:text-gray-400 text-sm md:text-base">
          Get personalized healthcare recommendations based on your symptoms
        </p>
      </div>

      {/* Disease/Symptoms Input */}
      <div className="mb-5">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Symptom or Disease
        </label>
        <div className="relative">
          <input
            type="text"
            value={topic}
            onChange={(e) => {
              setTopic(e.target.value);
              if (errors.topic) setErrors({ ...errors, topic: '' });
            }}
            placeholder="e.g. migraine, fever, diabetes"
            autoFocus
            className={`w-full px-4 py-3 md:py-4 rounded-lg border-2 transition-all focus:outline-none text-base ${
              errors.topic
                ? 'border-red-500 dark:border-red-400 bg-red-50 dark:bg-red-900/10'
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
            } focus:border-blue-500 dark:focus:border-blue-400`}
          />
          {!errors.topic && topic && (
            <Search className="absolute right-4 top-3 md:top-4 w-5 h-5 text-gray-400" />
          )}
        </div>
        {errors.topic && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center gap-1">
            <AlertCircle className="w-4 h-4" />
            {errors.topic}
          </p>
        )}
      </div>

      {/* Location Input */}
      <div className="mb-7">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Location Mode
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          <button
            type="button"
            onClick={() => {
              setLocationMode('current');
              if (errors.location) setErrors({ ...errors, location: '' });
              setLocationStatus({ type: '', message: '' });
            }}
            className={`rounded-lg border-2 px-4 py-3 text-left transition-all ${
              locationMode === 'current'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
            }`}
          >
            <span className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
              <LocateFixed className="w-4 h-4" />
              Use Current Location
            </span>
          </button>
          <button
            type="button"
            onClick={() => {
              setLocationMode('manual');
              if (errors.location) setErrors({ ...errors, location: '' });
              setLocationStatus({ type: '', message: '' });
            }}
            className={`rounded-lg border-2 px-4 py-3 text-left transition-all ${
              locationMode === 'manual'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
            }`}
          >
            <span className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
              <MapPin className="w-4 h-4" />
              Search Different City
            </span>
          </button>
        </div>

        {locationMode === 'manual' && (
          <input
            type="text"
            value={location}
            onChange={(e) => {
              setLocation(e.target.value);
              if (errors.location) setErrors({ ...errors, location: '' });
            }}
            placeholder="e.g. Indore, Mumbai, Delhi"
            className={`w-full px-4 py-3 md:py-4 rounded-lg border-2 transition-all focus:outline-none text-base ${
              errors.location
                ? 'border-red-500 dark:border-red-400 bg-red-50 dark:bg-red-900/10'
                : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
            } focus:border-blue-500 dark:focus:border-blue-400`}
          />
        )}

        {locationMode === 'current' && (
          <div className="space-y-3">
            <button
              type="button"
              onClick={detectCurrentLocation}
              disabled={isDetectingLocation}
              className="w-full py-3 rounded-lg font-semibold text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
            >
              {isDetectingLocation ? 'Detecting location...' : 'Detect Current Location'}
            </button>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {geo.label || 'No location detected yet.'}
            </p>
          </div>
        )}

        {errors.location && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center gap-1">
            <AlertCircle className="w-4 h-4" />
            {errors.location}
          </p>
        )}

        {!errors.location && locationStatus.message && (
          <p
            className={`mt-2 text-sm flex items-center gap-1 ${
              locationStatus.type === 'success'
                ? 'text-emerald-600 dark:text-emerald-400'
                : locationStatus.type === 'warning'
                ? 'text-amber-600 dark:text-amber-400'
                : 'text-blue-600 dark:text-blue-400'
            }`}
          >
            <AlertCircle className="w-4 h-4" />
            {locationStatus.message}
          </p>
        )}

        {locationMode === 'current' && (
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            If no popup appears: open site settings in your browser and set Location to Allow for localhost.
          </p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!isValid || isLoading}
        className={`w-full py-3 md:py-4 rounded-lg font-semibold text-white text-base md:text-lg transition-all duration-200 flex items-center justify-center gap-2 ${
          isValid && !isLoading
            ? 'bg-blue-600 hover:bg-blue-700 active:scale-95 shadow-md hover:shadow-lg'
            : 'bg-gray-400 dark:bg-gray-600 cursor-not-allowed opacity-60'
        }`}
      >
        {isLoading ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Generating Plan...
          </>
        ) : (
          'Get Healthcare Plan'
        )}
      </button>

      {/* Helper Text */}
      <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-6">
        Takes 15-30 seconds to generate personalized recommendations
      </p>
    </form>
  );
};

export default InputForm;
