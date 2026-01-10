import sys
import os

# ==============================================================================
# MÁQUINA VIRTUAL - EXECUTOR DE CÓDIGO OBJETO
# ==============================================================================
# Esta classe simula o computador hipotético que roda as instruções geradas.

class MaquinaVirtual:
    def __init__(self):
        self.dados = []       # Memória de dados (Variáveis - área D)
        self.instrucoes = []  # Memória de instruções (Código - área C)
        self.pilha = []       # Pilha de operandos (Stack - área S)
        self.pc = 0           # Program Counter (Aponta para a linha atual sendo executada)
        self.pilha_retorno = []  # Pilha de endereços de retorno para chamadas de procedimento

    def carregar(self, caminho):
        """ Lê o arquivo de texto e carrega as instruções na memória """
        print(f"--- Carregando programa: {caminho} ---")
        if not os.path.exists(caminho):
            print(f"Erro: Arquivo '{caminho}' não encontrado.")
            sys.exit(1)

        self.instrucoes = [] # Limpa instruções anteriores
        with open(caminho, 'r') as f:
            for linha in f:
                linha = linha.strip()
                if linha:
                    self.instrucoes.append(linha)
        print(f"Programa carregado com {len(self.instrucoes)} instruções.")

    def executar(self):
        print("\n=== INICIANDO EXECUÇÃO ===")
        print("--------------------------")
        
        while self.pc < len(self.instrucoes):
            instrucao = self.instrucoes[self.pc]
            
            # Remove comentários inline (ex: "DSVI 71 #funcao um")
            if '#' in instrucao:
                instrucao = instrucao.split('#')[0].strip()
            
            if not instrucao: 
                self.pc += 1
                continue

            partes = instrucao.split()
            op = partes[0]
            arg = None
            
            if len(partes) > 1:
                # Tenta converter argumento para número (int ou float)
                try:
                    arg = float(partes[1])
                    if arg.is_integer(): arg = int(arg)
                except ValueError:
                    arg = partes[1] # Mantém como string se não for número

            # DEBUG: Descomente a linha abaixo para ver passo-a-passo
            # print(f"PC: {self.pc} | INSTR: {op} {arg if arg is not None else ''} | PILHA: {self.pilha}")

            # --- Decodificação das Instruções ---
            
            if op == 'INPP': # Iniciar Programa Principal
                self.pc += 1
                
            elif op == 'PARA': # Parar Programa
                print("\n--------------------------")
                print("=== FIM DA EXECUÇÃO ===")
                break
                
            elif op == 'ALME': # Alocar Memória
                qtd = int(arg)
                for _ in range(qtd):
                    self.dados.append(0) # Inicializa variáveis com 0
                self.pc += 1
                
            elif op == 'CRCT': # Carregar Constante
                self.pilha.append(arg)
                self.pc += 1
                
            elif op == 'CRVL': # Carregar Valor (de variável)
                endereco = int(arg)
                if endereco < len(self.dados):
                    self.pilha.append(self.dados[endereco])
                else:
                    # Se tentar acessar memória não alocada, preenche com 0 e avisa (modo permissivo)
                    while len(self.dados) <= endereco:
                        self.dados.append(0)
                    self.pilha.append(self.dados[endereco])
                self.pc += 1
                
            elif op == 'ARMZ': # Armazenar (em variável)
                endereco = int(arg)
                if not self.pilha:
                    print(f"Erro de Execução (Linha {self.pc}): Pilha vazia ao tentar ARMAZENAR.")
                    sys.exit(1)
                valor = self.pilha.pop()
                if endereco < len(self.dados):
                    self.dados[endereco] = valor
                else:
                    while len(self.dados) <= endereco:
                        self.dados.append(0)
                    self.dados[endereco] = valor
                self.pc += 1
                
            elif op == 'SOMA':
                if len(self.pilha) < 2: 
                    print(f"Erro (Linha {self.pc}): Pilha vazia para SOMA. Pilha atual: {self.pilha}")
                    sys.exit(1)
                b = self.pilha.pop()
                a = self.pilha.pop()
                self.pilha.append(a + b)
                self.pc += 1
                
            elif op == 'SUBT':
                if len(self.pilha) < 2:
                    print(f"Erro (Linha {self.pc}): Pilha vazia para SUBT. Pilha atual: {self.pilha}")
                    sys.exit(1)
                b = self.pilha.pop()
                a = self.pilha.pop()
                self.pilha.append(a - b)
                self.pc += 1
                
            elif op == 'MULT':
                if len(self.pilha) < 2:
                    print(f"Erro (Linha {self.pc}): Pilha vazia para MULT. Pilha atual: {self.pilha}")
                    sys.exit(1)
                b = self.pilha.pop()
                a = self.pilha.pop()
                self.pilha.append(a * b)
                self.pc += 1
                
            elif op == 'DIVI':
                if len(self.pilha) < 2:
                    print(f"Erro (Linha {self.pc}): Pilha vazia para DIVI. Pilha atual: {self.pilha}")
                    sys.exit(1)
                b = self.pilha.pop()
                a = self.pilha.pop()
                if b == 0:
                    print("Erro: Divisão por Zero!")
                    sys.exit(1)
                self.pilha.append(a / b)
                self.pc += 1
                
            elif op == 'IMPR': # Imprimir
                if not self.pilha:
                    print(f"Erro (Linha {self.pc}): Pilha vazia para IMPR.")
                    sys.exit(1)
                valor = self.pilha.pop()
                print(f"SAÍDA: {valor}")
                self.pc += 1
                
            elif op == 'LEIT': # Leitura
                try:
                    valor_lido = input("Digite um valor de entrada: ")
                    # Tenta converter entrada para número
                    valor_num = float(valor_lido)
                    if valor_num.is_integer(): valor_num = int(valor_num)
                    self.pilha.append(valor_num)
                except ValueError:
                    print("Erro: A entrada deve ser numérica.")
                    sys.exit(1)
                except EOFError:
                    print("\nEntrada encerrada inesperadamente.")
                    sys.exit(1)
                self.pc += 1
                
            elif op == 'DSVF': # Desvio Se Falso
                if not self.pilha:
                    print(f"Erro (Linha {self.pc}): Pilha vazia para DSVF.")
                    sys.exit(1)
                condicao = self.pilha.pop()
                if not condicao: # 0 ou False
                    self.pc = int(arg)
                else:
                    self.pc += 1
                    
            elif op == 'DSVI': # Desvio Incondicional
                self.pc = int(arg)
                
            # Operadores Relacionais (empilham 1 se True, 0 se False)
            elif op == 'CPIG': # Igual
                if len(self.pilha) < 2: print("Erro: Pilha < 2 para CPIG"); sys.exit(1)
                b = self.pilha.pop(); a = self.pilha.pop()
                self.pilha.append(1 if a == b else 0)
                self.pc += 1
            elif op == 'CDIF': # Diferente
                if len(self.pilha) < 2: print("Erro: Pilha < 2 para CDIF"); sys.exit(1)
                b = self.pilha.pop(); a = self.pilha.pop()
                self.pilha.append(1 if a != b else 0)
                self.pc += 1
            elif op == 'CMAI': # Maior
                if len(self.pilha) < 2: print("Erro: Pilha < 2 para CMAI"); sys.exit(1)
                b = self.pilha.pop(); a = self.pilha.pop()
                self.pilha.append(1 if a > b else 0)
                self.pc += 1
            elif op == 'CMEN': # Menor
                if len(self.pilha) < 2: print("Erro: Pilha < 2 para CMEN"); sys.exit(1)
                b = self.pilha.pop(); a = self.pilha.pop()
                self.pilha.append(1 if a < b else 0)
                self.pc += 1
            elif op == 'CPMI': # Menor Igual
                if len(self.pilha) < 2: print("Erro: Pilha < 2 para CPMI"); sys.exit(1)
                b = self.pilha.pop(); a = self.pilha.pop()
                self.pilha.append(1 if a <= b else 0)
                self.pc += 1
            elif op == 'CPMA': # Maior Igual
                if len(self.pilha) < 2: print("Erro: Pilha < 2 para CPMA"); sys.exit(1)
                b = self.pilha.pop(); a = self.pilha.pop()
                self.pilha.append(1 if a >= b else 0)
                self.pc += 1
            
            # --- Comandos Extras (Opcional/Simplificado) ---
            elif op == 'CHPR': # Chamar Procedimento
                endereco_proc = int(arg)
                # Salva o endereço de retorno (próxima instrução)
                self.pilha_retorno.append(self.pc + 1)
                # Salta para o início do procedimento
                self.pc = endereco_proc
                
            elif op == 'RTPR': # Return Procedure
                # Retorna para o endereço salvo na pilha de retorno
                if self.pilha_retorno:
                    self.pc = self.pilha_retorno.pop()
                else:
                    # Se não houver endereço de retorno, é o fim do programa
                    self.pc += 1
                    
            elif op == 'DESM': # Desalocar/Desempilhar da pilha
                qtd = int(arg) if arg else 1
                for _ in range(qtd):
                    if self.pilha:
                        self.pilha.pop()
                self.pc += 1
            
            else:
                print(f"Aviso: Instrução '{op}' não implementada ou desconhecida na linha {self.pc}.")
                self.pc += 1

if __name__ == "__main__":
    # Teste isolado (se rodar direto o executor.py)
    vm = MaquinaVirtual()
    # Tenta achar o arquivo padrão subindo um nível
    path_padrao = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Dados', 'codigo_objeto.txt')
    
    if os.path.exists(path_padrao):
        vm.carregar(path_padrao)
        vm.executar()
    else:
        print("Arquivo codigo_objeto.txt não encontrado para teste isolado.")
        if len(sys.argv) > 1:
            vm.carregar(sys.argv[1])
            vm.executar()