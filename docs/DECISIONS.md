# Decisões de implementação

- FastAPI separa contratos HTTP da lógica de domínio e fornece OpenAPI automaticamente.
- Interface HTML/CSS/JS local elimina dependência de build de frontend para a demonstração.
- Dados sintéticos autorais tornam a execução reproduzível, sem coletar dados de usuários ou estabelecimentos.
- Modelos não são carregados de arquivos binários externos; o treinamento local usa apenas os dados versionados.
- Seeds fixas permitem reproduzir modelos e dados. Tempos de execução variam entre máquinas.
- Validação Pydantic e erros HTTP 422 distinguem entradas inválidas de respostas válidas sem resultados.
- A versão demonstrativa não implementa autenticação, persistência de uploads, filas ou uso multiusuário. Não é um serviço pronto para produção.
