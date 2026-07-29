name: Atualizar programas SC (Transferegov)

on:
  schedule:
    # 10:00 UTC = 07:00 no horário de Brasília (sem horário de verão) —
    # roda depois da atualização diária do Transferegov (feita até ~9h).
    - cron: "0 10 * * *"
  workflow_dispatch: {}   # permite rodar manualmente pelo botão "Run workflow" no GitHub

permissions:
  contents: write   # necessário para o job conseguir fazer commit/push do resultado

jobs:
  atualizar:
    runs-on: ubuntu-latest
    steps:
      - name: Clonar o repositório
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Instalar dependências
        run: pip install requests pandas

      - name: Baixar e filtrar programas de SC
        run: python filtrar_programas_sc.py

      - name: Publicar resultado (commit automático)
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add programas_sc.csv ultima_atualizacao.txt
          git diff --staged --quiet || git commit -m "Atualiza programas_sc.csv ($(date -u +%Y-%m-%d))"
          git push
