'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, Activity, GitPullRequest, Mail, MessageSquare, 
  RefreshCw, Layers, Terminal, ChevronRight, 
  ArrowUpRight, Zap, Settings, FileText, Key, Plus, 
  Send, Sparkles, Inbox, Edit3, Shield, CheckCircle2,
  Cpu, ArrowRight, CornerDownLeft, Sparkle, Flame, Search,
  Radio, Clock, Check, AlertCircle, Copy, HelpCircle,
  ExternalLink, Sliders, Play, Server, Database, Unlink, Trash2, Building2
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL 
  ? `${process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '')}/api/v1`
  : (typeof window !== 'undefined' && window.location.hostname === 'localhost' && window.location.port === '3000'
      ? 'http://localhost:8000/api/v1' 
      : '/api/v1');


export default function StartupOpsDashboard() {
  const [activeTab, setActiveTab] = useState<'command' | 'emails' | 'today' | 'integrations' | 'settings'>('command');
  const [loading, setLoading] = useState(false);
  const [workspace, setWorkspace] = useState({ id: 'default', name: 'StartupOps Core', slug: 'startup-core' });
  
  // Settings & Gemini Key State
  const [hasGeminiKey, setHasGeminiKey] = useState(false);
  const [geminiApiKeyInput, setGeminiApiKeyInput] = useState('');
  const [showKeyModal, setShowKeyModal] = useState(false);

  // Connect Modal State
  const [connectModalProvider, setConnectModalProvider] = useState<string | null>(null);
  const [tokenInput, setTokenInput] = useState('');
  const [accountNameInput, setAccountNameInput] = useState('');
  const [crmType, setCrmType] = useState('hubspot');
  const [crmEndpoint, setCrmEndpoint] = useState('');

  // Interactive Email Reply State
  const [emails, setEmails] = useState<any[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<any>(null);
  const [replyTo, setReplyTo] = useState('');
  const [replySubject, setReplySubject] = useState('');
  const [replyBody, setReplyBody] = useState('');
  const [isDraftingAI, setIsDraftingAI] = useState(false);
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [emailSearch, setEmailSearch] = useState('');
  const [selectedTone, setSelectedTone] = useState('professional');

  // Agent Chat State
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; text: string; intent?: string; plan?: any[]; timestamp?: string }>>([
    {
      role: 'assistant',
      text: "⚡ **StartupOps Autonomous Operations Center Online**\n\nI am continuously connected to your live operational streams (**GitHub**, **Gmail**, **Slack**, **Universal CRM** [HubSpot, Salesforce, Pipedrive, Zoho, Custom]). You can instruct me to audit repositories, triage customer support emails, or generate daily standup briefings.",
      timestamp: 'Active Now'
    }
  ]);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Data states
  const [integrations, setIntegrations] = useState<any[]>([]);
  const [notification, setNotification] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Auto-fetch data
  const refreshData = async () => {
    try {
      // Fetch Settings
      const setRes = await fetch(`${API_BASE}/settings`);
      if (setRes.ok) {
        const setData = await setRes.json();
        setHasGeminiKey(setData.has_gemini_key);
      }

      // Fetch Integrations
      const intRes = await fetch(`${API_BASE}/integrations`, { headers: { 'X-Workspace-Id': workspace.id } });
      if (intRes.ok) setIntegrations(await intRes.json());

      // Fetch Emails
      const emRes = await fetch(`${API_BASE}/emails`, { headers: { 'X-Workspace-Id': workspace.id } });
      if (emRes.ok) {
        const emData = await emRes.json();
        setEmails(emData);
        if (emData.length > 0 && !selectedEmail) {
          setSelectedEmail(emData[0]);
          setReplyTo(emData[0].sender);
          setReplySubject(emData[0].subject.startsWith('Re:') ? emData[0].subject : `Re: ${emData[0].subject}`);
        }
      }
    } catch (e) {
      console.log('Backend offline or initializing:', e);
    }
  };

  useEffect(() => {
    refreshData();
  }, [workspace.id]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const showToast = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4500);
  };

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Save Gemini Key
  const handleSaveGeminiKey = async () => {
    if (!geminiApiKeyInput.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ google_ai_studio_api_key: geminiApiKeyInput.trim() })
      });
      if (res.ok) {
        showToast('✅ Google AI Studio API Key saved successfully!');
        setHasGeminiKey(true);
        setShowKeyModal(false);
        setGeminiApiKeyInput('');
        await refreshData();
      }
    } catch (e) {
      showToast('Failed to save API key.');
    }
  };

  // Save Platform Integration Credentials
  const handleSaveIntegration = async () => {
    if (!connectModalProvider || !tokenInput.trim()) return;
    try {
      const creds: any = { token: tokenInput.trim() };
      if (connectModalProvider === 'hubspot' || connectModalProvider === 'crm') {
        creds.crm_type = crmType;
        if (crmEndpoint.trim()) creds.endpoint_url = crmEndpoint.trim();
      }
      const res = await fetch(`${API_BASE}/integrations/${connectModalProvider}/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-Id': workspace.id
        },
        body: JSON.stringify({
          provider: connectModalProvider,
          account_name: accountNameInput.trim() || `${crmType || connectModalProvider}-account`,
          credentials: creds,
          scopes: ['read', 'write']
        })
      });
      const data = await res.json();
      if (res.ok) {
        const crmLabel = (connectModalProvider === 'hubspot' || connectModalProvider === 'crm') ? crmType.toUpperCase() : connectModalProvider.toUpperCase();
        showToast(`✅ ${crmLabel} CRM connected successfully!`);
        setConnectModalProvider(null);
        setTokenInput('');
        setAccountNameInput('');
        setCrmEndpoint('');
        await refreshData();
      } else {
        showToast(`❌ ${data.detail || 'Connection failed.'}`);
      }
    } catch (e) {
      showToast('Error connecting integration.');
    }
  };


  // Trigger Live Sync
  const handleSyncProvider = async (provider: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/sync/${provider}`, {
        method: 'POST',
        headers: { 'X-Workspace-Id': workspace.id }
      });
      const data = await res.json();
      if (res.ok) {
        showToast(`🔄 Synced ${data.items_fetched || 0} live items from ${provider.toUpperCase()}`);
        await refreshData();
      } else {
        showToast(`❌ ${data.detail || 'Sync failed.'}`);
      }
    } catch (e) {
      showToast('Sync error.');
    } finally {
      setLoading(false);
    }
  };

  // Disconnect Platform Integration
  const handleDisconnectIntegration = async (provider: string) => {
    if (!confirm(`Are you sure you want to disconnect ${provider.toUpperCase()}? This will revoke access and wipe stored credentials and all platform data.`)) {
      return;
    }
    
    const provLower = provider.toLowerCase();
    // Optimistic UI update
    setIntegrations(prev => prev.filter(i => i.provider !== provLower));
    
    if (provLower === 'gmail' || provLower === 'google') {
      setEmails([]);
      setSelectedEmail(null);
      setReplyBody('');
      setReplySubject('');
      setReplyTo('');
    }
    
    try {
      const res = await fetch(`${API_BASE}/integrations/${provider}/disconnect`, {
        method: 'POST',
        headers: { 'X-Workspace-Id': workspace.id }
      });
      const data = await res.json();
      if (res.ok) {
        showToast(`🔌 ${data.message || `${provider.toUpperCase()} disconnected and data wiped.`}`);
      } else {
        showToast(`❌ ${data.detail || 'Failed to disconnect.'}`);
      }
    } catch (e) {
      showToast(`🔌 ${provider.toUpperCase()} disconnected.`);
    } finally {
      await refreshData();
    }
  };

  // Generate AI Draft Reply for Email
  const handleGenerateAIDraft = async (emailItem: any, tone: string = 'professional') => {
    setIsDraftingAI(true);
    setSelectedTone(tone);
    try {
      const res = await fetch(`${API_BASE}/emails/draft-reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_id: emailItem.id,
          sender: emailItem.sender,
          subject: emailItem.subject,
          body: emailItem.body || emailItem.snippet,
          tone: tone
        })
      });
      if (res.ok) {
        const data = await res.json();
        setReplyBody(data.draft_body || '');
        setReplySubject(data.draft_subject || (emailItem.subject.startsWith('Re:') ? emailItem.subject : `Re: ${emailItem.subject}`));
        showToast(`✨ Generated ${tone.toUpperCase()} reply using Gemini 2.5`);
      } else {
        showToast('Failed to generate draft. Please check Gemini API Key.');
      }
    } catch (e) {
      showToast('AI draft generation error.');
    } finally {
      setIsDraftingAI(false);
    }
  };

  // Send Email Reply directly
  const handleSendEmailReply = async () => {
    if (!replyTo || !replyBody.trim()) {
      showToast('Please provide recipient and reply body.');
      return;
    }
    setIsSendingEmail(true);
    try {
      const res = await fetch(`${API_BASE}/emails/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-Id': workspace.id
        },
        body: JSON.stringify({
          recipient: replyTo,
          subject: replySubject,
          body: replyBody,
          in_reply_to: selectedEmail?.id
        })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(`🚀 Email sent successfully to ${replyTo}!`);
        setReplyBody('');
        await refreshData();
      } else {
        showToast(`⚠️ ${data.message || 'Send simulated / requires verified SMTP.'}`);
      }
    } catch (e) {
      showToast('Network error while dispatching email.');
    } finally {
      setIsSendingEmail(false);
    }
  };

  // Dispatch Copilot Command
  const handleSendCommand = async (cmdText?: string) => {
    const textToSend = cmdText || query;
    if (!textToSend.trim() || loading) return;

    const userMsg = {
      role: 'user' as const,
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!cmdText) setQuery('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/agent/command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-Id': workspace.id
        },
        body: JSON.stringify({ command: textToSend })
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            text: data.final_response || 'Task executed successfully.',
            intent: data.intent,
            plan: data.plan,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
        await refreshData();
      } else {
        setMessages(prev => [...prev, { role: 'assistant', text: '⚠️ Failed to contact operations hub. Please ensure your Gemini API key is valid.' }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: '⚠️ Network error communicating with FastAPI backend.' }]);
    } finally {
      setLoading(false);
    }
  };

  // Filtered Emails
  const filteredEmails = emails.filter(em => 
    !emailSearch || 
    em.sender.toLowerCase().includes(emailSearch.toLowerCase()) || 
    em.subject.toLowerCase().includes(emailSearch.toLowerCase()) ||
    em.snippet.toLowerCase().includes(emailSearch.toLowerCase())
  );

  return (
    <div className="flex h-screen w-full bg-[#f0f4f9] text-slate-900 overflow-hidden font-sans select-none antialiased text-[15.5px]">
      
      {/* Toast Notification */}
      {notification && (
        <div className="fixed bottom-7 right-7 z-50 bg-white border-2 border-blue-500 text-slate-900 px-6 py-4 rounded-2xl shadow-2xl backdrop-blur-2xl flex items-center space-x-3.5 transition-all animate-bounce">
          <div className="p-1.5 rounded-full bg-blue-100 text-blue-600">
            <Zap className="w-5 h-5 shrink-0" />
          </div>
          <span className="text-sm font-bold text-slate-900">{notification}</span>
        </div>
      )}

      {/* Gemini API Key Modal */}
      {showKeyModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border-2 border-blue-200 rounded-3xl p-8 max-w-lg w-full shadow-2xl space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3.5">
                <div className="p-3 rounded-2xl bg-blue-50 text-blue-600 border border-blue-200">
                  <Key className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-extrabold text-lg text-slate-900">Google AI Studio Gemini Key</h3>
                  <p className="text-xs font-semibold text-slate-500">Powers multi-agent reasoning & automated replies</p>
                </div>
              </div>
              <button onClick={() => setShowKeyModal(false)} className="text-slate-400 hover:text-slate-700 text-lg p-1 cursor-pointer font-bold">✕</button>
            </div>
            
            <p className="text-sm text-slate-600 leading-relaxed bg-blue-50/70 p-4 rounded-2xl border border-blue-100 font-medium">
              Get your free API key at <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-blue-600 underline font-bold hover:text-blue-800">aistudio.google.com</a> to enable autonomous operations.
            </p>

            <div className="space-y-2">
              <label className="text-xs font-extrabold text-slate-700 block uppercase tracking-wider font-mono">API Key</label>
              <input
                type="password"
                value={geminiApiKeyInput}
                onChange={(e) => setGeminiApiKeyInput(e.target.value)}
                placeholder="AIzaSy..."
                className="w-full bg-slate-50 border-2 border-slate-200 rounded-2xl px-4 py-3.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 font-mono font-semibold"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => setShowKeyModal(false)}
                className="px-5 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-bold transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveGeminiKey}
                disabled={!geminiApiKeyInput.trim()}
                className="px-7 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 disabled:opacity-50 text-white rounded-xl text-sm font-extrabold shadow-lg shadow-blue-500/25 transition-all cursor-pointer"
              >
                Save Key
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Provider Connect / Edit Modal */}
      {connectModalProvider && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border-2 border-blue-200 rounded-3xl p-8 max-w-lg w-full shadow-2xl space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3.5">
                <div className="p-3 rounded-2xl bg-blue-50 text-blue-600 border border-blue-200">
                  <Layers className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-extrabold text-lg text-slate-900 capitalize">
                    {integrations.some(i => i.provider === connectModalProvider) ? 'Edit Connection' : 'Connect'} {connectModalProvider === 'hubspot' || connectModalProvider === 'crm' ? 'Universal CRM' : connectModalProvider}
                  </h3>
                  <p className="text-xs font-semibold text-slate-500">Live operational sync stream</p>
                </div>
              </div>
              <button onClick={() => setConnectModalProvider(null)} className="text-slate-400 hover:text-slate-700 text-lg p-1 cursor-pointer font-bold">✕</button>
            </div>

            {/* CRM Provider Selector when CRM is selected */}
            {(connectModalProvider === 'hubspot' || connectModalProvider === 'crm') && (
              <div className="space-y-2">
                <label className="text-xs font-extrabold text-slate-700 block uppercase tracking-wider font-mono">Select CRM Platform Type</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'hubspot', label: 'HubSpot' },
                    { id: 'salesforce', label: 'Salesforce' },
                    { id: 'pipedrive', label: 'Pipedrive' },
                    { id: 'zoho', label: 'Zoho CRM' },
                    { id: 'custom_crm', label: 'Custom CRM / REST' }
                  ].map((c) => (
                    <button
                      type="button"
                      key={c.id}
                      onClick={() => setCrmType(c.id)}
                      className={`py-2 px-2.5 rounded-xl text-xs font-black transition-all cursor-pointer border ${
                        crmType === c.id
                          ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                          : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                      }`}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="text-xs font-extrabold text-slate-700 block mb-1.5 uppercase tracking-wider font-mono">Account Identifier / Name</label>
                <input
                  type="text"
                  value={accountNameInput}
                  onChange={(e) => setAccountNameInput(e.target.value)}
                  placeholder={
                    connectModalProvider === 'github' ? 'GitHub username (e.g. divijbuddareddy)' :
                    connectModalProvider === 'slack' ? 'Slack Workspace name' :
                    connectModalProvider === 'gmail' ? 'Gmail address (e.g. you@gmail.com)' :
                    `${crmType.toUpperCase()} Account (e.g. Acme Corp CRM)`
                  }
                  className="w-full bg-slate-50 border-2 border-slate-200 rounded-2xl px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 font-medium"
                />
              </div>

              {/* Custom CRM endpoint URL if custom_crm */}
              {(connectModalProvider === 'hubspot' || connectModalProvider === 'crm') && crmType === 'custom_crm' && (
                <div>
                  <label className="text-xs font-extrabold text-slate-700 block mb-1.5 uppercase tracking-wider font-mono">CRM Endpoint / Webhook Base URL</label>
                  <input
                    type="text"
                    value={crmEndpoint}
                    onChange={(e) => setCrmEndpoint(e.target.value)}
                    placeholder="https://api.yourcrm.com/v1 or https://hooks.zapier.com/..."
                    className="w-full bg-slate-50 border-2 border-slate-200 rounded-2xl px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 font-mono font-medium"
                  />
                </div>
              )}

              <div>
                <label className="text-xs font-extrabold text-slate-700 block mb-1.5 uppercase tracking-wider font-mono">
                  {connectModalProvider === 'github' && 'Personal Access Token (PAT) (ghp_...)'}
                  {connectModalProvider === 'slack' && 'Slack Bot User Token (xoxb-...)'}
                  {connectModalProvider === 'gmail' && 'Google App Password (16 letters)'}
                  {(connectModalProvider === 'hubspot' || connectModalProvider === 'crm') && (
                    crmType === 'hubspot' ? 'HubSpot Private App Access Token (pat-na1-...)' :
                    crmType === 'salesforce' ? 'Salesforce Access Token / Security Token' :
                    crmType === 'pipedrive' ? 'Pipedrive API Token (40 chars)' :
                    crmType === 'zoho' ? 'Zoho CRM OAuth Token' :
                    'Custom CRM API Key / Bearer Token'
                  )}
                </label>
                <input
                  type="password"
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  placeholder={
                    connectModalProvider === 'github' ? 'ghp_...' :
                    connectModalProvider === 'slack' ? 'xoxb-...' :
                    connectModalProvider === 'gmail' ? 'xxxx xxxx xxxx xxxx' :
                    crmType === 'hubspot' ? 'pat-na1-...' :
                    crmType === 'salesforce' ? '00D... or Bearer Token' :
                    crmType === 'pipedrive' ? 'e.g. 5a1b2c3d4e5f...' :
                    crmType === 'zoho' ? '1000.xxxx...' :
                    'API_KEY_OR_BEARER_TOKEN'
                  }
                  className="w-full bg-slate-50 border-2 border-slate-200 rounded-2xl px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 font-mono font-semibold"
                />
                <p className="text-xs text-slate-500 mt-1.5 font-medium">
                  {connectModalProvider === 'gmail' && 'Create at: myaccount.google.com/apppasswords'}
                  {connectModalProvider === 'github' && 'Create at: github.com/settings/tokens'}
                  {(connectModalProvider === 'hubspot' || connectModalProvider === 'crm') && (
                    crmType === 'hubspot' ? 'Create in HubSpot: Settings -> Integrations -> Private Apps' :
                    crmType === 'salesforce' ? 'Create in Salesforce: Setup -> Apps -> App Manager -> Connected App' :
                    crmType === 'pipedrive' ? 'Find in Pipedrive: Settings -> Personal Preferences -> API' :
                    crmType === 'zoho' ? 'Find in Zoho: Setup -> Developer Space -> API Keys / OAuth' :
                    'Enter your custom REST CRM bearer token or webhook authorization key'
                  )}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              {integrations.some(i => i.provider === connectModalProvider) ? (
                <button
                  onClick={async () => {
                    const prov = connectModalProvider;
                    setConnectModalProvider(null);
                    await handleDisconnectIntegration(prov);
                  }}
                  className="px-4 py-3 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-600 rounded-xl text-sm font-bold transition-all flex items-center gap-2 cursor-pointer"
                >
                  <Unlink className="w-4 h-4 text-rose-500" />
                  Disconnect
                </button>
              ) : <div />}

              <div className="flex space-x-3">
                <button
                  onClick={() => setConnectModalProvider(null)}
                  className="px-5 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-bold transition-all cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveIntegration}
                  disabled={!tokenInput.trim()}
                  className="px-7 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 disabled:opacity-50 text-white rounded-xl text-sm font-extrabold shadow-lg shadow-blue-500/25 transition-all cursor-pointer"
                >
                  Save & Connect
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modern Blue & White Sidebar */}
      <aside className="w-72 border-r border-slate-200/90 bg-white flex flex-col justify-between shrink-0 z-20 shadow-sm">
        <div>
          {/* Brand Header */}
          <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-gradient-to-b from-blue-50/50 to-transparent">
            <div className="flex items-center space-x-3.5">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 via-blue-700 to-indigo-600 p-[1.5px] shadow-lg shadow-blue-500/25">
                <div className="w-full h-full bg-blue-600 rounded-2xl flex items-center justify-center">
                  <Bot className="w-6 h-6 text-white" />
                </div>
              </div>
              <div>
                <h1 className="font-black text-base tracking-tight text-slate-900 flex items-center gap-1.5">
                  StartupOps <span className="text-xs bg-blue-100 text-blue-700 font-mono px-2 py-0.5 rounded-full border border-blue-200 font-black">AI</span>
                </h1>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <p className="text-xs text-slate-500 font-bold truncate max-w-[140px]">{workspace.name}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-2">
            {[
              { id: 'command', label: 'Command Center', icon: Terminal, badge: 'Copilot', highlight: true },
              { id: 'emails', label: 'Emails & Support', icon: Inbox, count: emails.length || null, highlight: emails.length > 0 },
              { id: 'today', label: 'Today Dashboard', icon: Activity, count: null },
              { id: 'integrations', label: 'Integrations Hub', icon: Layers, count: integrations.length || null },
              { id: 'settings', label: 'Settings', icon: Settings, count: null }
            ].map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`w-full flex items-center justify-between px-4 py-3.5 rounded-2xl text-sm font-extrabold transition-all duration-200 cursor-pointer ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30'
                      : 'text-slate-600 hover:text-blue-700 hover:bg-blue-50/80'
                  }`}
                >
                  <div className="flex items-center space-x-3.5">
                    <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                    <span className="tracking-wide text-[14px]">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[10px] uppercase tracking-wider font-mono font-black px-2.5 py-0.5 rounded-full ${
                      isActive ? 'bg-white/20 text-white border border-white/40' : 'bg-blue-100 text-blue-700 border border-blue-200'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                  {item.count !== null && !item.badge && (
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-black ${
                      isActive 
                        ? 'bg-white/20 text-white' 
                        : item.highlight ? 'bg-blue-100 text-blue-700 border border-blue-200' : 'bg-slate-100 text-slate-500'
                    }`}>
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Integration Status Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/60 space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="flex items-center gap-1.5 font-mono font-bold text-xs text-slate-700">
              <Cpu className="w-4 h-4 text-blue-600" /> Gemini 2.5 Flash
            </span>
            <span className={`text-xs font-mono px-2.5 py-0.5 rounded-full font-extrabold flex items-center gap-1.5 ${
              hasGeminiKey ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
            }`}>
              <span className={`w-2 h-2 rounded-full ${hasGeminiKey ? 'bg-emerald-500' : 'bg-amber-500'}`} />
              {hasGeminiKey ? 'Active' : 'Missing Key'}
            </span>
          </div>
          <button
            onClick={() => setShowKeyModal(true)}
            className="w-full py-3 bg-white hover:bg-blue-50 border border-slate-200 text-slate-700 text-xs rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-sm cursor-pointer hover:border-blue-300"
          >
            <Key className="w-4 h-4 text-blue-600" />
            {hasGeminiKey ? 'Update Gemini Key' : 'Enter Gemini Key'}
          </button>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[#f0f4f9]">
        
        {/* Top Header HUD Bar */}
        <header className="h-16 border-b border-slate-200/90 bg-white/90 backdrop-blur-md px-8 flex items-center justify-between shrink-0 z-10 shadow-sm">
          <div className="flex items-center space-x-3.5">
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-xs font-mono font-bold text-blue-700">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-pulse" />
              <span>LIVE OPERATIONS HUB</span>
            </div>
            <span className="text-slate-300 font-bold">/</span>
            <span className="text-sm font-extrabold text-slate-900 capitalize">{activeTab.replace('_', ' ')}</span>
          </div>
          
          <div className="flex items-center space-x-3.5">
            <div className="hidden lg:flex items-center space-x-2.5 text-xs font-mono font-bold text-slate-600 mr-2">
              <span className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl flex items-center gap-1.5">
                <GitPullRequest className="w-4 h-4 text-indigo-600" /> GitHub: {integrations.find(i => i.provider === 'github') ? 'Synced' : 'Idle'}
              </span>
              <span className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl flex items-center gap-1.5">
                <Mail className="w-4 h-4 text-blue-600" /> Gmail: {emails.length} items
              </span>
              <span className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl flex items-center gap-1.5">
                <Building2 className="w-4 h-4 text-sky-600" /> CRM: {integrations.find(i => i.provider === 'hubspot' || i.provider === 'crm') ? 'Connected' : 'Idle'}
              </span>
            </div>

            <button
              onClick={() => setActiveTab('emails')}
              className="px-4 py-2 bg-blue-50 border border-blue-200 hover:bg-blue-100 text-blue-700 rounded-xl text-xs font-extrabold flex items-center gap-2 transition-all cursor-pointer"
            >
              <Mail className="w-4 h-4 text-blue-600" />
              Inbox ({emails.length})
            </button>
            <button
              onClick={() => setActiveTab('integrations')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-extrabold flex items-center gap-1.5 transition-all shadow-md shadow-blue-500/20 cursor-pointer"
            >
              <Plus className="w-4 h-4" /> Connect Stream
            </button>
          </div>
        </header>

        {/* Tab Viewport */}
        <div className="flex-1 overflow-y-auto p-8 bg-transparent">

          {/* ========================================================================= */}
          {/* SCREEN 1: MODERN BLUE & WHITE COMMAND CENTER */}
          {/* ========================================================================= */}
          {activeTab === 'command' && (
            <div className="max-w-5xl mx-auto flex flex-col h-full space-y-5">
              
              {/* Categorized Quick Action Matrix */}
              <div className="grid grid-cols-3 gap-4">
                {[
                  { 
                    tag: 'STANDUP',
                    tagColor: 'text-blue-700 border-blue-200 bg-blue-50',
                    title: 'Daily Standup Briefing', 
                    desc: 'Synthesizes GitHub repo commits, open PRs, and priority customer emails into an action list.', 
                    q: 'What needs my attention today across GitHub and Gmail?' 
                  },
                  { 
                    tag: 'SUPPORT',
                    tagColor: 'text-emerald-700 border-emerald-200 bg-emerald-50',
                    title: 'Triage Customer Inquiries', 
                    desc: 'Inspects live Gmail messages, analyzes sentiment, and drafts customer replies.', 
                    q: 'Check recent customer emails and prepare replies.' 
                  },
                  { 
                    tag: 'ENGINEERING',
                    tagColor: 'text-indigo-700 border-indigo-200 bg-indigo-50',
                    title: 'Audit Codebase & PRs', 
                    desc: 'Analyzes active pull requests, repository health, and unresolved blockers.', 
                    q: 'Summarize my GitHub repositories and issues.' 
                  }
                ].map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendCommand(item.q)}
                    className="p-5 rounded-2xl bg-white blue-card-interactive text-left flex flex-col justify-between group cursor-pointer transition-all border border-slate-200 hover:border-blue-500 shadow-sm"
                  >
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between">
                        <span className={`text-[10px] font-mono font-black uppercase px-2.5 py-1 rounded-full border ${item.tagColor}`}>
                          {item.tag}
                        </span>
                        <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                      </div>
                      <h4 className="text-sm font-black text-slate-900 group-hover:text-blue-700 transition-colors">
                        {item.title}
                      </h4>
                      <p className="text-xs text-slate-500 leading-relaxed font-medium line-clamp-2">
                        {item.desc}
                      </p>
                    </div>
                  </button>
                ))}
              </div>

              {/* Chat Stream Terminal Window */}
              <div className="flex-1 bg-white rounded-3xl p-6 overflow-y-auto space-y-4 min-h-[420px] shadow-lg flex flex-col justify-between border border-slate-200">
                
                {/* Terminal Header Bar */}
                <div className="flex items-center justify-between pb-3.5 border-b border-slate-100 text-xs text-slate-500 font-mono font-bold">
                  <div className="flex items-center space-x-2.5">
                    <span className="w-3 h-3 rounded-full bg-rose-400 inline-block" />
                    <span className="w-3 h-3 rounded-full bg-amber-400 inline-block" />
                    <span className="w-3 h-3 rounded-full bg-emerald-400 inline-block" />
                    <span className="ml-2 text-slate-800 font-black">StartupOps AI Copilot Terminal</span>
                  </div>
                  <div className="flex items-center space-x-4 text-xs">
                    <span className="text-blue-600 font-bold bg-blue-50 px-2.5 py-1 rounded-md border border-blue-100">ENGINE: GEMINI 2.5 FLASH</span>
                    <button 
                      onClick={() => setMessages([{ role: 'assistant', text: '⚡ Terminal cleared. Ready for operations commands.', timestamp: 'Active Now' }])}
                      className="text-slate-400 hover:text-slate-700 transition-colors cursor-pointer font-bold"
                    >
                      Clear Log
                    </button>
                  </div>
                </div>

                {/* Message Stream */}
                <div className="space-y-4 flex-1 overflow-y-auto pr-1">
                  {messages.map((msg, i) => (
                    <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className="flex items-start space-x-3.5 max-w-3xl">
                        {msg.role === 'assistant' && (
                          <div className="w-9 h-9 rounded-2xl bg-blue-600 flex items-center justify-center shrink-0 mt-0.5 shadow-md shadow-blue-500/25 text-white">
                            <Bot className="w-5 h-5" />
                          </div>
                        )}
                        
                        <div className={`rounded-2xl p-5 text-sm leading-relaxed ${
                          msg.role === 'user'
                            ? 'bg-blue-600 text-white shadow-md shadow-blue-500/25 font-semibold'
                            : 'bg-slate-50 border border-slate-200 text-slate-900 shadow-sm font-sans space-y-3 font-medium'
                        }`}>
                          {/* Structured Agent Intent & Execution Plan */}
                          {msg.intent && (
                            <div className="flex items-center space-x-2 pb-2 border-b border-slate-200 text-xs font-mono text-blue-700 font-bold">
                              <span className="px-2.5 py-1 rounded-md bg-blue-100/80 border border-blue-200 uppercase">
                                INTENT: {msg.intent}
                              </span>
                            </div>
                          )}

                          {msg.plan && msg.plan.length > 0 && (
                            <div className="bg-white p-3.5 rounded-xl border border-slate-200 space-y-2 font-mono text-xs shadow-sm">
                              <div className="text-xs font-extrabold text-slate-500 uppercase tracking-wider">Executed Plan Steps:</div>
                              {msg.plan.map((step, sIdx) => (
                                <div key={sIdx} className="flex items-center space-x-2 text-slate-800 font-bold">
                                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                                  <span>{step.description || JSON.stringify(step)}</span>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Response Text */}
                          <div className="whitespace-pre-wrap leading-relaxed text-[14.5px]">
                            {msg.text}
                          </div>

                          {/* Footer Timestamp & Copy */}
                          <div className="flex items-center justify-between pt-1 text-[11px] font-mono text-slate-400 font-bold">
                            <span>{msg.timestamp || 'Live'}</span>
                            {msg.role === 'assistant' && (
                              <button
                                onClick={() => copyToClipboard(msg.text, i)}
                                className="flex items-center gap-1.5 text-slate-500 hover:text-blue-700 transition-colors cursor-pointer font-bold"
                              >
                                {copiedIndex === i ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                                <span>{copiedIndex === i ? 'Copied' : 'Copy Response'}</span>
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="flex items-center space-x-3 text-blue-700 text-sm font-mono font-bold animate-pulse p-4 bg-blue-50 rounded-2xl w-fit border border-blue-200">
                      <Sparkles className="w-5 h-5 animate-spin text-blue-600" />
                      <span>Gemini Multi-Agent synthesizing across live operational streams...</span>
                    </div>
                  )}
                  <div ref={chatBottomRef} />
                </div>
              </div>

              {/* Floating Omnibar Input */}
              <form onSubmit={(e) => { e.preventDefault(); handleSendCommand(); }} className="relative flex flex-col space-y-2">
                <div className="relative flex items-center">
                  <div className="absolute left-4 text-blue-600">
                    <Sparkles className="w-5 h-5 animate-pulse" />
                  </div>
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Instruct StartupOps AI (e.g. 'Draft reply to customer inquiry' or 'Summarize recent GitHub commits')..."
                    className="w-full bg-white border-2 border-slate-200 focus:border-blue-600 focus:ring-4 focus:ring-blue-100 rounded-2xl pl-12 pr-36 py-4 text-sm text-slate-900 placeholder-slate-400 focus:outline-none shadow-md transition-all font-sans font-semibold"
                  />
                  <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className="absolute right-2.5 px-6 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 disabled:opacity-40 text-white rounded-xl text-sm font-black transition-all shadow-md shadow-blue-500/25 flex items-center gap-2 cursor-pointer"
                  >
                    <span>Dispatch</span>
                    <CornerDownLeft className="w-4 h-4" />
                  </button>
                </div>
                
                {/* Shortcut Helpers */}
                <div className="flex items-center justify-between px-3 text-xs text-slate-500 font-mono font-bold">
                  <div className="flex items-center space-x-2.5">
                    <span>Quick commands:</span>
                    <button type="button" onClick={() => setQuery('What needs my attention today?')} className="hover:text-blue-700 transition-colors cursor-pointer text-blue-600 font-black">/standup</button>
                    <span>•</span>
                    <button type="button" onClick={() => setQuery('Check recent customer emails and prepare replies.')} className="hover:text-blue-700 transition-colors cursor-pointer text-blue-600 font-black">/triage</button>
                    <span>•</span>
                    <button type="button" onClick={() => setQuery('Summarize my GitHub repositories and open issues.')} className="hover:text-blue-700 transition-colors cursor-pointer text-blue-600 font-black">/audit</button>
                  </div>
                  <div>Press <span className="text-slate-900 font-black">Enter</span> to execute</div>
                </div>
              </form>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SCREEN 2: INTERACTIVE EMAILS & SUPPORT HUB */}
          {/* ========================================================================= */}
          {activeTab === 'emails' && (
            <div className="grid grid-cols-5 gap-6 max-w-7xl mx-auto h-full">
              
              {/* Left Column: Email List */}
              <div className="col-span-2 bg-white rounded-3xl p-5 flex flex-col justify-between space-y-4 shadow-lg border border-slate-200">
                <div className="space-y-3.5 border-b border-slate-100 pb-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2.5">
                      <Mail className="w-5 h-5 text-blue-600" />
                      <h3 className="font-black text-sm text-slate-900 uppercase tracking-wider font-mono">Inbox Stream ({filteredEmails.length})</h3>
                    </div>
                    <button
                      onClick={() => handleSyncProvider('gmail')}
                      disabled={loading}
                      className="p-2 bg-slate-50 hover:bg-slate-100 text-slate-700 rounded-xl text-xs flex items-center gap-1.5 transition-all cursor-pointer border border-slate-200 font-bold"
                    >
                      <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                  </div>

                  {/* Search bar */}
                  <div className="relative flex items-center">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3.5" />
                    <input
                      type="text"
                      value={emailSearch}
                      onChange={(e) => setEmailSearch(e.target.value)}
                      placeholder="Search by sender or subject..."
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-3 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 font-medium"
                    />
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
                  {!integrations.some(i => i.provider === 'gmail') ? (
                    <div className="text-center py-16 px-4 text-slate-500 text-sm space-y-3.5">
                      <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center mx-auto text-blue-600 shadow-sm">
                        <Mail className="w-7 h-7" />
                      </div>
                      <div className="font-black text-slate-900 text-base">Connect Gmail</div>
                      <p className="text-xs text-slate-500 leading-relaxed font-medium">
                        Connect your Gmail account with a 16-letter Google App Password to triage customer support messages and send AI-assisted replies.
                      </p>
                      <button
                        onClick={() => {
                          setConnectModalProvider('gmail');
                          setAccountNameInput('');
                          setTokenInput('');
                        }}
                        className="px-5 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 text-white rounded-xl text-xs font-black shadow-md shadow-blue-500/25 cursor-pointer transition-all inline-flex items-center gap-2"
                      >
                        <Plus className="w-4 h-4" /> Connect Gmail
                      </button>
                    </div>
                  ) : filteredEmails.length === 0 ? (
                    <div className="text-center py-20 text-slate-400 text-sm space-y-2.5">
                      <Inbox className="w-10 h-10 text-slate-400 mx-auto opacity-50" />
                      <div className="font-bold">No emails found. Click Sync to fetch live Gmail messages.</div>
                    </div>
                  ) : (
                    filteredEmails.map((em) => (
                      <button
                        key={em.id}
                        onClick={() => {
                          setSelectedEmail(em);
                          setReplyTo(em.sender);
                          setReplySubject(em.subject.startsWith('Re:') ? em.subject : `Re: ${em.subject}`);
                        }}
                        className={`w-full p-4 rounded-2xl text-left border transition-all cursor-pointer ${
                          selectedEmail?.id === em.id
                            ? 'bg-blue-50/80 border-blue-500 shadow-md shadow-blue-500/10'
                            : 'bg-slate-50/60 border-slate-200 hover:border-blue-300 hover:bg-blue-50/30'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-sm font-black text-slate-900 truncate max-w-[170px]">{em.sender}</span>
                          <span className="text-xs text-slate-500 font-mono font-bold">{em.date?.slice(0, 16)}</span>
                        </div>
                        <div className="text-sm font-bold text-blue-700 truncate">{em.subject}</div>
                        <p className="text-xs text-slate-600 line-clamp-2 mt-1.5 font-medium leading-relaxed">{em.snippet}</p>
                      </button>
                    ))
                  )}
                </div>
              </div>

              {/* Right Column: Email Detail & AI Reply Composer */}
              <div className="col-span-3 bg-white rounded-3xl p-7 flex flex-col justify-between space-y-5 overflow-y-auto shadow-lg border border-slate-200">
                {selectedEmail ? (
                  <>
                    {/* Selected Email Header */}
                    <div className="space-y-3 border-b border-slate-100 pb-5">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-mono text-blue-700 font-black">From: {selectedEmail.sender}</span>
                        <span className="text-xs text-slate-500 font-mono font-bold">{selectedEmail.date}</span>
                      </div>
                      <h2 className="text-lg font-black text-slate-900">{selectedEmail.subject}</h2>
                      <div className="p-5 bg-slate-50 border border-slate-200 rounded-2xl text-sm text-slate-800 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto font-sans font-medium">
                        {selectedEmail.body || selectedEmail.snippet}
                      </div>
                    </div>

                    {/* Interactive AI Reply Composer */}
                    <div className="flex-1 space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-black uppercase tracking-wider text-slate-600 font-mono flex items-center gap-2">
                          <Edit3 className="w-4 h-4 text-blue-600" /> Interactive Smart Reply Composer
                        </span>
                        
                        {/* Quick AI Tone Selector */}
                        <div className="flex items-center space-x-2">
                          {['Professional', 'Friendly', 'Concise'].map((tone) => (
                            <button
                              key={tone}
                              onClick={() => handleGenerateAIDraft(selectedEmail, tone.toLowerCase())}
                              disabled={isDraftingAI}
                              className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all flex items-center gap-1.5 cursor-pointer border ${
                                selectedTone === tone.toLowerCase()
                                  ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                                  : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                              }`}
                            >
                              <Sparkles className="w-3 h-3 text-blue-500" />
                              {tone}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-xs font-bold text-slate-600 block mb-1 uppercase font-mono">Recipient</label>
                            <input
                              type="text"
                              value={replyTo}
                              onChange={(e) => setReplyTo(e.target.value)}
                              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-blue-600 font-mono font-bold"
                            />
                          </div>
                          <div>
                            <label className="text-xs font-bold text-slate-600 block mb-1 uppercase font-mono">Subject</label>
                            <input
                              type="text"
                              value={replySubject}
                              onChange={(e) => setReplySubject(e.target.value)}
                              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-blue-600 font-bold"
                            />
                          </div>
                        </div>

                        <div>
                          <label className="text-xs font-bold text-slate-600 block mb-1 uppercase font-mono">
                            Email Body (Review or edit AI draft before dispatch)
                          </label>
                          <textarea
                            rows={6}
                            value={replyBody}
                            onChange={(e) => setReplyBody(e.target.value)}
                            placeholder="Write your email reply here or select an AI tone above to draft instantly with Gemini..."
                            className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 leading-relaxed font-sans font-medium"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Send Controls */}
                    <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                      <span className="text-xs text-slate-500 font-mono font-bold flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Dispatches directly via Gmail SMTP / SSL
                      </span>
                      <button
                        onClick={handleSendEmailReply}
                        disabled={isSendingEmail || !replyBody.trim()}
                        className="px-7 py-3 bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-600 hover:from-emerald-700 hover:to-teal-700 disabled:opacity-40 text-white rounded-xl text-sm font-black shadow-md shadow-emerald-500/25 flex items-center gap-2 transition-all cursor-pointer"
                      >
                        <Send className={`w-4 h-4 ${isSendingEmail ? 'animate-spin' : ''}`} />
                        {isSendingEmail ? 'Sending via Gmail...' : 'Send Email via Gmail'}
                      </button>
                    </div>
                  </>
                ) : !integrations.some(i => i.provider === 'gmail') ? (
                  <div className="text-center py-20 px-8 space-y-5 max-w-md mx-auto my-auto">
                    <div className="w-16 h-16 rounded-3xl bg-blue-50 border border-blue-200 flex items-center justify-center mx-auto text-blue-600 shadow-md">
                      <Mail className="w-8 h-8" />
                    </div>
                    <div className="space-y-1.5">
                      <h3 className="text-lg font-black text-slate-900">Customer Support & Email Hub</h3>
                      <p className="text-sm text-slate-500 leading-relaxed font-medium">
                        Connect Gmail to ingest support inquiries, generate AI drafts with Gemini, and dispatch responses with 1-click.
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setConnectModalProvider('gmail');
                        setAccountNameInput('');
                        setTokenInput('');
                      }}
                      className="px-6 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 text-white rounded-xl text-sm font-black shadow-md shadow-blue-500/25 cursor-pointer transition-all inline-flex items-center gap-2"
                    >
                      <Plus className="w-4 h-4" /> Connect Gmail
                    </button>
                  </div>
                ) : (
                  <div className="text-center py-32 text-slate-400 text-sm space-y-3 font-medium">
                    <Mail className="w-10 h-10 text-slate-400 mx-auto opacity-50" />
                    <div>Select an email from the left pane to view details and draft replies.</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SCREEN 3: TODAY DASHBOARD */}
          {/* ========================================================================= */}
          {activeTab === 'today' && (
            <div className="space-y-6 max-w-6xl mx-auto">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-black text-slate-900">Live Operations Briefing</h2>
                  <p className="text-sm font-semibold text-slate-500">Continuous telemetry across connected systems.</p>
                </div>
                <div className="flex items-center space-x-3 bg-white border border-slate-200 px-5 py-2.5 rounded-2xl shadow-sm">
                  <span className="text-sm text-slate-500 font-bold">Active Streams:</span>
                  <span className="text-sm font-black text-blue-600 font-mono">{integrations.length} Connected</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="p-7 rounded-3xl bg-white blue-card-interactive space-y-4 shadow-sm border border-slate-200">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-slate-500 uppercase tracking-wider font-mono">Communications</span>
                    <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-mono font-black border border-blue-200">{emails.length} Messages</span>
                  </div>
                  <h3 className="font-black text-lg text-slate-900">Interactive Support & Email Hub</h3>
                  <p className="text-sm text-slate-500 leading-relaxed font-medium">Read messages, generate AI-drafted responses, and dispatch directly.</p>
                  <button 
                    onClick={() => setActiveTab('emails')}
                    className="text-sm text-blue-600 hover:text-blue-800 font-black flex items-center gap-1.5 pt-2 cursor-pointer"
                  >
                    Open Support Hub <ChevronRight className="w-4 h-4" />
                  </button>
                </div>

                <div className="p-7 rounded-3xl bg-white blue-card-interactive space-y-4 shadow-sm border border-slate-200">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-slate-500 uppercase tracking-wider font-mono">Platform Stream Hub</span>
                    <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs font-mono font-black border border-emerald-200">{integrations.length} Active</span>
                  </div>
                  <h3 className="font-black text-lg text-slate-900">Platform Integrations</h3>
                  <p className="text-sm text-slate-500 leading-relaxed font-medium">Connect GitHub, Slack, Gmail, and HubSpot CRM to ingest evidence automatically.</p>
                  <button 
                    onClick={() => setActiveTab('integrations')}
                    className="text-sm text-blue-600 hover:text-blue-800 font-black flex items-center gap-1.5 pt-2 cursor-pointer"
                  >
                    Manage Integrations <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SCREEN 4: INTEGRATIONS HUB */}
          {/* ========================================================================= */}
          {activeTab === 'integrations' && (
            <div className="max-w-5xl mx-auto space-y-7">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-black text-slate-900">Live Platform Connections</h2>
                  <p className="text-sm font-semibold text-slate-500">All credentials and tokens are encrypted at rest with AES-256-GCM.</p>
                </div>
                {integrations.length > 0 && (
                  <button
                    onClick={async () => {
                      if (confirm('Disconnect ALL integrations, wipe stored credentials, and clear all platform data?')) {
                        setIntegrations([]);
                        setEmails([]);
                        setSelectedEmail(null);
                        setReplyBody('');
                        for (const item of integrations) {
                          await fetch(`${API_BASE}/integrations/${item.provider}/disconnect`, {
                            method: 'POST',
                            headers: { 'X-Workspace-Id': workspace.id }
                          });
                        }
                        showToast('🔌 All integrations disconnected & platform data wiped.');
                        await refreshData();
                      }
                    }}
                    className="px-4 py-2 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-600 rounded-xl text-xs font-black flex items-center gap-2 transition-all cursor-pointer shadow-sm"
                  >
                    <Unlink className="w-4 h-4" /> Disconnect All ({integrations.length})
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                {[
                  { provider: 'github', name: 'GitHub', icon: GitPullRequest, help: 'Requires Personal Access Token (PAT) with repo scope' },
                  { provider: 'slack', name: 'Slack Workspace', icon: MessageSquare, help: 'Requires Bot User Token (xoxb-...)' },
                  { provider: 'gmail', name: 'Google / Gmail', icon: Mail, help: 'Requires Google App Password (16 letters)' },
                  { provider: 'hubspot', name: 'Universal CRM', icon: Building2, help: 'Supports HubSpot, Salesforce, Pipedrive, Zoho & Custom REST/Webhook' }
                ].map((item) => {
                  const Icon = item.icon;
                  const connected = integrations.find(i => i.provider === item.provider || (item.provider === 'hubspot' && (i.provider === 'crm' || i.provider === 'salesforce' || i.provider === 'pipedrive' || i.provider === 'zoho' || i.provider === 'custom_crm')));

                  return (
                    <div key={item.provider} className={`p-6 rounded-3xl bg-white blue-card-interactive space-y-4 flex flex-col justify-between border transition-all ${
                      connected ? 'border-blue-500 shadow-md shadow-blue-500/10' : 'border-slate-200 hover:border-blue-300'
                    }`}>
                      <div className="space-y-3.5">
                        <div className="flex items-center justify-between">
                          <div className={`p-3.5 rounded-2xl border ${
                            connected ? 'bg-emerald-50 border-emerald-200 text-emerald-600' : 'bg-blue-50 border-blue-200 text-blue-600'
                          }`}>
                            <Icon className="w-6 h-6" />
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className={`px-3 py-1 rounded-full text-xs font-mono font-black flex items-center gap-1.5 ${
                              connected ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500'
                            }`}>
                              {connected && <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />}
                              {connected ? 'Connected' : 'Not Connected'}
                            </span>
                            {connected && (
                              <button
                                onClick={() => handleDisconnectIntegration(item.provider)}
                                title={`Disconnect ${item.name}`}
                                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors border border-transparent hover:border-rose-200 cursor-pointer"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </div>
                        <div>
                          <h3 className="font-black text-lg text-slate-900">{item.name}</h3>
                          <p className="text-xs font-semibold text-slate-500 mt-1 leading-relaxed">{item.help}</p>
                          {connected && (
                            <div className="mt-3 flex items-center justify-between bg-blue-50/70 px-3 py-2 rounded-xl border border-blue-200">
                              <span className="text-xs text-blue-700 font-mono font-bold truncate">
                                Account: {connected.account_name}
                              </span>
                              <span className="text-xs text-emerald-600 font-mono font-black flex items-center gap-1">
                                <CheckCircle2 className="w-3.5 h-3.5" /> Active
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="space-y-2.5 pt-3.5 border-t border-slate-100">
                        {connected ? (
                          <>
                            <div className="grid grid-cols-2 gap-2">
                              <button
                                onClick={() => {
                                  setConnectModalProvider(item.provider);
                                  setAccountNameInput(connected?.account_name || '');
                                  setTokenInput('');
                                }}
                                className="w-full py-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-xl text-xs font-black transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                              >
                                <Key className="w-4 h-4 text-blue-600" />
                                Edit
                              </button>
                              <button
                                onClick={() => handleSyncProvider(item.provider)}
                                disabled={loading}
                                className="w-full py-2.5 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 text-white rounded-xl text-xs font-black transition-all flex items-center justify-center gap-1.5 shadow-md shadow-blue-500/25 cursor-pointer"
                              >
                                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                                Sync
                              </button>
                            </div>
                            <button
                              onClick={() => handleDisconnectIntegration(item.provider)}
                              className="w-full py-2.5 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-600 rounded-xl text-xs font-black transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                            >
                              <Unlink className="w-4 h-4 text-rose-500" />
                              Disconnect {item.name}
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => {
                              setConnectModalProvider(item.provider);
                              setAccountNameInput('');
                              setTokenInput('');
                            }}
                            className="w-full py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 text-white rounded-xl text-xs font-black transition-all flex items-center justify-center gap-2 shadow-md shadow-blue-500/25 cursor-pointer"
                          >
                            <Key className="w-4 h-4" />
                            Connect {item.name}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* ========================================================================= */}
              {/* STEP-BY-STEP PLATFORM CONNECTION INSTRUCTIONS & DIRECT LINKS */}
              {/* ========================================================================= */}
              <div className="pt-4 space-y-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 rounded-xl bg-blue-50 text-blue-600 border border-blue-200">
                      <HelpCircle className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-lg font-black text-slate-900">How to Obtain API Keys & Access Tokens</h3>
                      <p className="text-sm font-semibold text-slate-500">Step-by-step guides and direct links to connect any platform or CRM stream.</p>
                    </div>
                  </div>
                  <span className="px-3.5 py-1.5 rounded-full text-xs font-mono font-bold bg-slate-100 border border-slate-200 text-slate-700">
                    🔒 Zero-Storage Plaintext • Encrypted at Rest
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {/* Guide 1: GitHub */}
                  <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-4 hover:border-blue-300 transition-all shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-2.5 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-600">
                          <GitPullRequest className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="font-black text-sm text-slate-900">GitHub Personal Access Token (Classic)</h4>
                          <span className="text-xs font-mono font-bold text-indigo-600">Format: ghp_...</span>
                        </div>
                      </div>
                      <a
                        href="https://github.com/settings/tokens/new?scopes=repo,read:org,user:email&description=StartupOps_AI_Antigravity"
                        target="_blank"
                        rel="noreferrer"
                        className="px-4 py-2 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 rounded-xl text-xs font-black flex items-center gap-1.5 transition-all cursor-pointer"
                      >
                        Generate Token <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                    <ol className="text-sm text-slate-700 space-y-2 list-decimal list-inside leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200 font-medium">
                      <li>Click the <strong className="text-indigo-700">Generate Token</strong> link above (or go to <span className="font-mono text-xs font-bold text-slate-800">GitHub ➔ Settings ➔ Developer Settings ➔ Personal Access Tokens</span>).</li>
                      <li>Set Note to <strong className="text-slate-900 font-bold">StartupOps AI</strong>.</li>
                      <li>Check the <span className="text-indigo-700 font-mono text-xs font-bold">repo</span> scope (Full control of repositories) and <span className="text-indigo-700 font-mono text-xs font-bold">read:org</span>.</li>
                      <li>Click <strong>Generate token</strong> at the bottom and copy the string starting with <span className="font-mono font-bold text-indigo-700">ghp_...</span></li>
                    </ol>
                  </div>

                  {/* Guide 2: Slack Workspace */}
                  <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-4 hover:border-blue-300 transition-all shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-2.5 rounded-xl bg-sky-50 border border-sky-200 text-sky-600">
                          <MessageSquare className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="font-black text-sm text-slate-900">Slack Bot User OAuth Token</h4>
                          <span className="text-xs font-mono font-bold text-sky-600">Format: xoxb-...</span>
                        </div>
                      </div>
                      <a
                        href="https://api.slack.com/apps"
                        target="_blank"
                        rel="noreferrer"
                        className="px-4 py-2 bg-sky-50 hover:bg-sky-100 border border-sky-200 text-sky-700 rounded-xl text-xs font-black flex items-center gap-1.5 transition-all cursor-pointer"
                      >
                        Slack API Apps <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                    <ol className="text-sm text-slate-700 space-y-2 list-decimal list-inside leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200 font-medium">
                      <li>Go to <strong className="text-slate-900 font-bold">api.slack.com/apps</strong> and click <strong>Create New App</strong> ➔ From scratch.</li>
                      <li>Under <strong>OAuth & Permissions</strong>, scroll to <em>Bot Token Scopes</em> and add: <span className="text-sky-700 font-mono text-xs font-bold">channels:history</span>, <span className="text-sky-700 font-mono text-xs font-bold">channels:read</span>, <span className="text-sky-700 font-mono text-xs font-bold">chat:write</span>.</li>
                      <li>Click <strong>Install to Workspace</strong> at the top of the OAuth page.</li>
                      <li>Copy the generated <strong>Bot User OAuth Token</strong> starting with <span className="font-mono font-bold text-sky-700">xoxb-...</span></li>
                    </ol>
                  </div>

                  {/* Guide 3: Google / Gmail */}
                  <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-4 hover:border-blue-300 transition-all shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-600">
                          <Mail className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="font-black text-sm text-slate-900">Google 16-Letter App Password</h4>
                          <span className="text-xs font-mono font-bold text-blue-600">Format: xxxx xxxx xxxx xxxx</span>
                        </div>
                      </div>
                      <a
                        href="https://myaccount.google.com/apppasswords"
                        target="_blank"
                        rel="noreferrer"
                        className="px-4 py-2 bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 rounded-xl text-xs font-black flex items-center gap-1.5 transition-all cursor-pointer"
                      >
                        Google App Passwords <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                    <ol className="text-sm text-slate-700 space-y-2 list-decimal list-inside leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-200 font-medium">
                      <li>Ensure <strong>2-Step Verification</strong> is enabled on your Google Account.</li>
                      <li>Open the <strong className="text-blue-700 font-bold">Google App Passwords</strong> link above.</li>
                      <li>Enter App name <strong className="text-slate-900 font-bold">StartupOps AI</strong> and click <strong>Create</strong>.</li>
                      <li>Copy the 16-character password displayed on screen and paste it into the Connect modal.</li>
                    </ol>
                  </div>

                  {/* Guide 4: HubSpot / Salesforce / Any CRM */}
                  <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-4 hover:border-blue-300 transition-all shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="p-2.5 rounded-xl bg-cyan-50 border border-cyan-200 text-cyan-600">
                          <Building2 className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="font-black text-sm text-slate-900">Universal CRM Setup (Any CRM)</h4>
                          <span className="text-xs font-mono font-bold text-cyan-600">HubSpot • Salesforce • Pipedrive • Zoho • REST</span>
                        </div>
                      </div>
                      <a
                        href="https://app.hubspot.com/"
                        target="_blank"
                        rel="noreferrer"
                        className="px-4 py-2 bg-cyan-50 hover:bg-cyan-100 border border-cyan-200 text-cyan-700 rounded-xl text-xs font-black flex items-center gap-1.5 transition-all cursor-pointer"
                      >
                        CRM Portals <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                    <div className="text-sm text-slate-700 space-y-2.5 bg-slate-50 p-4 rounded-xl border border-slate-200 font-medium">
                      <div><strong className="text-slate-900">HubSpot:</strong> Private App Token (<span className="font-mono text-xs text-cyan-700 font-bold">pat-na1-...</span>) from <span className="font-bold">Settings ➔ Integrations ➔ Private Apps</span>.</div>
                      <div><strong className="text-slate-900">Salesforce:</strong> Connected App Security / Access Token from <span className="font-bold">Setup ➔ App Manager</span>.</div>
                      <div><strong className="text-slate-900">Pipedrive:</strong> Personal API Token from <span className="font-bold">Settings ➔ Personal Preferences ➔ API</span>.</div>
                      <div><strong className="text-slate-900">Zoho CRM:</strong> OAuth token from <span className="font-bold">Setup ➔ Developer Space</span>.</div>
                      <div><strong className="text-slate-900">Custom / Webhook CRM:</strong> Select <em>Custom CRM</em> and enter your REST endpoint URL + Bearer Key.</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SCREEN 5: SETTINGS */}
          {/* ========================================================================= */}
          {activeTab === 'settings' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div>
                <h2 className="text-2xl font-black text-slate-900">System & AI Settings</h2>
                <p className="text-sm font-semibold text-slate-500">Configure your Google AI Studio Gemini key and active workspace configuration.</p>
              </div>

              <div className="p-8 bg-white rounded-3xl space-y-6 shadow-sm border border-slate-200">
                <h3 className="text-sm font-black uppercase tracking-wider text-slate-500 font-mono">Google AI Studio API Key</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-6 bg-slate-50 rounded-2xl border border-slate-200">
                    <div>
                      <div className="text-base font-black text-slate-900 flex items-center gap-2.5">
                        Google Gemini Multi-Agent Hub
                        <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs font-mono border border-emerald-200 font-black">
                          {hasGeminiKey ? 'Active' : 'Missing'}
                        </span>
                      </div>
                      <div className="text-xs font-semibold text-slate-500 mt-1">Powers autonomous operations, multi-model fallback, and email smart replies.</div>
                    </div>
                    <button
                      onClick={() => setShowKeyModal(true)}
                      className="px-6 py-3 bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 text-white rounded-xl text-xs font-black shadow-md shadow-blue-500/25 cursor-pointer transition-all hover:scale-105"
                    >
                      {hasGeminiKey ? 'Change Key' : 'Enter API Key'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}

