"use client";

import { useState, useEffect, useRef, useCallback } from "react";

// ─── Color palette ────────────────────────────────────────────────────────────
const COLORS = [
  { name: "Red",       hex: "#EF4444" },
  { name: "Orange",    hex: "#F97316" },
  { name: "Amber",     hex: "#F59E0B" },
  { name: "Yellow",    hex: "#EAB308" },
  { name: "Lime",      hex: "#84CC16" },
  { name: "Green",     hex: "#22C55E" },
  { name: "Emerald",   hex: "#10B981" },
  { name: "Teal",      hex: "#14B8A6" },
  { name: "Cyan",      hex: "#06B6D4" },
  { name: "Sky",       hex: "#38BDF8" },
  { name: "Blue",      hex: "#3B82F6" },
  { name: "Indigo",    hex: "#6366F1" },
  { name: "Violet",    hex: "#8B5CF6" },
  { name: "Purple",    hex: "#A855F7" },
  { name: "Fuchsia",   hex: "#D946EF" },
  { name: "Pink",      hex: "#EC4899" },
  { name: "Rose",      hex: "#F43F5E" },
  { name: "Crimson",   hex: "#DC2626" },
  { name: "Maroon",    hex: "#9B1C1C" },
  { name: "Coral",     hex: "#FF6B6B" },
  { name: "Salmon",    hex: "#FCA5A5" },
  { name: "Gold",      hex: "#FFD700" },
  { name: "Navy",      hex: "#1E3A8A" },
  { name: "Olive",     hex: "#6B7232" },
  { name: "Turquoise", hex: "#2DD4BF" },
  { name: "Lavender",  hex: "#C4B5FD" },
  { name: "Mint",      hex: "#86EFAC" },
  { name: "Peach",     hex: "#FDBA74" },
  { name: "Slate",     hex: "#64748B" },
  { name: "Brown",     hex: "#92400E" },
] as const;

// ─── Types ────────────────────────────────────────────────────────────────────
type Color    = { name: string; hex: string };
type Screen   = "menu" | "game" | "over";
type GameMode = "classic" | "reverse" | "mixed" | "stroop";
type Feedback = "correct" | "wrong" | "timeout";

interface Question {
  correct:    Color;
  options:    Color[];
  showSwatch: boolean; // true → show swatch, pick name; false → show name, pick swatch
  textColor?: string;  // stroop: name rendered in this distracting color
}

// ─── Constants ────────────────────────────────────────────────────────────────
const QUESTION_TIME = 10;
const MAX_LIVES     = 3;
const FEEDBACK_MS   = 1400;

const MODE_CONFIG: {
  id: GameMode; name: string; desc: string; icon: string;
  gradient: string; glow: string;
}[] = [
  {
    id: "classic",  name: "Classic",  icon: "🎨",
    desc: "See a color — name it!",
    gradient: "from-violet-600 to-purple-700",
    glow: "shadow-violet-500/40",
  },
  {
    id: "reverse",  name: "Reverse",  icon: "🔍",
    desc: "See a name — find the swatch!",
    gradient: "from-sky-500 to-blue-600",
    glow: "shadow-sky-500/40",
  },
  {
    id: "mixed",    name: "Mixed",    icon: "🎲",
    desc: "Both modes at random!",
    gradient: "from-orange-500 to-rose-500",
    glow: "shadow-orange-500/40",
  },
  {
    id: "stroop",   name: "Stroop",   icon: "🧠",
    desc: "Ignore the text color — read the name!",
    gradient: "from-pink-500 to-fuchsia-600",
    glow: "shadow-pink-500/40",
  },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────
function makeQuestion(mode: GameMode): Question {
  const shuffled = [...COLORS].sort(() => Math.random() - 0.5);
  const correct  = shuffled[0];
  const wrong    = shuffled.slice(1, 4);
  const options  = [...wrong, correct].sort(() => Math.random() - 0.5);

  let showSwatch: boolean;
  if (mode === "classic")            showSwatch = true;
  else if (mode === "reverse")       showSwatch = false;
  else if (mode === "stroop")        showSwatch = false;
  else                               showSwatch = Math.random() > 0.5;

  let textColor: string | undefined;
  if (mode === "stroop") {
    const others = COLORS.filter(c => c.hex !== correct.hex);
    textColor = others[Math.floor(Math.random() * others.length)].hex;
  }

  return { correct, options, showSwatch, textColor };
}

function isLight(hex: string): boolean {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.58;
}

function getMultiplier(streak: number): number {
  if (streak >= 6) return 3;
  if (streak >= 3) return 2;
  return 1;
}

const INIT_SCORES: Record<GameMode, number> = { classic: 0, reverse: 0, mixed: 0, stroop: 0 };

// ─── Component ────────────────────────────────────────────────────────────────
export default function ColorMatch() {
  const [screen,      setScreen]      = useState<Screen>("menu");
  const [gameMode,    setGameMode]    = useState<GameMode>("classic");
  const [question,    setQuestion]    = useState<Question | null>(null);
  const [score,       setScore]       = useState(0);
  const [lives,       setLives]       = useState(MAX_LIVES);
  const [streak,      setStreak]      = useState(0);
  const [timeLeft,    setTimeLeft]    = useState(QUESTION_TIME);
  const [feedback,    setFeedback]    = useState<Feedback | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [questionTick, setQuestionTick] = useState(0);
  const [questionCount, setQuestionCount] = useState(0);
  const [highScores,  setHighScores]  = useState<Record<GameMode, number>>(INIT_SCORES);
  const [isNewRecord, setIsNewRecord] = useState(false);

  // Refs for stale-closure-safe access inside setInterval
  const answeredRef   = useRef(false);
  const timerRef      = useRef<ReturnType<typeof setInterval> | null>(null);
  const fbTimerRef    = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scoreRef      = useRef(0);
  const livesRef      = useRef(MAX_LIVES);
  const streakRef     = useRef(0);
  const gameModeRef   = useRef<GameMode>("classic");

  useEffect(() => { scoreRef.current    = score;    }, [score]);
  useEffect(() => { livesRef.current    = lives;    }, [lives]);
  useEffect(() => { streakRef.current   = streak;   }, [streak]);
  useEffect(() => { gameModeRef.current = gameMode; }, [gameMode]);

  // Load persisted high scores
  useEffect(() => {
    try {
      const raw = localStorage.getItem("cm_hs_v1");
      if (raw) setHighScores(JSON.parse(raw));
    } catch {}
  }, []);

  // ── Core answer processor (stable reference via useCallback + refs) ─────────
  const processAnswer = useCallback(
    (correct: boolean, isTimeout: boolean, optIdx: number | null) => {
      if (answeredRef.current) return;
      answeredRef.current = true;

      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }

      setSelectedIdx(optIdx);

      const curScore  = scoreRef.current;
      const curLives  = livesRef.current;
      const curStreak = streakRef.current;
      const curMode   = gameModeRef.current;

      let newScore  = curScore;
      let newLives  = curLives;
      let newStreak = curStreak;

      if (correct) {
        const mult = getMultiplier(curStreak);
        newScore  = curScore + 10 * mult;
        newStreak = curStreak + 1;
        setFeedback("correct");
      } else {
        newLives  = curLives - 1;
        newStreak = 0;
        setFeedback(isTimeout ? "timeout" : "wrong");
      }

      setScore(newScore);
      setLives(newLives);
      setStreak(newStreak);
      // Update refs immediately so timeout callback has accurate values
      scoreRef.current  = newScore;
      livesRef.current  = newLives;
      streakRef.current = newStreak;

      fbTimerRef.current = setTimeout(() => {
        if (newLives <= 0) {
          setHighScores(prev => {
            if (newScore > prev[curMode]) {
              const updated = { ...prev, [curMode]: newScore };
              try { localStorage.setItem("cm_hs_v1", JSON.stringify(updated)); } catch {}
              setIsNewRecord(true);
              return updated;
            }
            setIsNewRecord(false);
            return prev;
          });
          setScreen("over");
        } else {
          setQuestion(makeQuestion(curMode));
          setFeedback(null);
          setSelectedIdx(null);
          setTimeLeft(QUESTION_TIME);
          setQuestionCount(c => c + 1);
          setQuestionTick(t => t + 1);
        }
      }, FEEDBACK_MS);
    },
    []
  );

  // ── Timer — re-runs whenever questionTick or screen changes ─────────────────
  useEffect(() => {
    if (screen !== "game") return;
    answeredRef.current = false;

    timerRef.current = setInterval(() => {
      setTimeLeft(t => {
        if (t <= 1) {
          processAnswer(false, true, null);
          return 0;
        }
        return t - 1;
      });
    }, 1000);

    return () => { if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; } };
  }, [questionTick, screen, processAnswer]);

  // ── User picks an option ─────────────────────────────────────────────────────
  const handleOptionClick = (idx: number) => {
    if (answeredRef.current || !question) return;
    processAnswer(question.options[idx].hex === question.correct.hex, false, idx);
  };

  // ── Start / restart game ─────────────────────────────────────────────────────
  const startGame = (mode: GameMode) => {
    if (timerRef.current)   { clearInterval(timerRef.current);  timerRef.current  = null; }
    if (fbTimerRef.current) { clearTimeout(fbTimerRef.current); fbTimerRef.current = null; }

    const q = makeQuestion(mode);
    setGameMode(mode);    gameModeRef.current = mode;
    setScore(0);          scoreRef.current  = 0;
    setLives(MAX_LIVES);  livesRef.current  = MAX_LIVES;
    setStreak(0);         streakRef.current = 0;
    setQuestion(q);
    setFeedback(null);
    setSelectedIdx(null);
    setTimeLeft(QUESTION_TIME);
    setQuestionCount(0);
    setIsNewRecord(false);
    answeredRef.current = false;
    setQuestionTick(t => t + 1);
    setScreen("game");
  };

  const goToMenu = () => {
    if (timerRef.current)   { clearInterval(timerRef.current);  timerRef.current  = null; }
    if (fbTimerRef.current) { clearTimeout(fbTimerRef.current); fbTimerRef.current = null; }
    setFeedback(null);
    setScreen("menu");
  };

  // ─────────────────────────────────────────────────────────────────────────────
  // MENU SCREEN
  // ─────────────────────────────────────────────────────────────────────────────
  if (screen === "menu") {
    return (
      <div className="min-h-dvh bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 flex flex-col items-center justify-center p-4 sm:p-6">
        <div className="w-full max-w-sm animate-slide-up">

          {/* Title */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/5 border border-white/10 shadow-xl mb-4">
              <svg viewBox="0 0 32 32" className="w-10 h-10">
                <path d="M16,16 L16,2 A14,14 0 0,1 28.1,9 Z"  fill="#EF4444"/>
                <path d="M16,16 L28.1,9 A14,14 0 0,1 28.1,23 Z" fill="#EAB308"/>
                <path d="M16,16 L28.1,23 A14,14 0 0,1 16,30 Z" fill="#22C55E"/>
                <path d="M16,16 L16,30 A14,14 0 0,1 3.9,23 Z"  fill="#06B6D4"/>
                <path d="M16,16 L3.9,23 A14,14 0 0,1 3.9,9 Z"  fill="#3B82F6"/>
                <path d="M16,16 L3.9,9 A14,14 0 0,1 16,2 Z"    fill="#A855F7"/>
                <circle cx="16" cy="16" r="4.5" fill="#0f0f1a"/>
              </svg>
            </div>
            <h1 className="text-5xl font-black text-white tracking-tight leading-none">
              Color<span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-pink-400">Match</span>
            </h1>
            <p className="text-white/50 mt-2 text-base">How well do you know your colors?</p>
          </div>

          {/* Mode cards */}
          <div className="grid grid-cols-2 gap-3 mb-5">
            {MODE_CONFIG.map(m => (
              <button
                key={m.id}
                onClick={() => startGame(m.id)}
                className={`bg-gradient-to-br ${m.gradient} p-4 rounded-2xl text-left
                            hover:scale-[1.04] active:scale-[0.97] transition-transform duration-150
                            shadow-lg ${m.glow} focus:outline-none`}
              >
                <div className="text-2xl mb-1">{m.icon}</div>
                <div className="text-white font-bold text-base leading-tight">{m.name}</div>
                <div className="text-white/75 text-xs mt-1 leading-snug">{m.desc}</div>
                {highScores[m.id] > 0 && (
                  <div className="text-white/50 text-xs mt-2 font-medium">
                    Best: {highScores[m.id]}
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* How to play */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
            <p className="text-white/60 text-xs font-semibold uppercase tracking-widest mb-2">How to play</p>
            <ul className="text-white/45 text-sm space-y-1">
              <li>• Match colors before the timer runs out</li>
              <li>• Lose a life for every wrong answer</li>
              <li>• 3 wrong = game over</li>
              <li>• Chain correct answers for score multipliers 🔥</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // GAME OVER SCREEN
  // ─────────────────────────────────────────────────────────────────────────────
  if (screen === "over") {
    const modeInfo = MODE_CONFIG.find(m => m.id === gameMode)!;
    return (
      <div className="min-h-dvh bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 flex flex-col items-center justify-center p-4 sm:p-6">
        <div className="w-full max-w-sm text-center animate-slide-up">
          <div className="text-7xl mb-4 animate-pop">
            {isNewRecord ? "🏆" : score > 50 ? "🎉" : "💀"}
          </div>

          <h2 className="text-4xl font-black text-white mb-1">Game Over</h2>
          {isNewRecord && (
            <p className="text-yellow-400 font-bold text-base mb-3 animate-fade-in">
              ✨ New High Score!
            </p>
          )}

          <div className="bg-white/8 border border-white/10 rounded-3xl p-6 mb-5">
            <p className="text-white/50 text-xs uppercase tracking-widest mb-1">Your Score</p>
            <p className="text-6xl font-black text-white mb-5">{score}</p>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-white/40 text-xs mb-1">Mode</p>
                <p className="text-white font-bold text-sm">{modeInfo.icon} {modeInfo.name}</p>
              </div>
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-white/40 text-xs mb-1">Best</p>
                <p className="text-white font-bold">{highScores[gameMode]}</p>
              </div>
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-white/40 text-xs mb-1">Answered</p>
                <p className="text-white font-bold">{questionCount}</p>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => startGame(gameMode)}
              className={`flex-1 bg-gradient-to-r ${modeInfo.gradient} text-white font-bold py-4
                          rounded-2xl hover:opacity-90 active:scale-95 transition-all duration-150 text-lg shadow-lg`}
            >
              Play Again
            </button>
            <button
              onClick={goToMenu}
              className="flex-1 bg-white/10 border border-white/15 text-white font-bold py-4
                         rounded-2xl hover:bg-white/15 active:scale-95 transition-all duration-150 text-lg"
            >
              Menu
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────────
  // GAME SCREEN
  // ─────────────────────────────────────────────────────────────────────────────
  if (!question) return null;

  const isAnswered  = feedback !== null;
  const multiplier  = getMultiplier(streak);
  const timerPct    = (timeLeft / QUESTION_TIME) * 100;
  const timerColor  = timeLeft <= 3 ? "#EF4444" : timeLeft <= 6 ? "#F59E0B" : "#8B5CF6";
  const modeInfo    = MODE_CONFIG.find(m => m.id === gameMode)!;

  // Feedback text
  let fbText = "";
  if (feedback === "correct") {
    fbText = streak >= 3 ? `🔥 +${10 * multiplier} pts — ${multiplier}x streak!` : `✓ +${10 * multiplier} pts`;
  } else if (feedback === "timeout") {
    fbText = `⏰ Time's up! It was ${question.correct.name}`;
  } else if (feedback === "wrong") {
    fbText = `✗ Wrong! It was ${question.correct.name}`;
  }

  return (
    <div className="min-h-dvh bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950 flex flex-col items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-sm flex flex-col gap-4">

        {/* ── Top bar ─────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between">
          <button
            onClick={goToMenu}
            className="text-white/35 hover:text-white/70 transition-colors text-sm font-medium px-1 py-1"
            aria-label="Back to menu"
          >
            ← Menu
          </button>

          <div className="flex flex-col items-center">
            <span className="text-2xl font-black text-white">{score}</span>
            {streak >= 3 && (
              <span className="text-xs text-amber-400 font-bold -mt-0.5">{multiplier}× streak</span>
            )}
          </div>

          {/* Lives */}
          <div className="flex gap-1">
            {Array.from({ length: MAX_LIVES }).map((_, i) => (
              <svg key={i} className={`w-5 h-5 transition-all duration-300 ${i < lives ? "text-red-500 scale-100" : "text-white/15 scale-90"}`} viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
            ))}
          </div>
        </div>

        {/* ── Timer bar ───────────────────────────────────────────────────── */}
        <div className="w-full h-2.5 bg-white/8 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${timeLeft <= 3 ? "animate-pulse" : ""}`}
            style={{
              width: `${timerPct}%`,
              backgroundColor: timerColor,
              transition: "width 0.95s linear, background-color 0.4s",
            }}
          />
        </div>

        {/* ── Question display ────────────────────────────────────────────── */}
        {question.showSwatch ? (
          /* Swatch → pick name */
          <div
            className="w-full h-44 sm:h-52 rounded-3xl shadow-2xl border-2 border-white/10 transition-all duration-300"
            style={{ backgroundColor: question.correct.hex }}
            aria-label={`Color swatch: choose the correct name`}
          />
        ) : (
          /* Name → pick swatch (also used for stroop) */
          <div className="w-full h-44 sm:h-52 flex flex-col items-center justify-center rounded-3xl bg-white/5 border border-white/10 shadow-2xl gap-2">
            {gameMode === "stroop" && (
              <p className="text-white/30 text-xs uppercase tracking-widest">What color does it SAY?</p>
            )}
            <p
              className="text-5xl sm:text-6xl font-black tracking-tight leading-none"
              style={{ color: question.textColor ?? "#ffffff" }}
            >
              {question.correct.name.toUpperCase()}
            </p>
            {gameMode === "stroop" && (
              <p className="text-white/25 text-xs">Ignore the text color</p>
            )}
          </div>
        )}

        {/* ── Options grid ────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 gap-3">
          {question.options.map((opt, idx) => {
            const isSelected = selectedIdx === idx;
            const isCorrect  = opt.hex === question.correct.hex;
            const light      = isLight(opt.hex);

            if (question.showSwatch) {
              // Text buttons: show color name
              let cls = "h-16 sm:h-20 rounded-2xl font-bold text-base sm:text-lg transition-all duration-200 active:scale-95 focus:outline-none border-2 ";
              if (!isAnswered) {
                cls += "bg-white/8 hover:bg-white/16 text-white border-white/15 hover:border-white/30 hover:scale-[1.02]";
              } else if (isCorrect) {
                cls += "bg-green-500 text-white border-green-300 animate-pop";
              } else if (isSelected) {
                cls += "bg-red-500 text-white border-red-300 animate-shake";
              } else {
                cls += "bg-white/4 text-white/25 border-white/8";
              }
              return (
                <button key={opt.hex} onClick={() => handleOptionClick(idx)} disabled={isAnswered} className={cls}>
                  {opt.name}
                </button>
              );
            } else {
              // Swatch buttons: show colored box
              let cls = "h-20 sm:h-24 rounded-2xl transition-all duration-200 active:scale-95 focus:outline-none relative flex items-center justify-center overflow-hidden border-4 ";
              if (!isAnswered) {
                cls += "border-transparent hover:border-white/50 hover:scale-[1.03]";
              } else if (isCorrect) {
                cls += "border-green-300 ring-4 ring-green-400/30 animate-pop";
              } else if (isSelected) {
                cls += "border-red-400 ring-4 ring-red-400/30 animate-shake";
              } else {
                cls += "border-transparent opacity-35";
              }
              return (
                <button
                  key={opt.hex}
                  onClick={() => handleOptionClick(idx)}
                  disabled={isAnswered}
                  className={cls}
                  style={{ backgroundColor: opt.hex }}
                  aria-label={isAnswered ? opt.name : undefined}
                >
                  {isAnswered && isCorrect && (
                    <span className={`text-3xl font-black drop-shadow ${light ? "text-black/70" : "text-white/90"}`}>✓</span>
                  )}
                  {isAnswered && isSelected && !isCorrect && (
                    <span className={`text-3xl font-black drop-shadow ${light ? "text-black/70" : "text-white/90"}`}>✗</span>
                  )}
                </button>
              );
            }
          })}
        </div>

        {/* ── Feedback message ────────────────────────────────────────────── */}
        <div className="h-6 text-center">
          {feedback && (
            <p className={`text-sm font-semibold animate-fade-in ${
              feedback === "correct" ? "text-green-400" :
              feedback === "timeout" ? "text-amber-400" : "text-red-400"
            }`}>
              {fbText}
            </p>
          )}
        </div>

        {/* ── Footer ──────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between text-xs text-white/20">
          <span>{modeInfo.icon} {modeInfo.name}</span>
          <span>Q {questionCount + 1}</span>
          <span>{timeLeft}s</span>
        </div>

      </div>
    </div>
  );
}
