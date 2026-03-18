interface QuickPromptsProps {
  prompts: readonly string[];
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}

export function QuickPrompts({ prompts, onSelect, disabled = false }: QuickPromptsProps) {
  return (
    <div className="quick-prompts">
      {prompts.map((prompt) => (
        <button
          className="quick-prompt-chip"
          disabled={disabled}
          key={prompt}
          onClick={() => onSelect(prompt)}
          type="button"
        >
          {prompt}
        </button>
      ))}
    </div>
  );
}
