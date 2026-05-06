import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  TrendingUp, 
  Target, 
  Calendar, 
  DollarSign, 
  ArrowRight, 
  ArrowLeft, 
  CheckCircle2, 
  Info,
  RefreshCw,
  Zap,
  BookOpen,
  Pencil,
  Save,
  Layout,
  ChevronRight,
  Download,
  FileText,
  Lightbulb
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell
} from 'recharts';
import { cn } from './lib/utils';
import { getActionPlan, InvestmentProfile } from './services/gemini';

type Step = 'welcome' | 'goal' | 'timeline' | 'consistency' | 'nextAction' | 'result';

export default function App() {
  const [step, setStep] = useState<Step>('welcome');
  const [profile, setProfile] = useState<InvestmentProfile & { userNextStep: string }>({
    goal: '',
    timeline: 10,
    monthlyContribution: 100,
    startingAmount: 0,
    userNextStep: '',
  });
  const [illustrativeRate, setIllustrativeRate] = useState(0.07);
  const [isEditingNextStep, setIsEditingNextStep] = useState(false);
  const [isEditingVision, setIsEditingVision] = useState(false);
  const [aiResponse, setAiResponse] = useState<{ 
    vision: string; 
    principle: string;
    perspective: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Animation variants
  const pageVariants = {
    initial: { opacity: 0, x: 20 },
    enter: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
  };

  const handleNext = () => {
    if (step === 'welcome') setStep('goal');
    else if (step === 'goal') setStep('timeline');
    else if (step === 'timeline') setStep('consistency');
    else if (step === 'consistency') setStep('nextAction');
    else if (step === 'nextAction') {
      setStep('result');
      generatePlan();
    }
  };

  const handleBack = () => {
    if (step === 'goal') setStep('welcome');
    else if (step === 'timeline') setStep('goal');
    else if (step === 'consistency') setStep('timeline');
    else if (step === 'nextAction') setStep('consistency');
    else if (step === 'result') setStep('nextAction');
  };

  const generatePlan = async () => {
    setIsLoading(true);
    try {
      const result = await getActionPlan(profile);
      setAiResponse(result);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetAll = () => {
    setProfile({
      goal: '',
      timeline: 10,
      monthlyContribution: 100,
      startingAmount: 0,
      userNextStep: '',
    });
    setAiResponse(null);
    setStep('welcome');
  };

  // Compounding logic for visualization - using a purely illustrative growth rate
  const chartData = useMemo(() => {
    const data = [];
    let balance = profile.startingAmount;
    
    const steps = 5;
    const interval = Math.max(1, Math.floor(profile.timeline / steps));
    
    for (let year = 0; year <= profile.timeline; year++) {
      if (year === 0 || year === profile.timeline || year % interval === 0) {
        data.push({
          year: year === 0 ? 'Today' : `Year ${year}`,
          balance: Math.round(balance),
          isFinal: year === profile.timeline,
        });
      }
      balance = (balance + (profile.monthlyContribution * 12)) * (1 + illustrativeRate);
    }
    
    return data;
  }, [profile, illustrativeRate]);

  // Full calculation for stats
  const finalStats = useMemo(() => {
    let balance = profile.startingAmount;
    for (let year = 1; year <= profile.timeline; year++) {
      balance = (balance + (profile.monthlyContribution * 12)) * (1 + illustrativeRate);
    }
    const invested = profile.startingAmount + (profile.monthlyContribution * 12 * profile.timeline);
    return {
      balance: Math.round(balance),
      invested: invested,
      gain: Math.round(balance - invested)
    };
  }, [profile, illustrativeRate]);

  const finalBalance = finalStats.balance;
  const totalGain = finalStats.gain;

  return (
    <main className="min-h-screen bg-[#f5f5f5] text-slate-900 font-sans p-2 md:p-4 flex items-center justify-center">
      <div className={cn(
        "w-full bg-white rounded-[32px] shadow-sm border border-slate-100 overflow-hidden flex flex-col transition-all duration-500",
        step === 'result' ? "max-w-5xl" : "max-w-2xl"
      )}>
        
        {/* Progress Bar */}
        {step !== 'welcome' && step !== 'result' && (
          <div 
            className="flex h-1 bg-slate-100"
            role="progressbar"
            aria-label="Investment roadmap progress"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={
              step === 'goal' ? 20 : 
              step === 'timeline' ? 40 : 
              step === 'consistency' ? 60 : 
              step === 'nextAction' ? 80 : 100
            }
          >
            <motion.div 
              className="bg-slate-900 h-full"
              initial={{ width: 0 }}
              animate={{ 
                width: step === 'goal' ? '20%' : 
                       step === 'timeline' ? '40%' : 
                       step === 'consistency' ? '60%' : 
                       step === 'nextAction' ? '80%' : '100%' 
              }}
            />
          </div>
        )}

        <div className={cn(
          "flex-1 flex flex-col",
          step === 'result' ? "p-6 md:p-10" : "p-8 md:p-12"
        )}>
          <AnimatePresence mode="wait">
            {step === 'welcome' && (
              <motion.div 
                key="welcome"
                variants={pageVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="flex flex-col items-center text-center space-y-6 my-auto"
              >
                <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center text-white mb-4">
                  <TrendingUp size={32} />
                </div>
                <h1 className="text-4xl font-semibold tracking-tight">Take an important step.</h1>
                <p className="text-slate-500 text-lg max-w-md leading-relaxed">
                  Deciding to focus on your long-term goals is a big step. Let's map out a grounded plan to help you move forward with clarity and confidence.
                </p>
                <button 
                  onClick={handleNext}
                  className="mt-4 px-8 py-4 bg-slate-900 text-white rounded-full font-medium flex items-center gap-2 hover:bg-slate-800 transition-colors cursor-pointer group"
                  aria-label="Start building your investment plan"
                >
                  Start my plan
                  <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" aria-hidden="true" />
                </button>
              </motion.div>
            )}

            {step === 'goal' && (
              <motion.div 
                key="goal"
                variants={pageVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="space-y-8"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    <Target size={14} />
                    Step 1: Your Goal
                  </div>
                  <h2 className="text-3xl font-semibold">What are you working toward?</h2>
                  <p className="text-slate-500 text-sm leading-relaxed">
                    Setting a clear name will make it easier to stay consistent. <span className="text-slate-400">Select a common milestone or define your own unique vision.</span>
                  </p>
                </div>

                <div className="space-y-6">
                  <div className="relative group">
                    <label htmlFor="goal-input" className="sr-only">Investment Goal</label>
                    <input 
                      id="goal-input"
                      type="text"
                      value={profile.goal}
                      onChange={(e) => setProfile({...profile, goal: e.target.value})}
                      placeholder="e.g. A first home, travel foundation..."
                      className="w-full text-2xl py-4 border-b-2 border-slate-100 focus:border-indigo-500 outline-none transition-all placeholder:text-slate-200"
                      autoFocus
                    />
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      { term: 'Short-term', range: '1-5 years', icon: <TrendingUp size={14} />, goals: ['Emergency Fund', 'New Equipment', 'Summer Travel'], color: 'text-indigo-400' },
                      { term: 'Medium-term', range: '6-12 years', icon: <Calendar size={14} />, goals: ['Home Deposit', 'Wedding Fund', 'Vehicle Upgrade'], color: 'text-amber-500' },
                      { term: 'Long-term', range: '13+ years', icon: <Target size={14} />, goals: ['Retirement Fund', 'Education Costs', 'New Business Fund'], color: 'text-emerald-500' }
                    ].map(group => (
                      <div key={group.term} className="bg-slate-50/50 border border-slate-100 rounded-[28px] p-5 space-y-4 transition-all hover:bg-white hover:shadow-xl hover:shadow-slate-200/50 group/card">
                        <div className="space-y-1">
                          <div className={cn("flex items-center gap-1.5 font-bold uppercase tracking-[0.15em] text-[10px]", group.color)}>
                            {group.icon}
                            {group.term}
                          </div>
                          <p className="text-[10px] text-slate-400 font-medium">{group.range}</p>
                        </div>
                        <div className="flex flex-col gap-2">
                          {group.goals.map(g => (
                            <button 
                              key={g}
                              onClick={() => {
                                setProfile({...profile, goal: g});
                                if (group.term === 'Short-term') setProfile(p => ({...p, goal: g, timeline: 3}));
                                if (group.term === 'Medium-term') setProfile(p => ({...p, goal: g, timeline: 7}));
                                if (group.term === 'Long-term') setProfile(p => ({...p, goal: g, timeline: 20}));
                              }}
                              className={cn(
                                "text-left px-3.5 py-2.5 rounded-xl text-[11px] font-semibold transition-all flex items-center justify-between group/btn",
                                profile.goal === g 
                                  ? "bg-slate-900 text-white shadow-lg shadow-slate-200" 
                                  : "bg-white/80 text-slate-600 border border-slate-100/80 hover:border-slate-300 hover:text-slate-900"
                              )}
                            >
                              {g}
                              <ChevronRight size={12} className={cn(
                                "transition-transform group-hover/btn:translate-x-0.5",
                                profile.goal === g ? "opacity-100" : "opacity-0"
                              )} />
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  <p className="text-[10px] text-slate-400 text-center font-medium py-2">
                    Click a goal above to get started—you can refine your vision anytime.
                  </p>
                </div>

                <div className="pt-8 flex justify-between">
                  <button 
                    onClick={handleBack} 
                    className="text-slate-400 hover:text-slate-900 flex items-center gap-1 font-medium cursor-pointer"
                    aria-label="Go back to previous step"
                  >
                    <ArrowLeft size={18} aria-hidden="true" /> Back
                  </button>
                  <button 
                    disabled={!profile.goal}
                    onClick={handleNext}
                    className="px-6 py-3 bg-slate-900 text-white rounded-full font-medium disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer"
                    aria-label="Proceed to next step"
                  >
                    Next <ArrowRight size={18} aria-hidden="true" />
                  </button>
                </div>
              </motion.div>
            )}

            {step === 'timeline' && (
              <motion.div 
                key="timeline"
                variants={pageVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="space-y-8"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    <Calendar size={14} />
                    Step 2: Timeline
                  </div>
                  <h2 className="text-3xl font-semibold">How far away is this goal?</h2>
                  <p className="text-slate-500 text-sm leading-relaxed">Choose a timeframe that feels right. This helps tailor your plan to the length of your journey.</p>
                </div>

                <div className="space-y-10">
                  <div className="flex items-center justify-between">
                    <div className="flex items-baseline gap-3">
                      <span className="text-6xl font-bold font-display text-indigo-600" aria-live="polite">
                        {profile.timeline}
                      </span>
                      <div className="flex flex-col">
                        <span className="text-2xl text-slate-400 font-medium tracking-tight">years</span>
                      </div>
                    </div>
                    <div className="bg-slate-50 border border-slate-100 px-4 py-2 rounded-[20px] text-right">
                       <span className="block text-[8px] font-bold uppercase tracking-[0.2em] text-slate-400 mb-1">Target Year</span>
                       <span className="text-xl font-bold text-slate-900 font-display">
                        {new Date().getFullYear() + profile.timeline}
                       </span>
                    </div>
                  </div>
                  
                  <div className="relative pt-2">
                    <label htmlFor="timeline-range" className="sr-only">Investment Timeline in years</label>
                    <input 
                      id="timeline-range"
                      type="range"
                      min="1"
                      max="40"
                      value={profile.timeline}
                      onChange={(e) => setProfile({...profile, timeline: parseInt(e.target.value)})}
                      className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                    />
                    <div className="flex justify-between px-1 mt-4 text-[9px] font-bold text-slate-300 uppercase tracking-widest" aria-hidden="true">
                      <span>1 Year</span>
                      <span>10Y</span>
                      <span>20Y</span>
                      <span>30Y</span>
                      <span>40Y</span>
                    </div>
                  </div>
                  
                  {/* Archetype Indicator */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white border border-slate-100 rounded-[32px] p-6 shadow-sm shadow-slate-100/50 space-y-3">
                      <div className="flex items-center justify-between mb-3">
                        <div className="w-10 h-10 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-500">
                          <TrendingUp size={20} />
                        </div>
                        <span className={cn(
                          "text-[8px] font-bold uppercase tracking-[0.2em] px-2 py-1 rounded-full",
                          profile.timeline <= 5 ? "bg-indigo-50 text-indigo-400" : 
                          profile.timeline <= 12 ? "bg-amber-50 text-amber-500" : "bg-emerald-50 text-emerald-500"
                        )}>
                          {profile.timeline <= 5 ? 'Short-term (1-5y)' : profile.timeline <= 12 ? 'Medium-term (6-12y)' : 'Long-term (13y+)'}
                        </span>
                      </div>
                      <div className="space-y-1">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">
                          {profile.timeline <= 5 ? "The Near Goal" : profile.timeline <= 12 ? "The Growing Goal" : "The Future Vision"}
                        </h3>
                        <p className="text-xs text-slate-500 leading-relaxed font-medium">
                          {profile.timeline <= 5 
                            ? "When your goal is close, keeping your money safe and easy to reach is a smart move. You want to avoid big risks because you'll need this money soon."
                            : profile.timeline <= 12
                            ? "With several years ahead, you can aim for more growth. You have enough time to stay steady through small dips while your balance builds up."
                            : "You have the 'Time Advantage.' This long window lets you ignore daily changes because you're focused on letting your money work for you over decades."
                          }
                        </p>
                      </div>
                    </div>

                    <div className="bg-slate-900 text-white rounded-[32px] p-6 shadow-2xl shadow-slate-400/20 space-y-3 relative overflow-hidden">
                      <div className="absolute -right-4 -bottom-4 text-white/5 rotate-12">
                        <Zap size={100} />
                      </div>
                      <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center text-indigo-300">
                        <BookOpen size={20} />
                      </div>
                      <div className="space-y-1 relative z-10">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-300">Smart Approach</h3>
                        <p className="text-xs text-slate-400 leading-relaxed font-medium">
                          {profile.timeline <= 5 
                            ? "Preservation & Accessibility: In this short window, focus on avoiding big losses. Making sure your money is available when you need it is the smartest move right now."
                            : profile.timeline <= 12
                            ? "Balance & Growth: With more time, you can afford to aim for steady gains. You're building a bridge between today's efforts and tomorrow's results."
                            : "The Power of Patience: Think of this like planting a garden. The earlier you start and the longer you wait, the bigger your results can become."
                          }
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 flex justify-between">
                  <button 
                    onClick={handleBack} 
                    className="text-slate-400 hover:text-slate-900 flex items-center gap-1 font-medium cursor-pointer"
                    aria-label="Go back"
                  >
                    <ArrowLeft size={18} aria-hidden="true" /> Back
                  </button>
                  <button 
                    onClick={handleNext}
                    className="px-8 py-3 bg-slate-900 text-white rounded-full font-semibold flex items-center gap-2 shadow-lg shadow-slate-200 hover:shadow-xl hover:-translate-y-0.5 transition-all cursor-pointer"
                    aria-label="Proceed"
                  >
                    Next <ArrowRight size={18} aria-hidden="true" />
                  </button>
                </div>
              </motion.div>
            )}

            {step === 'consistency' && (
              <motion.div 
                key="consistency"
                variants={pageVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="space-y-8"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    <DollarSign size={14} />
                    Step 3: Consistency
                  </div>
                  <h2 className="text-3xl font-semibold">What can you contribute monthly?</h2>
                </div>

                <div className="space-y-6">
                  <div className="relative">
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 text-4xl text-slate-200 font-bold" aria-hidden="true">$</span>
                    <label htmlFor="contribution-input" className="sr-only">Monthly Contribution amount</label>
                    <input 
                      id="contribution-input"
                      type="number"
                      value={profile.monthlyContribution}
                      onChange={(e) => setProfile({...profile, monthlyContribution: parseInt(e.target.value) || 0})}
                      className="w-full text-6xl font-bold py-4 pl-8 border-none outline-none focus:ring-0"
                      autoFocus
                    />
                  </div>
                  <p className="text-slate-400 text-sm italic">
                    <Info size={14} className="inline mr-1" aria-hidden="true" /> Consistency is more important than amount. Any amount helps build the habit.
                  </p>
                </div>

                <div className="pt-8 flex justify-between">
                  <button 
                    onClick={handleBack} 
                    className="text-slate-400 hover:text-slate-900 flex items-center gap-1 font-medium cursor-pointer"
                    aria-label="Go back to previous step"
                  >
                    <ArrowLeft size={18} aria-hidden="true" /> Back
                  </button>
                  <button 
                    onClick={handleNext}
                    className="px-6 py-3 bg-slate-900 text-white rounded-full font-medium flex items-center gap-2 cursor-pointer"
                    aria-label="Proceed to next step"
                  >
                    Next <ArrowRight size={18} aria-hidden="true" />
                  </button>
                </div>
              </motion.div>
            )}

            {step === 'nextAction' && (
              <motion.div 
                key="nextAction"
                variants={pageVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="space-y-6"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    <CheckCircle2 size={14} />
                    Step 4: Your First Move
                  </div>
                  <h2 className="text-3xl font-semibold">What's your first move?</h2>
                  <p className="text-slate-600 leading-relaxed text-sm">
                    A plan is only as strong as its first day. Choose a pathway that fits how you learn best or write yours below.
                  </p>
                </div>

                {/* Path Choice Redesign */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pb-2">
                  {[
                    { id: 'research', title: 'The Researcher', group: 'Learning', action: 'Spend 15 minutes learning a new concept to help clarify your plan.', icon: <BookOpen size={18} /> },
                    { id: 'tool', title: 'The Architect', group: 'Plan', action: 'Draft a simple list of your monthly needs vs. wants.', icon: <Layout size={18} /> },
                    { id: 'habit', title: 'The Builder', group: 'Habit', action: 'Set a weekly reminder to check your progress balance.', icon: <Zap size={18} /> },
                    { id: 'social', title: 'The Connector', group: 'Support', action: 'Ask someone you trust about their first financial win.', icon: <RefreshCw size={18} /> },
                  ].map((tip) => (
                    <button
                      key={tip.id}
                      onClick={() => setProfile({ ...profile, userNextStep: tip.action })}
                      className={cn(
                        "flex flex-col p-4 rounded-[24px] border-2 transition-all duration-300 group cursor-pointer text-left",
                        profile.userNextStep === tip.action 
                          ? "bg-indigo-50 border-indigo-500 shadow-lg shadow-indigo-100/50" 
                          : "bg-white border-slate-100 hover:border-slate-200 hover:bg-slate-50/50"
                      )}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className={cn(
                          "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
                          profile.userNextStep === tip.action ? "bg-indigo-500 text-white" : "bg-slate-50 text-slate-400 group-hover:text-slate-500"
                        )}>
                          {tip.icon}
                        </div>
                        <div className={cn(
                          "transition-opacity",
                          profile.userNextStep === tip.action ? "opacity-100" : "opacity-0"
                        )}>
                          <CheckCircle2 size={16} className="text-indigo-500" />
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5 mb-1">
                          <span className={cn(
                            "text-[8px] font-bold uppercase tracking-widest",
                            profile.userNextStep === tip.action ? "text-indigo-600" : "text-slate-400"
                          )}>
                            {tip.title}
                          </span>
                          <span className="w-1 h-1 rounded-full bg-slate-200" />
                          <span className="text-[8px] font-bold text-slate-300 uppercase tracking-widest">{tip.group}</span>
                        </div>
                        <p className={cn(
                          "text-[13px] leading-snug font-medium",
                          profile.userNextStep === tip.action ? "text-indigo-950" : "text-slate-600"
                        )}>
                          {tip.action}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center px-1">
                    <label htmlFor="next-step-input" className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                      Or refine your specific move:
                    </label>
                  </div>
                  <div className="relative group">
                    <textarea 
                      id="next-step-input"
                      value={profile.userNextStep}
                      onChange={(e) => setProfile({...profile, userNextStep: e.target.value})}
                      placeholder="e.g., I'll open a dedicated savings pot tonight..."
                      className="w-full min-h-[70px] text-lg font-medium p-4 rounded-2xl bg-slate-50 border-2 border-transparent focus:border-indigo-500 focus:bg-white transition-all outline-none resize-none placeholder:text-slate-300"
                      aria-label="Your custom first step"
                    />
                    <div className="absolute bottom-4 right-4 text-slate-200 pointer-events-none group-focus-within:text-indigo-400 transition-colors">
                      <Zap size={18} />
                    </div>
                  </div>
                </div>

                <div className="pt-4 flex justify-between">
                  <button 
                    onClick={handleBack} 
                    className="text-slate-400 hover:text-slate-900 flex items-center gap-1 font-medium cursor-pointer"
                    aria-label="Go back"
                  >
                    <ArrowLeft size={18} aria-hidden="true" /> Back
                  </button>
                  <button 
                    disabled={!profile.userNextStep.trim()}
                    onClick={handleNext}
                    className={cn(
                      "px-8 py-3 rounded-full font-semibold flex items-center gap-2 transition-all cursor-pointer",
                      profile.userNextStep.trim() 
                        ? "bg-slate-900 text-white shadow-lg shadow-slate-200 hover:shadow-xl hover:-translate-y-0.5" 
                        : "bg-slate-100 text-slate-300 cursor-not-allowed"
                    )}
                    aria-label="Finalize and see your roadmap"
                  >
                    Finalize Roadmap <ArrowRight size={18} aria-hidden="true" />
                  </button>
                </div>
              </motion.div>
            )}

            {step === 'result' && (
              <motion.div 
                key="result"
                variants={pageVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="space-y-4 w-full"
              >
                {/* Header: The Vision */}
                <header className="flex items-center justify-between gap-4 pb-1">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <div className="text-indigo-500 font-bold uppercase text-[9px] tracking-[0.2em]">
                        Goal Destination
                      </div>
                      <span className={cn(
                        "px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-widest",
                        profile.timeline <= 5 ? "bg-indigo-50 text-indigo-500" : 
                        profile.timeline <= 10 ? "bg-amber-50 text-amber-500" : "bg-emerald-50 text-emerald-500"
                      )}>
                        {profile.timeline <= 5 ? 'Short-term' : profile.timeline <= 10 ? 'Medium-term' : 'Long-term'}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <h2 className="text-3xl md:text-4xl font-display font-bold tracking-tight text-slate-900 leading-none flex items-center gap-4 transition-colors">
                        {isLoading ? (
                          <span className="animate-pulse bg-slate-100 rounded w-64 h-10 block"></span>
                        ) : (
                          aiResponse?.vision
                        )}
                      </h2>
                    </div>
                  </div>
                  <button 
                    onClick={resetAll}
                    className="flex items-center gap-2 px-3 py-1.5 text-[9px] font-bold uppercase tracking-widest text-slate-400 hover:text-slate-900 border border-slate-100 rounded-full transition-colors shrink-0"
                    aria-label="Restart from the beginning"
                  >
                    <RefreshCw size={12} aria-hidden="true" />
                    Reset Data
                  </button>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
                  {/* Left: The Laboratory (Chart + Explorer) */}
                  <div className="md:col-span-8 space-y-4">
                    <section 
                      className="bg-white border-2 border-slate-900/5 rounded-[32px] p-5 md:p-6 space-y-6 shadow-2xl shadow-slate-200/50 relative overflow-hidden"
                      aria-labelledby="simulation-title"
                    >
                      <div className="flex justify-between items-center relative z-10">
                        <h3 id="simulation-title" className="text-[10px] font-display font-bold uppercase tracking-widest text-slate-400">
                          Growth Simulator
                        </h3>
                        <div className="flex items-center gap-3 text-[9px] font-bold text-slate-400">
                          <div className="flex items-center gap-1.5">
                            <div className="w-2 h-2 rounded-full bg-slate-100" />
                            Progress
                          </div>
                          <div className="flex items-center gap-1.5">
                            <div className="w-2 h-2 rounded-full bg-slate-900" />
                            Destination
                          </div>
                        </div>
                      </div>

                      <div className="h-[200px] w-full" role="img" aria-label="Hypothetical balance over time">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={chartData} margin={{ top: 10, right: 0, left: -25, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                            <XAxis 
                              dataKey="year" 
                              axisLine={false} 
                              tickLine={false}
                              tick={{ fontSize: 9, fill: '#94a3b8', fontWeight: 600 }}
                            />
                            <YAxis hide />
                            <Tooltip 
                              cursor={{ fill: 'rgba(15, 23, 42, 0.02)' }}
                              contentStyle={{ 
                                borderRadius: '12px', 
                                border: 'none', 
                                boxShadow: '0 20px 50px -12px rgb(0 0 0 / 0.15)',
                                fontSize: '10px',
                                padding: '12px'
                              }}
                              formatter={(value: number) => [`$${value.toLocaleString()}`, 'Hypothetical']}
                            />
                            <Bar 
                              dataKey="balance" 
                              radius={[8, 8, 0, 0]}
                              className="transition-all duration-300"
                            >
                              {chartData.map((entry, index) => (
                                <Cell 
                                  key={`cell-${index}`} 
                                  fill={entry.isFinal ? '#0f172a' : '#e2e8f0'} 
                                />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>

                      <div className="pt-4 border-t border-slate-50 space-y-3">
                        <div className="flex justify-between items-center group/rate relative">
                          <div className="flex items-center gap-2">
                            <label htmlFor="rate-slider" className="text-[9px] font-bold uppercase tracking-[0.15em] text-indigo-500">
                              Illustrative Growth Model
                            </label>
                            <div className="relative group/tooltip">
                              <Info size={12} className="text-slate-300 hover:text-indigo-400 cursor-help" />
                              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-3 bg-slate-900 text-white text-[10px] leading-relaxed rounded-xl opacity-0 group-hover/tooltip:opacity-100 transition-opacity pointer-events-none shadow-xl z-20">
                                <div className="font-bold text-indigo-300 mb-1">The Snowball Effect</div>
                                This illustrates how interest starts earning its own interest, accelerating progress over time.
                                <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-slate-900" />
                              </div>
                            </div>
                          </div>
                          <span className="font-display font-bold text-slate-900 bg-slate-50 px-2 py-0.5 rounded-lg border border-slate-100 text-sm" aria-live="polite">
                            {Math.round(illustrativeRate * 100)}%
                          </span>
                        </div>
                        <input 
                          id="rate-slider"
                          type="range" 
                          min="0" 
                          max="0.12" 
                          step="0.01" 
                          value={illustrativeRate}
                          onChange={(e) => setIllustrativeRate(parseFloat(e.target.value))}
                          className="w-full h-1.5 bg-slate-100 rounded-full appearance-none cursor-pointer accent-indigo-500 hover:accent-indigo-600 transition-all"
                        />
                        <p className="text-[9px] text-slate-400 leading-tight max-w-lg">
                          This is for exploration only. Market performance is not guaranteed and does not predict future results.
                        </p>
                      </div>
                    </section>
                  </div>

                  {/* Right: The Variables & Insight */}
                  <div className="md:col-span-4 space-y-4">
                    {/* Growth Insight Block */}
                    <section 
                      className="bg-white border border-emerald-100 rounded-[28px] p-4 space-y-3 shadow-sm shadow-emerald-50 relative overflow-hidden"
                      aria-labelledby="growth-title"
                    >
                      <div className="flex items-center justify-between gap-3 relative z-10">
                        <div className="flex items-center gap-2.5">
                          <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-500">
                            <TrendingUp size={18} />
                          </div>
                          <div className="min-w-0">
                            <h3 id="growth-title" className="text-[9px] font-bold uppercase tracking-[0.2em] text-emerald-500/80">
                              Growth Lesson
                            </h3>
                          </div>
                        </div>
                        {!isLoading && aiResponse?.principle && (
                          <div className="px-2.5 py-1 bg-emerald-50 text-emerald-600 rounded-lg text-[8px] font-bold uppercase tracking-widest border border-emerald-100 shrink-0">
                            {aiResponse.principle}
                          </div>
                        )}
                      </div>

                      <div className="relative z-10">
                        <div className="absolute -left-1 top-0 bottom-0 w-0.5 bg-emerald-100 rounded-full" />
                        <div className="pl-3">
                          <p className="text-slate-600 text-xs md:text-sm leading-relaxed font-medium">
                            {isLoading ? (
                              <span className="space-y-1.5 block animate-pulse">
                                <span className="h-2 bg-slate-50 rounded-full w-full block"></span>
                                <span className="h-2 bg-slate-50 rounded-full w-5/6 block"></span>
                                <span className="h-2 bg-slate-50 rounded-full w-4/6 block"></span>
                              </span>
                            ) : (
                              aiResponse?.perspective
                            )}
                          </p>
                        </div>
                      </div>
                    </section>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-white border border-slate-100 p-4 rounded-2xl shadow-sm col-span-2">
                        <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Total Outcome</div>
                        <div className="text-xl font-display font-bold text-slate-900" aria-live="polite">
                          ${finalBalance.toLocaleString()}
                        </div>
                      </div>
                      
                      <div className="bg-white border border-slate-100 p-4 rounded-2xl shadow-sm">
                        <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-0.5 whitespace-nowrap">Completion</div>
                        <div className="text-xl font-display font-bold text-slate-900 leading-none">
                          {new Date().getFullYear() + profile.timeline}
                        </div>
                      </div>

                      <div className="bg-white border border-slate-100 p-4 rounded-2xl shadow-sm">
                        <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-0.5 whitespace-nowrap">Monthly</div>
                        <div className="text-xl font-display font-bold text-slate-900">
                          ${profile.monthlyContribution}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                {/* Footer: The Action */}
                <footer className="pt-1">
                  <section 
                    className="bg-slate-900 text-white p-6 rounded-[32px] shadow-2xl shadow-slate-400/20 group relative overflow-hidden"
                    aria-labelledby="action-title"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
                      <div className="space-y-1.5 flex-1 pr-8">
                        <div className="flex items-center gap-2 text-slate-500 font-bold uppercase text-[9px] tracking-[0.2em]">
                          <Zap size={12} className={cn("transition-colors", isEditingNextStep ? "text-indigo-400" : "text-slate-400")} aria-hidden="true" />
                          <span id="action-title">The First Step</span>
                          {isEditingNextStep && (
                            <span className="text-indigo-400 animate-pulse font-bold tracking-widest text-[8px] bg-indigo-500/10 px-1.5 py-0.5 rounded">Editing</span>
                          )}
                        </div>
                        {isEditingNextStep ? (
                          <div className="space-y-3">
                            <textarea
                              value={profile.userNextStep}
                              onChange={(e) => setProfile({ ...profile, userNextStep: e.target.value })}
                              className="w-full bg-slate-800/50 text-xl font-display font-medium leading-tight p-3 rounded-xl border border-slate-700 focus:border-indigo-500 outline-none resize-none transition-all"
                              rows={2}
                              autoFocus
                            />
                            <button 
                              onClick={() => setIsEditingNextStep(false)}
                              className="px-5 py-2.5 bg-indigo-500 text-white text-[10px] font-bold uppercase tracking-widest rounded-xl shadow-lg shadow-indigo-500/20 hover:bg-indigo-600 active:scale-95 transition-all flex items-center gap-2 w-fit group/save"
                            >
                               <Save size={14} className="group-hover/save:scale-110 transition-transform" />
                               Update Goal
                            </button>
                          </div>
                        ) : (
                          <p 
                            className="text-xl font-display font-medium leading-tight group-hover:text-indigo-200 transition-colors cursor-pointer"
                            onClick={() => setIsEditingNextStep(true)}
                          >
                            {profile.userNextStep}
                          </p>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-3">
                        {!isEditingNextStep && (
                          <button 
                            onClick={() => setIsEditingNextStep(true)}
                            className="w-10 h-10 rounded-full border border-white/10 text-slate-500 hover:border-white/20 hover:text-white flex items-center justify-center transition-all duration-300"
                            aria-label="Edit first step"
                          >
                            <Pencil size={16} />
                          </button>
                        )}
                      </div>
                    </div>
                  </section>
                </footer>

                <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-4 print:hidden">
                  <div className="flex items-center gap-2">
                     <button 
                        onClick={() => window.print()}
                          className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 text-slate-600 rounded-2xl text-[10px] font-bold uppercase tracking-widest hover:border-indigo-200 hover:text-indigo-500 transition-all shadow-sm"
                        >
                          <FileText size={14} />
                          Export PDF
                        </button>
                        <button 
                          onClick={() => {
                            const blob = new Blob([
                              `MY FINANCIAL JOURNEY PLAN\n\n` +
                              `GOAL: ${profile.goal}\n` +
                              `WINDOW: ${profile.timeline} years\n` +
                              `MONTHLY HABIT: $${profile.monthlyContribution}\n` +
                              `STARTING WITH: $${profile.startingAmount}\n` +
                              `FIRST MOVE: ${profile.userNextStep}\n\n` +
                              `ESTIMATED OUTCOME: $${finalBalance.toLocaleString()}\n\n` +
                              `Created with Clarity Planner`
                            ], { type: 'text/plain' });
                            const url = URL.createObjectURL(blob);
                            const link = document.createElement('a');
                            link.href = url;
                            link.download = 'my-clarity-plan.txt';
                            link.click();
                          }}
                          className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 text-slate-600 rounded-2xl text-[10px] font-bold uppercase tracking-widest hover:border-indigo-200 hover:text-indigo-500 transition-all shadow-sm"
                        >
                          <Download size={14} />
                          Save Plan
                        </button>
                    </div>
                  </div>

                <p className="text-center text-[8px] text-slate-400 font-medium px-12 pt-2 leading-relaxed uppercase tracking-wider max-w-2xl mx-auto opacity-50">
                  Illustrative only. No guaranteed returns. Not financial advice.
                </p>
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </div>
    </main>
  );
}
