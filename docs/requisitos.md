# Requisitos funcionais

RF01 - Cadastrar Usuário: O sistema deve permitir o cadastro de novos usuários no AD, aceitando parâmetro opcional de matrícula e a OU de destino.

RF02 - Reativar Usuário: O sistema deve permitir a reativação de contas desativadas, com opção de movê-las para uma OU específica.

RF03 - Redefinir Senha: O sistema deve permitir redefinir a senha de um usuário.

RF04 - Consultar Dados de Usuário: O sistema deve buscar e retornar os atributos e o status atual da conta do usuário no AD a partir de seu usuário.

# Requisitos Não funcionais

RNF01 - A API deve ser apenas utilizada por quem possui sua chave

RNF02 - A aplicação deve registrar logs de ações em todos os níveis, debug, info, warning, error. Não deve registrar senhas

RNF03 - A aplicação necessita de uma service account com permissão de criação, desativação, modificação e redefinição de senha no AD

RNF04 - A API necessita que o AD responda na porta 636 (LDAPS)

RNF05 - O tráfego entre o cliente consumidor deve ser obrigatóriamente HTTPS

RNF06 - As requisições ao AD devem ter um timeout de 5 segundos para evitar o travamento da aplicação

RNF07 - A aplicação não pode deletar usuários