import pandas as pd

def csv_entrada(caminho_csv_entrada='links.csv', caminho_csv_saida='links.csv'):
    """
    Lê um arquivo CSV com a estrutura fornecida, extrai apenas a coluna de links,
    removendo o cabeçalho e as colunas anteriores, e salva o resultado em um novo CSV.

    Args:
        caminho_csv_entrada (str): O caminho para o arquivo CSV original (ex: 'links.csv'). Padão links.csv.
        caminho_csv_saida (str): O caminho para o novo arquivo CSV com apenas os links. Padão links.csv.
    """
    try:
        # 1. Carregar o arquivo CSV
        # O pandas vai ler a primeira linha como cabeçalho por padrão.
        df = pd.read_csv(caminho_csv_entrada)

        # 2. Identificar a coluna de links
        # Pelo seu exemplo, a coluna de links é a 5ª coluna (índice 4, se começarmos do 0).
        # O nome da coluna é 'text' no cabeçalho fornecido.
        coluna_links = 'text'

        if coluna_links not in df.columns:
            return False, f"A coluna '{coluna_links}' não foi encontrada no arquivo CSV. Colunas disponíveis: {df.columns.tolist()}"

        # 3. Extrair apenas a coluna de links
        df_apenas_links = df[[coluna_links]]

        # 4. Salvar os links em um novo arquivo CSV
        # header=False: Não escreve o nome da coluna ('text') no novo arquivo.
        # index=False: Não escreve o índice do DataFrame no novo arquivo.
        # encoding='utf-8': Garante a compatibilidade com caracteres especiais nos links.
        df_apenas_links.to_csv(caminho_csv_saida, header=False, index=False, encoding='utf-8')

        return True, None

    except FileNotFoundError:
        return False, f"Erro: O arquivo '{caminho_csv_entrada}' não foi encontrado. Verifique o caminho."
    except pd.errors.EmptyDataError:
        return False, f"Erro: O arquivo '{caminho_csv_entrada}' está vazio ou mal formatado."
    except Exception as e:
        return False, f"Ocorreu um erro ao processar o arquivo CSV: {e}"

# --- Exemplo de Uso ---
if __name__ == "__main__":
    # Executar a função
    print(csv_entrada()[1])
