import re

# Definindo o esquema do banco de dados
METADATA = {
    'cliente': ['id', 'nome', 'email'],
    'pedido': ['id', 'valor_total', 'cliente_id'],
    'produto': ['id', 'nome', 'preco'],
}

def validar_consulta(consulta):
    # Expressão regular para extrair partes da consulta
    regex_select = r"SELECT\s+(.*?)\s+FROM\s+(\w+)(?:\s+JOIN\s+(\w+))?"
    match = re.search(regex_select, consulta, re.IGNORECASE)

    if not match:
        return "Consulta inválida: Sintaxe incorreta."

    colunas = match.group(1).split(',')
    tabela1 = match.group(2)
    tabela2 = match.group(3)

    # Validar tabelas
    tabelas_validas = [tabela1]
    if tabela2:
        tabelas_validas.append(tabela2)

    for tabela in tabelas_validas:
        if tabela not in METADATA:
            return f"Consulta inválida: Tabela '{tabela}' não existe."

    # Validar colunas
    for coluna in colunas:
        coluna = coluna.strip()
        if tabela1 and coluna not in METADATA[tabela1]:
            return f"Consulta inválida: Coluna '{coluna}' não existe na tabela '{tabela1}'."
        if tabela2 and coluna not in METADATA[tabela2]:
            return f"Consulta inválida: Coluna '{coluna}' não existe na tabela '{tabela2}'."

    return "Consulta válida."

# Testando o script com algumas consultas
consulta=input("Input Query: ")
resultado = validar_consulta(consulta)
print(f"Consulta: '{consulta}' -> Resultado: {resultado}")
