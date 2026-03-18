import { useEffect, useState } from "react";

interface ThinkingPanelProps {
  steps: readonly string[];
  subtitle: string;
  title: string;
}

export function ThinkingPanel({ steps, subtitle, title }: ThinkingPanelProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setActiveIndex((current) => {
        if (current >= steps.length - 1) {
          return current;
        }
        return current + 1;
      });
    }, 1100);

    return () => window.clearInterval(intervalId);
  }, [steps]);

  return (
    <div className="thinking-card">
      <div className="thinking-header">
        <div className="thinking-pulse" />
        <div>
          <strong>{title}</strong>
          <p>{subtitle}</p>
        </div>
      </div>
      <ol className="thinking-steps">
        {steps.map((step, index) => (
          <li className={index <= activeIndex ? "is-active" : ""} key={step}>
            <span className="thinking-step-bullet" />
            <span>{step}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
