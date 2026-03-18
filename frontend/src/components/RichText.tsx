import type { ReactNode } from "react";

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${keyPrefix}-strong-${index}`}>{part.slice(2, -2)}</strong>;
    }

    return <span key={`${keyPrefix}-text-${index}`}>{part}</span>;
  });
}

export function RichText({ content }: { content: string }) {
  const lines = content.split("\n");
  const blocks: ReactNode[] = [];
  let listItems: string[] = [];

  function flushList(keyPrefix: string) {
    if (!listItems.length) {
      return;
    }

    blocks.push(
      <ul className="rich-text-list" key={`${keyPrefix}-list`}>
        {listItems.map((item, index) => (
          <li key={`${keyPrefix}-item-${index}`}>{renderInline(item, `${keyPrefix}-${index}`)}</li>
        ))}
      </ul>
    );
    listItems = [];
  }

  lines.forEach((rawLine, index) => {
    const line = rawLine.trim();
    const keyPrefix = `line-${index}`;

    if (!line) {
      flushList(keyPrefix);
      return;
    }

    if (/^[-*]\s+/.test(line)) {
      listItems.push(line.replace(/^[-*]\s+/, ""));
      return;
    }

    flushList(keyPrefix);

    if (line.startsWith("### ")) {
      blocks.push(
        <h4 className="rich-text-h4" key={keyPrefix}>
          {renderInline(line.slice(4), keyPrefix)}
        </h4>
      );
      return;
    }

    if (line.startsWith("## ")) {
      blocks.push(
        <h3 className="rich-text-h3" key={keyPrefix}>
          {renderInline(line.slice(3), keyPrefix)}
        </h3>
      );
      return;
    }

    if (line.startsWith("# ")) {
      blocks.push(
        <h2 className="rich-text-h2" key={keyPrefix}>
          {renderInline(line.slice(2), keyPrefix)}
        </h2>
      );
      return;
    }

    blocks.push(
      <p className="rich-text-paragraph" key={keyPrefix}>
        {renderInline(line, keyPrefix)}
      </p>
    );
  });

  flushList("final");

  return <div className="rich-text">{blocks}</div>;
}
