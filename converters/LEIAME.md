# Conversores de exportações de wearables

Transformam a exportação de um relógio/app no **CSV canónico** do SmartTracking
(`metric_type,metric_value,unit,measured_at`), que entra pelo `POST /import`.

Correm **no computador do utilizador, sem internet**. A exportação em bruto
nunca sai do dispositivo: só as métricas da lista branca (`steps`,
`heart_rate`, `sleep_duration_min`) passam para o ficheiro final. GPS,
peso, notas, contactos e tudo o resto ficam de fora — minimização de dados
na origem (RGPD, art. 5.º, n.º 1, al. c)).

## Estado de cada conversor

| Formato   | Como se obtém a exportação                                   | Estado |
|-----------|--------------------------------------------------------------|--------|
| `csv`     | qualquer app que exporte CSV + um mapeamento em `mappings/`  | Testado com exemplo; serve para qualquer marca com CSV |
| `apple`   | Saúde → perfil → Exportar todos os dados de saúde            | Formato bem documentado; testado com exemplo fictício |
| `samsung` | Samsung Health → Definições → Transferir dados pessoais      | Construído a partir de documentação pública; **por validar com exportação real** |
| `huawei`  | Huawei Health → Centro de privacidade → Pedir os seus dados  | Estrutura conhecida, chaves **por confirmar** com exportação real (ver abaixo) |

## Utilização

```powershell
# Ver o que existe numa exportação, sem converter
python convert.py --formato apple --inspecionar export.zip

# Converter
python convert.py --formato csv --mapping mappings/exemplo-relogio.json exportacao.csv
python convert.py --formato apple --fonte Watch export.zip
python convert.py --formato samsung pasta_samsunghealth
python convert.py --formato huawei --mapping mappings/huawei.json pasta_huawei
```

O resultado é um ficheiro `<nome>_canonico.csv`, pronto a enviar.

## Huawei: como completar o mapeamento

A Huawei não publica que "chave" corresponde a passos, pulsação ou sono na
exportação do Centro de privacidade. Com uma exportação real:

1. `python convert.py --formato huawei --inspecionar <pasta>` lista as chaves;
2. os ficheiros XLSX que vêm na exportação descrevem cada campo;
3. preenche-se `mappings/huawei.json` com as chaves certas.

## Acrescentar uma marca

- Exporta CSV? Basta um mapeamento novo em `mappings/` (ver `exemplo-relogio.json`).
- Outro formato? Um módulo novo em `converters/` com `name`, `convert_path()`
  e `inspect()` (ver `base.py`).

## Testes

```powershell
python -m pytest tests
```
