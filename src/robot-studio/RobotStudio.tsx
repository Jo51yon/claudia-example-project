import { useEffect, useMemo, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import type { RobotStudioHost, TreeNode } from './host';
import Robot from './Robot';
import { BROWSER_VOICE, CATEGORIES, COLOURS, VOICES, chirpVoiceName, isChirpVoice } from './options';
import { useSpeech } from './useSpeech';
import { useRobotState } from './useRobotState';

type Page = 'studio' | 'settings' | 'about';

const CSS = `
.rs-root{min-height:100vh;display:flex;flex-direction:column;color:var(--text);background:#0E1116;position:relative;overflow:hidden}
.rs-bg{position:fixed;inset:0;z-index:0;pointer-events:none;
  background:radial-gradient(900px 600px at 72% 18%,rgba(76,148,140,.28),transparent 60%),
             radial-gradient(700px 520px at 14% 86%,rgba(201,162,39,.18),transparent 62%),
             linear-gradient(180deg,#10141B,#0A0C10)}
.rs-bg::after{content:'';position:absolute;inset:0;
  background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px);
  background-size:44px 44px;mask-image:radial-gradient(ellipse at 60% 40%,#000 25%,transparent 75%);animation:rs-drift 38s linear infinite}
@keyframes rs-drift{to{background-position:44px 44px,44px 44px}}
.rs-nav{position:relative;z-index:2;display:flex;align-items:center;gap:20px;padding:0 22px;height:56px;border-bottom:1px solid var(--hairline);background:rgba(19,22,27,.82);backdrop-filter:blur(8px)}
.rs-brand{font-family:var(--font-display);font-weight:700;letter-spacing:.02em;display:flex;align-items:center;gap:10px}
.rs-tabs{display:flex;gap:4px;flex:1}
.rs-tab{background:none;border:0;color:var(--text-dim);padding:8px 14px;border-radius:8px;cursor:pointer;font:inherit}
.rs-tab[aria-current=page]{color:var(--text);background:var(--surface-raised)}
.rs-main{position:relative;z-index:1;flex:1;display:flex;min-height:0}
.rs-left{width:268px;flex:none;border-right:1px solid var(--hairline);background:rgba(27,31,38,.78);backdrop-filter:blur(6px);padding:16px 12px;overflow:auto}
.rs-left h2{font-family:var(--font-display);font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--text-dim);margin:2px 8px 10px}
.rs-stage{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;padding:24px 20px;min-width:0}
.rs-robot{width:min(360px,70vw);filter:drop-shadow(0 22px 34px rgba(0,0,0,.5))}
.rs-robot.speaking{animation:rs-bob .5s ease-in-out infinite alternate}
@keyframes rs-bob{to{transform:translateY(-5px)}}
.rs-say{width:min(640px,100%);display:flex;flex-direction:column;gap:10px;background:rgba(27,31,38,.86);border:1px solid var(--hairline);border-radius:12px;padding:14px}
.rs-say textarea{width:100%;min-height:84px;resize:vertical;background:var(--ink);color:var(--text);border:1px solid var(--hairline);border-radius:8px;padding:10px;font:inherit}
.rs-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.rs-page{position:relative;z-index:1;flex:1;overflow:auto;padding:28px;max-width:980px;margin:0 auto;width:100%}
.rs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.rs-pill{font-size:.72rem;padding:2px 8px;border-radius:999px;border:1px solid var(--hairline);color:var(--text-dim)}
.rs-sw{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:2px;border:1px solid rgba(255,255,255,.3)}
@media (max-width:760px){.rs-main{flex-direction:column}.rs-left{width:100%;border-right:0;border-bottom:1px solid var(--hairline);max-height:38vh}
  .rs-nav{flex-wrap:wrap;height:auto;padding:8px 14px;gap:6px 12px}.rs-brand .rs-pill{display:none}
  .rs-tabs{order:3;flex:1 1 100%;overflow-x:auto}.rs-page{padding:20px 16px}}
`;

export default function RobotStudio({ host }: { host: RobotStudioHost }) {
  const { supabase, Tree, Card } = host;
  const [session, setSession] = useState<Session | null>(null);
  const [page, setPage] = useState<Page>('studio');
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['colour', 'hair']));
  const speech = useSpeech(supabase, host.supabaseUrl, host.publishableKey, !!session);
  const { attrs: stored, change, text, setText, saved } = useRobotState(supabase, session, (t, voice) => { void speech.speak(t, voice); });
  // Without Chirp the Robot voice is the selection: the Chirp voices are greyed out, the stored choice is kept for later.
  const chirpOff = speech.chirp !== true;
  const attrs = useMemo(() => (chirpOff && isChirpVoice(stored.voice) ? { ...stored, voice: BROWSER_VOICE } : stored), [stored, chirpOff]);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: l } = supabase.auth.onAuthStateChange((_e, s) => setSession(s));
    return () => l.subscription.unsubscribe();
  }, [supabase]);

  const nodes: TreeNode[] = useMemo(() => CATEGORIES.map((c) => ({
    id: c.key,
    label: c.label,
    indicators: <span className="rs-pill">{attrs[c.key]}</span>,
    children: c.options.map((o) => ({
      id: `${c.key}:${o}`,
      disabled: c.key === 'voice' && chirpOff && isChirpVoice(o),
      title: c.key === 'voice' && chirpOff && isChirpVoice(o) ? 'Available when Chirp is switched on' : undefined,
      label: <span style={{ fontWeight: attrs[c.key] === o ? 700 : 400 }}>
        {c.key === 'colour' && <span className="rs-sw" style={{ background: COLOURS[o] }} />}
        {c.key === 'voice' ? (o === BROWSER_VOICE ? 'Robot · built-in' : `${o} · ${VOICES.find((v) => v.id === o)?.gender} · Chirp`) : o}
        {attrs[c.key] === o ? ' ✓' : ''}
      </span>,
    })),
  })), [attrs, chirpOff]);

  const toggle = (id: string) => setExpanded((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });
  const select = (id: string) => {
    const [key, value] = id.split(':');
    if (!value || (key === 'voice' && chirpOff && isChirpVoice(value))) return;
    change({ [key]: value });
  };

  return (
    <div className="rs-root">
      <style>{CSS}</style>
      <div className="rs-bg" />
      <header className="rs-nav">
        <div className="rs-brand"><span aria-hidden>🤖</span> Robot Studio <span className="rs-pill">Claudia example project</span></div>
        <nav className="rs-tabs" aria-label="Robot Studio">
          {(['studio', 'settings', 'about'] as Page[]).map((p) => (
            <button key={p} className="rs-tab" aria-current={page === p ? 'page' : undefined} onClick={() => setPage(p)}>
              {p === 'studio' ? 'Studio' : p === 'settings' ? 'Settings' : 'About'}
            </button>
          ))}
        </nav>
        <a href={host.ledgerHref} style={{ color: 'var(--text-dim)', fontSize: '.85rem' }}>Ledger &amp; tasks →</a>
        {session ? <span className="rs-pill" title={session.user.email ?? ''}>signed in</span>
          : <a href={host.signInHref} className="btn sm">Sign in</a>}
      </header>

      {page === 'studio' && (
        <div className="rs-main">
          <aside className="rs-left" aria-label="Robot attributes">
            <h2>Design your robot</h2>
            <Tree nodes={nodes} expanded={expanded} onToggle={toggle} onSelect={select} />
          </aside>
          <section className="rs-stage">
            <div className={`rs-robot${speech.speaking ? ' speaking' : ''}`}>
              <Robot attrs={attrs} mouth={speech.mouth} speaking={speech.speaking} />
            </div>
            <div className="rs-say">
              <label htmlFor="rs-text" className="dim" style={{ fontSize: '.8rem' }}>What should it say?</label>
              <textarea id="rs-text" value={text} maxLength={600} onChange={(e) => setText(e.target.value)} />
              <div className="rs-row">
                <button className="btn" disabled={!text.trim()} onClick={() => (speech.speaking ? speech.stop() : void speech.speak(text, attrs.voice))}>
                  {speech.speaking ? '■ Stop' : '▶ Speak'}
                </button>
                <span className="dim" style={{ fontSize: '.82rem' }}>Voice: {isChirpVoice(attrs.voice) ? chirpVoiceName(attrs.voice) : 'Robot'}</span>
                <span className="rs-pill">{isChirpVoice(attrs.voice) ? 'Chirp 3 HD' : 'built-in robot voice'}</span>
                <span className="dim" style={{ fontSize: '.8rem', marginLeft: 'auto' }}>{text.length}/600</span>
              </div>
              {speech.note && <div role="status" style={{ fontSize: '.82rem', color: 'var(--brass)' }}>{speech.note}</div>}
              {!saved && <div className="dim" style={{ fontSize: '.8rem' }}>Sign in to save your robot and control it from a chat.</div>}
            </div>
          </section>
        </div>
      )}

      {page === 'settings' && (
        <main className="rs-page">
          <h1 style={{ fontFamily: 'var(--font-display)', marginTop: 0 }}>Settings</h1>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.05rem' }}>Control the robot from a chat (MCP)</h2>
          <p className="dim" style={{ maxWidth: 680 }}>
            Connect Claude, or another assistant that supports MCP, to Robot Studio. Four tools then drive this page live:
            <code> robot_options</code>, <code>robot_get</code>, <code>robot_set</code> (colour, hair, glasses, hat, neckwear, voice) and
            <code> robot_say</code> (makes it speak). Try: “give the robot a crown and shades, pick the Puck voice, and have it say good morning.”
          </p>
          {session
            ? host.renderConnect()
            : <p><a href={host.signInHref} className="btn">Sign in to connect an assistant</a></p>}
        </main>
      )}

      {page === 'about' && (
        <main className="rs-page">
          <h1 style={{ fontFamily: 'var(--font-display)', marginTop: 0 }}>About this example</h1>
          <p className="dim" style={{ maxWidth: 680 }}>
            Robot Studio was built through the Claudia ledger (design, develop, test, demo) and is made from shared Claudia components rather than new ones.
          </p>
          <div className="rs-grid">
            <Card title="ClaudiaTree" description="The left pane: categories open to options, keyboard operable, selection applied to the robot." badges={<span className="rs-pill">shared</span>} fallback={<span style={{ fontSize: '2rem' }}>🌳</span>} />
            <Card title="ConnectAIPanel" description="Settings: one panel to connect Claude and other assistants to the MCP endpoint, list and revoke connections." badges={<span className="rs-pill">shared</span>} fallback={<span style={{ fontSize: '2rem' }}>🔌</span>} />
            <Card title="ClaudiaCard" description="These cards. Each shared component keeps one copy, so a fix lands everywhere." badges={<span className="rs-pill">shared</span>} fallback={<span style={{ fontSize: '2rem' }}>🃏</span>} />
            <Card title="Ledger" description="The design, develop, test and demo tasks that produced this page are on the example project's ledger." onClick={() => { window.location.href = host.ledgerHref; }} fallback={<span style={{ fontSize: '2rem' }}>📋</span>} />
          </div>
        </main>
      )}
    </div>
  );
}
