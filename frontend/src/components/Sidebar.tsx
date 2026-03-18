import { ASSISTANT_NAME, SIDEBAR_CONTENT, getUiCopy } from "../data/profile";
import type { SidebarCard, UiLanguage } from "../types";

interface SidebarProps {
  isOpen: boolean;
  language: UiLanguage;
  onOpenContact: () => void;
  onClose: () => void;
}

function Section(props: { title: string; items: SidebarCard[]; openLabel: string }) {
  return (
    <section className="sidebar-section">
      <h3 className="sidebar-section-title">{props.title}</h3>
      <div className="sidebar-list">
        {props.items.map((item) => {
          const eyebrow = <span className="sidebar-item-eyebrow">{item.eyebrow}</span>;
          const body = (
            <>
              {eyebrow}
              <strong>{item.title}</strong>
              <p>{item.description}</p>
              {item.note ? <span className="sidebar-item-note">{item.note}</span> : null}
              {item.href ? <span className="sidebar-item-cta">{item.ctaLabel ?? props.openLabel}</span> : null}
            </>
          );

          if (!item.href) {
            return (
              <article className="sidebar-item" key={`${props.title}-${item.title}`}>
                {body}
              </article>
            );
          }

          return (
            <a
              className="sidebar-item sidebar-item-link"
              download={item.download}
              href={item.href}
              key={`${props.title}-${item.title}`}
              rel={item.external ? "noreferrer" : undefined}
              target={item.external ? "_blank" : undefined}
            >
              {body}
            </a>
          );
        })}
      </div>
    </section>
  );
}

export function Sidebar({ isOpen, language, onClose, onOpenContact }: SidebarProps) {
  const copy = getUiCopy(language);
  const content = SIDEBAR_CONTENT[language];

  return (
    <>
      <div className={`sidebar-backdrop ${isOpen ? "is-open" : ""}`} onClick={onClose} aria-hidden="true" />
      <aside className={`sidebar ${isOpen ? "is-open" : ""}`}>
        <div className="sidebar-scroll">
          <div className="sidebar-profile">
            <div className="sidebar-profile-top">
              <div>
                <span className="sidebar-badge">{copy.sidebarTitle}</span>
                <h2>{ASSISTANT_NAME}</h2>
              </div>
              <button className="sidebar-close" onClick={onClose} type="button">
                {copy.close}
              </button>
            </div>
            <p>{copy.sidebarIntro}</p>
          </div>

          <section className="sidebar-section">
            <h3 className="sidebar-section-title">{copy.factsTitle}</h3>
            <ul className="sidebar-facts">
              {copy.heroFacts.map((fact) => (
                <li key={fact}>{fact}</li>
              ))}
            </ul>
          </section>

          <Section items={content.highlights} openLabel={copy.openLabel} title={copy.highlightsTitle} />
          <Section items={content.projects} openLabel={copy.openLabel} title={copy.projectsTitle} />

          <section className="sidebar-section">
            <h3 className="sidebar-section-title">{copy.linksTitle}</h3>
            <div className="sidebar-link-list">
              {content.links.map((link) => (
                link.kind === "contact" ? (
                  <button
                    className="sidebar-link sidebar-link-button"
                    key={link.label}
                    onClick={onOpenContact}
                    type="button"
                  >
                    <div>
                      <strong>{link.label}</strong>
                      <p>{link.description}</p>
                    </div>
                    <span>{link.ctaLabel ?? copy.openLabel}</span>
                  </button>
                ) : (
                  <a
                    className={`sidebar-link ${link.placeholder ? "is-placeholder" : ""}`}
                    download={link.download}
                    href={link.href}
                    key={link.label}
                    rel={link.external ? "noreferrer" : undefined}
                    target={link.external ? "_blank" : undefined}
                  >
                    <div>
                      <strong>{link.label}</strong>
                      <p>{link.description}</p>
                    </div>
                    <span>{link.ctaLabel ?? (link.placeholder ? copy.updateLabel : copy.openLabel)}</span>
                  </a>
                )
              ))}
            </div>
          </section>
        </div>
      </aside>
    </>
  );
}
