#!/usr/bin/env python3
"""
Baixa o arquivo oficial de "Programas Disponibilizados" do Transferegov
(módulo Discricionárias e Legais), filtra apenas os registros relevantes
para Santa Catarina/Chapecó e salva um CSV pequeno, pronto para o
CAPTA+ Radar IA buscar sem esbarrar no limite de 100MB do Google Apps
Script (Utilities.unzip).

Regras de filtro (mesmas usadas no CAPTA+, baseadas no modelo de dados
oficial - SchemaSpy, tabela "programa" do bd_portal):
  - SIT_PROGRAMA == "Disponibilizado"  (descarta Cadastrado/Inativo)
  - UF_PROGRAMA vazio (atende o Brasil todo) OU contém "SC"

Saída: programas_sc.csv (separado por vírgula, UTF-8), na raiz do repositório.
"""

import io
import sys
import zipfile
from datetime import datetime, timezone

import requests
import pandas as pd

URL_ORIGEM = "https://repositorio.dados.gov.br/seges/detru/siconv_programa.csv.zip"
ARQUIVO_SAIDA = "programas_sc.csv"
ARQUIVO_METADADOS = "ultima_atualizacao.txt"

# Alguns servidores .gov.br reagem melhor a um cabeçalho de navegador real.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/zip,application/octet-stream,text/csv,*/*",
}


def baixar_zip(url: str) -> bytes:
    print(f"Baixando: {url}")
    resposta = requests.get(url, headers=HEADERS, timeout=180, verify=True)
    resposta.raise_for_status()
    conteudo = resposta.content
    print(f"Download concluído: {len(conteudo) / (1024 * 1024):.1f} MB (compactado)")
    return conteudo


def extrair_csv(conteudo_zip: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as z:
        nomes_csv = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not nomes_csv:
            raise RuntimeError("Nenhum arquivo .csv encontrado dentro do .zip baixado.")
        nome_csv = nomes_csv[0]
        print(f"Lendo dentro do zip: {nome_csv}")
       with z.open(nome_csv) as f:
            # CORRIGIDO: o arquivo original é UTF-8 com BOM (não Latin-1 como
            # se poderia supor por ser um dado de governo brasileiro antigo).
            # Ler como Latin-1 causava "mojibake" (ex.: "ção" virava "Ã§Ã£o").
            df = pd.read_csv(
                f,
                sep=";",
                encoding="utf-8-sig",
                dtype=str,
                low_memory=False,
                on_bad_lines="skip",
            )
    print(f"Linhas lidas do arquivo original: {len(df):,}")
    return df


def filtrar_sc(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().upper() for c in df.columns]

    if "SIT_PROGRAMA" not in df.columns or "UF_PROGRAMA" not in df.columns:
        print("AVISO: colunas SIT_PROGRAMA/UF_PROGRAMA não encontradas — "
              "o layout do arquivo pode ter mudado. Colunas disponíveis:")
        print(list(df.columns))
        raise RuntimeError("Layout do CSV mudou — script precisa de ajuste manual.")

    situacao_ok = df["SIT_PROGRAMA"].fillna("").str.strip().str.lower() == "disponibilizado"

    uf = df["UF_PROGRAMA"].fillna("").str.strip()
    uf_ok = (uf == "") | uf.str.contains(r"(^|[^A-Za-z])SC([^A-Za-z]|$)", case=False, regex=True)

    filtrado = df[situacao_ok & uf_ok].copy()
    print(f"Linhas após filtro (Disponibilizado + UF vazia/SC): {len(filtrado):,}")
    return filtrado


def salvar(df: pd.DataFrame):
    df.to_csv(ARQUIVO_SAIDA, sep=",", encoding="utf-8", index=False)
    print(f"Arquivo salvo: {ARQUIVO_SAIDA} ({len(df):,} linhas)")

    agora = datetime.now(timezone.utc).isoformat()
    with open(ARQUIVO_METADADOS, "w", encoding="utf-8") as f:
        f.write(f"Última atualização (UTC): {agora}\n")
        f.write(f"Registros no arquivo filtrado: {len(df)}\n")
        f.write(f"Fonte original: {URL_ORIGEM}\n")


def main():
    try:
        conteudo_zip = baixar_zip(URL_ORIGEM)
        df = extrair_csv(conteudo_zip)
        filtrado = filtrar_sc(df)
        salvar(filtrado)
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
