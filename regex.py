
import re

METADATA = {
    'cliente': ['idcliente', 'nome', 'email', 'telefone', 'endereco'],
    'produto': ['idproduto', 'nomeproduto', 'descricao', 'preco', 'estoque'],
    'pedido': ['idpedido', 'idcliente', 'datapedido', 'valortotalpedido', 'status'],
    'itempedido': ['iditempedido', 'idpedido', 'idproduto', 'quantidade', 'precounitario'],
    'fornecedor': ['idfornecedor', 'nomefornecedor', 'contato', 'endereco'],
    'produtofornecedor': ['idproduto', 'idfornecedor', 'custo']
}

def convert_sql_to_relational_algebra(query):
    query = query.lower()
    
    # --- 1. Extração de Componentes (Assumindo sintaxe SELECT...FROM...[JOIN]...[WHERE]) ---
    
    # a. Projeção (SELECT)
    # Procura por 'select' e tudo até 'from' (ignora aliases simples por simplicidade)
    select_match = re.search(r'select\s+(.*?)\s+from', query)
    columns_str = select_match.group(1).strip() if select_match else '*'
    
    # b. Junções/Produtos Cartesianos (FROM e JOIN)
    # Tabela principal FROM
    from_match = re.search(r'from\s+([a-z0-9_]+)', query)
    base_table = from_match.group(1) if from_match else ''
    
    # JOINS e condições ON
    join_parts = re.findall(r'(join\s+([a-z0-9_]+)(\s+on\s+([a-z0-9_.]+\s*[=<>!]+\s*[a-z0-9_.]+)))', query)
    
    # c. Seleção (WHERE)
    # Procura por 'where' e tudo até o final ou até a próxima cláusula importante (ORDER BY, GROUP BY, etc.)
    where_match = re.search(r'where\s+(.*?)(?:\s+group\s+by|\s+order\s+by|$)', query)
    condition_str = where_match.group(1).strip() if where_match else ''

    # --- 2. Construção da Expressão de Álgebra Relacional (do interior para o exterior) ---
    
    # Parte interna: Junções (Produto Cartesiano + Seleção ou Junção Natural/Theta Join)
    
    # Junção (JOIN) e Condição ON
    current_expression = base_table
    join_conditions = []
    
    for _, join_table, _, on_condition in join_parts:
        if on_condition:
            # Junção Theta: T1 \bowtie_{condição} T2
            current_expression = f"({current_expression} \\bowtie_{{{on_condition.strip()}}} {join_table})"
            # Limpa a condição ON para evitar duplicidade na cláusula WHERE (se a condição for de seleção)
            # Nota: Em um processador real, a junção Theta é preferida, movendo a condição ON para o \bowtie.
        else:
            # Produto Cartesiano: T1 \times T2
            current_expression = f"({current_expression} \\times {join_table})"
    
    # Seleção (\sigma)
    if condition_str:
        # Aplica a seleção (WHERE) na expressão de junção
        relational_algebra = f"\\sigma_{{{condition_str}}}({current_expression})"
    else:
        relational_algebra = current_expression
        
    # Projeção (\pi)
    # Aplica a projeção (SELECT) na expressão resultante
    relational_algebra = f"\\pi_{{{columns_str}}}({relational_algebra})"
    
    return relational_algebra

def validate_sql_query(query):
    query = query.lower()
    errors = []

    # 1. Validar a sintaxe básica (SELECT, FROM, WHERE, JOIN, ON)
    if not re.search(r'select\s+.+\s+from\s+.+', query):
        errors.append("Erro de sintaxe: A consulta deve conter SELECT e FROM.")
        return False, errors

    # Extrair tabelas
    from_match = re.search(r'from\s+([a-z0-9_]+)', query)
    join_matches = re.findall(r'join\s+([a-z0-9_]+)', query)
    
    tables_in_query = []
    if from_match:
        tables_in_query.append(from_match.group(1))
    tables_in_query.extend(join_matches)
    
    tables_in_query = list(set(tables_in_query)) # Remover duplicatas

    if not tables_in_query:
        errors.append("Erro: Nenhuma tabela encontrada na cláusula FROM/JOIN.")
        return False, errors

    # Validar tabelas
    for table in tables_in_query:
        if table not in METADATA:
            errors.append(f"Erro: Tabela '{table}' não existe no esquema.")

    if errors: # Se já houver erros de tabela, não prosseguir com colunas
        return False, errors

    # Extrair colunas
    select_clause = re.search(r'select\s+(.*?)\s+from', query)
    if select_clause:
        columns_str = select_clause.group(1)
        # Remove aliases like 'col as alias' or 'table.col' to get just 'col'
        columns_in_query = [col.split('.')[-1].strip() for col in columns_str.split(',')]
        columns_in_query = [col for col in columns_in_query if col != '*'] # Ignore '*' for now
    else:
        errors.append("Erro: Não foi possível extrair colunas da cláusula SELECT.")
        return False, errors

    # Validar colunas
    for col in columns_in_query:
        found_in_any_table = False
        for table in tables_in_query:
            if col in METADATA.get(table, []):
                found_in_any_table = True
                break
        if not found_in_any_table:
            errors.append(f"Erro: Coluna '{col}' não encontrada em nenhuma das tabelas especificadas ({', '.join(tables_in_query)}).")

    if errors:
        return False, errors

    return True, []

# --- Exemplos de Uso ---
if __name__ == "__main__":

    query = input("Input SQL Query: ")

    print(f"Consulta: {query}")
    is_valid, validation_errors = validate_sql_query(query)
    if is_valid:
        alg_query = convert_sql_to_relational_algebra(query)
        print ("Alg:",alg_query)
        print("Resultado: Consulta SQL válida.")
    else:
        print("Resultado: Consulta SQL inválida.")
        for error in validation_errors:
            print(f"  - {error}")


