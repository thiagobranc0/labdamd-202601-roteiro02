# Reflexão — Roteiro 02: Transparência em Sistemas Distribuídos

**Nome:** [Seu nome completo]  
**Data:** [Data de realização]

---

## 1. Síntese

**Pergunta:** Qual dos 7 tipos de transparência você considera mais difícil de implementar corretamente em um sistema real? Justifique com um argumento técnico baseado nos exercícios realizados.

**Resposta:**

Considero a transparência de **concorrência** a mais difícil de implementar corretamente porque requer coordenação entre processos completamente isolados, rodando potencialmente em máquinas diferentes. Na Tarefa 6, observei que uma simples operação de leitura-modificação-escrita no Redis gerou uma **race condition** quando executada por dois processos em paralelo, resultando em perda de R$300 no saldo da conta. A solução exigiu um **lock distribuído** implementado com `SET NX EX` do Redis, que é fundamentalmente diferente de um `threading.Lock()` local — o lock precisa ser armazenado em um recurso externo compartilhado, ter um TTL para prevenir deadlocks se um processo travar, e incluir lógica de retry para que processos concorrentes possam aguardar a liberação do recurso. O principal desafio é que, diferentemente de sincronização local (que depende de memória compartilhada), locks distribuídos dependem de comunicação de rede sujeita a latência, falhas e partições, tornando a implementação muito mais complexa e suscetível a edge cases como split-brain scenarios ou perda de conectividade durante a seção crítica.

---

## 2. Trade-offs

**Pergunta:** Descreva um cenário concreto de um sistema que você conhece (app, site, jogo) em que esconder completamente a distribuição levaria a um sistema menos resiliente para o usuário final.

**Resposta:**

Um exemplo clássico é o **Google Drive** que precisa mostrar explicitamente o status de sincronização dos arquivos. Se o sistema escondesse completamente a operação distribuída de upload/sincronização e fingisse que arquivos são salvos instantaneamente (como em um sistema de arquivos local), o usuário poderia editar um documento, ver o salvamento local, desligar o computador e perder todo o trabalho porque a **operação assíncrona** de sincronização com a nuvem ainda não havia terminado. Ao expor visualmente o estado através do ícone de sincronização ("nuvem com seta", "check verde", "X vermelho"), o sistema permite que o usuário tome decisões informadas — como aguardar a conclusão da sincronização antes de desligar a máquina ou alternar para modo offline consciente de que há **consistência eventual** pendente. Isso torna a experiência mais resiliente porque o usuário entende que há uma **operação de rede** acontecendo, ajusta suas expectativas sobre latência, e pode diagnosticar problemas (como falta de espaço ou conectividade) em tempo real, em vez de descobrir a perda de dados horas depois.

---

## 3. Conexão com Labs anteriores

**Pergunta:** Como o conceito de `async/await` explorado no Lab 02 se conecta com a decisão de quebrar a transparência conscientemente, vista na Tarefa 7?

**Resposta:**

O `async/await` é uma forma deliberada de **quebrar a transparência** ao expor explicitamente que uma operação é distribuída, assíncrona e sujeita a falhas de rede. Enquanto a transparência tradicional busca fazer um sistema distribuído parecer centralizado, a Tarefa 7 demonstra que **transparência excessiva** pode ser prejudicial — o `anti_pattern.py` finge que uma chamada remota é local, escondendo latência e possibilidade de falha, o que viola as **Falácias da Computação Distribuída** de Peter Deutsch ("latência é zero", "rede é confiável"). O `bom_pattern.py` quebra conscientemente essa ilusão usando `async def fetch_user_remote()`, que sinaliza visualmente no código que a operação pode **suspender a execução** do event loop, aguardando I/O de rede. O retorno `Optional[dict]` e o parâmetro `timeout` explícito forçam o chamador a usar `await` e tratar falhas, tornando o código mais resiliente. Este paradoxo ilustra que, em sistemas distribuídos, às vezes é necessário **expor** certas características (latência, falhas) em vez de ocultá-las, permitindo que desenvolvedores escrevam código com expectativas realistas e tratamento adequado de erros.

---

## 4. GIL e multiprocessing

**Pergunta:** Explique com suas palavras por que a Tarefa 6 usa `multiprocessing` em vez de `threading`. O que é o GIL e por que ele interfere na demonstração de race conditions em Python?

**Resposta:**

O **GIL (Global Interpreter Lock)** é um mutex que protege o acesso às estruturas internas do interpretador CPython, permitindo que apenas uma thread execute bytecode Python por vez, mesmo em sistemas multi-core. Na Tarefa 6, se usássemos `threading.Thread()` em vez de `multiprocessing.Process()`, a race condition poderia não se manifestar de forma reproduzível porque o GIL serializaria parcialmente o acesso à variável compartilhada, mascarando o problema real de concorrência. Com `multiprocessing`, cada processo tem seu **próprio espaço de memória e próprio GIL**, simulando fielmente um ambiente distribuído onde múltiplas instâncias da aplicação rodam em máquinas diferentes — cada uma fazendo `saldo_atual = int(r.get("conta:saldo"))` de forma completamente independente, sem qualquer sincronização em nível de interpretador. Isso torna a race condition real, reproduzível e pedagogicamente mais clara, demonstrando por que locks distribuídos (Redis) são necessários em ambientes distribuídos, ao contrário de locks locais (`threading.Lock()`) que só funcionam dentro de um único processo.

---

## 5. Desafio técnico

**Pergunta:** Descreva uma dificuldade técnica encontrada durante o laboratório (incluindo o provisionamento do Redis Cloud), o processo de diagnóstico e a solução. Se não houve dificuldade, descreva o exercício mais interessante e explique por que.

**Resposta:**

O desafio técnico mais significativo ocorreu na Tarefa 6 (transparência de concorrência) com o lock distribuído via Redis. Inicialmente, ao executar `com_concorrencia.py`, o segundo processo lançava `RuntimeError: Recurso 'conta:saldo' em uso` porque o lock estava sendo disputado simultaneamente pelos dois processos sem nenhuma estratégia de espera — o `r.set(key, "1", nx=True, ex=ttl)` retornava `False` para o segundo processo, e o código falhava imediatamente. O diagnóstico revelou que, diferente de um `threading.Lock()` local que tem blocking nativo, um **lock distribuído** precisa implementar explicitamente a lógica de **retry com backoff** para simular comportamento bloqueante através da rede. A solução foi adicionar um loop de 10 tentativas com `time.sleep(0.1)` entre elas, permitindo que o segundo processo aguardasse a liberação do lock pelo primeiro. Este foi o exercício mais interessante porque demonstrou a diferença entre sincronização local (memória compartilhada) e distribuída (coordenação via rede): a race condition foi real e reproduzível com `multiprocessing`, o saldo final mostrou perda de R$300 sem o lock, e depois ficou correto (R$500) com a sincronização adequada, evidenciando como **exclusão mútua distribuída** é fundamentalmente mais complexa que sua contraparte local.
