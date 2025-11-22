import re
import sys
import os

# --- Definição dos Tipos de Tokens e Palavras Reservadas ---
# Usamos um dicionário para verificar se um identificador é palavra reservada
RESERVED_WORDS = {
    'program': 'PROGRAM', 'var': 'VAR', 'integer': 'INTEGER', 'real': 'REAL',
    'procedure': 'PROCEDURE', 'begin': 'BEGIN', 'end': 'END', 'if': 'IF',
    'then': 'THEN', 'else': 'ELSE', 'while': 'WHILE', 'do': 'DO',
    'read': 'READ', 'write': 'WRITE'
}

# Lista de padrões (Regex) ordenados por prioridade
# O formato é: (Nome do Token, Regex)
TOKEN_PATTERNS = [
    ('COMMENT', r'\{[^}]*\}|/\*[\s\S]*?\*/'), # Ignorar comentários { } ou /* */
    ('WHITESPACE', r'\s+'),                   # Ignorar espaços
    ('NUM_REAL', r'\d+\.\d+'),                # 10.5
    ('NUM_INT', r'\d+'),                      # 10
    ('ASSIGN', r':='),                        # :=
    ('OP_REL', r'>=|<=|<>|=|<|>'),            # Relacionais
    ('OP_ADD', r'[+-]'),                      # + -
    ('OP_MUL', r'[*/]'),                      # * /
    ('DELIM', r'[;.:(),$]'),                  # Delimitadores
    ('ID', r'[a-zA-Z][a-zA-Z0-9_]*'),         # Identificadores
    ('UNKNOWN', r'.'),                        # Qualquer outra coisa (Erro)
]

class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}', Line:{self.line})"

def ler_codigo_fonte(nome_arquivo):
    if not os.path.exists(nome_arquivo):
        # Cria arquivo padrão se não existir
        with open(nome_arquivo, 'w') as f:
            f.write("program teste var a: integer; begin a := 10; end.")
    
    with open(nome_arquivo, 'r', encoding='utf-8') as f:
        return f.read()

def gerar_tokens(codigo):
    tokens = []
    linha_atual = 1
    posicao = 0
    
    # Compilar todos os regex em um único padrão grande
    # Ex: (?P<NUM_INT>\d+) | (?P<ASSIGN>:=) ...
    regex_parts = []
    for name, pattern in TOKEN_PATTERNS:
        regex_parts.append(f'(?P<{name}>{pattern})')
    
    master_regex = re.compile('|'.join(regex_parts))
    
    # Iterar sobre o código encontrando os padrões
    for match in master_regex.finditer(codigo):
        tipo = match.lastgroup
        valor = match.group(tipo)
        
        # Atualizar contagem de linhas baseada nos newlines encontrados
        if tipo == 'WHITESPACE':
            linha_atual += valor.count('\n')
            continue
            
        if tipo == 'COMMENT':
            linha_atual += valor.count('\n')
            continue
            
        if tipo == 'UNKNOWN':
            print(f"Erro Léxico: Caractere inesperado '{valor}' na linha {linha_atual}")
            continue
            
        # Se for identificador, verifica se é palavra reservada
        if tipo == 'ID':
            tipo = RESERVED_WORDS.get(valor.lower(), 'IDENT')
            
        tokens.append(Token(tipo, valor, linha_atual))
        
    return tokens

def main():
    # Define arquivo de entrada
    arquivo_entrada = 'correto.pascal.txt'
    if len(sys.argv) > 1:
        arquivo_entrada = sys.argv[1]
        
    print(f"--- Lendo arquivo: {arquivo_entrada} ---")
    codigo = ler_codigo_fonte(arquivo_entrada)
    
    tokens = gerar_tokens(codigo)
    
    # Salva e imprime tokens
    caminho_saida = 'tokens_saida.txt'
    with open(caminho_saida, 'w') as f:
        for t in tokens:
            print(t)
            f.write(str(t) + '\n')
            
    print(f"\nSucesso! {len(tokens)} tokens gerados em '{caminho_saida}'.")

if __name__ == '__main__':
    main()