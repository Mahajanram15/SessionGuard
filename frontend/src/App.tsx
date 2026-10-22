import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardShell } from './pages/DashboardShell';
import { TelemetryDemoPage } from './pages/TelemetryDemoPage';
import { LearnSphereLandingPage } from './pages/learnsphere/LearnSphereLandingPage';
import { apiClient, createAppApiClient } from './services/api';
import { DashboardStats, HealthResponse } from './types';
import { BehavioralSDK, TelemetryStats } from '@behavioral-integrity/sdk';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'learnsphere' | 'sandbox' | 'overview'>('learnsphere');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Initialize Singleton SDK instance for the application
  const sdk = useMemo(() => {
    return new BehavioralSDK({
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
      batchIntervalMs: 2000,
      maxBatchSize: 40,
      sampleRateMouseHz: 30,
      debug: false,
    });
  }, []);

  const [sdkStats, setSdkStats] = useState<TelemetryStats>(() => sdk.getStats());

  const refreshSdkStats = useCallback(() => {
    setSdkStats(sdk.getStats());
  }, [sdk]);

  // Poll SDK stats periodically to reflect live background buffer flushes
  useEffect(() => {
    const timer = setInterval(() => {
      refreshSdkStats();
    }, 1000);
    return () => clearInterval(timer);
  }, [refreshSdkStats]);

  // Shared instrumented domain API client bound to active SDK session
  const appClient = useMemo(() => {
    return createAppApiClient({
      getSessionId: () => sdk.getSessionId(),
      onTelemetryEmitted: () => {
        refreshSdkStats();
      },
    });
  }, [sdk, refreshSdkStats]);

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [healthData, statsData] = await Promise.all([
          apiClient.getHealth().catch(() => ({
            status: 'online (foundation)',
            version: '0.1.0',
            timestamp: new Date().toISOString(),
            components: {
              database: 'ready',
              feature_engine: 'ready',
              ml_models: 'initialized',
              api_gateway: 'ready',
            },
          })),
          apiClient.getDashboardStats().catch(() => ({
            total_sessions: 1,
            active_sessions: 1,
            average_risk_score: 0.18,
            decision_distribution: {
              ALLOW: 1,
              CHALLENGE: 0,
              RATE_LIMIT: 0,
              BLOCK: 0,
            },
            recent_flagged_sessions: [],
          })),
        ]);

        setHealth(healthData);
        setStats(statsData);
      } catch (err) {
        console.error('Failed to load system state:', err);
      } finally {
        setLoading(false);
      }
    }

    loadInitialData();
  }, []);

  return (
    <div className={`min-h-screen flex flex-col font-sans ${activeTab === 'learnsphere' ? 'bg-[#ECEAF6]' : 'bg-background'}`}>
      <Navbar
        systemHealth={health?.status || 'initializing'}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isStreaming={sdkStats.isRunning}
      />

      {activeTab === 'learnsphere' ? (
        <div className="flex-1 w-full">
          <LearnSphereLandingPage
            appClient={appClient}
            sdk={sdk}
            stats={sdkStats}
            onRefreshStats={refreshSdkStats}
            onExploreCatalog={() => setActiveTab('learnsphere')}
            onNavigateToMatrix={() => setActiveTab('overview')}
          />
        </div>
      ) : (
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'sandbox' ? (
            <TelemetryDemoPage
              sdk={sdk}
              stats={sdkStats}
              onRefreshStats={refreshSdkStats}
            />
          ) : (
            <DashboardShell
              stats={stats}
              health={health}
              loading={loading}
              currentSessionId={sdkStats.sessionId}
            />
          )}
        </main>
      )}

      <footer className={`border-t py-6 text-center text-xs font-mono transition-colors ${
        activeTab === 'learnsphere'
          ? 'bg-[#ECEAF6] border-purple-200/60 text-slate-500'
          : 'bg-background border-border/60 text-slate-500'
      }`}>
        CrossTrace Behavioral Integrity Verification &bull; LearnSphere Demonstration &copy; 2026
      </footer>
    </div>
  );
};

export default App;

