import { COLOURS, type RobotAttributes } from './options';

/**
 * The robot, drawn as SVG so every attribute is a visible change and nothing needs an image file.
 * mouth is 0 (closed) to 1 (wide open); the Studio drives it from the audio level while speaking.
 */
export default function Robot({ attrs, mouth, speaking }: { attrs: RobotAttributes; mouth: number; speaking: boolean }) {
  const body = COLOURS[attrs.colour] ?? COLOURS.teal;
  const dark = 'rgba(0,0,0,.35)';
  const mouthH = 4 + mouth * 26;
  return (
    <svg viewBox="0 0 300 380" role="img" aria-label={`Robot: ${attrs.colour}, ${attrs.hair} hair, ${attrs.glasses} glasses, ${attrs.hat} hat`}
      style={{ width: '100%', maxWidth: 360, height: 'auto', overflow: 'visible' }}>
      <ellipse cx="150" cy="366" rx="86" ry="9" fill="rgba(0,0,0,.35)" />
      {/* antenna */}
      <line x1="150" y1="58" x2="150" y2="30" stroke={dark} strokeWidth="6" strokeLinecap="round" />
      <circle cx="150" cy="26" r="9" fill={speaking ? '#F6D860' : '#8B93A1'}>
        {speaking && <animate attributeName="opacity" values="1;.35;1" dur=".7s" repeatCount="indefinite" />}
      </circle>
      {/* body */}
      <rect x="92" y="236" width="116" height="112" rx="22" fill={body} />
      <rect x="92" y="236" width="116" height="112" rx="22" fill="none" stroke={dark} strokeWidth="4" />
      <circle cx="128" cy="292" r="8" fill={dark} /><circle cx="172" cy="292" r="8" fill="#F6D860" />
      <rect x="56" y="248" width="30" height="76" rx="15" fill={body} stroke={dark} strokeWidth="4" />
      <rect x="214" y="248" width="30" height="76" rx="15" fill={body} stroke={dark} strokeWidth="4" />
      <rect x="132" y="218" width="36" height="24" rx="6" fill={dark} />
      {/* head */}
      <rect x="64" y="56" width="172" height="166" rx="34" fill={body} stroke={dark} strokeWidth="4" />
      {/* hair, behind the hat */}
      {attrs.hair === 'tuft' && <path d="M130 58 C128 36 150 30 154 46 C162 34 176 44 170 58 Z" fill="#2A2F3A" />}
      {attrs.hair === 'mohawk' && <path d="M138 58 L142 20 L152 50 L160 14 L166 52 L174 24 L176 58 Z" fill="#E0765B" />}
      {attrs.hair === 'spikes' && <path d="M84 62 L92 30 L110 58 L126 24 L142 58 L158 24 L176 58 L192 30 L208 58 L216 32 L220 66 Z" fill="#2A2F3A" />}
      {attrs.hair === 'curl' && <g fill="none" stroke="#2A2F3A" strokeWidth="8" strokeLinecap="round"><path d="M100 60 C90 40 118 34 118 52 C118 62 106 62 108 52" /><path d="M150 56 C140 34 172 28 172 48 C172 60 156 60 160 48" /><path d="M200 60 C190 40 218 34 218 52" /></g>}
      {/* eyes */}
      <circle cx="118" cy="128" r="17" fill="#F7F5EE" /><circle cx="182" cy="128" r="17" fill="#F7F5EE" />
      <circle cx="120" cy="130" r="8" fill="#1B1F26" /><circle cx="180" cy="130" r="8" fill="#1B1F26" />
      {/* glasses */}
      {attrs.glasses === 'round' && <g fill="none" stroke="#1B1F26" strokeWidth="5"><circle cx="118" cy="128" r="24" /><circle cx="182" cy="128" r="24" /><line x1="142" y1="128" x2="158" y2="128" /></g>}
      {attrs.glasses === 'square' && <g fill="none" stroke="#1B1F26" strokeWidth="5"><rect x="90" y="106" width="52" height="42" rx="6" /><rect x="158" y="106" width="52" height="42" rx="6" /><line x1="142" y1="124" x2="158" y2="124" /></g>}
      {attrs.glasses === 'shades' && <g><rect x="88" y="108" width="54" height="38" rx="10" fill="#14171C" /><rect x="158" y="108" width="54" height="38" rx="10" fill="#14171C" /><line x1="142" y1="122" x2="158" y2="122" stroke="#14171C" strokeWidth="5" /></g>}
      {/* mouth: height follows the audio level */}
      <rect x="116" y={186 - mouthH / 2} width="68" height={mouthH} rx={Math.min(14, mouthH / 2)} fill="#1B1F26" />
      {mouth > 0.25 && <rect x="126" y={186 - mouthH / 2 + 2} width="48" height={Math.min(7, mouthH / 3)} rx="3" fill="#F7F5EE" />}
      {/* neckwear */}
      {attrs.neckwear === 'bowtie' && <g fill="#C0533E" stroke={dark} strokeWidth="3"><path d="M150 244 L116 226 L116 262 Z" /><path d="M150 244 L184 226 L184 262 Z" /><circle cx="150" cy="244" r="8" /></g>}
      {attrs.neckwear === 'scarf' && <g><rect x="106" y="226" width="88" height="20" rx="10" fill="#E0765B" stroke={dark} strokeWidth="3" /><rect x="168" y="238" width="20" height="52" rx="8" fill="#E0765B" stroke={dark} strokeWidth="3" /></g>}
      {/* hats */}
      {attrs.hat === 'cap' && <g><path d="M70 78 C72 30 228 30 230 78 Z" fill="#3A4252" stroke={dark} strokeWidth="4" /><rect x="190" y="68" width="62" height="14" rx="7" fill="#3A4252" stroke={dark} strokeWidth="4" /></g>}
      {attrs.hat === 'tophat' && <g><rect x="106" y="-4" width="88" height="70" rx="6" fill="#1B1F26" stroke={dark} strokeWidth="3" /><rect x="84" y="60" width="132" height="14" rx="7" fill="#1B1F26" stroke={dark} strokeWidth="3" /><rect x="106" y="40" width="88" height="12" fill="#C0533E" /></g>}
      {attrs.hat === 'beanie' && <g><path d="M72 80 C70 20 230 20 228 80 Z" fill="#8B7BD8" stroke={dark} strokeWidth="4" /><rect x="68" y="72" width="164" height="16" rx="8" fill="#6E5FC0" /><circle cx="150" cy="22" r="11" fill="#F7F5EE" /></g>}
      {attrs.hat === 'crown' && <path d="M96 70 L96 24 L122 48 L150 12 L178 48 L204 24 L204 70 Z" fill="#C9A227" stroke={dark} strokeWidth="4" strokeLinejoin="round" />}
    </svg>
  );
}
