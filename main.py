import sys
import os

# Adiciona o diretório atual ao PATH para o Python encontrar as pastas
diretorio_raiz = os.path.dirname(os.path.abspath(__file__))
sys.path.append(diretorio_raiz)

# Tenta importar o módulo sintático da pasta AnalisadorSintatico
try:
    from AnalisadorSintatico import analisadorSintatico
    from CodigoObjeto import executor # Import da Parte 2
except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    print("Verifique se as pastas 'AnalisadorSintatico' e 'CodigoObjeto' existem e contêm os arquivos '__init__.py' (opcional) e os scripts corretos.")
    # Ajuda visual para debugging
    print(f"Diretório Raiz detectado: {diretorio_raiz}")
    print(f"Conteúdo do PATH: {sys.path}")
    sys.exit(1)

def ler_codigo():
    """ Lê o arquivo codigo.txt da pasta Dados """
    caminho_dados = os.path.join(diretorio_raiz, 'Dados', 'codigo.txt')
    try:
        with open(caminho_dados, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{caminho_dados}' não encontrado.")
        sys.exit(1)

def main():
    print("==============================================")
    print("      COMPILADOR LALG - PASCAL (PARTE 1)      ")
    print("==============================================\n")

    # Lê o código fonte (Pascal) do arquivo codigo.txt
    codigo_fonte = ler_codigo()

    # --- ETAPA 1: ANÁLISE LÉXICA ---
    try:
        print(">>> Etapa 1: Análise Léxica...")
        # Chamamos a função do sintatico.py que gera o tokens.txt
        analisadorSintatico.gerar_arquivo_tokens_formatado(codigo_fonte)
        print("   [OK] Tokens gerados em 'Dados/tokens.txt'.\n")
    except Exception as e:
        print(f"   [ERRO] Falha na Análise Léxica: {e}")
        sys.exit(1)

    # --- ETAPA 2, 3 e 4: SINTÁTICO, SEMÂNTICO E GERAÇÃO ---
    # Com o compilador Ascendente (Bottom-Up), essas etapas ocorrem juntas.
    try:
        print(">>> Etapa 2: Análise Sintática")
        print(">>> Etapa 3: Análise Semântica")
        print(">>> Etapa 4: Geração de Código Objeto")
        
        # Reinicia o gerador de código para garantir limpeza
        analisadorSintatico.gerador = analisadorSintatico.GeradorCodigo()
        analisadorSintatico.gerador.adicionar_instrucao("INPP")
        
        # Executa o parser
        analisadorSintatico.parser.parse(codigo_fonte, lexer=analisadorSintatico.lexer)
        
        # Salva o arquivo objeto
        caminho_obj = os.path.join(diretorio_raiz, 'Dados', 'codigo_objeto.txt')
        with open(caminho_obj, 'w') as f_out:
            for linha in analisadorSintatico.gerador.codigo:
                f_out.write(linha + '\n')
                
        print(f"   [OK] Código Objeto gerado em '{caminho_obj}'.\n")
        
    except Exception as e:
        print(f"   [ERRO] Falha durante a compilação: {e}")
        sys.exit(1)

    # --- PARTE 2: EXECUÇÃO ---
    print("==============================================")
    print(">>> Iniciando Parte 2: Execução da Máquina Hipotética")
    print("==============================================")
    
    try:
        vm = executor.MaquinaHipotetica()
        # O executor já sabe onde buscar o arquivo gerado (na pasta Dados)
        caminho_obj_completo = os.path.join(diretorio_raiz, 'Dados', 'codigo_objeto.txt')
        vm.carregar(caminho_obj_completo)
        vm.executar()
    except Exception as e:
        print(f"   [ERRO CRÍTICO NA EXECUÇÃO]: {e}")

    print("==============================================")
    print("      COMPILAÇÃO E EXECUÇÃO CONCLUÍDA COM SUCESSO!       ")
    print("==============================================")

if __name__ == "__main__":
    main()