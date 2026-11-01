import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { createClient } from '@supabase/supabase-js'
import { Activity, Bell, Bot, BriefcaseBusiness, CreditCard, Database, FileCheck2, LayoutDashboard, LogOut, Menu, Search, Settings, ShieldCheck, Users, X } from 'lucide-react'
import './styles.css'

const nav = [
  ['Dashboard', LayoutDashboard], ['User Management', Users], ['Subscriptions', CreditCard],
  ['Payments', CreditCard], ['Notifications', Bell], ['Reports & Analytics', Activity],
  ['Business Management', BriefcaseBusiness], ['AI Usage Monitoring', Bot], ['Audit Logs', FileCheck2],
  ['Privacy & Compliance', ShieldCheck], ['Settings', Settings],
]

const supabase = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_ANON_KEY)

const emptyDashboard = { source: 'reconnecting', metrics: { users: { total: 0, available: false }, subscriptions: { free: 0, plus: 0, premium: 0, active: 0, available: false }, payments: { total: 0, by_status: {}, verified: 0, available: false }, notifications: { total: 0, read: 0, unread: 0, available: false }, business: { available: false }, ai: { available: false }, audit_logs: { available: false }, privacy: { available: false } }, recent_activity: [] }

async function loadDashboard(accessToken) {
  let lastError
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch('/api/v1/admin/dashboard', { headers: { Authorization: `Bearer ${accessToken}` } })
      if (response.ok) return response.json()
      lastError = new Error(`dashboard request returned ${response.status}`)
    } catch (error) { lastError = error }
    await new Promise(resolve => window.setTimeout(resolve, 800 * (attempt + 1)))
  }
  throw lastError || new Error('dashboard request failed')
}

function Metric({ label, value, note, unavailable }) {
  return <article className="metric card"><p>{label}</p><strong>{unavailable ? '—' : value}</strong><small>{unavailable ? 'Not available in current schema' : note}</small></article>
}

function App() {
  const [session, setSession] = useState(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [authLoading, setAuthLoading] = useState(true)
  const [authError, setAuthError] = useState('')
  const [resetSent, setResetSent] = useState(false)
  const [setupMode, setSetupMode] = useState(false)
  const [setupLoading, setSetupLoading] = useState(false)
  const [confirmation, setConfirmation] = useState('')
  const [data, setData] = useState(null)
  const [moduleRows, setModuleRows] = useState([])
  const [menuOpen, setMenuOpen] = useState(false)
  const [active, setActive] = useState('Dashboard')

  useEffect(() => { supabase.auth.getSession().then(({ data: { session: current } }) => { setSession(current); setAuthLoading(false) }); const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, current) => setSession(current)); return () => subscription.unsubscribe() }, [])
  useEffect(() => { if (setupMode) { setAuthError(''); setResetSent(false) } }, [setupMode])
  useEffect(() => {
    if (!session?.access_token) return undefined
    let activeRequest = true
    const refresh = () => loadDashboard(session.access_token).then(result => { if (activeRequest) setData(result) }).catch(() => { if (activeRequest) setData(current => current || emptyDashboard) })
    refresh()
    const retry = window.setInterval(refresh, 10000)
    return () => { activeRequest = false; window.clearInterval(retry) }
  }, [session])
  useEffect(() => {
    const path = { 'User Management': '/api/v1/admin/users', 'Subscriptions': '/api/v1/admin/subscriptions', 'Payments': '/api/v1/admin/payments-live', 'Notifications': '/api/v1/admin/notifications', 'Business Management': '/api/v1/admin/business', 'AI Usage Monitoring': '/api/v1/admin/ai-usage' }[active]
    if (!session?.access_token || !path) return
    fetch(path, { headers: { Authorization: `Bearer ${session.access_token}` } }).then(r => r.ok ? r.json() : []).then(setModuleRows).catch(() => setModuleRows([]))
  }, [active, session])
  useEffect(() => {
    if (!session?.access_token) return undefined
    const refresh = () => loadDashboard(session.access_token).then(setData).catch(() => setData(current => current || emptyDashboard))
    const tables = ['users', 'user_subscriptions', 'payments', 'user_notifications', 'business_profiles', 'swot_analyses', 'ai_conversations', 'ai_messages', 'finance_messages']
    let channel = supabase.channel('admin-live-dashboard')
    tables.forEach(table => { channel = channel.on('postgres_changes', { event: '*', schema: 'public', table }, refresh) })
    channel.subscribe()
    const fallback = window.setInterval(refresh, 30000)
    return () => { window.clearInterval(fallback); supabase.removeChannel(channel) }
  }, [session])

  if (authLoading) return <main className="auth-shell"><section className="auth-card card"><p className="muted">Checking secure admin session…</p></section></main>
  if (!session) return <main className="auth-shell"><section className="auth-card card"><div className="brand-mark">T</div><p className="eyebrow">TECHSPOT INFOTECH LLP</p><h1>{setupMode ? 'Set Admin Password' : 'Admin workspace'}</h1><p className="muted">{setupMode ? 'Create your password, then sign in.' : 'Sign in with your authorized Supabase administrator account.'}</p>{setupMode ? <form onSubmit={async e => { e.preventDefault(); if (setupLoading) return; setAuthError(''); setSetupLoading(true); const controller = new AbortController(); const timeout = window.setTimeout(() => controller.abort(), 15000); try { const r = await fetch('/api/v1/admin/setup-password', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password,confirmation}),signal:controller.signal}); const body = await r.json(); if (!r.ok) setAuthError(body.detail || 'Password setup failed'); else { setSetupMode(false); setPassword(''); setConfirmation(''); setResetSent(true) } } catch (error) { setAuthError(error.name === 'AbortError' ? 'Password setup timed out. Check the backend connection and try again.' : 'Password setup could not be completed. Try again.') } finally { window.clearTimeout(timeout); setSetupLoading(false) } }}><label>Email address<input type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label><label className="field-gap">New password<input type="password" value={password} onChange={e => setPassword(e.target.value)} minLength="8" required /></label><label className="field-gap">Confirm password<input type="password" value={confirmation} onChange={e => setConfirmation(e.target.value)} minLength="8" required /></label>{authError && <div className="error-banner auth-error">{authError}</div>}<button type="submit" className="primary" disabled={setupLoading}>{setupLoading ? 'Setting password…' : 'Set password'}</button><button type="button" className="forgot" onClick={() => setSetupMode(false)} disabled={setupLoading}>Back to login</button></form> : <><form onSubmit={async e => { e.preventDefault(); setAuthError(''); const { error: signInError } = await supabase.auth.signInWithPassword({ email, password }); if (signInError) setAuthError(signInError.message) }}><label>Email address<input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="admin email" required /></label><label className="field-gap">Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="password" required /></label>{authError && <div className="error-banner auth-error">{authError}</div>}{resetSent && <div className="success-banner">Password set successfully. Sign in now.</div>}<button className="primary">Sign in securely</button></form><button className="forgot" onClick={() => setSetupMode(true)}>Set Admin Password</button><button className="forgot" onClick={async () => { setAuthError(''); const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, { redirectTo: window.location.origin }); if (resetError) setAuthError(resetError.message); else setResetSent(true) }}>Forgot password?</button></>}<p className="hint">Access is granted only to active administrators assigned in Supabase.</p></section></main>

  const m = data?.metrics || {}
  return <div className="app-shell">
    <aside className={menuOpen ? 'sidebar open' : 'sidebar'}><div className="logo"><span className="brand-mark">T</span><span>Techspot <small>ADMIN</small></span><button className="icon mobile-close" onClick={() => setMenuOpen(false)}><X size={18} /></button></div><nav>{nav.map(([label, Icon]) => <button key={label} className={active === label ? 'nav-item active' : 'nav-item'} onClick={() => { setActive(label); setMenuOpen(false) }}><Icon size={17} /><span>{label}</span></button>)}</nav><div className="sidebar-foot"><div className="status-dot" /> Connected to current database schema</div></aside>
    <section className="content"><header className="topbar"><button className="icon mobile-menu" onClick={() => setMenuOpen(true)}><Menu size={20} /></button><div className="crumb"><span>Workspace</span><b>/</b><strong>{active}</strong></div><div className="top-actions"><div className="search"><Search size={16} /><input placeholder="Search" /></div><button className="icon"><Bell size={18} /></button><div className="avatar">{session.user.email?.[0]?.toUpperCase() || 'A'}</div><button className="logout" onClick={() => supabase.auth.signOut()}><LogOut size={15} /> Log out</button></div></header>
    <main className="main"><div className="page-heading"><div><p className="eyebrow">OVERVIEW</p><h1>{active}</h1><p className="muted">Operational visibility from the records currently available to this deployment.</p></div><span className="schema-badge"><Database size={14} /> Live schema mode</span></div>
      {active !== 'Dashboard' ? <ModulePage active={active} rows={moduleRows} /> : <>
      {data?.source === 'reconnecting' && <div className="success-banner">Connecting to live database data…</div>}
      <div className="metric-grid"><Metric label="Registered users" value={m.users?.total} unavailable={!m.users?.available} /><Metric label="Active subscriptions" value={m.subscriptions?.active ?? 0} note="Current records" /><Metric label="Verified payments" value={m.payments?.verified ?? 0} note="Success / verified statuses" /><Metric label="Unread notifications" value={m.notifications?.unread ?? 0} note="Current records" /></div>
      <div className="section-row"><section className="card panel"><div className="panel-head"><div><p className="eyebrow">SUBSCRIPTIONS</p><h2>Plan distribution</h2></div><span className="pill">Current records</span></div><div className="bars"><Bar label="Free" value={m.subscriptions?.free ?? 0} max={Math.max(1, m.subscriptions?.free ?? 0, m.subscriptions?.plus ?? 0, m.subscriptions?.premium ?? 0)} color="blue" /><Bar label="Plus" value={m.subscriptions?.plus ?? 0} max={Math.max(1, m.subscriptions?.free ?? 0, m.subscriptions?.plus ?? 0, m.subscriptions?.premium ?? 0)} color="violet" /><Bar label="Premium" value={m.subscriptions?.premium ?? 0} max={Math.max(1, m.subscriptions?.free ?? 0, m.subscriptions?.plus ?? 0, m.subscriptions?.premium ?? 0)} color="green" /></div></section><section className="card panel"><div className="panel-head"><div><p className="eyebrow">PAYMENTS</p><h2>Payment status</h2></div><span className="pill">Read-only</span></div><div className="status-list">{Object.entries(m.payments?.by_status || {}).filter(([,v]) => v > 0).map(([k,v]) => <div key={k}><span>{k}</span><b>{v}</b></div>)}{!Object.values(m.payments?.by_status || {}).some(Boolean) && <p className="muted">No payment records available.</p>}</div></section></div>
      <section className="card panel"><div className="panel-head"><div><p className="eyebrow">DATA COVERAGE</p><h2>Connected modules</h2></div><span className="pill">Accuracy first</span></div><div className="coverage-grid">{[['Subscriptions',m.subscriptions?.available],['Payments',m.payments?.available],['Notifications',m.notifications?.available],['Users',m.users?.available],['Business',m.business?.available],['AI usage',m.ai?.available],['Audit logs',m.audit_logs?.available],['Privacy',m.privacy?.available]].map(([label,ok]) => <div key={label} className={ok ? 'coverage available' : 'coverage'}><span className="coverage-dot" /><div><b>{label}</b><small>{ok ? 'Available' : 'Schema required'}</small></div></div>)}</div></section>
      </>}
    </main></section>
  </div>
}

function Bar({ label, value, max, color }) { return <div className="bar-row"><span>{label}</span><div className="bar-track"><i className={color} style={{ width: `${Math.round((value / max) * 100)}%` }} /></div><b>{value}</b></div> }

function ModulePage({ active, rows }) {
  const columns = {
    'User Management': [['name', 'Name'], ['phone_number', 'Phone'], ['city', 'City'], ['plan', 'Plan'], ['account_status', 'Status'], ['created_at', 'Registered']],
    'Subscriptions': [['user_id', 'User ID'], ['tier', 'Plan'], ['status', 'Status'], ['payment_status', 'Payment'], ['start_date', 'Start date'], ['end_date', 'End date']],
    'Payments': [['user_name', 'User'], ['plan', 'Plan'], ['amount', 'Amount'], ['currency', 'Currency'], ['payment_gateway', 'Gateway'], ['payment_status', 'Status'], ['payment_date', 'Date']],
    'Notifications': [['user_id', 'User ID'], ['title', 'Title'], ['notification_type', 'Type'], ['read', 'Read'], ['sent_at', 'Sent']],
    'Business Management': [['business_name', 'Business'], ['industry_name', 'Industry'], ['location', 'Location'], ['business_stage', 'Stage'], ['available_capital', 'Capital'], ['created_at', 'Created']],
    'AI Usage Monitoring': [['conversation_type', 'Type'], ['status', 'Status'], ['conversations', 'Conversations'], ['first_request', 'First request'], ['last_request', 'Last request']],
  }[active]
  if (!columns) return <section className="empty card"><div className="empty-icon"><Database size={22} /></div><h2>{active}</h2><p>This module requires dedicated Supabase tables that are not present in the current schema. No fabricated records are shown.</p></section>
  return <section className="card panel module-table"><div className="panel-head"><div><p className="eyebrow">LIVE SUPABASE DATA</p><h2>{active}</h2></div><span className="pill">{rows.length} records</span></div>{rows.length === 0 ? <p className="muted">No records available in the connected database.</p> : <div className="table-wrap"><table><thead><tr>{columns.map(([, label]) => <th key={label}>{label}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={row.id || i}>{columns.map(([key]) => <td key={key}>{formatValue(row[key])}</td>)}</tr>)}</tbody></table></div>}</section>
}

function formatValue(value) { if (value === null || value === undefined || value === '') return '—'; if (typeof value === 'boolean') return value ? 'Yes' : 'No'; if (typeof value === 'object') return JSON.stringify(value); return String(value).replace('T', ' ').replace('Z', '') }

createRoot(document.getElementById('root')).render(<App />)
