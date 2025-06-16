# NF-e Pagamentos

Este projeto automatiza a extração de dados de Notas Fiscais Eletrônicas de Consumidor (NFC-e) do portal da Sefaz RS, salvando os dados em CSV para melhorar a gestão financeira.

## Índice

- [Sobre](#sobre)
- [Funcionalidades](#funcionalidades)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Estrutura dos Arquivos](#estrutura-dos-arquivos)
- [Contribuição](#contribuição)
- [Licença](#licença)
- [Contato](#contato)

## Sobre

O NF-e Pagamentos automatiza processos fiscais, garantindo conformidade com a legislação brasileira e integração com sistemas de pagamento. Ele realiza scraping dos dados das NFC-e a partir de links, estruturando e exportando as informações relevantes.

## Funcionalidades

- Extração automática de dados de NFC-e a partir de links
- Estruturação e limpeza de arquivos CSV de entrada
- Salvamento dos dados extraídos em CSV (produtos, emitente, consumidor, totais)
- Log detalhado de erros e operações
- Configuração flexível via arquivo JSON
- Suporte a modo debug (processamento offline de HTML salvo)
- Atualização automática da lista de links processados

## Pré-requisitos

- Python 3.8+
- [pip](https://pip.pypa.io/en/stable/)
- Linux

## Instalação

Clone o repositório:

```bash
git clone https://github.com/AlexC2624/NF-e.git
cd NF-e
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

> **Dependências principais:**  
> `pandas`, `requests`, `beautifulsoup4`

## Configuração

1. **Arquivo `.env`** (opcional, para integração futura):

```env
CERT_PATH=./certificado.pfx
CERT_PASSWORD=sua_senha
AMBIENTE=producao # ou homologacao
```

2. **Arquivo de configuração:**  
Edite `config_selectors.json` para ajustar seletores HTML, caminhos de arquivos e parâmetros de execução.

3. **Arquivo de entrada:**  
Coloque os links das NFC-e no arquivo `links.csv` (um por linha).  
O script pode estruturar o CSV automaticamente se necessário.

## Uso

Execute o script principal:

```bash
python main.py
```

O script irá:
- Ler os links do arquivo CSV configurado
- Baixar e processar cada NFC-e
- Salvar os dados extraídos em `dados/dados_nfe.csv`
- Atualizar o arquivo de links removendo os já processados

### Exemplo de estrutura do arquivo de entrada (`links.csv`):

```
https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?p=XXXXXXXXXXXXXXX|xx
https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?p=YYYYYYYYYYYYYYY|xx
```

## Estrutura dos Arquivos

- `main.py`: Script principal de extração e processamento
- `estruturar.py`: Função para estruturar/limpar o CSV de entrada
- `config_selectors.json`: Configurações de seletores HTML e parâmetros
- `links.csv`: Lista de links das NFC-e a serem processadas
- `dados/`: Pasta onde os dados extraídos e HTMLs são salvos
- `logs/`: Pasta com arquivos de log de execução

## Contribuição

Contribuições são bem-vindas! Por favor, abra uma issue ou envie um pull request.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

## Contato

- Nome: Alex
- Email: alex.cargnin.2006@gmail.com
- GitHub: [AlexC2624](https://github.com/AlexC2624)
