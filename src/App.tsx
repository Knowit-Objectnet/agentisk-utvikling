import { useEffect, useState, type FormEvent } from 'react'
import {
  ArrowDownRight, ArrowLeft, ArrowRight, ArrowUpRight, Building2, Check,
  ChevronLeft, ChevronRight, CircleHelp, ExternalLink, FileText, Globe2,
  Hash, Info, Landmark, LoaderCircle, MapPin, Search, Users, X,
} from 'lucide-react'

type Address = {
  adresse?: string[]
  postnummer?: string
  poststed?: string
  kommune?: string
  land?: string
}

type Company = {
  organisasjonsnummer: string
  navn: string
  organisasjonsform?: { kode: string; beskrivelse: string }
  forretningsadresse?: Address
  postadresse?: Address
  naeringskode1?: { kode: string; beskrivelse: string }
  antallAnsatte?: number
  stiftelsesdato?: string
  registreringsdatoEnhetsregisteret?: string
  registrertIMvaregisteret?: boolean
  registrertIForetaksregisteret?: boolean
  konkurs?: boolean
  underAvvikling?: boolean
  underTvangsavviklingEllerTvangsopplosning?: boolean
  vedtektsfestetFormaal?: string[]
  aktivitet?: string[]
  hjemmeside?: string
}

type SearchResult = {
  _embedded?: { enheter: Company[] }
  page?: { number: number; totalElements: number; totalPages: number }
}

const API = 'https://data.brreg.no/enhetsregisteret/api/enheter'
const PAGE_SIZE = 10

function formatOrgNumber(value: string) {
  return value.replace(/^(\d{3})(\d{3})(\d{3})$/, '$1 $2 $3')
}

function formatDate(value?: string) {
  if (!value) return 'Ikke oppgitt'
  return new Intl.DateTimeFormat('nb-NO', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(`${value}T12:00:00`))
}

function formatAddress(address?: Address) {
  if (!address) return 'Ikke oppgitt'
  return [address.adresse?.join(', '), [address.postnummer, address.poststed].filter(Boolean).join(' '), address.land && address.land !== 'Norge' ? address.land : null]
    .filter(Boolean).join(', ') || 'Ikke oppgitt'
}

function companyStatus(company: Company) {
  if (company.konkurs) return 'Konkurs'
  if (company.underAvvikling || company.underTvangsavviklingEllerTvangsopplosning) return 'Under avvikling'
  return 'Aktiv'
}

function DetailRow({ icon: Icon, label, children }: { icon: typeof Building2; label: string; children: React.ReactNode }) {
  return (
    <div className="detail-row">
      <span className="detail-icon"><Icon size={18} strokeWidth={1.8} /></span>
      <div className="detail-row-content"><span className="detail-label">{label}</span><span className="detail-value">{children}</span></div>
    </div>
  )
}

function CompanyDetail({ company }: { company: Company }) {
  const status = companyStatus(company)
  const url = `${API}/${company.organisasjonsnummer}`
  const website = company.hjemmeside ? (company.hjemmeside.startsWith('http') ? company.hjemmeside : `https://${company.hjemmeside}`) : null

  return (
    <article className="detail-panel">
      <div className="detail-topline"><span>VIRKSOMHETSPROFIL</span><a href={url} target="_blank" rel="noreferrer" title="Se data hos Brønnøysundregistrene"><ExternalLink size={17} /></a></div>
      <div className="company-avatar large"><Building2 size={30} strokeWidth={1.55} /></div>
      <h2>{company.navn}</h2>
      <p className="detail-org">Org.nr. {formatOrgNumber(company.organisasjonsnummer)}</p>
      <div className="detail-badges"><span className={`status-badge ${status !== 'Aktiv' ? 'status-warning' : ''}`}><span className="status-dot" />{status}</span><span className="type-badge">{company.organisasjonsform?.beskrivelse || 'Virksomhet'}</span></div>

      <div className="detail-divider" />
      <div className="detail-section-heading">Om virksomheten</div>
      <div className="detail-rows">
        <DetailRow icon={Hash} label="Organisasjonsnummer">{formatOrgNumber(company.organisasjonsnummer)}</DetailRow>
        <DetailRow icon={Landmark} label="Organisasjonsform">{company.organisasjonsform?.beskrivelse || 'Ikke oppgitt'}</DetailRow>
        <DetailRow icon={MapPin} label="Forretningsadresse">{formatAddress(company.forretningsadresse)}</DetailRow>
        {company.postadresse && <DetailRow icon={MapPin} label="Postadresse">{formatAddress(company.postadresse)}</DetailRow>}
        <DetailRow icon={FileText} label="Næringskode">{company.naeringskode1 ? `${company.naeringskode1.kode} · ${company.naeringskode1.beskrivelse}` : 'Ikke oppgitt'}</DetailRow>
        <DetailRow icon={Users} label="Ansatte">{company.antallAnsatte !== undefined ? company.antallAnsatte.toLocaleString('nb-NO') : 'Ikke oppgitt'}</DetailRow>
        <DetailRow icon={Building2} label="Stiftet">{formatDate(company.stiftelsesdato)}</DetailRow>
        <DetailRow icon={Globe2} label="Registrert i Enhetsregisteret">{formatDate(company.registreringsdatoEnhetsregisteret)}</DetailRow>
        {website && <DetailRow icon={Globe2} label="Nettside"><a className="inline-link" href={website} target="_blank" rel="noreferrer">{company.hjemmeside} <ArrowUpRight size={14} /></a></DetailRow>}
      </div>

      <div className="detail-divider" />
      <div className="detail-section-heading">Registreringer</div>
      <div className="registration-row"><span>Foretaksregisteret</span><span className={company.registrertIForetaksregisteret ? 'registered' : 'not-registered'}>{company.registrertIForetaksregisteret ? <><Check size={14} /> Registrert</> : 'Ikke registrert'}</span></div>
      <div className="registration-row"><span>Merverdiavgiftsregisteret</span><span className={company.registrertIMvaregisteret ? 'registered' : 'not-registered'}>{company.registrertIMvaregisteret ? <><Check size={14} /> Registrert</> : 'Ikke registrert'}</span></div>

      {(company.vedtektsfestetFormaal?.length || company.aktivitet?.length) ? <>
        <div className="detail-divider" />
        <div className="detail-section-heading">Virksomhetens formål</div>
        <p className="purpose-text">{(company.vedtektsfestetFormaal?.length ? company.vedtektsfestetFormaal : company.aktivitet)?.join(' ')}</p>
      </> : null}

      <a className="source-link" href={url} target="_blank" rel="noreferrer">Se hos Brønnøysundregistrene <ArrowUpRight size={16} /></a>
    </article>
  )
}

export default function App() {
  const [input, setInput] = useState('')
  const [query, setQuery] = useState('')
  const [refresh, setRefresh] = useState(0)
  const [page, setPage] = useState(0)
  const [result, setResult] = useState<SearchResult | null>(null)
  const [selected, setSelected] = useState<Company | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [mobileDetail, setMobileDetail] = useState(false)

  useEffect(() => {
    if (!query) return
    const controller = new AbortController()
    const digits = query.replace(/\s/g, '')
    const isNumber = /^\d{9}$/.test(digits)
    const endpoint = isNumber ? `${API}/${digits}` : `${API}?${new URLSearchParams({ navn: query, size: String(PAGE_SIZE), page: String(page) })}`

    async function load() {
      setLoading(true)
      setError('')
      setResult(null)
      setSelected(null)
      setMobileDetail(false)
      try {
        const response = await fetch(endpoint, { signal: controller.signal })
        if (response.status === 404) {
          setResult({ _embedded: { enheter: [] }, page: { number: page, totalElements: 0, totalPages: 0 } })
          return
        }
        if (!response.ok) throw new Error('Kunne ikke hente data akkurat nå. Prøv igjen om litt.')
        const data = await response.json()
        const searchResult: SearchResult = isNumber ? { _embedded: { enheter: [data as Company] }, page: { number: 0, totalElements: 1, totalPages: 1 } } : data
        setResult(searchResult)
        setSelected(searchResult._embedded?.enheter?.[0] ?? null)
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : 'Noe gikk galt. Prøv igjen.')
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    void load()
    return () => controller.abort()
  }, [query, page, refresh])

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const value = input.trim()
    if (!value) { setError('Skriv inn et navn eller organisasjonsnummer.'); return }
    if (/^[\d\s]+$/.test(value) && !/^\d{9}$/.test(value.replace(/\s/g, ''))) {
      setError('Et organisasjonsnummer må bestå av 9 siffer.'); return
    }
    setError('')
    setPage(0)
    setQuery(value)
    if (value === query && page === 0) setRefresh((current) => current + 1)
  }

  function example(value: string) {
    setInput(value)
    setPage(0)
    setQuery(value)
    setError('')
  }

  function reset() {
    setInput('')
    setQuery('')
    setResult(null)
    setSelected(null)
    setError('')
    setMobileDetail(false)
  }

  const companies = result?._embedded?.enheter ?? []
  const total = result?.page?.totalElements ?? 0
  const totalPages = result?.page?.totalPages ?? 0

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={reset} aria-label="Selskapsinnsikt – tilbake til start"><span className="brand-symbol"><Building2 size={22} strokeWidth={2.1} /></span><span>Selskaps<span className="brand-accent">innsikt</span></span></button>
        <div className="sidebar-group"><span className="sidebar-label">ARBEIDSOMRÅDE</span><button className="nav-item active" onClick={reset}><Search size={18} /> Søk i virksomheter</button></div>
        <div className="sidebar-bottom"><div className="sidebar-tip"><span className="tip-icon"><Info size={18} /></span><strong>Offentlige data</strong><p>Opplysningene hentes direkte fra Enhetsregisteret hos Brønnøysundregistrene.</p><a href="https://www.brreg.no/" target="_blank" rel="noreferrer">Les mer <ArrowUpRight size={14} /></a></div><div className="sidebar-footer"><span className="footer-mark">S</span><span>En enklere vei til<br />bedriftsinformasjon</span></div></div>
      </aside>

      <div className="workspace">
        <header className="topbar"><div className="mobile-brand"><span className="brand-symbol"><Building2 size={19} /></span><strong>Selskapsinnsikt</strong></div><div className="breadcrumbs"><span>Oversikt</span><ChevronRight size={15} /><strong>Virksomhetssøk</strong></div><a className="topbar-source" href="https://data.brreg.no/enhetsregisteret/api/" target="_blank" rel="noreferrer"><span className="live-dot" /> Data fra Brønnøysundregistrene <ArrowUpRight size={15} /></a></header>

        <main className="main-content">
          <div className="eyebrow"><span className="eyebrow-line" /> VIRKSOMHETSSØK <span className="eyebrow-line" /></div>
          <h1>Finn innsikt om <span>norske virksomheter.</span></h1>
          <p className="intro">Søk på navn eller organisasjonsnummer og få oversikt over offentlig registrert bedriftsinformasjon – på ett sted.</p>

          <form className="search-form" onSubmit={submit} role="search"><Search size={21} className="search-icon" /><input aria-label="Søk etter navn eller organisasjonsnummer" value={input} onChange={(event) => setInput(event.target.value)} placeholder="Søk etter bedriftsnavn eller organisasjonsnummer" autoComplete="off" />{input && <button type="button" className="clear-button" onClick={() => { setInput(''); setError('') }} aria-label="Tøm søk"><X size={17} /></button>}<button type="submit" className="search-button">Søk <ArrowRight size={18} /></button></form>
          <div className="search-meta"><span><CircleHelp size={15} /> Prøv for eksempel</span><button onClick={() => example('Equinor')}>Equinor <ArrowUpRight size={13} /></button><button onClick={() => example('Knowit')}>Knowit <ArrowUpRight size={13} /></button><button onClick={() => example('923609016')}>923 609 016 <ArrowUpRight size={13} /></button></div>

          {error && <div className="error-message" role="alert"><Info size={18} />{error}</div>}

          {!query && <div className="welcome-grid"><div className="welcome-card"><div className="welcome-icon"><Search size={26} /></div><span className="card-number">01 / SØK</span><h2>Start med et søk</h2><p>Skriv inn navnet på en virksomhet eller et ni-sifret organisasjonsnummer i søkefeltet over.</p><span className="card-corner"><ArrowUpRight size={21} /></span></div><div className="welcome-card"><div className="welcome-icon purple"><FileText size={26} /></div><span className="card-number">02 / UTFORSK</span><h2>Få oversikt</h2><p>Se adresse, bransje, antall ansatte, registreringer og andre offentlige opplysninger.</p><span className="card-corner"><ArrowDownRight size={21} /></span></div><div className="welcome-note"><span className="note-star">✳</span><div><strong>Åpne og oppdaterte data</strong><p>Alle opplysninger kommer fra Brønnøysundregistrenes Enhetsregister og vises slik de er registrert.</p></div><ExternalLink size={17} /></div></div>}

          {loading && <div className="loading-state" role="status"><LoaderCircle size={26} className="spin" /><strong>Søker i Enhetsregisteret</strong><span>Henter virksomheter …</span></div>}

          {!loading && result && <section className="results-section" aria-label="Søkeresultater"><div className="results-heading"><div><span className="section-kicker">SØKERESULTATER</span><h2>{total === 0 ? 'Ingen treff' : `${total.toLocaleString('nb-NO')} ${total === 1 ? 'virksomhet' : 'virksomheter'} funnet`}</h2><p>Resultater for «{query}»</p></div><button className="new-search" onClick={reset}><ArrowLeft size={16} /> Nytt søk</button></div>
            {total === 0 ? <div className="empty-state"><div className="empty-icon"><Search size={28} /></div><h3>Vi fant ingen virksomheter</h3><p>Prøv et annet navn, sjekk stavemåten eller søk med organisasjonsnummer.</p></div> : <div className="results-grid"><div className={`results-list ${mobileDetail ? 'mobile-hidden' : ''}`}><div className="list-heading"><span>VIRKSOMHETER</span><span>{page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} av {total.toLocaleString('nb-NO')}</span></div>{companies.map((company) => <button key={company.organisasjonsnummer} className={`result-item ${selected?.organisasjonsnummer === company.organisasjonsnummer ? 'selected' : ''}`} onClick={() => { setSelected(company); setMobileDetail(true) }}><span className="company-avatar"><Building2 size={23} strokeWidth={1.7} /></span><span className="result-info"><strong>{company.navn}</strong><span>Org.nr. {formatOrgNumber(company.organisasjonsnummer)}</span><span className="result-location"><MapPin size={13} /> {company.forretningsadresse?.poststed || company.forretningsadresse?.land || 'Adresse ikke oppgitt'} <span className="result-separator">·</span> {company.organisasjonsform?.kode || '–'}</span></span><ChevronRight size={18} className="result-arrow" /></button>)}{totalPages > 1 && <div className="pagination"><button disabled={page === 0} onClick={() => setPage(page - 1)} aria-label="Forrige side"><ChevronLeft size={18} /></button><span>Side {page + 1} av {totalPages}</span><button disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)} aria-label="Neste side"><ChevronRight size={18} /></button></div>}</div><div className={`detail-wrap ${mobileDetail ? 'mobile-visible' : ''}`}>{mobileDetail && <button className="mobile-back" onClick={() => setMobileDetail(false)}><ArrowLeft size={18} /> Tilbake til resultater</button>}{selected && <CompanyDetail company={selected} />}</div></div>}
          </section>}
        </main>
        <footer className="main-footer"><span>© {new Date().getFullYear()} Selskapsinnsikt</span><span>Kilde: <a href="https://www.brreg.no/" target="_blank" rel="noreferrer">Brønnøysundregistrene <ArrowUpRight size={13} /></a></span></footer>
      </div>
    </div>
  )
}
