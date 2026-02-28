import React from 'react';
import { PowerOff, Zap, Leaf, Droplet, ThumbsUp, MessageSquare, Share2, ExternalLink, Reply, Heart } from 'lucide-react';

export function CommunityFeed() {
    return (
        <div className="bg-black/60 backdrop-blur-2xl border-white/10 rounded-2xl flex flex-col h-full overflow-hidden">
            <div className="p-6 border-b border-white/10 flex justify-between items-center bg-black/20">
                <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">Community Feed</h2>
                    <p className="text-sm text-slate-400">Local utility news & community tips</p>
                </div>
                <button className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 transition-colors">
                    <span className="material-symbols-outlined">filter_list</span>
                </button>
            </div>

            <div className="flex-grow overflow-y-auto p-6 space-y-6">
                {/* Feed Item 1 */}
                <div className="border-b border-white/10 pb-6 last:border-0 last:pb-0">
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-orange-500/20 flex items-center justify-center text-orange-400 flex-shrink-0 shadow-inner">
                            <PowerOff size={24} />
                        </div>
                        <div className="flex-grow">
                            <div className="flex justify-between items-start mb-1">
                                <h4 className="font-bold text-white">Scheduled Power Cut: Ernakulam North</h4>
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-red-500/20 text-red-400 uppercase tracking-widest border border-red-500/30">Alert</span>
                            </div>
                            <p className="text-sm text-slate-400 leading-relaxed">Maintenance work planned for tomorrow from 9 AM to 2 PM. Charge your devices in advance!</p>
                            <div className="flex items-center gap-4 mt-3">
                                <button className="text-xs font-bold text-primary hover:text-orange-400 flex items-center gap-1.5 transition-colors">
                                    <ThumbsUp size={14} /> 24 Thanked
                                </button>
                                <button className="text-xs font-bold text-slate-500 hover:text-slate-300 flex items-center gap-1.5 transition-colors">
                                    <MessageSquare size={14} /> 8 Comments
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Feed Item 2 */}
                <div className="border-b border-white/10 pb-6 last:border-0 last:pb-0">
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-green-500/20 flex items-center justify-center text-green-400 flex-shrink-0 shadow-inner">
                            <Leaf size={24} />
                        </div>
                        <div className="flex-grow">
                            <div className="flex justify-between items-start mb-1">
                                <h4 className="font-bold text-white">Solar Subsidy Tip</h4>
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-green-500/20 text-green-400 uppercase tracking-widest border border-green-500/30">Community Tip</span>
                            </div>
                            <p className="text-sm text-slate-400 leading-relaxed">"I just applied for the ANERT solar subsidy through K-Smart. The process is much faster now if you have your latest bill ready." - <span className="font-bold text-slate-300">Meera R.</span></p>
                            <div className="flex items-center gap-4 mt-3">
                                <button className="text-xs font-bold text-primary hover:text-orange-400 flex items-center gap-1.5 transition-colors">
                                    <ThumbsUp size={14} /> 56 Thanked
                                </button>
                                <button className="text-xs font-bold text-slate-500 hover:text-slate-300 flex items-center gap-1.5 transition-colors">
                                    <Share2 size={14} /> Share
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Feed Item 3 */}
                <div className="border-b border-white/10 pb-6 last:border-0 last:pb-0">
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 flex items-center justify-center text-accent-cyan flex-shrink-0 shadow-inner">
                            <Droplet size={24} />
                        </div>
                        <div className="flex-grow">
                            <div className="flex justify-between items-start mb-1">
                                <h4 className="font-bold text-white">New Water Connection Portal</h4>
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-cyan-500/20 text-accent-cyan uppercase tracking-widest border border-cyan-500/30">Utility News</span>
                            </div>
                            <p className="text-sm text-slate-400 leading-relaxed">KWA has launched a revamped portal for new domestic connections. Track applications in real-time.</p>
                            <div className="flex items-center gap-4 mt-3">
                                <button className="text-xs font-bold text-primary hover:text-orange-400 flex items-center gap-1.5 transition-colors">
                                    <ThumbsUp size={14} /> 12 Thanked
                                </button>
                                <button className="text-xs font-bold text-slate-500 hover:text-slate-300 flex items-center gap-1.5 transition-colors">
                                    <ExternalLink size={14} /> Read More
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export function YourImpact() {
    return (
        <div className="bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl p-6 relative overflow-hidden group">
            <div className="absolute -right-10 -top-10 w-32 h-32 bg-accent-cyan/10 rounded-full filter blur-2xl group-hover:bg-accent-cyan/20 transition-colors pointer-events-none"></div>

            <h3 className="font-bold text-white mb-4 tracking-tight flex items-center gap-2 relative z-10">
                <span className="w-2 h-2 rounded-full bg-accent-cyan"></span>
                Your Impact
            </h3>

            <div className="relative h-40 w-full mb-4 z-10">
                <svg className="w-full h-full" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" fill="none" r="45" stroke="rgba(255,255,255,0.05)" strokeWidth="8"></circle>
                    <circle cx="50" cy="50" fill="none" r="45" stroke="#119bb0" strokeDasharray="210 282" strokeLinecap="round" strokeWidth="8" transform="rotate(-90 50 50)"></circle>
                    <text className="text-[14px] font-bold fill-white" fontFamily="Quicksand, sans-serif" textAnchor="middle" x="50" y="46">Top 15%</text>
                    <text className="text-[9px] font-semibold fill-slate-400 uppercase tracking-widest" fontFamily="Quicksand, sans-serif" textAnchor="middle" x="50" y="62">Community Saver</text>
                </svg>
            </div>

            <p className="text-xs text-center text-slate-300 italic font-medium relative z-10">
                "You used 20% less water than your neighborhood average this month!"
            </p>
        </div>
    );
}

export function NeighborHelp() {
    return (
        <div className="bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl p-6 flex flex-col gap-4 relative overflow-hidden group">
            <div className="absolute -left-10 -bottom-10 w-32 h-32 bg-primary/10 rounded-full filter blur-2xl group-hover:bg-primary/20 transition-colors pointer-events-none"></div>

            <h3 className="font-bold text-white tracking-tight flex items-center gap-2 relative z-10">
                <span className="w-2 h-2 rounded-full bg-primary"></span>
                Neighbor Help
            </h3>

            <div className="relative z-10 space-y-3">
                {/* User 1 */}
                <div className="bg-black/20 border border-white/5 p-3 rounded-xl flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-slate-800 overflow-hidden border border-white/10 shrink-0">
                        <img alt="avatar" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDQg2QZDENbJM4bR8AURdnzQZaiAlgFEADoa3qBAeUbMzpVNuWT7pqP7RAg7_FupldF4AWou5VeM2VA9NidIkkkyLJ67wAdG4WrkUrf3M6pNLqhAjqToqnsgx9zGdXbklypk-iXCmEoJwDU7enwhi3oDPYiXgPgwEfyHYQb6urvmCsVt-yvNziR2vyjMecBUhW4ZOqpijT5R1siZuwilLqTqt0CTp7WWR03E2tGwhOwSai8PDBSvwKdyY_HucX31MZKAuBa97FDJgE" className="w-full h-full object-cover" />
                    </div>
                    <div className="flex-grow">
                        <p className="text-sm font-bold text-slate-200 leading-tight">Rahim asked about KSEB</p>
                        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mt-0.5">2 mins ago</p>
                    </div>
                    <button className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center hover:bg-primary hover:text-white transition-colors">
                        <Reply size={16} />
                    </button>
                </div>

                {/* User 2 */}
                <div className="bg-black/20 border border-white/5 p-3 rounded-xl flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-slate-800 overflow-hidden border border-white/10 shrink-0">
                        <img alt="avatar" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBXWJ8uSE_WTl16H_8V-WkGwNKzkIbVuH359VQBXJc9dKd9Y8aiOdHwqkrAM9Anay3WO-cWlTWtsAG35hPXaTCWsl86Lyj_p-CPmwvARbmbLRTkZ4tRGz1Xn3CELjl1NE0yTl9jANtxQZ0XxShSSLBI7bPsakwWvNmZH2XkuMoNZ6mtj6BCGkbroSyGSpebPumWKgH7VDQw9sr5lppXVmxJTFRBpKk6fxD3UjXu-SyveQktyuPz38Y0586ZkOfOGsudq0FigODwF3M" className="w-full h-full object-cover" />
                    </div>
                    <div className="flex-grow">
                        <p className="text-sm font-bold text-slate-200 leading-tight">Lekshmi shared a bill tip</p>
                        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mt-0.5">1 hour ago</p>
                    </div>
                    <button className="w-8 h-8 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center hover:bg-red-500 hover:text-white transition-colors">
                        <Heart size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
}
