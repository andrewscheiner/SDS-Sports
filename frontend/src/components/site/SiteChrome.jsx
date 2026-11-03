const SITE = process.env.REACT_APP_SITE_URL || "";
const LINKS = [["Home", "#home"], ["Products", "#services"], ["About", "#about"]];

export const SiteHeader = () => (
  <header className="w-[min(1200px,calc(100%-48px))] h-[88px] mx-auto flex items-center justify-between" data-testid="site-header">
    <a href={`${SITE}/#home`} className="flex items-center gap-3 text-white no-underline" data-testid="site-logo-link">
      <img src="/sds-logo.png" alt="Scheiner Digital Solutions" className="w-[46px] h-[46px] object-contain" />
      <span className="hidden md:inline text-[1.05rem] font-[650]">Scheiner Digital Solutions</span>
    </a>
    <nav className="nav flex items-center gap-3.5 md:gap-[30px]">
      {LINKS.map(([l, h]) => (
        <a key={l} href={`${SITE}/${h}`} data-testid={`site-nav-${l.toLowerCase()}`} className="hidden sm:inline">{l}</a>
      ))}
      <a href="#sports" data-testid="site-nav-sports" className="!text-white">Sports</a>
      <a href={`${SITE}/#contact`} className="nav-contact" data-testid="site-nav-contact">Contact</a>
    </nav>
  </header>
);

export const SiteFooter = () => (
  <footer className="p-[30px] text-center text-[#718789] bg-[#071719] border-t border-white/[0.06]" data-testid="site-footer">
    <p className="m-0">© {new Date().getFullYear()} Scheiner Digital Solutions</p>
  </footer>
);
