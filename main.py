import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import os
import re
import json # Importar o módulo json
import logging as log

# --- 1. Configuração do Logger ---
# Define o nome do arquivo de log
log_file_name = f"{datetime.now().strftime('%Y-%m-%d')}.log"
log_path = os.path.join(os.getcwd(), "logs", log_file_name) # Pasta 'logs' no diretório atual

# Cria a pasta 'logs' se ela não existir
os.makedirs(os.path.dirname(log_path), exist_ok=True)

# Cria a pasta para armazenar os dados se não existir
os.makedirs("dados", exist_ok=True)

# Configura o logger básico
# log.basicConfig configura o logger root (padrão)
log.basicConfig(
    level=log.ERROR, # Define o nível mínimo de mensagens a serem gravadas
    format='%(asctime)s - %(levelname)s - %(message)s', # Formato da mensagem de log
    filename=log_path, # Nome do arquivo onde o log será salvo
    filemode='a', # 'a' para append (anexar ao arquivo se existir), 'w' para write (sobrescrever)
    encoding='utf-8' # Codificação do arquivo de log
)

# --- Carregar Configurações do JSON ---
config_json = 'config_selectors.json' # Caminho do arquivo de configuração
if not os.path.exists(config_json):
    log.info(f"Arquivo de configuração '{config_json}' não encontrado. Criando um novo arquivo com os valores padrão.")
    with open(config_json, 'w', encoding='utf-8') as f:
        f.write('''
{
    "metadata": {
        "versao_config": "1.1",
        "data_ultima_atualizacao": "2025-06-15",
        "autor": "Alex",
        "descricao": "Este arquivo contém as configurações de seletores HTML para o scraping de NFC-e do portal da Sefaz RS. Ajuste os valores dentro de 'emitente', 'totais', 'itens' e 'consumidor' se o layout da página da NFC-e mudar.",
        "instrucoes_gerais": "Mantenha a 'versao_config' atualizada. Para habilitar requisições reais, defina 'debug.requisição_na_web' como 'True'. Certifique-se de que o arquivo CSV de entrada ('path_csv_entrada') esteja no local correto."
    },
    "geral": {
        "path_csv_entrada": "links.csv",
        "estruturar_csv": "True",
        "chave_acesso_class": "chave",
        "csv_saida": "dados_nfe.csv",
        "pasta_dados": "dados",
        "nome_inicial_html": "response_rs_",
        "tempo_entre_requisicoes": 5,
        "timeout_requisicao": 30
    },
    "debug": {
        "requisição_na_web": "True",
        "chave_para_requisição": "chave_acesso"
    },
    "emitente": {
        "div_principal_class": "txtCenter",
        "nome_emitente_id": "u20",
        "cnpj_endereco_class": "text"
    },
    "totais": {
        "div_principal_id": "totalNota",
        "linha_total_id": "linhaTotal",
        "valor_numb_class": "totalNumb"
    },
    "itens": {
        "tabela_itens_id": "tabResult",
        "linha_item_id_regex": "Item \\\\+ \\\\d+",
        "nome_produto_class": "txtTit",
        "qtd_class": "Rqtd",
        "un_class": "RUN",
        "vl_unit_class": "RvlUnit",
        "vl_total_item_class": "valor"
    },
    "consumidor": {
        "collapsible_div_data_role": "collapsible",
        "collapsible_h4_text": "Consumidor",
        "list_view_data_role": "listview"
    }
}
    ''')

try:
    with open(config_json, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    log.error(f"Erro: Arquivo '{config_json}' não encontrado. Certifique-se de que está na mesma pasta.")
    exit() # Encerra o script se o arquivo de configuração não for encontrado
except json.JSONDecodeError:
    log.error(f"Erro: Falha ao decodificar '{config_json}'. Verifique a sintaxe JSON.")
    print(f"Erro de decodificação JSON: {config_json}")
    exit()

# --- Configurações Iniciais ---
path_entrada = CONFIG['geral']['path_csv_entrada']
if os.path.exists(path_entrada):
    try:
        if CONFIG['geral']['estruturar_csv'] == 'True':
            from estruturar import csv_entrada
            resultado = csv_entrada(CONFIG['geral']['path_csv_entrada'])
            if resultado[0] is False:
                if not 'https://www.sefaz.rs.gov.br/' in resultado[1]:
                    log.error(resultado[1])
                    print(resultado[1])
                    exit()
            df_csv_link_entrada = pd.read_csv(path_entrada, header=None)
        else: df_csv_link_entrada = pd.read_csv(path_entrada, header=None)

    except pd.errors.EmptyDataError:
        log.error(f"Arquivo de entrada vazio: {path_entrada}")
        print(f"\tO arquivo '{path_entrada}' está vazio. Adicione links para consulta.\n")
        exit()

    csv_link_entrada = df_csv_link_entrada[0].tolist()  # Converte a coluna do DataFrame em uma lista

else:
    log.error(f"Erro: O arquivo '{path_entrada}' não foi encontrado. Verifique o caminho em config_selectors.json.")
    print(f"Arquivo de entrada não encontrado: {path_entrada}")
    exit()

qtdd_notas = len(csv_link_entrada)

dados_notas = []
# É melhor gerenciar a lista de links que ainda precisam ser processados
# em vez de constantemente sobrescrever o CSV inteiro em cada iteração.
# Vamos manter o controle dos links restantes.
remaining_links = csv_link_entrada[:] # Faz uma cópia para modificar

# --- Loop para Processar os Links ---
for i, link in enumerate(csv_link_entrada): # Itera sobre a lista original
    print(f"\nProcessando link {i+1}/{qtdd_notas}: {link}")
    try:
        # ATENÇÃO: As linhas abaixo usar o arquivo HTML salvo para depuração.
        if CONFIG['debug']['requisição_na_web'] == 'False':
            log.info("Modo de depuração ativo. Usando HTML salvo em vez de fazer uma requisição na web.")
            path = os.path.join(CONFIG['geral']['pasta_dados'], f'{CONFIG['geral']['nome_inicial_html']}{CONFIG['debug']['chave_para_requisição']}.html')
            with open(path, "r", encoding="utf-8") as f:
                class Response: # Classe dummy para simular o objeto response do requests
                    def __init__(self, text):
                        self.text = text
                response = Response(f.read())
            chave_acesso_url = "N/A_DEBUG" # Definir uma chave de acesso para o debug

        else:   # Requisição na web
            if i != 0:
                time.sleep(CONFIG['geral']['tempo_entre_requisicoes'])  # Respeitar o tempo entre requisições
            response = requests.get(link, timeout=CONFIG['geral']['timeout_requisicao'])
            response.raise_for_status() # Lança um erro para status de erro HTTP (4xx ou 5xx)
            log.debug(f"Status da requisição: {response.status_code} - {response.reason}")
            chave_acesso_url = link.split('p=')[1].split('|')[0]
            log.debug(f"Chave de Acesso extraída do link: {chave_acesso_url}")
            html_nome = f"{CONFIG['geral']['nome_inicial_html']}{chave_acesso_url}.html" # Nome do arquivo com base na chave de acesso
            html_path = os.path.join(CONFIG['geral']['pasta_dados'], html_nome)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"HTML da resposta salvo em {html_path} para verificação.")

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- Extração da Chave de Acesso (do HTML, mais robusto) ---
        print("Extraindo dados da nota fiscal...")
        chave_acesso = "N/A"
        chave_tag = soup.find('span', class_=CONFIG['geral']['chave_acesso_class'])
        if chave_tag:
            chave_acesso = re.sub(r'\s+', '', chave_tag.text.strip())
        print(f"  Chave de Acesso: {chave_acesso}")

        # --- Extração dos Dados do Emitente ---
        nome_emitente = "N/A"
        cnpj_emitente = "N/A"
        endereco_emitente = "N/A"

        div_emitente = soup.find('div', class_=CONFIG['emitente']['div_principal_class'])
        if div_emitente:
            nome_emitente_tag = div_emitente.find('div', id=CONFIG['emitente']['nome_emitente_id'])
            if nome_emitente_tag:
                nome_emitente = nome_emitente_tag.text.strip()

            cnpj_tag = div_emitente.find('div', class_=CONFIG['emitente']['cnpj_endereco_class'])
            if cnpj_tag and "CNPJ:" in cnpj_tag.text:
                cnpj_emitente = cnpj_tag.text.replace("CNPJ:", "").strip()

            endereco_tags = div_emitente.find_all('div', class_=CONFIG['emitente']['cnpj_endereco_class'])
            if len(endereco_tags) > 1:
                endereco_emitente = endereco_tags[1].text.strip().replace('\n', ' ').replace(' ,', ',').strip()
                endereco_emitente = re.sub(r'\s+', ' ', endereco_emitente)

        print(f"  Emitente: {nome_emitente} (CNPJ: {cnpj_emitente})")
        print(f"  Endereço Emitente: {endereco_emitente}")


        # --- Extração do Valor Total da Nota e Desconto ---
        valor_total_nota = "N/A"
        valor_descontos = "N/A"
        valor_a_pagar = "N/A"

        total_nota_div = soup.find('div', id=CONFIG['totais']['div_principal_id'])
        if total_nota_div:
            for linha in total_nota_div.find_all('div', id=CONFIG['totais']['linha_total_id']):
                label_tag = linha.find('label')
                span_total_numb = linha.find('span', class_=CONFIG['totais']['valor_numb_class'])
                if label_tag and span_total_numb:
                    label_text = label_tag.text.strip()
                    value_text = span_total_numb.text.strip()

                    if "Valor total R$:" in label_text:
                        valor_total_nota = value_text
                    elif "Descontos R$:" in label_text:
                        valor_descontos = value_text
                    elif "Valor a pagar R$:" in label_text:
                        valor_a_pagar = value_text
        print(f"  Valor Total (Produtos/Serviços): {valor_total_nota}")
        print(f"  Descontos: {valor_descontos}")
        print(f"  Valor a Pagar: {valor_a_pagar}")


        # --- Extração dos Itens da Nota ---
        produtos = []
        tabela_itens = soup.find('table', id=CONFIG['itens']['tabela_itens_id'])
        if tabela_itens:
            for row in tabela_itens.find_all('tr', id=re.compile(CONFIG['itens']['linha_item_id_regex'])):
                td_nome_valor = row.find_all('td')
                if len(td_nome_valor) >= 2:
                    nome_produto_tag = td_nome_valor[0].find('span', class_=CONFIG['itens']['nome_produto_class'])
                    nome_produto = nome_produto_tag.text.strip() if nome_produto_tag else 'N/A'

                    qtd_tag = td_nome_valor[0].find('span', class_=CONFIG['itens']['qtd_class'])
                    qtd = qtd_tag.text.replace('Qtde.:', '').strip() if qtd_tag else 'N/A'

                    un_tag = td_nome_valor[0].find('span', class_=CONFIG['itens']['un_class'])
                    un = un_tag.text.replace('UN:', '').strip() if un_tag else 'N/A'

                    vl_unit_tag = td_nome_valor[0].find('span', class_=CONFIG['itens']['vl_unit_class'])
                    vl_unit = vl_unit_tag.text.replace('Vl. Unit.:', '').strip() if vl_unit_tag else 'N/A'

                    vl_total_item_tag = td_nome_valor[1].find('span', class_=CONFIG['itens']['vl_total_item_class'])
                    vl_total_item = vl_total_item_tag.text.strip() if vl_total_item_tag else 'N/A'

                    produtos.append({
                        'Nome Produto': nome_produto,
                        'Quantidade': qtd,
                        'Unidade': un,
                        'Valor Unitário': vl_unit,
                        'Valor Total Item': vl_total_item
                    })
        print(f"  Total de Itens encontrados: {len(produtos)}")
        for item in produtos:
            print(f"    - {item['Nome Produto']} (Qtd: {item['Quantidade']}, R$ {item['Valor Total Item']})")

        # --- Extração dos Dados do Consumidor ---
        cpf_consumidor = "N/A"
        nome_consumidor = "N/A"
        endereco_consumidor = "N/A"

        collapsible_consumidor_div = None
        all_collapsible_divs = soup.find_all('div', {'data-role': CONFIG['consumidor']['collapsible_div_data_role']})
        for div in all_collapsible_divs:
            h4_tag = div.find('h4')
            if h4_tag and CONFIG['consumidor']['collapsible_h4_text'] in h4_tag.text:
                collapsible_consumidor_div = div
                break

        if collapsible_consumidor_div:
            list_items = collapsible_consumidor_div.find('ul', {'data-role': CONFIG['consumidor']['list_view_data_role']}).find_all('li')
            for li in list_items:
                if 'CPF:' in li.text:
                    match_cpf = re.search(r'CPF:\s*([\d\.-]+)', li.text)
                    if match_cpf:
                        cpf_consumidor = match_cpf.group(1).strip()
                elif 'Nome:' in li.text:
                    nome_consumidor = li.text.replace('Nome:', '').strip()
                elif 'Logradouro:' in li.text:
                    endereco_consumidor = li.text.replace('Logradouro:', '').strip().replace('\n', ' ').replace(' ,', ',').strip()
                    endereco_consumidor = re.sub(r'\s+', ' ', endereco_consumidor)

        print(f"  Consumidor: {nome_consumidor} (CPF: {cpf_consumidor})")
        print(f"  Endereço Consumidor: {endereco_consumidor}")


        # --- Adicionar os Dados à Lista Final ---
        dados_notas.append({
            'Chave de Acesso': chave_acesso,
            'Nome Emitente': nome_emitente,
            'CNPJ Emitente': cnpj_emitente,
            'Endereco Emitente': endereco_emitente,
            'Valor Total Nota (Produtos/Serviços)': valor_total_nota,
            'Descontos': valor_descontos,
            'Valor a Pagar': valor_a_pagar,
            'Itens da Nota': produtos,
            'Nome Consumidor': nome_consumidor,
            'CPF Consumidor': cpf_consumidor,
            'Endereco Consumidor': endereco_consumidor,
            'Link Original': link
        })
        # Remove o link processado com sucesso da lista remaining_links
        remaining_links.remove(link)

    except requests.exceptions.RequestException as e:
        log.error(f"Erro de conexão ou HTTP ao acessar o link '{link}': '{e}'")
    except AttributeError as e:
        log.error(f"Erro de atributo (seletor não encontrado ou NoneType): '{e}', verifique o HTML salvo e ajuste os seletores de BeautifulSoup para este tipo de nota. HTML salvo em '{html_path}' se necessário.")
    except IndexError as e:
        log.error(f"Erro de índice de lista: '{e}', pode ser um problema na extração da chave de acesso ou nas colunas da tabela de itens. Link: {link}")
    except Exception as e:
        log.error(f"Ocorreu um erro inesperado: '{e}'. Link: {link}")


# --- Após o loop, escreve os links restantes de volta para o CSV de entrada ---
if remaining_links:
    df_remaining = pd.DataFrame(remaining_links)
    df_remaining.to_csv(path_entrada, index=False, header=False, mode='w', encoding='utf-8')
    print(f"\nLinks restantes atualizados em '{path_entrada}'")
else:
    # Se todos os links foram processados com sucesso, limpa o CSV de entrada
    open(path_entrada, 'w').close() # Limpa o arquivo
    print(f"\nTodos os links foram processados. '{path_entrada}' foi limpo.")


# --- Salvar os Dados em CSV ---
if dados_notas:
    for nota in dados_notas:
        if isinstance(nota.get('Itens da Nota'), list):
            nota['Itens da Nota'] = json.dumps(nota['Itens da Nota'], ensure_ascii=False)

    df_notas = pd.DataFrame(dados_notas)
    csv_nome = CONFIG['geral']['csv_saida']
    path_saida = os.path.join(CONFIG['geral']['pasta_dados'], csv_nome)

    # Verifica se o path existe para decidir se inclui o cabeçalho
    if os.path.exists(path_saida):
        df_notas.to_csv(path_saida, index=False, encoding='utf-8', mode='a', header=False)
    else:
        df_notas.to_csv(path_saida, index=False, encoding='utf-8', mode='a')
    print(f"\nDados salvos em '{path_saida}'")
else:
    print("\nNenhum dado foi extraído. Verifique os links e os seletores.")
