import React from 'react';
import Layout from './components/Layout';
import AnimatedBackground from './components/AnimatedBackground';
import HeroSentinel from './components/HeroSentinel';
import { ProblemEgypt, SentinelSolution } from './components/ProblemSolution';
import HighwayPipeline from './components/HighwayPipeline';
import LiveHighwaySimulation from './components/LiveHighwaySimulation';
import { SentinelMetrics, BusinessModelCanvas } from './components/MetricsBusiness';
import { EgyptImpact, RoadmapTodo } from './components/ImpactRoadmap';

function App() {
  return (
    <Layout>
      <AnimatedBackground />
      <HeroSentinel />
      <ProblemEgypt />
      <SentinelSolution />
      <HighwayPipeline />
      <LiveHighwaySimulation />
      <SentinelMetrics />
      <BusinessModelCanvas />
      <EgyptImpact />
      <RoadmapTodo />
    </Layout>
  );
}

export default App;
