import { useCallback, useEffect, useRef, useState } from 'react';
import type { Session, SupabaseClient } from '@supabase/supabase-js';
import { DEFAULT_ROBOT, sanitise, type RobotAttributes } from './options';

/**
 * The robot's attributes, saved per signed-in user in claudia_example_robot and kept live over Realtime, so the MCP
 * tools (robot_set, robot_say) change this page from a chat. A bumped say_seq means "speak say_text now".
 * Signed out, the robot still works but only in this tab: nothing is saved and no chat can reach it.
 */
export function useRobotState(supabase: SupabaseClient, session: Session | null, onSay: (text: string, voice: string) => void) {
  const [attrs, setAttrs] = useState<RobotAttributes>(DEFAULT_ROBOT);
  const [text, setText] = useState('Hello! I am a robot built from the shared Claudia component library.');
  const [ready, setReady] = useState(false);
  const seqRef = useRef<number | null>(null);
  const attrsRef = useRef(attrs);
  attrsRef.current = attrs;
  const onSayRef = useRef(onSay);
  onSayRef.current = onSay;
  const saveTimer = useRef<number | null>(null);
  const userId = session?.user.id ?? null;

  useEffect(() => {
    if (!userId) { setReady(true); seqRef.current = null; return; }
    let stopped = false;
    const apply = (row: { attributes?: unknown; say_seq?: number; say_text?: string }) => {
      const next = { ...DEFAULT_ROBOT, ...sanitise(row.attributes) };
      if (JSON.stringify(next) !== JSON.stringify(attrsRef.current)) setAttrs(next);
      const seq = row.say_seq ?? 0;
      if (seqRef.current !== null && seq > seqRef.current && row.say_text) {
        setText(row.say_text);
        onSayRef.current(row.say_text, next.voice);
      }
      seqRef.current = seq;
    };
    supabase.from('claudia_example_robot').select('attributes, say_seq, say_text').eq('user_id', userId).maybeSingle()
      .then(({ data }) => { if (!stopped) { if (data) apply(data); else seqRef.current = 0; setReady(true); } });
    const channel = supabase.channel(`robot:${userId}`)
      .on('postgres_changes', { event: '*', schema: 'public', table: 'claudia_example_robot', filter: `user_id=eq.${userId}` },
        (payload) => { if (payload.new && 'attributes' in payload.new) apply(payload.new as never); })
      .subscribe();
    return () => { stopped = true; supabase.removeChannel(channel); };
  }, [supabase, userId]);

  const change = useCallback((patch: Partial<RobotAttributes>) => {
    const next = { ...attrsRef.current, ...patch };
    setAttrs(next);
    if (!userId) return;
    if (saveTimer.current) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => {
      supabase.rpc('claudia_example_robot_save', { p_attributes: next }).then(() => undefined);
    }, 350);
  }, [supabase, userId]);

  return { attrs, change, text, setText, ready, saved: !!userId };
}
