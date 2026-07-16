
import sys
import os
import json
from datetime import datetime, timedelta

# Adiciona o diretório do projeto ao path para que os módulos possam ser importados
sys.path.append("/home/ubuntu/PySalon/PySalon-main")

from src import dados, servicos, agendamentos

# Caminho para a pasta de dados de teste
TEST_DATA_DIR = "/home/ubuntu/PySalon/PySalon-main/data_test"
ARQ_USUARIOS_TEST = os.path.join(TEST_DATA_DIR, "usuarios.json")
ARQ_SERVICOS_TEST = os.path.join(TEST_DATA_DIR, "servicos.json")
ARQ_AGENDAMENTOS_TEST = os.path.join(TEST_DATA_DIR, "agendamentos.json")

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

def test_servicos_crud():
    print("\n--- Teste: CRUD de Serviços ---")
    setup_test_environment()

    # Testar adicionar serviço
    original_input = __builtins__.input
    inputs_add = iter([
        "Corte de Cabelo",
        "Corte moderno",
        "75.00",
        "45"
    ])
    __builtins__.input = lambda _: next(inputs_add)
    
    catalogo = servicos.carregar_catalogo()
    servicos.adicionar_servico(catalogo)
    reloaded_catalogo = servicos.carregar_catalogo()
    assert "1" in reloaded_catalogo, "Serviço não adicionado."
    assert reloaded_catalogo["1"]["nome"] == "Corte de Cabelo", "Nome do serviço incorreto."
    print("SUCESSO: Serviço adicionado e persistido.")

    # Testar editar serviço
    inputs_edit = iter([
        "1", # ID do serviço a editar
        "Corte e Barba", # Novo nome
        "", # Manter descrição
        "85.00", # Novo preço
        "60" # Nova duração
    ])
    __builtins__.input = lambda _: next(inputs_edit)
    servicos.editar_servico(reloaded_catalogo) # Passa o catálogo atualizado
    reloaded_catalogo_edit = servicos.carregar_catalogo()
    assert reloaded_catalogo_edit["1"]["nome"] == "Corte e Barba", "Serviço não editado."
    assert reloaded_catalogo_edit["1"]["preco"] == 85.0, "Preço do serviço não editado."
    print("SUCESSO: Serviço editado e persistido.")

    # Testar remover serviço
    inputs_remove = iter([
        "1", # ID do serviço a remover
        "s" # Confirmar remoção
    ])
    __builtins__.input = lambda _: next(inputs_remove)
    servicos.remover_servico(reloaded_catalogo_edit) # Passa o catálogo atualizado
    reloaded_catalogo_remove = servicos.carregar_catalogo()
    assert "1" not in reloaded_catalogo_remove, "Serviço não removido."
    print("SUCESSO: Serviço removido.")

    __builtins__.input = original_input
    teardown_test_environment()

def test_agendamentos_logic():
    print("\n--- Teste: Lógica de Agendamentos ---")
    setup_test_environment()

    # Preparar dados para o teste
    dados.garantir_admin_padrao()
    usuarios = dados.carregar_usuarios()
    id_cliente = "cliente123"
    usuarios[id_cliente] = {"id": id_cliente, "nome": "Cliente Teste", "email": "c@t.com", "senha": "123", "tipo": "cliente", "status": "ativo"}
    dados.salvar_usuarios(usuarios)

    catalogo = servicos.carregar_catalogo()
    id_servico = "1"
    catalogo[id_servico] = {"id": id_servico, "nome": "Servico Teste", "preco": 100.0, "duracao": 60, "descricao": "Desc"}
    dados.salvar_servicos(catalogo)

    # Testar gerar_slots_do_dia
    slots_dia = agendamentos.gerar_slots_do_dia()
    assert len(slots_dia) > 0, "Não gerou slots para o dia."
    print(f"SUCESSO: Gerados {len(slots_dia)} slots para o dia.")

    # Testar horarios_disponiveis (dia limpo)
    data_teste = (datetime.now() + timedelta(days=7)).strftime("%d/%m/%Y") # Uma semana no futuro
    horarios_livres = agendamentos.horarios_disponiveis({}, data_teste, 60) # Agenda vazia
    assert len(horarios_livres) > 0, "Não encontrou horários livres em dia limpo."
    print(f"SUCESSO: Encontrados {len(horarios_livres)} horários livres em dia limpo.")

    # Testar adicionar agendamento
    original_input = __builtins__.input
    inputs_agendar = iter([
        id_servico, # Escolhe o serviço
        data_teste, # Data do agendamento
        "1" # Escolhe o primeiro horário disponível
    ])
    __builtins__.input = lambda _: next(inputs_agendar)

    agenda = agendamentos.carregar_agendamentos()
    agendamentos.adicionar_agendamento(agenda, catalogo, id_cliente, usuarios[id_cliente]["nome"])
    reloaded_agenda = agendamentos.carregar_agendamentos()
    assert len(reloaded_agenda) == 1, "Agendamento não adicionado."
    assert reloaded_agenda["1"]["id_cliente"] == id_cliente, "ID do cliente no agendamento incorreto."
    print("SUCESSO: Agendamento adicionado e persistido.")

    # Testar horarios_disponiveis (com agendamento existente)
    horarios_livres_ocupado = agendamentos.horarios_disponiveis(reloaded_agenda, data_teste, 60)
    assert len(horarios_livres_ocupado) < len(horarios_livres), "Horários ocupados não foram considerados."
    print("SUCESSO: Horários disponíveis consideram agendamentos existentes.")

    # Testar cancelar agendamento
    inputs_cancelar = iter([
        "1", # ID do agendamento a cancelar
        "s" # Confirmar cancelamento
    ])
    __builtins__.input = lambda _: next(inputs_cancelar)

    agendamentos.cancelar_agendamento(reloaded_agenda, id_cliente)
    reloaded_agenda_cancel = agendamentos.carregar_agendamentos()
    assert reloaded_agenda_cancel["1"]["status"] == "cancelado", "Agendamento não cancelado."
    print("SUCESSO: Agendamento cancelado.")

    __builtins__.input = original_input
    teardown_test_environment()

if __name__ == "__main__":
    try:
        test_servicos_crud()
        test_agendamentos_logic()
        print("\nTodos os testes de agendamentos e serviços passaram!")
    except AssertionError as e:
        print(f"\nFALHA NO TESTE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUm erro inesperado ocorreu durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

