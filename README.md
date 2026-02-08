# Compilador Pascal - Projeto Completo

Este projeto implementa um compilador completo para um código em linguagem Pascal, desenvolvido como parte da disciplina de Compiladores. O compilador realiza análise léxica, sintática, semântica e geração de código objeto para uma máquina virtual baseada em pilha.

## Estrutura do Projeto

O projeto está organizado nos seguintes diretórios:

- **`AnalisadorSintatico/`**: Contém `analisadorSintatico.py`, o núcleo do compilador que integra:
  - Analisador léxico (PLY Lex)
  - Analisador sintático (PLY Yacc)
  - Gerador de código objeto
- **`AnalisadorSemantico/`**: Contém `analisadorSemantico.py` responsável pela verificação de tipos, escopos e declarações de variáveis/procedimentos.
- **`CodigoObjeto/`**: Contém `executor.py`, a máquina virtual que executa o código objeto gerado.
- **`Dados/`**: Pasta que armazena arquivos de entrada e saída:
  - `codigo.txt`: Código-fonte Pascal de entrada
  - `tokens.txt`: Lista de tokens gerados pela análise léxica
  - `codigo_objeto.txt`: Código objeto (bytecode) gerado para a máquina virtual
- **`main.py`**: Script principal que orquestra todo o processo de compilação e execução

## Tecnologias Utilizadas

- **Python 3.x** (recomendado 3.6+)
- **PLY (Python Lex-Yacc)**: Framework para análise léxica e sintática

## Pré-requisitos

1. **Python 3.6 ou superior** instalado
2. **Biblioteca PLY** instalada:

   ```bash
   pip install ply
   ```

3. Código-fonte Pascal válido em `Dados/codigo.txt`

## Instalação

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/seu-usuario/Compilador.git
   cd Compilador
   ```

2. **Verifique a versão do Python:**

   ```bash
   python --version
   ```

3. **Instale as dependências:**

   ```bash
   pip install ply
   ```

## Executando o Compilador

### Execução Completa (Recomendado)

Para compilar e executar o código Pascal de uma só vez:

```bash
python main.py
```

Este comando realiza automaticamente:

1. ✅ Análise léxica (tokenização)
2. ✅ Análise sintática (parsing)
3. ✅ Análise semântica (validações)
4. ✅ Geração de código objeto
5. ✅ Execução na máquina virtual

### Execução Modular (Opcional)

#### 1. Compilar sem Executar

Se desejar apenas compilar sem executar:

```bash
python AnalisadorSintatico/analisadorSintatico.py
```

Este comando gera os arquivos `tokens.txt` e `codigo_objeto.txt` em `Dados/`.

#### 2. Executar Código Objeto Existente

Para executar um código objeto previamente gerado:

```bash
python CodigoObjeto/executor.py
```

Útil para re-executar sem recompilar.

## Arquivos Gerados

Durante a compilação, os seguintes arquivos são criados em `Dados/`:

| Arquivo             | Descrição                                     |
| ------------------- | --------------------------------------------- |
| `tokens.txt`        | Lista de tokens identificados no código-fonte |
| `codigo_objeto.txt` | Bytecode gerado para a máquina virtual        |

## Exemplo de Código Pascal

Arquivo: `Dados/codigo.txt`

```pascal
program exemplo;
var a, b, soma: integer;
begin
    read(a);
    read(b);
    soma := a + b;
    write(soma)
end.
```

## Características Suportadas

✅ Declaração de variáveis (`integer`, `real`)  
✅ Operações aritméticas (`+`, `-`, `*`, `/`)  
✅ Comandos de entrada/saída (`read`, `write`)  
✅ Estruturas condicionais (`if-then-else`)  
✅ Estruturas de repetição (`while-do`)  
✅ Procedimentos com parâmetros  
✅ Escopos locais e globais  
✅ Validação semântica (tipos, declarações, escopos)

## Instruções da Máquina Virtual

A máquina virtual suporta as seguintes instruções:

| Instrução                                      | Descrição                                |
| ---------------------------------------------- | ---------------------------------------- |
| `INPP`                                         | Iniciar programa                         |
| `PARA`                                         | Parar execução                           |
| `ALME n`                                       | Alocar memória (n posições)              |
| `CRCT n`                                       | Carregar constante                       |
| `CRVL n`                                       | Carregar valor da variável no endereço n |
| `ARMZ n`                                       | Armazenar no endereço n                  |
| `SOMA`                                         | Somar dois valores da pilha              |
| `SUBT`                                         | Subtrair dois valores da pilha           |
| `MULT`                                         | Multiplicar dois valores da pilha        |
| `DIVI`                                         | Dividir dois valores da pilha            |
| `IMPR`                                         | Imprimir valor da pilha                  |
| `LEIT`                                         | Ler entrada do usuário                   |
| `DSVF n`                                       | Desviar se falso para linha n            |
| `DSVI n`                                       | Desviar incondicionalmente para linha n  |
| `CPIG`, `CDIF`, `CMAI`, `CMEN`, `CPMA`, `CPMI` | Comparações                              |
| `CHPR n`                                       | Chamar procedimento no endereço n        |
| `RTPR`                                         | Retornar de procedimento                 |
| `DESM n`                                       | Desalocar memória                        |

## Tratamento de Erros

O compilador detecta e reporta:

- ❌ **Erros léxicos**: Caracteres inválidos
- ❌ **Erros sintáticos**: Estrutura incorreta do código
- ❌ **Erros semânticos**: Variáveis não declaradas, tipos incompatíveis, procedimentos inexistentes

## Observações

- Certifique-se de que `Dados/codigo.txt` existe e contém código Pascal válido antes de executar
- Em caso de erro, o processo é interrompido com mensagem descritiva
- O arquivo `parsetab.py` pode ser gerado automaticamente pelo PLY (pode ser ignorado no Git)

---

**Desenvolvido como projeto na Disciplina de Compiladores**
