import React, { useState } from 'react';

const JoinQueue = () => {
  const [businessName, setBusinessName] = useState('');
  const [queueId, setQueueId] = useState('');
  const [showTicket, setShowTicket] = useState(false);

  const handleJoinQueue = () => {
    if (businessName.trim() && queueId.trim()) {
      setShowTicket(true);
    }
  };

  const handleCloseTicket = () => {
    setShowTicket(false);
    setBusinessName('');
    setQueueId('');
  };

  return (
    <div
      className="min-h-screen bg-black relative overflow-hidden flex items-center justify-center bg-cover bg-center"
      style={{ backgroundImage: `url('/img/bg1.jpg')` }}
    >
      {/* Overlay blur and dark tint */}
      <div className="absolute inset-0" />

      {/* Main UI Card */}
      <div
        className={`relative z-10 transition-all duration-700 ease-out ${
          showTicket ? 'scale-95 opacity-80' : 'scale-100 opacity-100'
        }`}
      >
        <div className="backdrop-blur-lg bg-black/50 border border-white/10 rounded-3xl p-12 shadow-2xl min-w-[400px] text-white font-mono space-y-6">
          <h1
            className="text-4xl text-center tracking-wide"
            style={{
              fontFamily: 'JetBrains Mono, Orbitron, monospace',
            }}
          >
            Join Queue
          </h1>

          {/* Input Fields */}
          <div className="space-y-4">
            <div>
              <label className="block mb-1 text-gray-300">Business Name</label>
              <input
                type="text"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                className="w-full px-4 py-2 rounded-md bg-gray-800 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-white/20"
                placeholder="Enter business name"
              />
            </div>

            <div>
              <label className="block mb-1 text-gray-300">Queue ID</label>
              <input
                type="text"
                value={queueId}
                onChange={(e) => setQueueId(e.target.value)}
                className="w-full px-4 py-2 rounded-md bg-gray-800 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-white/20"
                placeholder="Enter queue ID"
              />
            </div>
          </div>

          {/* Join Button */}
          <div className="flex justify-center pt-4">
            <button
              onClick={handleJoinQueue}
              disabled={!businessName || !queueId || showTicket}
              className={`
                relative px-8 py-4 font-bold rounded-xl
                bg-gray-900 border border-white/20 text-white
                transform transition-all duration-300 ease-out
                hover:scale-105 hover:shadow-lg
                active:scale-95
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {showTicket ? 'Joined!' : 'Join Queue'}
            </button>
          </div>
        </div>
      </div>

      {/* Queue Ticket Modal */}
      <div
        className={`fixed inset-0 flex items-center justify-center z-20 p-4 transition-all duration-700 ease-out ${
          showTicket ? 'opacity-100 visible' : 'opacity-0 invisible'
        }`}
        style={{
          backgroundImage: `url('/img/bg1.jpg')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backdropFilter: 'blur(10px)',
        }}
      >
        <div
          className={`backdrop-blur-xl bg-black/60 border border-white/10 rounded-2xl p-8 max-w-sm w-full transform transition-all duration-700 ease-out shadow-xl ${
            showTicket
              ? 'scale-100 translate-y-0 opacity-100'
              : 'scale-90 translate-y-10 opacity-0'
          }`}
        >
          <div className="space-y-6 font-mono text-white">
            {/* Ticket Header */}
            <div className="flex items-center gap-3 text-2xl">
              <span>🎟️</span>
              <span>Queue Ticket</span>
            </div>

            {/* Ticket Details */}
            <div className="space-y-4 text-gray-300">
              <div className="flex justify-between items-center py-2 border-b border-white/10">
                <span className="text-gray-400">Queue ID:</span>
                <span className="text-white font-semibold">{queueId}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/10">
                <span className="text-gray-400">Business:</span>
                <span className="text-white font-semibold">{businessName}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-white/10">
                <span className="text-gray-400">Your Position:</span>
                <span className="text-white font-semibold">7</span>
              </div>
            </div>

            {/* Close Button */}
            <div className="pt-4">
              <button
                onClick={handleCloseTicket}
                className="w-full py-3 px-6 bg-gray-800 hover:bg-gray-700 rounded-lg font-mono text-white transition-all duration-300 border border-white/10"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Custom Fonts */}
      <style jsx>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@400;700&display=swap');
      `}</style>
    </div>
  );
};

export default JoinQueue;
