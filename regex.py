import re
from graph_builder import display_graph, build_operator_graph, optimize_operator_graph

# --- METADADOS ATUALIZADOS (conforme Imagem 01 do PDF) ---
METADATA = {
    'categoria': ['idcategoria', 'descricao'],
    'produto': ['idproduto', 'nome', 'descricao', 'preco', 'quantestoque', 'categoria_idcategoria'],
    'tipocliente': ['idtipocliente', 'descricao'],
    'cliente': ['idcliente', 'nome', 'email', 'nascimento', 'senha', 'tipocliente_idtipocliente', 'dataregistro'],
    'tipoendereco': ['idtipoendereco', 'descricao'],
    'endereco': ['idendereco', 'enderecopadrao', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 'cep', 'tipoendereco_idtipoendereco', 'cliente_idcliente'],
    'telefone': ['numero', 'cliente_idcliente'],
    'status': ['idstatus', 'descricao'],
    'pedido': ['idpedido', 'status_idstatus', 'datapedido', 'valortotalpedido', 'cliente_idcliente'],
    'pedido_has_produto': ['idpedidoproduto', 'pedido_idpedido', 'produto_idproduto', 'quantidade', 'precounitario']
}

def normalize_query(query: str) -> str:
    query = query.lower()
    query = re.sub(r'\s+', ' ', query) 
    query = query.strip().rstrip(';')   
    return query

#H1 --- Validação de Consulta SQL (HU1) ---
def validate_sql_query(query):
    query = normalize_query(query)
    errors = []

    if not re.search(r'select\s+.+\s+from\s+.+', query):
        errors.append("Erro de sintaxe: faltam SELECT e FROM.")
        return False, errors

    from_match = re.search(r'from\s+([a-z0-9_]+)', query)
    join_matches = re.findall(r'join\s+([a-z0-9_]+)', query)

    tables = []
    if from_match:
        tables.append(from_match.group(1))
    tables.extend(join_matches)
    tables = list(set(tables))

    if not tables:
        errors.append("Nenhuma tabela encontrada.")
        return False, errors

    for t in tables:
        if t not in METADATA:
            errors.append(f"Tabela inválida: {t}")

    if errors:
        return False, errors

    select_match = re.search(r'select\s+(.*?)\s+from', query)
    if not select_match:
        errors.append("Cláusula SELECT inválida.")
        return False, errors

    columns_str = select_match.group(1)
    columns = [c.strip().split('.')[-1] for c in columns_str.split(',') if c.strip() != '*']

    for c in columns:
        found = any(c in METADATA[t] for t in tables)
        if not found:
            errors.append(f"Coluna inválida: {c}")

    if re.search(r'where', query):
        if not re.search(r'(=|<>|<|>|<=|>=)', query):
            errors.append("Faltam operadores válidos em WHERE.")

    return (len(errors) == 0), errors


# --- Conversão para Álgebra Relacional (HU2) ---
def convert_sql_to_relational_algebra(query):
    query = normalize_query(query)

    select_match = re.search(r'select\s+(.*?)\s+from', query)
    columns_str = select_match.group(1).strip() if select_match else '*'

    from_match = re.search(r'from\s+([a-z0-9_]+)', query)
    base_table = from_match.group(1) if from_match else ''

    join_parts = re.findall(r'join\s+([a-z0-9_]+)\s+on\s+([a-z0-9_.]+\s*(?:=|<>|<|>|<=|>=)\s*[a-z0-9_.]+)', query)
    where_match = re.search(r'where\s+(.*)', query)

    op_replacements = {
        '<>': '≠',
        '<=': '≤',
        '>=': '≥'
    }

    def fix_ops(cond):
        for k, v in op_replacements.items():
            cond = cond.replace(k, v)
        return cond

    current_expr = base_table
    for join_table, condition in join_parts:
        condition = fix_ops(condition)
        current_expr = f"({current_expr} ⋈_{{{condition}}} {join_table})"

    if where_match:
        condition_str = fix_ops(where_match.group(1))
        current_expr = f"σ_{{{condition_str}}}({current_expr})"

    rel_alg = f"π_{{{columns_str}}}({current_expr})"
    return rel_alg


if __name__ == "__main__":
    from regex import validate_sql_query, convert_sql_to_relational_algebra

    query = """
    Select cliente.nome, pedido.idPedido, pedido.DataPedido, pedido.ValorTotalPedido
    from Cliente
    Join pedido on cliente.idcliente = pedido.Cliente_idCliente
    where cliente.TipoCliente_idTipoCliente = 1 and pedido.ValorTotalPedido = 0;
    """

    print("Consulta SQL:")
    print(query.strip()) 
    ok, errs = validate_sql_query(query)
    if ok:
        print("\nConsulta válida!")
        alg = convert_sql_to_relational_algebra(query)
        print("\nÁlgebra Relacional:")
        print(alg)

        print("\n--- Grafo Original ---")
        root = build_operator_graph(alg)
        display_graph(root)

        print("\n--- Grafo Otimizado ---")
        optimized = optimize_operator_graph(root)
        display_graph(optimized)
    else:
        print("Erros de validação:")
        for e in errs:
            print(" -", e)