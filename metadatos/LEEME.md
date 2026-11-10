# Catalog of the corpus

[English](#english) · [Español](#español)

## English

| File | One row per | What it has |
| --- | --- | --- |
| `textos.csv` | text | The work: title, volume, author, order of the author, topic, genre, original language, translator, first edition, words, paths of the files |
| `ediciones.csv` | text | The 19th- or 20th-century edition the text comes from, the PDF used and a measure of OCR quality |
| `autores.csv` | author | Dates and places of birth and death, order, source of the data |
| `catalogo.xlsx` | | The three tables and the meaning of each column |

`textos-base.csv` and `autores.csv` are written by hand. `1-catalogo.ipynb` builds the other files from them and from `../textos-limpios/`.

```python
import pandas as pd
texts = pd.read_csv("metadatos/textos.csv")
texts[texts["author_institution"] == "Jesuita"]   # Texts by Jesuits
texts[texts["first_edition"] < 1600]              # Works first printed in the sixteenth century
```

**Vocabulary.** `topic` and `author_institution` use the vocabulary of my [dashboard of the Jesuit missionary libraries](https://github.com/vegafabianr/jesuit-missionary-libraries). `genre` is the form of the text. `authorship` is `segura`, `atribuida` or `varios autores`.

**First edition.** `first_edition` is the year of the first printed edition, in the language in which the work was written. `first_edition_source` gives the record that supports it: the [Universal Short Title Catalogue](https://www.ustc.ac.uk/) (USTC), the [Biblioteca Nacional de España](https://catalogo.bne.es/) (BNE), the [Incunabula Short Title Catalogue](https://data.cerl.org/istc/) (ISTC) or the Italian [SBN](https://opac.sbn.it/). A note in parentheses means that the record covers only part of the text. In 13 works the date is approximate (`aproximada: ...`): taken from the introduction of the 19th- or 20th-century edition, from the earliest edition found, or, failing that, from the death of the author.

**Authors.** `source` in `autores.csv` says where each row comes from: the dashboard, Wikidata (with its identifier), the headings of the BNE or a catalog record.

## Español

| Archivo | Una fila por | Qué tiene |
| --- | --- | --- |
| `textos.csv` | texto | La obra: título, tomo, autor, orden del autor, tema, género, lengua original, traductor, primera edición, palabras, rutas de los archivos |
| `ediciones.csv` | texto | La edición de los siglos XIX o XX de la que sale el texto, el PDF usado y una medida de la calidad del OCR |
| `autores.csv` | autor | Fechas y lugares de nacimiento y muerte, orden, fuente de los datos |
| `catalogo.xlsx` | | Las tres tablas y el significado de cada columna |

`textos-base.csv` y `autores.csv` se escriben a mano. `1-catalogo.ipynb` arma los demás archivos a partir de ellos y de `../textos-limpios/`.

```python
import pandas as pd
texts = pd.read_csv("metadatos/textos.csv")
texts[texts["author_institution"] == "Jesuita"]   # Textos de jesuitas
texts[texts["first_edition"] < 1600]              # Obras impresas por primera vez en el siglo XVI
```

**Vocabulario.** `topic` y `author_institution` usan el vocabulario de mi [dashboard de las bibliotecas misionales jesuíticas](https://github.com/vegafabianr/jesuit-missionary-libraries). `genre` es la forma del texto. `authorship` es `segura`, `atribuida` o `varios autores`.

**Primera edición.** `first_edition` es el año de la primera edición impresa, en la lengua en que se escribió la obra. `first_edition_source` da el registro que la respalda: el [Universal Short Title Catalogue](https://www.ustc.ac.uk/) (USTC), la [Biblioteca Nacional de España](https://catalogo.bne.es/) (BNE), el [Incunabula Short Title Catalogue](https://data.cerl.org/istc/) (ISTC) o el [SBN](https://opac.sbn.it/) italiano. Una nota entre paréntesis indica que el registro cubre solo parte del texto. En 13 obras la fecha es aproximada (`aproximada: ...`): sale de la introducción de la edición del XIX o XX, de la edición más antigua localizada o, a falta de ambas, de la muerte del autor.

**Autores.** `source` en `autores.csv` dice de dónde sale cada fila: el dashboard, Wikidata (con su identificador), los encabezamientos de la BNE o un registro de catálogo.
