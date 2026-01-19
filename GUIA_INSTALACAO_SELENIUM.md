# Guia de Instalação - Scraper Automático ComexStat

Este guia explica como instalar e configurar o scraper automático que faz download dos dados do ComexStat via interface web.

## Requisitos

1. **Python 3.8+**
2. **Selenium** - Biblioteca Python para automação web
3. **ChromeDriver** - Driver para controlar o navegador Chrome

## Passo 1: Instalar Selenium

```bash
pip install selenium
```

Ou usando o requirements.txt:

```bash
pip install -r backend/requirements.txt
```

## Passo 2: Instalar ChromeDriver

### Opção A: Instalação Automática (Recomendado)

O ChromeDriver pode ser instalado automaticamente usando o `webdriver-manager`:

```bash
pip install webdriver-manager
```

Depois, atualize o código para usar:

```python
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
```

### Opção B: Instalação Manual

1. **Verificar versão do Chrome:**
   - Abra o Chrome
   - Vá em `Configurações` > `Sobre o Chrome`
   - Anote a versão (ex: 120.0.6099.109)

2. **Baixar ChromeDriver:**
   - Acesse: https://chromedriver.chromium.org/downloads
   - Baixe a versão correspondente à do seu Chrome
   - Extraia o arquivo `chromedriver.exe`

3. **Adicionar ao PATH:**
   - **Windows:**
     - Coloque `chromedriver.exe` em uma pasta (ex: `C:\chromedriver\`)
     - Adicione ao PATH do sistema:
       - Painel de Controle > Sistema > Configurações Avançadas > Variáveis de Ambiente
       - Adicione `C:\chromedriver\` ao PATH
   
   - **Linux/Mac:**
     ```bash
     sudo mv chromedriver /usr/local/bin/
     sudo chmod +x /usr/local/bin/chromedriver
     ```

## Passo 3: Testar Instalação

Execute o script de teste:

```bash
python projeto_comex/backend/scripts/testar_scraper_automatico.py
```

## Como Funciona

O scraper automático:

1. **Abre o navegador Chrome** (em modo headless ou visível)
2. **Navega para** `https://comexstat.mdic.gov.br/pt/dados-gerais`
3. **Preenche os filtros** (ano, mês, tipo de operação)
4. **Clica no botão de download**
5. **Aguarda o download** ser concluído
6. **Salva o arquivo CSV** na pasta configurada

## Modo de Uso

### Modo Headless (Sem Interface Gráfica)
```python
scraper = ComexStatScraper()
arquivo = scraper.baixar_dados(2025, 12, "Ambos", headless=True)
```

### Modo Visível (Para Debug)
```python
scraper = ComexStatScraper()
arquivo = scraper.baixar_dados(2025, 12, "Ambos", headless=False)
```

## Solução de Problemas

### Erro: "ChromeDriver não encontrado"
- Verifique se o ChromeDriver está no PATH
- Ou use `webdriver-manager` para instalação automática

### Erro: "Selenium não está disponível"
- Instale o Selenium: `pip install selenium`

### Download não funciona
- Execute em modo não-headless (`headless=False`) para ver o que acontece
- Verifique se a página carregou corretamente
- Verifique se os filtros foram preenchidos
- Verifique se o botão de download foi encontrado

### Página não carrega
- Verifique sua conexão com a internet
- Verifique se o site está acessível: https://comexstat.mdic.gov.br/pt/dados-gerais

## Integração Automática

O scraper já está integrado ao `EnrichedDataCollector`. Ele será usado automaticamente quando:

1. Não houver arquivos CSV locais
2. O download direto via URL falhar
3. Selenium e ChromeDriver estiverem instalados

## Notas Importantes

- O scraper pode levar alguns minutos para baixar cada mês
- É recomendado limitar a 6 meses por vez para evitar timeouts
- O modo headless é mais rápido, mas o modo visível ajuda no debug
- Os arquivos são salvos em `comex_data/comexstat_csv/`


