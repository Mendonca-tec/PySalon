
import sys
import os
import json

# Adiciona o diretório do projeto ao path para que os módulos possam ser importados
sys.path.append('/home/ubuntu/PySalon/PySalon-main')

from src import dados
from src import cadastro

# Caminho para a pasta de dados de teste
TEST_DATA_DIR = '/home/ubuntu/PySalon/PySalon-main/data_test'
ARQ_USUARIOS_TEST = os.path.join(TEST_DATA_DIR, 'usuarios.json')
ARQ_SERVICOS_TEST = os.path.join(TEST_DATA_DIR, 'servicos.json')
ARQ_AGENDAMENTOS_TEST = os.path.join(TEST_DATA_DIR, 'agendamentos.json')

def setup_test_environment():
    # Cria uma pasta de dados de teste separada
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    # Redireciona os caminhos de dados para os arquivos de teste
    dados.PASTA_DADOS = TEST_DATA_DIR
    dados.ARQ_USUARIOS = ARQ_USUARIOS_TEST
    dados.ARQ_SERVICOS = ARQ_SERVICOS_TEST
    dados.ARQ_AGENDAMENTOS = ARQ_AGENDAMENTOS_TEST
    # Limpa arquivos de teste existentes
    if os.path.exists(ARQ_USUARIOS_TEST): os.remove(ARQ_USUARIOS_TEST)
    if os.path.exists(ARQ_SERVICOS_TEST): os.remove(ARQ_SERVICOS_TEST)
    if os.path.exists(ARQ_AGENDAMENTOS_TEST): os.remove(ARQ_AGENDAMENTOS_TEST)

def teardown_test_environment():
    # Limpa os arquivos de teste e a pasta
    if os.path.exists(ARQ_USUARIOS_TEST): os.remove(ARQ_USUARIOS_TEST)
    if os.path.exists(ARQ_SERVICOS_TEST): os.remove(ARQ_SERVICOS_TEST)
    if os.path.exists(ARQ_AGENDAMENTOS_TEST): os.remove(ARQ_AGENDAMENTOS_TEST)
    if os.path.exists(TEST_DATA_DIR): os.rmdir(TEST_DATA_DIR)

def test_garantir_admin_padrao():
    print("\n--- Teste: Garantir Admin Padrão ---")
    setup_test_environment()
    dados.garantir_admin_padrao()
    usuarios = dados.carregar_usuarios()
    assert "admin" in usuarios, "Admin padrão não foi criado."
    assert usuarios["admin"]["email"] == "admin@salao.com", "Email do admin padrão incorreto."
    print("SUCESSO: Admin padrão criado e verificado.")
    teardown_test_environment()

def test_cadastro_novo_cliente():
    print("\n--- Teste: Cadastro de Novo Cliente ---")
    setup_test_environment()
    dados.garantir_admin_padrao() # Garante que o admin exista para não interferir
    usuarios = dados.carregar_usuarios()

    # Mock de inputs para a função criar_conta
    original_input = __builtins__.input
    inputs = iter([
        "Cliente Teste",
        "11999998888",
        "cliente@teste.com",
        "senha123",
        "senha123"
    ])
    __builtins__.input = lambda _: next(inputs)

    novo_id = cadastro.criar_conta(usuarios)
    assert novo_id is not None, "Falha ao criar novo cliente."
    reloaded_usuarios = dados.carregar_usuarios()
    assert novo_id in reloaded_usuarios, "Novo cliente não persistiu."
    assert reloaded_usuarios[novo_id]["email"] == "cliente@teste.com", "Email do novo cliente incorreto."
    print("SUCESSO: Novo cliente cadastrado e persistido.")

    __builtins__.input = original_input # Restaura o input original
    teardown_test_environment()

def test_email_ja_em_uso():
    print("\n--- Teste: Email já em Uso ---")
    setup_test_environment()
    dados.garantir_admin_padrao()
    usuarios = dados.carregar_usuarios()

    # Primeiro cadastro
    original_input = __builtins__.input
    inputs1 = iter([
        "Cliente Um",
        "11111111111",
        "duplicado@teste.com",
        "senha1",
        "senha1"
    ])
    __builtins__.input = lambda _: next(inputs1)
    cadastro.criar_conta(usuarios)

    # Tentativa de segundo cadastro com o mesmo email
    inputs2 = iter([
        "Cliente Dois",
        "22222222222",
        "duplicado@teste.com", # Email duplicado
        "senha2",
        "senha2",
        "Cliente Dois", # Repete para passar a validação de email
        "22222222222",
        "outro@teste.com",
        "senha2",
        "senha2"
    ])
    __builtins__.input = lambda _: next(inputs2)

    # A função criar_conta imprime a mensagem de erro e continua o loop
    # Para este teste, vamos apenas verificar se não adicionou um novo usuário com o mesmo email
    # e se a mensagem de erro foi impressa (o que é difícil de testar programaticamente sem mockar stdout)
    # Por simplicidade, vamos verificar se o número de usuários não aumentou indevidamente
    
    # A função criar_conta() do PySalon original não retorna None em caso de email duplicado, 
    # ela continua pedindo input. Para testar isso de forma automatizada, precisaríamos
    # de um mock mais complexo ou refatorar a função. Por enquanto, vamos simular o fluxo
    # e verificar se o email duplicado não gera um novo usuário.

    # Para este teste, vamos simular a entrada do usuário para que ele tente cadastrar
    # um email duplicado e depois um email válido para prosseguir.
    
    # A função `cadastro.criar_conta` é interativa. Para testar o cenário de email duplicado,
    # precisaríamos de um mock de `input` que retornasse o email duplicado e depois um válido.
    # O teste abaixo simula isso e verifica se o email duplicado não resulta em um novo usuário.

    # Reinicia o input para a segunda tentativa
    inputs_duplicado = iter([
        "Nome Duplicado",
        "99999999999",
        "duplicado@teste.com", # Email que já existe
        "senha_dup",
        "senha_dup",
        "Nome Valido", # Entradas para um cadastro bem-sucedido após a falha
        "88888888888",
        "valido@teste.com",
        "senha_valido",
        "senha_valido"
    ])
    __builtins__.input = lambda _: next(inputs_duplicado)

    # Captura a saída para verificar a mensagem de erro (opcional, mas bom para depuração)
    from io import StringIO
    from contextlib import redirect_stdout
    f = StringIO()
    with redirect_stdout(f):
        cadastro.criar_conta(usuarios) # Isso vai tentar cadastrar o duplicado e depois o válido
    output = f.getvalue()
    
    reloaded_usuarios = dados.carregar_usuarios()
    assert "duplicado@teste.com" in [u["email"] for u in reloaded_usuarios.values()], "Email duplicado não foi registrado inicialmente."
    assert "valido@teste.com" in [u["email"] for u in reloaded_usuarios.values()], "Email válido não foi registrado após tentativa duplicada."
    assert output.count("E-mail já em uso") >= 1, "Mensagem de email já em uso não foi exibida."
    print("SUCESSO: Tratamento de email já em uso verificado.")

    __builtins__.input = original_input
    teardown_test_environment()

def test_validar_email():
    print("\n--- Teste: Validação de Email ---")
    assert cadastro.validar_email("teste@exemplo.com") is True, "Email válido falhou."
    assert cadastro.validar_email("invalido") is False, "Email inválido passou."
    assert cadastro.validar_email("invalido@") is False, "Email inválido passou."
    assert cadastro.validar_email("@invalido.com") is False, "Email inválido passou."
    print("SUCESSO: Validação de email funcionando corretamente.")

if __name__ == "__main__":
    try:
        test_garantir_admin_padrao()
        test_cadastro_novo_cliente()
        test_email_ja_em_uso()
        test_validar_email()
        print("\nTodos os testes de usuários e persistência passaram!")
    except AssertionError as e:
        print(f"\nFALHA NO TESTE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUm erro inesperado ocorreu durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

