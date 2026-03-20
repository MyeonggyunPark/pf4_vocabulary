import { useState } from 'react'
import {
  Bot,
  Brain,
  ChartSpline,
  CheckCircle2,
  ChevronRight,
  Flame,
  FolderHeart,
  GraduationCap,
  Home,
  Languages,
  MessageSquareMore,
  NotebookPen,
  RotateCcw,
  Sparkles,
  Target,
} from 'lucide-react'
import './App.css'

const views = [
  { id: 'dashboard', label: '대시보드', icon: Home },
  { id: 'flashcards', label: '플래시카드', icon: Languages },
  { id: 'practice', label: 'AI 첨삭', icon: Bot },
]

const customLists = [
  { title: '초록책 핵심 동사', words: 42, tone: 'from-emerald-500 to-emerald-700' },
  { title: '여행 독일어 생존 표현', words: 28, tone: 'from-lime-500 to-emerald-600' },
  { title: '헷갈리는 명사 성', words: 36, tone: 'from-teal-500 to-emerald-700' },
  { title: 'B1 시험 필수 어휘', words: 54, tone: 'from-slate-700 to-emerald-700' },
]

const practiceFeedback = {
  incorrect: 'Ich entschuldige für mein Fehler.',
  corrected: 'Ich entschuldige mich für meinen Fehler.',
  explanation:
    '"entschuldigen"은 여기서 재귀형으로 쓰여 "sich entschuldigen für" 형태가 됩니다. 또 "Fehler"는 남성 명사라 Akkusativ에서 "meinen Fehler"가 됩니다.',
}

function Sidebar({ activeView, onSelect }) {
  return (
    <aside className="w-full shrink-0 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-[0_24px_60px_rgba(15,23,42,0.08)] backdrop-blur xl:w-80">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-600 text-white shadow-lg shadow-emerald-200">
          <GraduationCap size={24} />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700">초록책 AI</p>
          <h1 className="text-xl font-semibold text-slate-900">독일어 단어장</h1>
        </div>
      </div>

      <nav className="space-y-2">
        {views.map((view) => {
          const IconComponent = view.icon
          const { id, label } = view
          const isActive = activeView === id
          return (
            <button
              key={id}
              type="button"
              onClick={() => onSelect(id)}
              className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left transition ${
                isActive
                  ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-200'
                  : 'text-slate-600 hover:bg-emerald-50 hover:text-emerald-700'
              }`}
            >
              <IconComponent size={20} />
              <span className="font-medium">{label}</span>
              <ChevronRight size={18} className={`ml-auto transition ${isActive ? 'opacity-100' : 'opacity-0'}`} />
            </button>
          )
        })}
      </nav>

      <div className="mt-8 rounded-[1.75rem] bg-gradient-to-br from-emerald-900 via-emerald-800 to-lime-700 p-5 text-white">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.26em] text-emerald-100/80">AI 학습 도우미</p>
        <h2 className="text-lg font-semibold">지금 바로 첨삭 연습을 시작해보세요.</h2>
        <p className="mt-2 text-sm leading-6 text-emerald-50/85">
          문장 교정, 표현 수정, 문법 설명을 한 화면에서 바로 받을 수 있습니다.
        </p>
        <button
          type="button"
          onClick={() => onSelect('practice')}
          className="mt-5 inline-flex items-center gap-2 rounded-full bg-white/95 px-4 py-2 text-sm font-semibold text-emerald-900 transition hover:bg-white"
        >
          AI 첨삭 열기
          <Sparkles size={16} />
        </button>
      </div>
    </aside>
  )
}

function TopTabs({ activeView, onSelect }) {
  return (
    <div className="flex flex-wrap gap-3">
      {views.map((view) => {
        const IconComponent = view.icon
        const { id, label } = view
        const isActive = activeView === id
        return (
          <button
            key={id}
            type="button"
            onClick={() => onSelect(id)}
            className={`inline-flex items-center gap-2 rounded-full border px-4 py-2.5 text-sm font-semibold transition ${
              isActive
                ? 'border-emerald-600 bg-emerald-600 text-white shadow-lg shadow-emerald-100'
                : 'border-slate-200 bg-white text-slate-600 hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-700'
            }`}
          >
            <IconComponent size={16} />
            {label}
          </button>
        )
      })}
    </div>
  )
}

function ProgressRing({ value, label, sublabel }) {
  const degrees = Math.round((value / 100) * 360)
  return (
    <div className="flex items-center gap-4 rounded-[1.75rem] border border-slate-100 bg-white p-5 shadow-md">
      <div
        className="progress-ring flex h-24 w-24 items-center justify-center rounded-full"
        style={{ '--progress-angle': `${degrees}deg` }}
      >
        <div className="flex h-[72px] w-[72px] flex-col items-center justify-center rounded-full bg-slate-50 text-center">
          <span className="text-2xl font-bold text-slate-900">{value}%</span>
          <span className="text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-400">달성</span>
        </div>
      </div>
      <div>
        <p className="text-sm font-semibold text-slate-500">{label}</p>
        <p className="text-2xl font-semibold text-slate-900">{sublabel}</p>
      </div>
    </div>
  )
}

function DashboardView({ onStart }) {
  return (
    <section className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <div className="rounded-[2rem] bg-gradient-to-br from-emerald-950 via-emerald-800 to-lime-700 p-8 text-white shadow-[0_30px_80px_rgba(5,150,105,0.25)]">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-emerald-100/80">학습 대시보드</p>
          <h2 className="mt-3 max-w-xl text-4xl font-semibold leading-tight">
            Guten Morgen! 오늘의 독일어 공부를 시작해볼까요?
          </h2>
          <p className="mt-4 max-w-xl text-base leading-7 text-emerald-50/85">
            한국어 사용자에게 맞춘 단어 암기, AI 첨삭, 학습 추적 기능으로 독일어 실력을 꾸준히 쌓아보세요.
          </p>
          <button
            type="button"
            onClick={onStart}
            className="mt-8 inline-flex items-center gap-3 rounded-full bg-white px-6 py-3 text-base font-semibold text-emerald-900 shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
          >
            오늘의 학습 시작하기
            <ChevronRight size={18} />
          </button>
        </div>

        <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
          <ProgressRing value={72} label="오늘의 목표" sublabel="20개 단어" />
          <div className="rounded-[1.75rem] border border-slate-100 bg-white p-5 shadow-md">
            <div className="flex items-center gap-3 text-amber-500">
              <Flame size={22} />
              <span className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">연속 학습</span>
            </div>
            <p className="mt-4 text-3xl font-semibold text-slate-900">5일</p>
            <p className="mt-2 text-sm text-slate-500">이번 주 학습 흐름이 아주 좋습니다.</p>
          </div>
          <div className="rounded-[1.75rem] border border-slate-100 bg-white p-5 shadow-md">
            <div className="flex items-center gap-3 text-emerald-600">
              <CheckCircle2 size={22} />
              <span className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">완전히 익힌 단어</span>
            </div>
            <p className="mt-4 text-3xl font-semibold text-slate-900">184</p>
            <p className="mt-2 text-sm text-slate-500">B1 문법과 독해를 위한 기초가 잘 쌓이고 있어요.</p>
          </div>
        </div>
      </div>

      <div className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-md">
        <div className="mb-5 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.26em] text-emerald-700">내 단어장</p>
            <h3 className="mt-2 text-2xl font-semibold text-slate-900">약한 부분 중심으로 학습하기</h3>
          </div>
          <div className="hidden items-center gap-2 rounded-full bg-slate-100 px-4 py-2 text-sm font-medium text-slate-500 md:inline-flex">
            <FolderHeart size={16} />
            좌우로 넘겨보기
          </div>
        </div>

        <div className="flex gap-4 overflow-x-auto pb-2">
          {customLists.map((list) => (
            <article
              key={list.title}
              className={`min-w-[260px] rounded-[1.75rem] bg-gradient-to-br ${list.tone} p-5 text-white shadow-lg transition hover:-translate-y-1 hover:shadow-xl`}
            >
              <div className="flex items-center justify-between">
                <NotebookPen size={20} className="text-white/80" />
                <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em]">
                  {list.words}개 단어
                </span>
              </div>
              <h4 className="mt-8 text-xl font-semibold">{list.title}</h4>
              <p className="mt-3 text-sm leading-6 text-white/80">
                반복 암기, 문법 복습, 플래시카드 학습에 바로 활용할 수 있는 맞춤 묶음입니다.
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

function FlashcardView() {
  const [flipped, setFlipped] = useState(false)

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.26em] text-emerald-700">
            플래시카드 학습
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-900">
            한 번에 한 단어씩 정확하게 익히기
          </h2>
        </div>
        <button
          type="button"
          onClick={() => setFlipped((current) => !current)}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-600 transition hover:border-emerald-200 hover:bg-emerald-50 hover:text-emerald-700"
        >
          <RotateCcw size={16} />
          카드 뒤집기
        </button>
      </div>

      <div className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-md">
        <div className="flashcard-shell mx-auto max-w-3xl">
          <button
            type="button"
            onClick={() => setFlipped((current) => !current)}
            className="flashcard-card"
          >
            <div className={`flashcard-rotator ${flipped ? "is-flipped" : ""}`}>
              <div className="flashcard-face flashcard-front bg-emerald-50/30">
                <div className="mb-8 inline-flex rounded-full bg-emerald-100 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700">
                  눌러서 뒤집기
                </div>
                <p className="text-4xl font-bold text-slate-900 sm:text-5xl">
                  das Haus
                </p>
                <p className="mt-5 max-w-md text-base leading-7 text-slate-500">
                  먼저 관사를 확인하고, 복수형을 떠올린 뒤 짧은 예문까지
                  말해보세요.
                </p>
              </div>

              <div className="flashcard-face flashcard-back bg-emerald-50/30">
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
                    명사
                  </span>
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
                    복수형: Häuser
                  </span>
                </div>
                <p className="mt-6 text-3xl font-semibold text-slate-900">집</p>
                <div className="mt-6 rounded-[1.5rem] border border-emerald-100 bg-white p-5 text-left text-slate-900 shadow-sm">
                  <div className="flex items-center gap-2 text-sm font-semibold text-emerald-900">
                    <Brain size={16} />
                    AI 선생님 메모
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-700">
                    💡 복수형에서는 움라우트가 들어가는지 꼭 확인하세요.
                  </p>
                </div>
              </div>
            </div>
          </button>
        </div>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <button className="rounded-full bg-rose-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-rose-100 transition hover:-translate-y-0.5 hover:bg-rose-600">
            모르겠어요
          </button>
          <button className="rounded-full bg-amber-400 px-5 py-3 text-sm font-semibold text-slate-900 shadow-lg shadow-amber-100 transition hover:-translate-y-0.5 hover:bg-amber-300">
            어려워요
          </button>
          <button className="rounded-full bg-emerald-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-100 transition hover:-translate-y-0.5 hover:bg-emerald-700">
            알겠어요
          </button>
        </div>
      </div>
    </section>
  );
}

function PracticeView() {
  const [input, setInput] = useState('Ich entschuldige für mein Fehler.')

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.26em] text-emerald-700">AI 첨삭 연습</p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-900">작문, 교정, 문법 설명을 한 번에</h2>
      </div>

      <div className="rounded-[2rem] border border-emerald-100 bg-gradient-to-br from-emerald-900 via-emerald-800 to-slate-900 p-6 text-white shadow-[0_24px_60px_rgba(5,150,105,0.18)]">
        <div className="flex items-start gap-4">
          <div className="mt-1 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/10">
            <MessageSquareMore size={24} />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-100/80">오늘의 미션</p>
            <p className="mt-3 text-lg font-medium leading-8">
              다음 단어를 사용해 문장을 만들어 보세요: <span className="font-semibold text-lime-200">entschuldigen</span>,
              <span className="font-semibold text-lime-200"> Fehler</span>. (뜻: 나는 내 실수에 대해 사과한다.)
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-md">
        <label htmlFor="german-practice" className="mb-3 block text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
          독일어 문장 작성
        </label>
        <textarea
          id="german-practice"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          className="min-h-40 w-full rounded-[1.5rem] border border-slate-200 bg-slate-50 px-5 py-4 text-base text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-emerald-300 focus:bg-white focus:ring-4 focus:ring-emerald-100"
          placeholder="여기에 독일어 문장을 입력하세요..."
        />
        <div className="mt-4 flex items-center justify-between gap-3">
          <p className="text-sm text-slate-500">AI가 문법, 격 변화, 자연스러운 표현을 함께 확인합니다.</p>
          <button className="inline-flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-100 transition hover:-translate-y-0.5 hover:bg-emerald-700">
            첨삭 받기
            <Sparkles size={16} />
          </button>
        </div>
      </div>

      <div className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-md">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
            <ChartSpline size={22} />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">AI 첨삭 결과</p>
            <h3 className="mt-1 text-2xl font-semibold text-slate-900">모호하지 않고 분명한 피드백</h3>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="rounded-[1.5rem] border border-rose-100 bg-rose-50 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-500">내가 쓴 문장</p>
            <p className="mt-4 text-lg leading-8 text-slate-700">
              Ich <span className="text-rose-600 line-through decoration-2">entschuldige für mein Fehler</span>.
            </p>
          </div>
          <div className="rounded-[1.5rem] border border-emerald-100 bg-emerald-50 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-600">수정된 문장</p>
            <p className="mt-4 text-lg font-semibold leading-8 text-emerald-800">{practiceFeedback.corrected}</p>
          </div>
        </div>

        <div className="mt-4 rounded-[1.5rem] border border-slate-100 bg-slate-50 p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">쉬운 설명</p>
          <p className="mt-3 text-sm leading-7 text-slate-700">{practiceFeedback.explanation}</p>
        </div>
      </div>
    </section>
  )
}

function App() {
  const [activeView, setActiveView] = useState("dashboard");

  return (
    <div className="min-h-screen app-background">
      <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col gap-6 px-4 py-4 sm:px-6 lg:px-8 xl:flex-row xl:py-8">
        <Sidebar activeView={activeView} onSelect={setActiveView} />

        <main className="flex-1 rounded-[2rem] border border-white/80 bg-white/60 p-4 shadow-[0_24px_60px_rgba(15,23,42,0.08)] backdrop-blur sm:p-6 lg:p-8">
          <header className="mb-8 flex flex-col gap-5 border-b border-slate-200/80 pb-6 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-emerald-700">
                <Target size={14} />
                맞춤형 독일어 단어장
              </div>
              <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                한국어 사용자에게 맞춘 독일어 학습 웹
              </h1>
              <p className="mt-3 max-w-3xl text-base leading-7 text-slate-600">
                대시보드, 플래시카드, AI 첨삭 화면을 오가며 단어 학습과 문장
                연습을 자연스럽게 이어가세요.
              </p>
            </div>
            <TopTabs activeView={activeView} onSelect={setActiveView} />
          </header>

          {activeView === "dashboard" && (
            <DashboardView onStart={() => setActiveView("flashcards")} />
          )}
          {activeView === "flashcards" && <FlashcardView />}
          {activeView === "practice" && <PracticeView />}
        </main>
      </div>
    </div>
  );
}

export default App
