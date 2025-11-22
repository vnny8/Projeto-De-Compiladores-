# ==============================================================================
# ANALISADOR SEMÂNTICO (COM SUPORTE A ESCOPO)
# ==============================================================================
# Esta classe gerencia a tabela de símbolos usando uma pilha.
# O índice 0 da lista é o escopo Global.
# Novos escopos (procedimentos) são empilhados no topo da lista.

class AnalisadorSemantico:
    def __init__(self):
        # Inicializa a pilha com o escopo global (um dicionário vazio)
        self.tabela_escopos = [{}] 
        # Contador para gerar endereços de memória sequenciais (simplificação da VM)
        self.contador_memoria = 0

    def entrar_escopo(self):
        """ 
        Chamado quando o parser entra em um 'procedure'.
        Cria um novo dicionário vazio no topo da pilha para guardar variáveis locais.
        """
        self.tabela_escopos.append({})

    def sair_escopo(self):
        """ 
        Chamado quando o parser sai de um 'procedure'.
        Remove o escopo do topo da pilha, 'esquecendo' as variáveis locais.
        """
        self.tabela_escopos.pop()

    def adicionar_variavel(self, nome, tipo, categoria='var'):
        """ 
        Adiciona uma variável no ESCOPO ATUAL (o último da lista).
        Permite que uma variável local tenha o mesmo nome de uma global (Shadowing).
        """
        escopo_atual = self.tabela_escopos[-1]
        
        # Verifica se a variável já existe APENAS no escopo atual
        if nome in escopo_atual:
            raise Exception(f"Erro Semântico: A variável '{nome}' já foi declarada neste escopo.")
        
        # Registra a variável com seus metadados
        escopo_atual[nome] = {
            'tipo': tipo.upper(),
            'endereco': self.contador_memoria,
            'categoria': categoria
        }
        
        # Aloca um endereço de memória e incrementa o contador
        # Nota: Na VM simplificada deste projeto, endereços são sempre globais e sequenciais.
        endereco_alocado = self.contador_memoria
        self.contador_memoria += 1
        return endereco_alocado

    def verificar_declaracao(self, nome):
        """ 
        Busca por uma variável começando do escopo mais interno (local)
        até o mais externo (global).
        """
        # A função reversed() permite iterar da pilha do topo para a base
        for escopo in reversed(self.tabela_escopos):
            if nome in escopo:
                return escopo[nome]['endereco']
        
        # Se percorreu todos os escopos e não achou:
        raise Exception(f"Erro Semântico: A variável '{nome}' não foi declarada.")

    def obter_tipo(self, nome):
        """ Retorna o tipo da variável (INTEGER ou REAL) """
        for escopo in reversed(self.tabela_escopos):
            if nome in escopo:
                return escopo[nome]['tipo']
        
        raise Exception(f"Erro Semântico: A variável '{nome}' não foi declarada.")