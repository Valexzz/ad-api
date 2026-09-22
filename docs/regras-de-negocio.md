# Regras de negócio

RN02 - O cadastro pode definir para a senha ser alterada no primeiro login ou não.

RN03 - O sistema deve informar se a senha da pessoa expirou.

RN04 - O sistema deve informar se a pessoa está sem cadastro (retornando 404), inativa ou cadastrada.

RN05 - O sistema deve permitir a redefinição de senha sem necessidade de informar a senha atual.

RN06 - O sistema deve verificar a complexidade da senha antes de enviar para o AD de forma parametrizável. Os parâmetros são: 
- Tamanho mínimo
- Obrigatoriedade de letras minúsculas
- Obrigatoriedade de letras maiúsculas
- Obrigatoriedade de números
- Obrigatoriedade de caracteres especiais (!@#$%&*)

RN07 - Para cadastro de usuário, o sistema pode fornecer o primeiro nome e o sobrenome, ou o nome completo, no qual o sistema irá separar, com a primeira palavra sendo o primeiro nome e o resto o sobrenome.