import AnimatedBackground from './components/AnimatedBackground';
import HeroSentinel from './components/HeroSentinel';
import HighwayPipeline from './components/HighwayPipeline';
import HighwayRiskEngineSection from './components/HighwayRiskEngineSection';
import { EgyptImpact, HackathonReadiness, RoadmapTodo } from './components/ImpactRoadmap';
import Layout from './components/Layout';
import LiveHighwaySimulation from './components/LiveHighwaySimulation';
import { BusinessModelCanvas, SentinelMetrics } from './components/MetricsBusiness';
import PitchDeckExport from './components/PitchDeckExport';
import { ProblemEgypt, SentinelSolution } from './components/ProblemSolution';

function App() {
  if (window.location.pathname === '/pitch') {
    return <PitchDeckExport />;
  }

  return (
    <Layout>
      <AnimatedBackground />
      <HeroSentinel />
      <ProblemEgypt />
      <SentinelSolution />
      <HighwayPipeline />
      <LiveHighwaySimulation />
      <HighwayRiskEngineSection />
      <SentinelMetrics />
      <BusinessModelCanvas />
      <EgyptImpact />
      <HackathonReadiness />
      <RoadmapTodo />
    </Layout>
  );
}

export default App;
