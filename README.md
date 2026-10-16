# Recuperação — saudedospes.online

Estado verificado em 16-10-2026. O domínio está activo e foi confirmado pelo utilizador como próprio.

Na cópia pública do repositório, o token temporário de contexto usado pela telemetria Lovable foi removido dos dois HTML capturados. Não é necessário para renderizar a oferta; os eventos da plataforma podem deixar de ser associados ao projecto original.

## O que foi recuperado

- Uma landing page de vendas, servida inicialmente com HTML renderizado e hidratada por dois bundles JavaScript (Vite/TanStack Start/React).
- O funil visível tem **1 etapa**. Não existe quiz, recolha de idade/género, formulário de lead ou ramo de respostas nesta página.
- Há 10 perguntas frequentes interactivas. O crawler abriu as 10 e guardou as respostas.
- Dois botões de compra conduzem a sessões externas da Wiapy. Não foram submetidos formulários nem iniciada uma compra.
- O espelho tem **32 ficheiros** locais: HTML, bundles, CSS e imagens (incluindo as imagens dos depoimentos sob `__l5e/assets-v1/`).

## Correr localmente

Na pasta `outputs/`:

```powershell
python serve.py
```

Abra `http://127.0.0.1:8000/`. Rotas sem ficheiro e sem extensão, como `/0/0`, devolvem `index.html`; ficheiros estáticos inexistentes continuam a devolver 404. Todas as respostas incluem `X-Funnel-Mirror: saudedospes-local-v1`, para identificar este servidor.

O site usa caminhos desde a raiz (`/assets/...` e `/__l5e/...`) e `basepath` vazio no router. Publique na raiz do domínio; alojá-lo num subdirectório exige alterar esses caminhos e o resolvedor de imports. `vercel.json` fornece o fallback SPA e deixa os prefixos de assets e analytics passarem para os ficheiros/rotas próprios. A configuração segue a precedência de filesystem e rewrites documentada pela [Vercel](https://vercel.com/docs/project-configuration/vercel-json).

## Actualizar o espelho

```powershell
python mirror.py
```

Por omissão, os ficheiros existentes são mantidos e só se descarregam novos. Para actualizar o conteúdo já presente:

```powershell
python mirror.py --refresh
```

O espelho segue referências HTML, CSS e JavaScript recursivamente, resolve imports relativamente ao ficheiro que os contém e limita os downloads ao domínio original. `confirmed-404.txt` regista referências candidatas que foram pedidas ao servidor e receberam HTTP 404; inclui caminhos de template/glob sem ficheiro real e o carregador opcional de replay. Não são assets disponíveis omitidos do espelho.

## Auditoria de assets

```powershell
python audit_assets.py
```

Resultado desta captura: 34 referências locais distintas no HTML/código; 33 presentes e 1 referência de código que o servidor confirmou como 404 (`/__l5e/rrweb-record.js`). **Ficheiros existentes em falta no disco: 0.** As outras 12 respostas 404 da descoberta recursiva são caminhos produzidos por templates/globs e não referências literais de assets usados na página.

## Capturar a página

`crawl.py` usa Playwright, Node.js e uma instalação local de Chrome/Edge. Exemplo neste ambiente Codex:

```powershell
python crawl.py --node "C:\Users\Usuario\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" --node-modules "C:\Users\Usuario\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules" --browser "C:\Program Files\Google\Chrome\Application\chrome.exe"
```

O resultado fica em `capture_landing/`: HTML, texto, screenshot integral, links/opções, respostas FAQ, pedidos de rede agrupados por domínio e erros do browser. A captura verificada encontrou **0 erros JavaScript/HTTP e 0 recursos locais falhados**, 24 pedidos registados, 4 tentativas de tracking bloqueadas pelo crawler e 2 links de checkout. Não foram enviados dados nem dados de pagamento.

`serve.py` e `crawl.py` destinam-se a uma captura na raiz. O servidor local não implementa APIs de analytics nem backend de vendas.

Ao abrir o espelho manualmente num browser, os scripts de tracking do HTML e dos bundles continuam activos e podem registar a visita nas contas associadas aos IDs acima. O `crawl.py` bloqueia essas chamadas durante a captura; para testes manuais sem tracking, desactive temporariamente as integrações na cópia local.

## Integrações e pontos a rever antes de republicar

### Checkout e backend

Não há submissão de quiz nem endpoint de lead no código da landing page. Os botões fazem navegação HTTP GET para o checkout Wiapy:

- Plano básico — `https://pay.wiapy.com/o98zMWNdo8zj`
- Plano completo — `https://pay.wiapy.com/nVFVUGM-bEF`

O gateway cria/gerencia a sessão fora deste espelho. O fluxo depois destas ligações, os métodos internos da Wiapy, confirmação de pagamento, entrega do produto e reembolso não foram verificados. A página local não processa vendas.

### Caminhos base

1. `site/index.html` referencia bundles, CSS e imagens com caminhos absolutos desde `/`.
2. `site/assets/index-CYaMqJdg.js` resolve módulos preload com prefixo `/` e declara `basepath: ""` para o router.
3. Os assets de depoimento e eventos usam o prefixo de plataforma `/__l5e/`.

O destino de publicação precisa manter estes caminhos na raiz. Alterar apenas os `<script>` do HTML deixa o resolvedor de imports e os assets internos a apontar para o sítio errado.

### Pixels e telemetria

IDs encontrados directamente no código da página:

- UTMify: `6a126f5b4f33ca5953ac05bc` (`window.pixelId`); carrega `pixel.js` e `utms/latest.js`.
- Trackerfy: `px_UbgOTpmtptprZ9ua1Dt-oBR3` (atributo `data-tracking-id` em `px.js`).

Durante a execução ao vivo dos scripts, o crawler também observou o pixel Meta `2081811115698528` carregado por código de terceiros. Esse ID não aparece nos bundles da página, por isso fica identificado como runtime/terceiro, não como literal próprio. UTMify também consultou `api.ipify.org`/`api6.ipify.org` na execução observada. O crawler local bloqueia estes scripts e a chamada `POST /__l5e/trackevents`; a página original pode transmitir visitas para as contas configuradas. Revise os IDs e as contas antes de publicar.

O bundle de eventos tem suporte a eventos e replay, com endpoints `/__l5e/trackevents` e `/__l5e/replay`; o HTML observado não define taxa de amostragem de replay e o carregador `rrweb-record.js` respondeu 404. Não há evidência de replay activo nesta captura. O servidor local não implementa estes endpoints e não deve ser usado para recolha de métricas.

Não foram encontrados Firebase Remote Config, Amplitude ou LaunchDarkly nos ficheiros recolhidos.

### Identificação legal

O rodapé só mostra `© 2026 | Todos os direitos reservados.`. Não encontrei nome de entidade, morada, e-mail de suporte, termos, política de privacidade ou links para outras ofertas. A meta tag `author` diz `Lovable`, que identifica a ferramenta, não a entidade legal. Acrescente/valide os dados legais e os links antes de republicar.

## Verificações concluídas

- [x] Servidor local abre a página com 0 erros de JavaScript e 0 pedidos locais falhados.
- [x] Auditoria: 0 ficheiros existentes em falta; referências 404 estão confirmadas e listadas.
- [x] Percurso no espelho: uma etapa; 10 respostas FAQ capturadas.
- [x] Ramos de idade/género: não existem na aplicação observada.
- [x] Rota profunda `/0/0`: HTTP 200, HTML fallback e cabeçalho distintivo do servidor.
- [x] README regista limitações de analytics, checkout, backend e dados legais.
- [x] IDs de checkout e pixels foram incluídos só quando vistos em HTML, bundles ou pedidos de runtime; a criação de sessão da Wiapy permanece não determinada.

