# Planejamento LIA - Offline

## Bugs conhecidos
- Chunk sem contexto
- Resposta mistura seções diferentes 

## Melhorias para fazer
- Conectar Redis pra manter o histórico  de sessões

## Ideias novas
- Atalho de debug no front para ver os chunks usados na resposta
- Botão "corrigir resposta" que salva a resposta certa junto com a errada 
- Separar logs por sessão_id

## Para estudar 
- FastAPI streaming responde
- Deploy com Docker no RunPod (ou outro lugar)
- Substituir InMemoryChatMessageHistory por RedisChatMessageHistory