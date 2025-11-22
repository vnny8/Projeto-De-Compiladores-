import ply.yacc as yacc
import ply.lex as lex
import sys
import os

# ==============================================================================
# CONFIGURAÇÃO DE PATHS (Para rodar de qualquer lugar)
# ==============================================================================
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_ATUAL) # Sobe um nível

# Adiciona pastas ao path para importar o semântico
sys.path.append(os.path.join(DIRETORIO_RAIZ, 'AnalisadorSemantico'))

# Configura caminhos dos arquivos de dados
# Tenta achar Dados na raiz (padrão) ou na pasta atual
PASTA_DADOS = os.path.join(DIRETORIO_RAIZ, 'Dados')
if not os.path.exists(PASTA_DADOS):
    PASTA_DADOS = os.path.join(DIRETORIO_ATUAL, 'Dados')

ARQUIVO_TOKENS = os.path.join(PASTA_DADOS, 'tokens.txt')
ARQUIVO_CODIGO_OBJETO = os.path.join(PASTA_DADOS, 'codigo_objeto.txt')

# Importação do Semântico
try:
    from analisadorSemantico import AnalisadorSemantico
except ImportError:
    # Fallback caso o nome do arquivo seja diferente ou path falhe
    print("AVISO: Não foi possível importar 'analisadorSemantico'. Verifique o nome do arquivo.")
    # Classe Mock para não quebrar se o arquivo não estiver lá
    class AnalisadorSemantico:
        def adicionar_variavel(self, n, t, c='var'): return 0
        def verificar_declaracao(self, n): return 0
        def obter_tipo(self, n): return 'INTEGER'
        def entrar_escopo(self): pass
        def sair_escopo(self): pass

# ==============================================================================
# CLASSE AUXILIAR: GERADOR DE CÓDIGO
# ==============================================================================
# Esta classe é o "cérebro" da geração de código. Ela é responsável por guardar
# as instruções da máquina hipotética e conversar com o analisador semântico.

class GeradorCodigo:
    def __init__(self):
        # Aqui eu inicializo a lista que vai guardar as instruções geradas (ex: INPP, SOMA).
        self.codigo = []
        
        # Eu instancio o Analisador Semântico aqui dentro.
        # Isso permite que eu valide os tipos e escopos ANTES de gerar o código.
        self.semantico = AnalisadorSemantico()

    def adicionar_instrucao(self, instrucao, argumento=None):
        """
        Eu uso esta função sempre que preciso escrever uma nova linha no código objeto.
        Se a instrução tiver argumento (ex: CRCT 10), eu formato a string.
        Caso contrário (ex: SOMA), eu salvo apenas o comando.
        """
        linha = f"{instrucao} {argumento}" if argumento is not None else instrucao
        self.codigo.append(linha)
        
        # Eu retorno o índice (número da linha) atual.
        # Isso é CRUCIAL para o 'Backpatching': eu preciso saber o endereço dessa linha
        # caso eu precise fazer um desvio (GOTO/JUMP) para cá depois.
        return len(self.codigo) - 1

    def corrigir_salto(self, indice_instrucao, destino):
        """
        Técnica de Backpatching:
        Quando eu leio um IF ou WHILE, eu gero um desvio (DSVF) mas ainda não sei
        onde o bloco termina. Então eu deixo um "buraco" ou placeholder.
        Mais tarde, quando chego no fim do bloco, chamo esta função para voltar
        naquela linha antiga e preencher o endereço correto do destino.
        """
        # Pego a instrução original (ex: "DSVF -1") e separo o comando
        instrucao_atual = self.codigo[indice_instrucao].split()[0]
        # Reescrevo a linha com o destino correto (ex: "DSVF 50")
        self.codigo[indice_instrucao] = f"{instrucao_atual} {destino}"

# Crio uma instância global do gerador para ser acessada por todas as regras do parser abaixo.
gerador = GeradorCodigo()


# ==============================================================================
# PARTE 1: ANALISADOR LÉXICO (DEFINIÇÕES DE TOKENS)
# ==============================================================================
# Aqui eu defino o vocabulário da linguagem. O PLY usa isso para quebrar o texto em tokens.

# Lista oficial de tokens que meu compilador reconhece.
tokens = (
    'PROGRAM', 'VAR', 'INTEGER', 'REAL', 'PROCEDURE',
    'BEGIN', 'END', 'IF', 'THEN', 'ELSE', 'WHILE', 'DO',
    'READ', 'WRITE', 'IDENT', 'NUM_INT', 'NUM_REAL',
    'ASSIGN', 'EQ', 'NEQ', 'LT', 'GT', 'LTE', 'GTE',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'SEMICOLON', 'DOT', 'COLON', 'LPAREN', 'RPAREN', 'COMMA', 'DOLLAR'
)

# Dicionário de Palavras Reservadas.
# Eu uso isso para distinguir se 'begin' é uma variável (identificador) ou o comando BEGIN.
reserved = {
    'program': 'PROGRAM', 'var': 'VAR', 'integer': 'INTEGER', 'real': 'REAL',
    'procedure': 'PROCEDURE', 'begin': 'BEGIN', 'end': 'END', 'if': 'IF',
    'then': 'THEN', 'else': 'ELSE', 'while': 'WHILE', 'do': 'DO',
    'read': 'READ', 'write': 'WRITE'
}

# --- Expressões Regulares Simples (Regex) ---
# Aqui eu ensino o Lexer a reconhecer os símbolos visuais da linguagem.

t_ASSIGN = r':='     # Atribuição
t_EQ = r'='          # Igual
t_NEQ = r'<>'        # Diferente (Pascal usa <>)
t_LTE = r'<='        # Menor ou Igual
t_GTE = r'>='        # Maior ou Igual
t_LT = r'<'          # Menor
t_GT = r'>'          # Maior
t_PLUS = r'\+'       # Soma (uso \ para escapar o caractere especial)
t_MINUS = r'-'       # Subtração
t_TIMES = r'\*'      # Multiplicação
t_DIVIDE = r'/'      # Divisão
t_SEMICOLON = r';'   # Ponto e vírgula
t_DOT = r'\.'        # Ponto final
t_COLON = r':'       # Dois pontos
t_LPAREN = r'\('     # Abre parênteses
t_RPAREN = r'\)'     # Fecha parênteses
t_COMMA = r','       # Vírgula
t_DOLLAR = r'\$'     # Cifrão (delimitador de bloco na gramática LALG)

# Caracteres a serem ignorados (Espaços e Tabulações)
t_ignore = ' \t'

# --- Funções para Tokens Complexos ---
# Para tokens que exigem processamento (como converter string para número), eu uso funções.

def t_COMMENT(t):
    # Expressão Regular para ignorar comentários.
    # Pega tudo entre { } OU tudo entre /* */
    r'\{[^}]*\}|/\*[\s\S]*?\*/'
    pass # 'pass' significa: não gere token, apenas ignore e continue.

def t_NUM_REAL(t):
    # Reconhece números com ponto flutuante (ex: 10.5)
    r'\d+\.\d+'
    t.value = float(t.value) # Converto o texto para float do Python
    return t

def t_NUM_INT(t):
    # Reconhece números inteiros (apenas dígitos)
    r'\d+'
    t.value = int(t.value) # Converto o texto para int do Python
    return t

def t_IDENT(t):
    # Reconhece identificadores. Regra: Deve começar com letra.
    r'[a-zA-Z][a-zA-Z0-9_]*'
    # Aqui eu verifico: se a palavra achada está no dicionário 'reserved',
    # então é uma palavra reservada (ex: IF), senão é um IDENT (nome de variável).
    t.type = reserved.get(t.value.lower(), 'IDENT')
    return t

def t_newline(t):
    # Esta função conta as linhas. É essencial para mostrar onde o erro ocorreu.
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    # Tratamento de erro léxico: Caractere inválido encontrado.
    print(f"Erro Léxico: Caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1) # Pulo o caractere ruim e tento continuar.

# Inicializo o Lexer com as regras acima
lexer = lex.lex()

# --- Função Auxiliar de Saída ---

def gerar_arquivo_tokens_formatado(codigo_fonte):
    """
    Esta função não faz parte da compilação em si, mas foi pedida no projeto.
    Ela gera um arquivo 'tokens.txt' listando todos os tokens encontrados,
    formatados como [Tipo, Valor].
    """
    print(f"--- Gerando arquivo de tokens em: {ARQUIVO_TOKENS} ---")
    # Crio um lexer temporário só para isso
    meu_lexer = lex.lex()
    meu_lexer.input(codigo_fonte)
    lista_saida = []
    
    while True:
        tok = meu_lexer.token()
        if not tok: break # Fim do arquivo
        
        # Traduzo os nomes técnicos do PLY para nomes amigáveis
        tipo_formatado = ""
        if tok.type in reserved.values(): tipo_formatado = "Palavras Reservadas"
        elif tok.type == 'IDENT': tipo_formatado = "Identificador"
        elif tok.type in ['NUM_INT', 'NUM_REAL']: tipo_formatado = "Numeral"
        elif tok.type in ['ASSIGN', 'EQ', 'NEQ', 'LT', 'GT', 'LTE', 'GTE', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE']: tipo_formatado = "Operador"
        else: tipo_formatado = "Pontuacao"
            
        lista_saida.append(f"[{tipo_formatado}, {tok.value}]")
        
    # Salvo no arquivo
    with open(ARQUIVO_TOKENS, 'w') as f:
        for l in lista_saida: f.write(l + '\n')
    print("Arquivo de tokens gerado com sucesso.")


# ==============================================================================
# PARTE 2: ANALISADOR SINTÁTICO E SEMÂNTICO (PARSER)
# ==============================================================================
# Aqui defino a gramática BNF. Cada função 'p_' representa uma regra de produção.
# Quando o parser reconhece a estrutura, ele executa o código Python dentro da função.

def p_programa(p):
    '''programa : PROGRAM IDENT corpo DOT'''
    # Regra inicial: Programa começa com 'program', tem um nome, um corpo e termina com ponto.
    # Quando chego aqui, o programa todo foi processado com sucesso.
    gerador.adicionar_instrucao("PARA") # Gero a instrução de parada da máquina.
    print("Análise Sintática e Semântica concluída com sucesso!")

def p_corpo(p):
    '''corpo : dc BEGIN comandos END'''
    # Estrutura do corpo: Declarações (dc) -> begin -> comandos -> end
    pass

# --- Regras de Declaração (dc) ---

def p_dc(p):
    # CORREÇÃO AQUI: Adicionado 'dc_p mais_dc' para permitir recursão de procedimentos
    '''dc : dc_v mais_dc
          | dc_p mais_dc
          | empty'''
    pass

def p_mais_dc(p):
    '''mais_dc : SEMICOLON dc
               | empty'''
    pass

def p_dc_v(p):
    '''dc_v : VAR variaveis COLON tipo_var'''
    # DECLARAÇÃO DE VARIÁVEIS (ex: var a, b : integer)
    # INTEGRAÇÃO SEMÂNTICA:
    lista_vars = p[2] # Lista de nomes vinda de p_variaveis
    tipo = p[4]       # Tipo (REAL ou INTEGER) vindo de p_tipo_var
    
    for var_nome in lista_vars:
        try:
            # Passo 1: Registro no Semântico. Se duplicar, ele dá erro.
            gerador.semantico.adicionar_variavel(var_nome, tipo)
            
            # Passo 2: Se ok, aloco espaço na memória (Geração de Código)
            gerador.adicionar_instrucao("ALME", 1)
        except Exception as e:
            print(f"ERRO SEMÂNTICO na linha {p.lineno(1)}: {e}")
            sys.exit(1) # Interrompo a compilação

def p_tipo_var(p):
    '''tipo_var : REAL
                | INTEGER'''
    p[0] = p[1] # Retorno o tipo encontrado para usar na regra acima

def p_variaveis(p):
    '''variaveis : IDENT mais_var'''
    # Recursão para pegar múltiplas variáveis (a, b, c)
    # Se p[2] retornar uma lista, somo com a variável atual.
    if p[2]: p[0] = [p[1]] + p[2]
    else: p[0] = [p[1]]

def p_mais_var(p):
    '''mais_var : COMMA variaveis
                | empty'''
    if len(p) > 2: p[0] = p[2] # Continua a lista
    else: p[0] = [] # Fim da lista

# --- Regras de Procedures ---
# Aqui adicionamos os marcadores para abrir e fechar escopo corretamente
def p_inicio_escopo(p):
    '''inicio_escopo : empty'''
    gerador.semantico.entrar_escopo()

def p_fim_escopo(p):
    '''fim_escopo : empty'''
    gerador.semantico.sair_escopo()

def p_dc_p(p):
    # Regra Procedure: procedure nome (params) corpo
    # Usamos inicio_escopo e fim_escopo para delimitar variáveis locais
    '''dc_p : PROCEDURE IDENT inicio_escopo parameters corpo_p fim_escopo'''
    pass

def p_parameters(p):
    '''parameters : LPAREN lista_par RPAREN
                  | empty'''
    pass

def p_lista_par(p):
    '''lista_par : variaveis COLON tipo_var mais_par'''
    # Parâmetros de função
    lista_vars = p[1]
    tipo = p[3]
    for var_nome in lista_vars:
        try:
            gerador.semantico.adicionar_variavel(var_nome, tipo)
            gerador.adicionar_instrucao("ALME", 1)
        except Exception as e:
            print(f"ERRO SEMÂNTICO (Parâmetros): {e}")
            sys.exit(1)
    pass

def p_mais_par(p):
    '''mais_par : SEMICOLON lista_par
                | empty'''
    pass

def p_corpo_p(p):
    # CORREÇÃO AQUI: Removido 'SEMICOLON' do final.
    # O ponto e vírgula é tratado pela regra 'mais_dc' lá em cima.
    '''corpo_p : dc_loc BEGIN comandos END'''
    pass

# --- CORREÇÃO AQUI: Declarações Locais ---
# Ajustei aqui para não exigir ponto e vírgula no final da última declaração

def p_dc_loc(p):
    '''dc_loc : dc_v mais_dcloc
              | empty'''
    pass

def p_mais_dcloc(p):
    '''mais_dcloc : SEMICOLON dc_v mais_dcloc
                  | empty'''
    pass
# -----------------------------------------

# --- Regras de Comandos ---

def p_comandos(p):
    '''comandos : comando mais_comandos'''
    pass

def p_mais_comandos(p):
    '''mais_comandos : comandos
                     | empty'''
    pass

def p_pt_virgula_opc(p):
    '''pt_virgula_opc : SEMICOLON
                      | empty'''
    pass

def p_comando_read(p):
    '''comando : READ LPAREN IDENT RPAREN pt_virgula_opc'''
    # Comando READ (Leitura)
    gerador.adicionar_instrucao("LEIT") # Gera instrução de ler input
    try:
        # Validação Semântica: A variável existe?
        endereco = gerador.semantico.verificar_declaracao(p[3])
        # Se existe, salvo o valor lido no endereço dela (ARMZ)
        gerador.adicionar_instrucao("ARMZ", endereco)
    except Exception as e:
        print(f"ERRO SEMÂNTICO: {e}")
        sys.exit(1)

def p_comando_write(p):
    '''comando : WRITE LPAREN IDENT RPAREN pt_virgula_opc'''
    # Comando WRITE (Escrita)
    try:
        # Validação Semântica: Busco onde a variável está
        endereco = gerador.semantico.verificar_declaracao(p[3])
        # Carrego o valor dela pra pilha (CRVL)
        gerador.adicionar_instrucao("CRVL", endereco)
        # Imprimo (IMPR)
        gerador.adicionar_instrucao("IMPR")
    except Exception as e:
        print(f"ERRO SEMÂNTICO: {e}")
        sys.exit(1)

def p_comando_assign(p):
    '''comando : IDENT ASSIGN expressao pt_virgula_opc'''
    # Comando de Atribuição (Ex: x := 10)
    try:
        # Validação Semântica: Variável alvo existe?
        endereco = gerador.semantico.verificar_declaracao(p[1])
        
        # Nota: O valor da 'expressao' já foi calculado e está no topo da pilha
        # graças à execução prévia da regra 'expressao' (parser ascendente).
        
        # Então eu só salvo o topo da pilha na variável (ARMZ)
        gerador.adicionar_instrucao("ARMZ", endereco)
    except Exception as e:
        print(f"ERRO SEMÂNTICO: {e}")
        sys.exit(1)

def p_comando_if(p):
    '''comando : IF condicao THEN comandos pfalsa DOLLAR'''
    # BACKPATCHING DO IF
    # Quando executei 'condicao', gerei um DSVF (Desvio se Falso) incompleto.
    indice_dsvf = p[2]
    
    # Agora eu sei onde o bloco THEN termina (é a linha atual).
    destino_final = len(gerador.codigo)
    
    if p[5] is not None:
        # Caso com ELSE: O salto do IF deve ir para o ELSE.
        # E o ELSE deve ter gerado um salto para o fim.
        # Simplificação: Corrijo o salto do ELSE para vir para cá (fim).
        indice_dsvi_then = p[5]
        gerador.corrigir_salto(indice_dsvi_then, destino_final)
    else:
        # Caso sem ELSE: O salto do IF vem direto para cá (fim).
        gerador.corrigir_salto(indice_dsvf, destino_final)

def p_condicao(p):
    '''condicao : expressao relacao expressao'''
    # Comparação: Exp1 OP Exp2
    # A regra 'relacao' já gerou a instrução de comparação (ex: CMEN).
    # Se for falso, eu tenho que pular o bloco THEN.
    # Como não sei o tamanho do bloco ainda, gero um DSVF com placeholder (-1).
    instrucao_salto = gerador.adicionar_instrucao("DSVF", -1)
    # Retorno o índice desse salto para a regra 'comando_if' corrigir depois.
    p[0] = instrucao_salto

def p_pfalsa(p):
    '''pfalsa : ELSE comandos
              | empty'''
    # Regra auxiliar para o ELSE
    if len(p) > 2:
        p[0] = None 
    else:
        p[0] = None

def p_comando_while(p):
    '''comando : WHILE condicao DO comandos DOLLAR'''
    # BACKPATCHING DO WHILE
    indice_dsvf = p[2] # Pego o índice do salto gerado na condição
    
    # O destino da saída é a linha atual (fim do loop)
    destino_saida = len(gerador.codigo)
    
    # Corrijo o DSVF para pular para fora do loop se a condição falhar
    gerador.corrigir_salto(indice_dsvf, destino_saida)

# --- Regras de Suporte (Chamadas de Procedimentos) ---
def p_comando_chamada(p):
    '''comando : IDENT lista_arg pt_virgula_opc'''
    pass

def p_lista_arg(p):
    '''lista_arg : LPAREN argumentos RPAREN
                 | empty'''
    pass

def p_argumentos(p):
    '''argumentos : IDENT mais_ident'''
    pass

def p_mais_ident(p):
    '''mais_ident : COMMA argumentos
                  | empty'''
    pass

# --- Regras Matemáticas e Lógicas ---

def p_relacao(p):
    '''relacao : EQ
               | NEQ
               | GTE
               | LTE
               | GT
               | LT'''
    # Mapeio os operadores do código fonte para instruções da VM
    if p[1] == '=': gerador.adicionar_instrucao("CPIG")  # Compara Igual
    elif p[1] == '<>': gerador.adicionar_instrucao("CDIF") # Compara Diferente
    elif p[1] == '>=': gerador.adicionar_instrucao("CMAI") # Compara Maior/Igual (Aprox)
    elif p[1] == '<=': gerador.adicionar_instrucao("CMEN") # Compara Menor/Igual
    elif p[1] == '>': gerador.adicionar_instrucao("CMAI")  # Compara Maior
    elif p[1] == '<': gerador.adicionar_instrucao("CMEN")  # Compara Menor

def p_expressao(p):
    '''expressao : termo outros_termos'''
    pass

def p_outros_termos(p):
    '''outros_termos : op_ad termo outros_termos
                     | empty'''
    pass

def p_op_ad(p):
    '''op_ad : PLUS
             | MINUS'''
    # Operações de Soma e Subtração
    if p[1] == '+': gerador.adicionar_instrucao("SOMA")
    elif p[1] == '-': gerador.adicionar_instrucao("SUBT")

def p_termo(p):
    '''termo : op_un fator mais_fatores'''
    pass

def p_op_un(p):
    '''op_un : MINUS
             | empty'''
    pass

def p_mais_fatores(p):
    '''mais_fatores : op_mul fator mais_fatores
                    | empty'''
    pass

def p_op_mul(p):
    '''op_mul : TIMES
              | DIVIDE'''
    # Operações de Multiplicação e Divisão
    if p[1] == '*': gerador.adicionar_instrucao("MULT")
    elif p[1] == '/': gerador.adicionar_instrucao("DIVI")

def p_fator_id(p):
    '''fator : IDENT'''
    # Fator Variável: Se aparece um nome na conta (ex: a + 10)
    try:
        # Busco o endereço da variável
        endereco = gerador.semantico.verificar_declaracao(p[1])
        # Carrego o valor da memória para o topo da pilha (CRVL)
        gerador.adicionar_instrucao("CRVL", endereco)
    except Exception as e:
        print(f"ERRO SEMÂNTICO: {e}")
        sys.exit(1)

def p_fator_num(p):
    '''fator : NUM_INT
             | NUM_REAL'''
    # Fator Numérico: Se aparece um número literal (ex: 10)
    # Carrego a constante para o topo da pilha (CRCT)
    gerador.adicionar_instrucao("CRCT", p[1])

def p_fator_grupo(p):
    '''fator : LPAREN expressao RPAREN'''
    # Expressão entre parênteses: A lógica já foi resolvida recursivamente em 'expressao'
    pass

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    # Tratamento de Erro Sintático
    if p:
        print(f"Erro Sintático: Token inesperado '{p.value}' na linha {p.lineno}")
    else:
        print("Erro Sintático: Fim de arquivo inesperado")

# Inicializo o Parser
parser = yacc.yacc()

if __name__ == '__main__':
    try:
        with open(os.path.join(PASTA_DADOS, 'codigo.txt'), 'r') as f:
            code = f.read()
        gerar_arquivo_tokens_formatado(code)
        gerador.adicionar_instrucao("INPP")
        parser.parse(code, lexer=lexer)
        with open(ARQUIVO_CODIGO_OBJETO, 'w') as f:
            for l in gerador.codigo: f.write(l+'\n')
        print("Execução direta concluída.")
    except Exception as e:
        print(e)