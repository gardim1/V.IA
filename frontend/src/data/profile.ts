import type { SidebarCard, SidebarLink, UiLanguage } from "../types";

export const ASSISTANT_NAME = "Vinnie";
export const DEFAULT_LANGUAGE: UiLanguage = "pt-BR";

export const UI_COPY = {
  "pt-BR": {
    appTitle: "Portfolio AI",
    tagline: "Vinnie, o assistente do portfólio de Vinicius Silva Gardim",
    emptyTitle: "Como posso ajudar?",
    emptySubtitle:
      "Sou o Vinnie, assistente virtual do Vinicius Silva Gardim. Posso responder sobre carreira, projetos, stack, objetivos e como ele trabalha.",
    quickPromptLabel: "Perguntas sugeridas",
    chatTitle: "Nova conversa",
    runtimeHint: "OpenAI primeiro, fallback local",
    sessionLabel: "Sessão",
    composerPlaceholder: "Pergunte qualquer coisa sobre o Vinicius...",
    send: "Enviar",
    menu: "Perfil",
    close: "Fechar",
    footerNote: "O Vinnie responde com base no portfólio e na base documental do Vinicius.",
    providerLoading: "Pensando",
    thinkingTitle: "Vinnie está pensando",
    thinkingSubtitle: "Buscando contexto, checando a base e montando a resposta final.",
    assistantLabel: "Vinnie",
    userLabel: "Você",
    languageToggle: "Idioma",
    sidebarTitle: "Portfolio",
    factsTitle: "Resumo rápido",
    sidebarIntro:
      "O Vinnie é o assistente virtual do Vinicius. Ele não é o Vinicius: foi criado para apresentar os projetos, a experiência e o perfil profissional dele.",
    highlightsTitle: "Highlights",
    projectsTitle: "Projetos",
    linksTitle: "Links",
    openLabel: "Abrir",
    updateLabel: "Atualizar",
    downloadLabel: "Baixar",
    internalLabel: "Projeto interno",
    welcome:
      "Oi! Eu sou o Vinnie, assistente do portfólio do Vinicius. Pode perguntar sobre skills, projetos, carreira, objetivos, hobbies ou modo de trabalho.",
    contactTitle: "Contato",
    contactSubtitle: "Preencha seus dados e o Vinicius pode retornar depois.",
    contactNameLabel: "Nome",
    contactCompanyLabel: "Empresa",
    contactEmailLabel: "Email",
    contactSourceLabel: "Onde você encontrou o portfólio?",
    contactMessageLabel: "Mensagem",
    contactSubmitLabel: "Enviar contato",
    contactCancelLabel: "Cancelar",
    contactSuccess: "Contato enviado com sucesso.",
    contactError: "Não foi possível enviar o contato agora.",
    contactSourceOptions: [
      { value: "linkedin", label: "LinkedIn" },
      { value: "github", label: "GitHub" },
      { value: "recomendacao", label: "Recomendação" },
      { value: "site_vagas", label: "Site de vagas" },
      { value: "outros", label: "Outros" }
    ],
    quickPrompts: [
      "Quais são as principais skills técnicas do Vinicius?",
      "Quais projetos mais relevantes o Vinicius já desenvolveu?",
      "Onde o Vinicius quer chegar nos próximos 5 anos?",
      "Quais são os hobbies do Vinicius?",
      "Como o Vinicius trabalha em equipe e se comunica?"
    ],
    thinkingSteps: [
      "Entendendo a pergunta",
      "Buscando sinais e keywords",
      "Consultando a base vetorial",
      "Selecionando os melhores trechos",
      "Escrevendo a resposta final"
    ],
    heroFacts: [
      "Backend, automação e IA aplicada",
      "Experiência com RAG, APIs e visão computacional",
      "Foco atual em Python, automação e IA no contexto financeiro"
    ]
  },
  "en-US": {
    appTitle: "Portfolio AI",
    tagline: "Vinnie, the assistant for Vinicius Silva Gardim's portfolio",
    emptyTitle: "How can I help?",
    emptySubtitle:
      "I am Vinnie, Vinicius Silva Gardim's virtual assistant. I can answer about his career, projects, stack, goals and work style.",
    quickPromptLabel: "Suggested prompts",
    chatTitle: "New chat",
    runtimeHint: "OpenAI first, local fallback",
    sessionLabel: "Session",
    composerPlaceholder: "Ask anything about Vinicius...",
    send: "Send",
    menu: "Profile",
    close: "Close",
    footerNote: "Vinnie answers based on Vinicius' portfolio and document base.",
    providerLoading: "Thinking",
    thinkingTitle: "Vinnie is thinking",
    thinkingSubtitle: "Searching for context, checking the knowledge base and preparing the final answer.",
    assistantLabel: "Vinnie",
    userLabel: "You",
    languageToggle: "Language",
    sidebarTitle: "Portfolio",
    factsTitle: "Quick facts",
    sidebarIntro:
      "Vinnie is Vinicius' virtual assistant. He is not Vinicius himself: he was built to present his projects, experience and professional profile.",
    contactTitle: "Contact",
    contactSubtitle: "Share your details and Vinicius can get back to you later.",
    contactNameLabel: "Name",
    contactCompanyLabel: "Company",
    contactEmailLabel: "Email",
    contactSourceLabel: "Where did you find this portfolio?",
    contactMessageLabel: "Message",
    contactSubmitLabel: "Send contact",
    contactCancelLabel: "Cancel",
    contactSuccess: "Contact sent successfully.",
    contactError: "Could not send the contact right now.",
    contactSourceOptions: [
      { value: "linkedin", label: "LinkedIn" },
      { value: "github", label: "GitHub" },
      { value: "recomendacao", label: "Recommendation" },
      { value: "site_vagas", label: "Job board" },
      { value: "outros", label: "Other" }
    ],
    highlightsTitle: "Highlights",
    projectsTitle: "Projects",
    linksTitle: "Links",
    openLabel: "Open",
    updateLabel: "Update",
    downloadLabel: "Download",
    internalLabel: "Internal project",
    welcome:
      "Hi! I am Vinnie, the assistant for Vinicius' portfolio. Ask me about skills, projects, career, goals, hobbies or work style.",
    quickPrompts: [
      "What are Vinicius' main technical skills?",
      "Which projects matter most in Vinicius' portfolio?",
      "Where does Vinicius want to be in the next 5 years?",
      "What are Vinicius' main hobbies?",
      "How does Vinicius communicate and work with teams?"
    ],
    thinkingSteps: [
      "Interpreting the question",
      "Scanning for relevant signals",
      "Consulting the vector store",
      "Selecting the strongest context",
      "Drafting the final answer"
    ],
    heroFacts: [
      "Backend, automation and applied AI",
      "Experience with RAG, APIs and computer vision",
      "Current focus on Python, automation and AI in finance"
    ]
  }
} as const;

export const SIDEBAR_CONTENT: Record<
  UiLanguage,
  {
    highlights: SidebarCard[];
    projects: SidebarCard[];
    links: SidebarLink[];
  }
> = {
  "pt-BR": {
    highlights: [
      {
        eyebrow: "Foco atual",
        title: "Python, automação e IA aplicada",
        description: "Atuando com automação e inteligência artificial aplicada a sistemas e processos."
      },
      {
        eyebrow: "Stack",
        title: "FastAPI, LangChain, SQL e integrações",
        description: "Base forte em backend, APIs, banco de dados, automação e projetos inteligentes com uso real."
      },
      {
        eyebrow: "Estilo",
        title: "Execução prática e produto",
        description: "Interesse em construir coisas úteis que ligam tecnologia, negócio e impacto real."
      }
    ],
    projects: [
      {
        eyebrow: "RAG",
        title: "AI para suporte empresarial",
        description: "Busca vetorial, contexto documental e geração de respostas com LLM para uso interno.",
        note: "Projeto interno de empresa"
      },
      {
        eyebrow: "Computer vision",
        title: "YOLO para medição de tecidos",
        description: "Projeto com a DASA para medir tecidos patológicos usando visão computacional.",
        href: "https://github.com/gardim1/stunning-sniffle",
        external: true,
        ctaLabel: "Ver projeto"
      },
      {
        eyebrow: "Interface",
        title: "Chat corporativo com Blazor",
        description: "Experiência com interface, fluxo de interação e lógica aplicada a sistema corporativo.",
        note: "Projeto interno de empresa"
      },
      {
        eyebrow: "Computer vision",
        title: "Cálculo de velocidade de bolinhas de ping-pong",
        description: "Projeto para calcular velocidade de bolinhas de ping-pong com base em visão computacional e análise de deslocamento em vídeo.",
        href: "https://youtu.be/o2vsGWBBpwI?si=3_uiNXigwlsYdgCQ",
        external: true,
        ctaLabel: "Ver demo"
      }
    ],
    links: [
      {
        label: "LinkedIn",
        href: "https://www.linkedin.com/in/vinicius-gardim-756085251/",
        description: "Perfil profissional com experiência, carreira e formação.",
        external: true
      },
      {
        label: "GitHub",
        href: "https://github.com/gardim1",
        description: "Repositórios, experimentos e projetos públicos do Vinicius.",
        external: true
      },
      {
        label: "Currículo",
        href: "/downloads/CURRICULO_VINICIUS_GARDIMc.pdf",
        description: "Baixe o currículo em português.",
        download: "CURRICULO_VINICIUS_GARDIMc.pdf",
        ctaLabel: "Baixar"
      },
      {
        label: "Contato",
        href: "#contato",
        description: "Abra um formulário para o Vinicius retornar o contato.",
        ctaLabel: "Abrir form",
        kind: "contact"
      }
    ]
  },
  "en-US": {
    highlights: [
      {
        eyebrow: "Current focus",
        title: "Python, automation and applied AI",
        description: "Working on automation and AI applied to real systems and processes."
      },
      {
        eyebrow: "Stack",
        title: "FastAPI, LangChain, SQL and integrations",
        description: "Strong backend foundation with APIs, databases, automation and intelligent systems."
      },
      {
        eyebrow: "Work style",
        title: "Practical execution and product mindset",
        description: "Strong interest in building useful things that connect technology, business and real impact."
      }
    ],
    projects: [
      {
        eyebrow: "RAG",
        title: "AI for enterprise support",
        description: "Vector search, document context and LLM responses designed for internal support use cases.",
        note: "Internal company project"
      },
      {
        eyebrow: "Computer vision",
        title: "YOLO for tissue measurement",
        description: "Project with DASA focused on pathology tissue measurement using computer vision.",
        href: "https://github.com/gardim1/stunning-sniffle",
        external: true,
        ctaLabel: "View project"
      },
      {
        eyebrow: "Interface",
        title: "Corporate chat with Blazor",
        description: "Experience with interface flow, interaction design and logic in business software.",
        note: "Internal company project"
      },
      {
        eyebrow: "Computer vision",
        title: "Ping-pong ball speed calculation",
        description: "Project focused on calculating ping-pong ball speed using computer vision and video displacement analysis.",
        href: "https://youtu.be/o2vsGWBBpwI?si=3_uiNXigwlsYdgCQ",
        external: true,
        ctaLabel: "Watch demo"
      }
    ],
    links: [
      {
        label: "LinkedIn",
        href: "https://www.linkedin.com/in/vinicius-gardim-756085251/",
        description: "Professional profile with experience, career highlights and education.",
        external: true
      },
      {
        label: "GitHub",
        href: "https://github.com/gardim1",
        description: "Public repositories, experiments and side projects by Vinicius.",
        external: true
      },
      {
        label: "Resume",
        href: "/downloads/CV_VINICIUS_GARDIM.pdf",
        description: "Download the English resume.",
        download: "CV_VINICIUS_GARDIM.pdf",
        ctaLabel: "Download"
      },
      {
        label: "Contact",
        href: "#contact",
        description: "Open a form so Vinicius can reach back later.",
        ctaLabel: "Open form",
        kind: "contact"
      }
    ]
  }
};

export function getUiCopy(language: UiLanguage) {
  return UI_COPY[language];
}
