/**
 * What the hosting app (Claudia) hands Robot Studio. The package owns the robot, its catalogue, speech and state; the
 * host owns sign-in, the Supabase client and the shared Claudia components, so the package never imports Claudia code.
 */
import type { ComponentType, ReactNode } from 'react';
import type { SupabaseClient } from '@supabase/supabase-js';

export interface TreeNode {
  id: string;
  label: ReactNode;
  indicators?: ReactNode;
  children?: TreeNode[];
  disabled?: boolean;
  title?: string;
}

export interface RobotStudioHost {
  supabase: SupabaseClient;
  supabaseUrl: string;
  publishableKey: string;
  /** The Robot Studio MCP endpoint shown on the Settings page. */
  mcpUrl: string;
  /** Link to the project's ledger, and where "Sign in" goes. */
  ledgerHref: string;
  signInHref: string;
  Tree: ComponentType<{ nodes: TreeNode[]; expanded: Set<string>; onToggle: (id: string) => void; onSelect?: (id: string) => void }>;
  Card: ComponentType<{ title: string; description?: string; badges?: ReactNode; fallback?: ReactNode; onClick?: () => void }>;
  /** The Settings page's "connect an assistant" panel, rendered by the host (needs its own RPCs). */
  renderConnect: () => ReactNode;
}
