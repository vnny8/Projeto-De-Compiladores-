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
        
        # Tabela de procedimentos: guarda nome -> {'endereco': int, 'num_params': int, 'params': [enderecos]}
        self.tabela_procedimentos = {}
        
        # Pilha para rastrear quantidade de variáveis alocadas por escopo (para DESM)
        self.variaveis_por_escopo = []

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

# Cria uma instância global do gerador para ser acessada por todas as regras do parser abaixo.
gerador = GeradorCodigo()


# ==============================================================================
# PARTE 1: ANALISADOR LÉXICO (DEFINIÇÕES DE TOKENS)
# ==============================================================================
# Vocabulário da linguagem. O PLY usa isso para quebrar o texto em tokens.
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
# Usa-se isso para distinguir se 'begin' é uma variável (identificador) ou o comando BEGIN.
reserved = {
    'program': 'PROGRAM', 'var': 'VAR', 'integer': 'INTEGER', 'real': 'REAL',
    'procedure': 'PROCEDURE', 'begin': 'BEGIN', 'end': 'END', 'if': 'IF',
    'then': 'THEN', 'else': 'ELSE', 'while': 'WHILE', 'do': 'DO',
    'read': 'READ', 'write': 'WRITE'
}

# --- Expressões Regulares Simples (Regex) ---
# O Lexer é ensinado a reconhecer os símbolos visuais da linguagem.
# As variáveis com t_ também são usadas automaticamente pelo Python Lex
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
# Para tokens que exigem processamento (como converter string para número), usa-se funções.

def t_COMMENT(t):
    # Expressão Regular para ignorar comentários.
    # Pega tudo entre { } OU tudo entre /* */
    r'\{[^}]*\}|/\*[\s\S]*?\*/'
    pass # Não gera token, apenas ignora e continua.

def t_NUM_REAL(t):
    # Reconhece números com ponto flutuante (ex: 10.5)
    r'\d+\.\d+'
    t.value = float(t.value) # Converte o texto para float do Python
    return t

def t_NUM_INT(t):
    # Reconhece números inteiros (apenas dígitos)
    r'\d+'
    t.value = int(t.value) # Converte o texto para int do Python
    return t

def t_IDENT(t):
    # Reconhece identificadores. Regra: Deve começar com letra.
    r'[a-zA-Z][a-zA-Z0-9_]*'
    # Se a palavra achada está no dicionário 'reserved',
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
    t.lexer.skip(1) # Pula o caractere ruim

# Inicializa o Lexer com as regras acima
# o PLY (Python Lex-Yacc) detecta as funções que usam t_ e as utiliza ao chamar o comando abaixo
lexer = lex.lex()

# --- Função Auxiliar de Saída ---

def gerar_arquivo_tokens_formatado(codigo_fonte):
    """
    Esta função gera um arquivo 'tokens.txt' listando todos os tokens encontrados,
    formatados como [Tipo, Valor].
    """
    print(f"--- Gerando arquivo de tokens em: {ARQUIVO_TOKENS} ---")
    # Cria um lexer temporário só para isso
    meu_lexer = lex.lex()
    meu_lexer.input(codigo_fonte)
    lista_saida = []
    
    while True:
        tok = meu_lexer.token()
        if not tok: break # Fim do arquivo
        
        # Traduz os nomes técnicos do PLY para nomes legíveis
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
# Gramática BNF. Cada função 'p_' representa uma regra de produção.
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
    '''dc : dc_v mais_dc
          | dc_p mais_dc
          | empty'''
    # Declarações podem ser: variáveis (dc_v), procedimentos (dc_p) ou nenhuma (empty).
    # Permite múltiplas declarações encadeadas através da regra 'mais_dc'.
    # Exemplo: var a: integer; var b: real; procedure teste begin end
    pass

def p_mais_dc(p):
    '''mais_dc : SEMICOLON dc
               | empty'''
    # Permite encadear múltiplas declarações separadas por ponto e vírgula.
    # Se não houver ponto e vírgula, assume que não há mais declarações (empty).
    # Exemplo: var a: integer; var b: real (o ; permite continuar declarando)
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
            
            # Se estivermos dentro de um procedimento, incrementa contador
            if gerador.variaveis_por_escopo:
                gerador.variaveis_por_escopo[-1] += 1
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
# Aqui adiciono os marcadores para abrir e fechar escopo corretamente
def p_inicio_escopo(p):
    '''inicio_escopo : empty'''
    gerador.semantico.entrar_escopo()
    # Inicia contador de variáveis para este escopo
    gerador.variaveis_por_escopo.append(0)
    # Gera pulo para não executar declaração do procedure
    instrucao_pulo = gerador.adicionar_instrucao("DSVI", -1)
    # Marca onde o procedimento começa (após o DSVI)
    endereco_inicio_proc = len(gerador.codigo)
    p[0] = {'pulo': instrucao_pulo, 'inicio': endereco_inicio_proc}

def p_fim_escopo(p):
    '''fim_escopo : empty'''
    # Desaloca todas as variáveis do escopo (parâmetros + locais)
    num_vars = gerador.variaveis_por_escopo.pop() if gerador.variaveis_por_escopo else 0
    if num_vars > 0:
        gerador.adicionar_instrucao("DESM", num_vars)
    gerador.semantico.sair_escopo()
    # Adiciona retorno
    gerador.adicionar_instrucao("RTPR")

def p_dc_p(p):
    # Regra Procedure: procedure nome (params) corpo
    # Usamos inicio_escopo e fim_escopo para delimitar variáveis locais
    '''dc_p : PROCEDURE IDENT inicio_escopo parameters corpo_p fim_escopo'''
    nome_proc = p[2]
    info_escopo = p[3]
    indice_pulo = info_escopo['pulo']
    endereco_inicio = info_escopo['inicio']
    enderecos_params = p[4] if p[4] else []
    
    # NÃO insere ARMZs no meio do código, isso quebra os saltos
    # Em vez disso, guardo apenas a info e processo na chamada
    
    gerador.tabela_procedimentos[nome_proc] = {
        'endereco': endereco_inicio,
        'num_params': len(enderecos_params),
        'params': enderecos_params
    }
    
    # Corrige o salto para pular todo o corpo do procedimento
    destino = len(gerador.codigo)
    gerador.corrigir_salto(indice_pulo, destino)

def p_parameters(p):
    '''parameters : LPAREN lista_par RPAREN
                  | empty'''
    if len(p) > 2:
        # Retorna a lista de endereços dos parâmetros
        enderecos = p[2] if p[2] else []
        # Após alocar todos os parâmetros, gera ARMZs para desempilhar da pilha
        # Os parâmetros são desempilhados na MESMA ordem (pois pilha guarda último empilhado no topo)
        for endereco in enderecos:
            gerador.adicionar_instrucao("ARMZ", endereco)
        p[0] = enderecos
    else:
        p[0] = []

def p_lista_par(p):
    '''lista_par : variaveis COLON tipo_var mais_par'''
    # Parâmetros de função
    lista_vars = p[1]
    tipo = p[3]
    enderecos_params = []
    for var_nome in lista_vars:
        try:
            endereco = gerador.semantico.adicionar_variavel(var_nome, tipo)
            gerador.adicionar_instrucao("ALME", 1)
            # Incrementa contador de variáveis no escopo do procedimento
            if gerador.variaveis_por_escopo:
                gerador.variaveis_por_escopo[-1] += 1
            enderecos_params.append(endereco)
        except Exception as e:
            print(f"ERRO SEMÂNTICO (Parâmetros): {e}")
            sys.exit(1)
    
    # Acumula com os parâmetros que vem depois (de mais_par)
    if p[4]:
        enderecos_params.extend(p[4])
    
    # Retorna TODOS os endereços dos parâmetros
    p[0] = enderecos_params

def p_mais_par(p):
    '''mais_par : SEMICOLON lista_par
                | empty'''
    if len(p) > 2:
        p[0] = p[2]  # Retorna os endereços dos próximos parâmetros
    else:
        p[0] = []

def p_corpo_p(p):
    '''corpo_p : dc_loc BEGIN comandos END'''
    # Corpo de um procedimento: declarações locais seguidas de bloco begin-end.
    # Exemplo: var x: integer; begin x := 10; write(x) end
    pass

# --- Declarações Locais ---
# Variáveis declaradas dentro de procedimentos (escopo local)

def p_dc_loc(p):
    '''dc_loc : dc_v mais_dcloc
              | empty'''
    # Declarações locais de variáveis dentro de procedimentos.
    # Pode ter várias declarações (mais_dcloc) ou nenhuma (empty).
    pass

def p_mais_dcloc(p):
    # O SEMICOLON é separador. Se tem, espera mais uma declaração.
    # Se não tem, empty.
    '''mais_dcloc : SEMICOLON dc_loc
                  | empty'''
    pass
# -----------------------------------------

# --- Regras de Comandos ---

def p_comandos(p):
    '''comandos : comando mais_comandos'''
    # Reconhece uma sequência de comandos: um comando seguido de mais comandos.
    # Exemplo: a := 10; b := 20; write(a)
    pass

def p_mais_comandos(p):
    '''mais_comandos : comandos
                     | empty'''
    # Permite encadear múltiplos comandos ou finalizar a sequência (empty).
    # Recursivo: permite quantos comandos forem necessários.
    pass

# --- REGRA AUXILIAR PARA PONTO E VÍRGULA OPCIONAL ---
# Necessária para comandos read/write/assign que podem ou não ter ;
def p_pt_virgula_opc(p):
    '''pt_virgula_opc : SEMICOLON
                      | empty'''
    pass

def p_comando_read(p):
    # Aceita ; opcional no final
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
    # Aceita ; opcional no final
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
    # Aceita ; opcional no final
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
    indice_dsvf = p[2]
    resultado_pfalsa = p[5]
    
    destino_final = len(gerador.codigo)
    
    if resultado_pfalsa:
        # Tem ELSE: resultado_pfalsa é uma tupla (indice_dsvi, inicio_else)
        indice_dsvi, inicio_else = resultado_pfalsa
        # DSVF pula para o início do ELSE
        gerador.corrigir_salto(indice_dsvf, inicio_else)
        # DSVI do fim do THEN pula para o fim
        gerador.corrigir_salto(indice_dsvi, destino_final)
    else:
        # Sem ELSE: DSVF pula direto para o fim
        gerador.corrigir_salto(indice_dsvf, destino_final)

def p_condicao(p):
    '''condicao : expressao relacao expressao'''
    # Avalia condições relacionais (ex: a > 10, b <= 5).
    # As expressões já foram calculadas e estão na pilha.
    # Gera a instrução de comparação apropriada seguida de desvio condicional (DSVF).
    op = p[2]  # Operador relacional retornado pela regra 'relacao'
    if op == '=': gerador.adicionar_instrucao("CPIG")    # Igual
    elif op == '<>': gerador.adicionar_instrucao("CDIF") # Diferente
    elif op == '>=': gerador.adicionar_instrucao("CPMA") # Maior ou Igual
    elif op == '<=': gerador.adicionar_instrucao("CPMI") # Menor ou Igual
    elif op == '>': gerador.adicionar_instrucao("CMAI")  # Maior
    elif op == '<': gerador.adicionar_instrucao("CMEN")  # Menor
    
    # Gera desvio condicional com endereço placeholder (-1) para backpatching posterior
    instrucao_salto = gerador.adicionar_instrucao("DSVF", -1)
    p[0] = instrucao_salto

def p_pfalsa(p):
    '''pfalsa : marca_else ELSE comandos
              | empty'''
    if len(p) > 2:
        # Retorna (índice do DSVI, início do ELSE)
        indice_dsvi = p[1]
        inicio_else = indice_dsvi + 1
        p[0] = (indice_dsvi, inicio_else)
    else:
        p[0] = None

def p_marca_else(p):
    '''marca_else : empty'''
    # Gera DSVI para o THEN pular o ELSE
    indice = gerador.adicionar_instrucao("DSVI", -1)
    p[0] = indice

def p_comando_while(p):
    '''comando : WHILE condicao DO comandos DOLLAR'''
    # BACKPATCHING DO WHILE
    # p[2] é o índice do DSVF gerado pela condição
    indice_dsvf = p[2]
    
    # Preciso voltar para o INÍCIO da avaliação da condição,
    # antes dos CRVLs que carregam os operandos.
    # A condição gera: CRVL CRVL comparação DSVF
    # Então o início é 3 instruções antes do DSVF
    inicio_while = indice_dsvf - 3
    
    # Gero um salto incondicional de volta ao início do WHILE
    gerador.adicionar_instrucao("DSVI", inicio_while)
    
    # O destino da saída é a linha atual (fim do loop)
    destino_saida = len(gerador.codigo)
    
    # Corrijo o DSVF para pular para fora do loop se a condição falhar
    gerador.corrigir_salto(indice_dsvf, destino_saida)

# --- Regras de Suporte (Chamadas de Procedimentos) ---
def p_comando_chamada(p):
    # Aceita ; opcional no final
    '''comando : IDENT lista_arg pt_virgula_opc'''
    nome_proc = p[1]
    argumentos = p[2] if p[2] else []
    
    # Verifica se o procedimento foi declarado
    if nome_proc not in gerador.tabela_procedimentos:
        print(f"ERRO SEMÂNTICO: Procedimento '{nome_proc}' não foi declarado.")
        return
    
    info_proc = gerador.tabela_procedimentos[nome_proc]
    endereco_proc = info_proc['endereco']
    num_params = info_proc['num_params']
    enderecos_params = info_proc['params']
    
    # Verifica se o número de argumentos está correto
    if len(argumentos) != num_params:
        print(f"ERRO SEMÂNTICO: Procedimento '{nome_proc}' espera {num_params} argumentos, mas recebeu {len(argumentos)}.")
        return
    
    # Calcula endereço de retorno (linha após CHPR)
    # PUSHER será na linha atual, depois vêm num_params linhas de PARAM, depois CHPR
    # Então retorno = linha_atual + 1 (PUSHER) + num_params (PARAMs) + 1 (CHPR) = linha_atual + num_params + 2
    endereco_retorno = len(gerador.codigo) + num_params + 2
    
    # Gera PUSHER com endereço de retorno
    gerador.adicionar_instrucao("PUSHER", endereco_retorno)
    
    # Para cada argumento, gera PARAM com o endereço do argumento
    # PARAMs são gerados na ordem REVERSA para que o primeiro argumento
    # fique no topo da pilha (LIFO), permitindo desempilhamento correto com ARMZ
    for arg_nome in reversed(argumentos):
        endereco_arg = gerador.semantico.verificar_declaracao(arg_nome)
        gerador.adicionar_instrucao("PARAM", endereco_arg)
    
    # Gera chamada ao procedimento
    gerador.adicionar_instrucao("CHPR", endereco_proc)

def p_lista_arg(p):
    '''lista_arg : LPAREN argumentos RPAREN
                 | empty'''
    # Reconhece a lista de argumentos em uma chamada de procedimento.
    # Pode ser: (arg1, arg2, arg3) ou vazia quando não há parênteses.
    # Exemplo: soma(a, b) ou teste (sem argumentos)
    if len(p) > 2:
        # Tem parênteses: retorna a lista de nomes dos argumentos
        p[0] = p[2] if p[2] else []
    else:
        # Não tem parênteses: procedimento sem argumentos
        p[0] = []

def p_argumentos(p):
    '''argumentos : IDENT mais_ident'''
    # Retorna lista de nomes dos argumentos
    lista = [p[1]]
    if p[2]:
        lista.extend(p[2])
    p[0] = lista

def p_mais_ident(p):
    '''mais_ident : COMMA argumentos
                  | empty'''
    if len(p) > 2:
        p[0] = p[2]  # Continua a lista
    else:
        p[0] = []

# --- Regras Matemáticas e Lógicas ---
def p_relacao(p):
    '''relacao : EQ
               | NEQ
               | GTE
               | LTE
               | GT
               | LT'''
    # Mapeio os operadores do código fonte e APENAS RETORNO O SÍMBOLO.
    p[0] = p[1]

def p_expressao(p):
    '''expressao : termo outros_termos'''
    pass

def p_outros_termos(p):
    '''outros_termos : op_ad termo outros_termos
                     | empty'''
    # GERAÇÃO DE CÓDIGO AQUI:
    # A estrutura é: expressao -> termo (já empilhado) outros_termos
    # outros_termos -> op (p[1]) termo (p[2] - já empilhado) ...
    # Assim que p[2] termina, o segundo operando está na pilha
    if len(p) > 2:
        if p[1] == '+': gerador.adicionar_instrucao("SOMA")
        elif p[1] == '-': gerador.adicionar_instrucao("SUBT")

def p_op_ad(p):
    '''op_ad : PLUS
             | MINUS'''
    # Apenas retorna o operador
    p[0] = p[1]

def p_termo(p):
    '''termo : op_un fator mais_fatores'''
    # Define um termo matemático: pode ter sinal negativo opcional, um fator base
    # e operações de multiplicação/divisão encadeadas.
    # Exemplo: -5 * 3 / 2 (op_un=-5, fator=3, mais_fatores=/2)
    pass

def p_op_un(p):
    '''op_un : MINUS
             | empty'''
    # Operador unário: reconhece o sinal de menos para números negativos.
    # Pode ser vazio (empty) quando o número é positivo.
    # Exemplo: -10 (tem MINUS) ou 10 (empty)
    pass

def p_mais_fatores(p):
    '''mais_fatores : op_mul fator mais_fatores
                    | empty'''
    # GERAÇÃO DE CÓDIGO AQUI:
    # termo -> fator (já empilhado) mais_fatores
    # mais_fatores -> op (p[1]) fator (p[2] - já empilhado) ...
    if len(p) > 2:
        if p[1] == '*': gerador.adicionar_instrucao("MULT")
        elif p[1] == '/': gerador.adicionar_instrucao("DIVI")

def p_op_mul(p):
    '''op_mul : TIMES
              | DIVIDE'''
    # Reconhece operadores de multiplicação (*) e divisão (/).
    # Retorna o símbolo do operador para uso posterior na geração de código.
    # Exemplo: 10 * 5 retorna '*', 20 / 4 retorna '/'
    p[0] = p[1]

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