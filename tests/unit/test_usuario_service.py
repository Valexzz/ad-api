# tests/unit/test_usuario_service.py
import pytest
from typing import Optional

from ad_api.domain.model import Usuario, StatusUsuario
from ad_api.domain.ports import UsuarioRepository
from ad_api.services.usuario_service import UsuarioService
from ad_api.errors import UsuarioNaoEncontradoError


class FakeUsuarioRepository(UsuarioRepository):
    def __init__(self, usuarios: list[Usuario] | None = None):
        self._usuarios = {u.login: u for u in (usuarios or [])}

    def buscar_por_login(self, login: str) -> Optional[Usuario]:
        return self._usuarios.get(login)

def test_deve_retornar_usuario_quando_login_existir():
    usuario_existente = Usuario(
        login="joao.silva",
        primeiro_nome="João",
        sobrenome="Silva",
        status=StatusUsuario.ATIVO,
        matricula="12345"
    )
    repo = FakeUsuarioRepository(usuarios=[usuario_existente])
    service = UsuarioService(usuario_repository=repo)

    resultado = service.buscar_usuario_por_login("joao.silva")

    assert resultado == usuario_existente
    assert resultado.get_nome_completo() == "João Silva"

def test_deve_lancar_excecao_quando_usuario_nao_existir():
    repo = FakeUsuarioRepository(usuarios=[])
    service = UsuarioService(usuario_repository=repo)

    with pytest.raises(UsuarioNaoEncontradoError) as exc_info:
        service.buscar_usuario_por_login("login.inexistente")

    assert "Usuário com login login.inexistente não encontrado" in str(exc_info.value)