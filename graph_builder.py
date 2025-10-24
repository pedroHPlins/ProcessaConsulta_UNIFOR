import re

# --- Nó de Operador (mesmo do passo anterior) ---
class OperatorNode:
    def __init__(self, operator, children=None):
        self.operator = operator
        self.children = children if children else []

    def __repr__(self):
        return f"OperatorNode({self.operator})"


# --- Construção do Grafo (HU3, igual antes) ---
def build_operator_graph(rel_alg_expr):
    tokens = re.split(r'(?<=\))', rel_alg_expr)
    tokens = [t.strip() for t in tokens if t.strip()]

    if not rel_alg_expr.startswith("π_"):
        raise ValueError("Expressão inválida ou sem projeção externa.")

    proj_match = re.match(r'π_\{(.*?)\}\((.*)\)', rel_alg_expr)
    projection_attrs = proj_match.group(1)
    inner_expr = proj_match.group(2)
    proj_node = OperatorNode(f"π {{{projection_attrs}}}")

    if inner_expr.startswith("σ_"):
        sel_match = re.match(r'σ_\{(.*?)\}\((.*)\)', inner_expr)
        condition = sel_match.group(1)
        join_expr = sel_match.group(2)
        sel_node = OperatorNode(f"σ {{{condition}}}")
        proj_node.children.append(sel_node)
        parent = sel_node
    else:
        join_expr = inner_expr
        parent = proj_node

    join_pattern = r'\((.*?)\s⋈_\{(.*?)\}\s(.*?)\)'
    join_match = re.match(join_pattern, join_expr)

    if join_match:
        left_table = join_match.group(1)
        condition = join_match.group(2)
        right_table = join_match.group(3)
        join_node = OperatorNode(f"⋈ {{{condition}}}", [OperatorNode(left_table), OperatorNode(right_table)])
        parent.children.append(join_node)
    else:
        parent.children.append(OperatorNode(join_expr))

    return proj_node


def display_graph(node, level=0):
    indent = "   " * level
    print(f"{indent}- {node.operator}")
    for child in node.children:
        display_graph(child, level + 1)


# --- HU4: Otimização da árvore de operadores ---
def optimize_operator_graph(node):
    """
    Aplica heurísticas básicas de otimização:
      1. Empurra σ para baixo (pushing selection)
      2. Ordena junções restritivas primeiro
      3. Mantém π apenas no topo
    """
    if node is None:
        return None

    # Otimiza recursivamente os filhos
    node.children = [optimize_operator_graph(c) for c in node.children]

    # Heurística 1: empurrar seleção σ para mais próximo das tabelas
    if node.operator.startswith("σ") and len(node.children) == 1:
        child = node.children[0]
        if child.operator.startswith("⋈"):
            cond = node.operator[2:].strip(" {}")
            conds = [c.strip() for c in cond.split("and")]
            left = child.children[0]
            right = child.children[1]
            new_left = left
            new_right = right
            for c in conds:
                if left.operator in c:
                    new_left = OperatorNode(f"σ {{{c}}}", [left])
                elif right.operator in c:
                    new_right = OperatorNode(f"σ {{{c}}}", [right])
            new_join = OperatorNode(child.operator, [new_left, new_right])
            return new_join  

    # Heurística 2: ordenar junções restritivas primeiro
    if node.operator.startswith("⋈") and len(node.children) == 2:
        left, right = node.children
        restr_score = node.operator.count("and") + node.operator.count("or")
        if restr_score > 1:
            node.operator = node.operator.replace("and", "∧")  

    return node



