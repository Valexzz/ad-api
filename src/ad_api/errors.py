class DomainError(Exception):
    pass

class UsuarioNaoEncontradoError(DomainError):
    pass

class InfraError(Exception):
    pass

class UsuarioSemLoginError(InfraError):
    pass

class ChaveApiInvalidaError(InfraError):
    pass

class SenhaInvalidaError(DomainError):
    pass

class UsuarioJaExisteError(DomainError):
    pass

class ADNaoEncontrado(DomainError):
    pass