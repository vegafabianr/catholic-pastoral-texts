# A corpus of early modern Catholic texts in Spanish, from nineteenth- and twentieth-century editions

[Español](#español) · [English](#english)

[![Abrir en Colab / Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vegafabianr/catholic-pastoral-texts/blob/main/primeros-pasos.ipynb)

## Español

Textos religiosos católicos escritos en español, o traducidos al español, antes de 1800. Salen de ediciones de los siglos XIX y XX, cuya impresión regular un motor de OCR lee con pocos errores. Sirven para el análisis textual: comparar autores, órdenes religiosas, géneros y épocas.

**En breve.** 151 textos, 123 obras, unos 17,1 millones de palabras. Cada texto viene en dos versiones: una limpia, con la grafía de la edición, y otra modernizada. Tasa de error por carácter, contra una transcripción de referencia de 17 páginas: 0,74 % en la versión limpia y 0,68 % en la modernizada, sin contar las tildes.

### 1. Descargar los textos

Hay tres caminos. Elegí uno.

- **Sin instalar nada, en Google Colab.** Hacé clic en el botón **Open in Colab** de arriba. Se abre el notebook `primeros-pasos.ipynb`, que descarga el corpus y trae todos los ejemplos de esta página listos para correr (menú *Entorno de ejecución → Ejecutar todas*).
- **Todo el corpus, a tu computadora.** Arriba de la lista de archivos, hacé clic en el botón verde **`<> Code`** y después en **Download ZIP** (o usá [este enlace directo](https://github.com/vegafabianr/catholic-pastoral-texts/archive/refs/heads/main.zip)). Descomprimí el archivo: la carpeta `textos-modernizados/` tiene un `.txt` por texto.
- **Con git**, si lo usás: `git clone https://github.com/vegafabianr/catholic-pastoral-texts.git`

Para un texto suelto, abrilo en la carpeta `textos-modernizados/` y usá el botón de descarga (*Download raw file*) que aparece arriba a la derecha del texto.

### 2. Abrir el corpus en Python

Abrí Jupyter (o Python) **dentro de la carpeta descomprimida** y cargá la tabla de textos con pandas:

```python
import pandas as pd

texts = pd.read_csv("metadatos/textos.csv")        # una fila por texto: obra, autor, primera edición...
editions = pd.read_csv("metadatos/ediciones.csv")  # una fila por texto: la edición del XIX o XX usada

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

text = read_text("textos-modernizados/luis-de-granada-guia-de-pecadores.txt")
print(text[:500])
```

Sin descargar nada, también se pueden leer desde internet:

```python
import pandas as pd, urllib.request

BASE = "https://raw.githubusercontent.com/vegafabianr/catholic-pastoral-texts/main/"
texts = pd.read_csv(BASE + "metadatos/textos.csv")
text = urllib.request.urlopen(BASE + texts.loc[0, "modern_file"]).read().decode("utf-8")
```

Los nombres de archivo dan autor, título y tomo (`rodriguez-ejercicio-de-perfeccion-y-virtudes-cristianas-tomo2.txt`). La columna `modern_file` de `textos.csv` tiene la ruta de cada texto.

### 3. Análisis bibliográfico con pandas

`textos.csv` describe cada texto: título, autor, orden religiosa del autor (`author_institution`), tema (`topic`), género (`genre`), lengua original, traductor y año de la primera edición (`first_edition`). Una obra en varios tomos ocupa varias filas con el mismo `work_id`.

```python
works = texts.drop_duplicates("work_id")                  # una fila por obra

works["author_institution"].value_counts()                # obras por orden religiosa
pd.crosstab(works["topic"], works["genre"])               # obras por tema y género
works[works["first_edition"] < 1600]                      # obras impresas por primera vez en el siglo XVI
works[(works["author_institution"] == "Jesuita") & (works["original_language"] != "español")]  # jesuitas traducidos

# Obras por década de primera edición, en un gráfico
(works["first_edition"] // 10 * 10).value_counts().sort_index().plot(kind="bar", figsize=(12, 3))
```

El significado de cada columna está en `metadatos/catalogo.xlsx` (hoja *columnas*) y en `metadatos/LEEME.md`. El Excel sirve también para filtrar a mano.

### 4. Análisis textual

Los textos conservan unas pocas marcas: `<pb n="12"/>` (salto de página), `<head>` (título), `<small>` (letra chica) y `<foreign xml:lang="la">` (pasaje en latín). Para contar palabras conviene quitarlas:

```python
import re
from collections import Counter

def words(text):
    text = re.sub(r"<[^>]+>", " ", text)           # quitar las marcas
    return re.findall(r"[^\W\d_]+", text.lower())  # palabras, en minúscula

counts = Counter(words(text))
counts.most_common(30)                              # palabras más frecuentes

# Concordancia: cada aparición de "conciencia" con su contexto
for m in list(re.finditer(r"\bconciencia\b", text))[:10]:
    print(text[m.start() - 60:m.end() + 60].replace("\n", " "))
```

El notebook [`primeros-pasos.ipynb`](primeros-pasos.ipynb) sigue con más ejemplos: palabras vacías, concordancias y el vocabulario que distingue a dos grupos de autores (jesuitas y carmelitas) con scikit-learn.

### 5. Analizar en Voyant Tools, sin programar

[Voyant Tools](https://voyant-tools.org/) analiza textos en el navegador: frecuencias, nubes de palabras, tendencias, contextos.

**El corpus completo ya está cargado:** [abrirlo en Voyant](https://voyant-tools.org/?corpus=9b3cdbaeec7055ab26e73a1352736732). Son los 151 textos de `textos-modernizados/`, sin marcas y **sin tildes** (Voyant no distingue entonces *el* de *él*, *si* de *sí* ni *mas* de *más*). Cada documento tiene título, autor, fecha de la primera edición y orden o estado del autor (*collection*). Como **Trends** muestra los documentos en el orden del corpus y no por fecha, están ordenados por año de la primera edición, y cada título empieza con ese año.

**Para trabajar con una selección**, la última parte de `primeros-pasos.ipynb` arma `seleccion-voyant.zip` con los textos que elijas (por ejemplo, todos los de un autor), con tildes y sin marcas. En Voyant, pulsá **Upload** y elegí ese archivo.

### Contenido

| Carpeta o archivo | Qué tiene |
| --- | --- |
| `textos-modernizados/` | Un `.txt` por texto, con grafía modernizada. Para la mayoría de los análisis, usar esta |
| `textos-limpios/` | Los mismos textos, con la grafía de la edición |
| `textos-ocr/` | La salida del OCR, una fila por renglón, con su posición en la página |
| `metadatos/` | La obra, su autor y su primera edición (`textos.csv`), la edición usada (`ediciones.csv`), los autores (`autores.csv`), todo junto en `catalogo.xlsx` |
| `primeros-pasos.ipynb` | El tutorial de esta página |
| `ocr-piloto/` | Los notebooks que van del PDF a las dos versiones del texto |
| `registro-modernizacion.csv.gz`, `registro-correcciones.csv` | Cada palabra que cambió la modernización |

### Método

1. **Selección.** Obras escritas o traducidas al español antes de 1800, en una edición impresa del siglo XIX en adelante; una edición por obra.
2. **Texto.** De cada PDF se cortan portadas, licencias, índices y el material de editores posteriores. Los PDF no están en este repositorio.
3. **OCR.** Tesseract 5.4, modelo `spa`, 300 DPI.
4. **Limpieza.** Reglas basadas en la posición y el tamaño de cada renglón quitan encabezados, notas al pie, notas al margen y adornos.
5. **Modernización.** Reglas para la grafía y las tildes, corrección de errores de OCR con el vocabulario del corpus y una lista de formas antiguas ("ansí" → "así").

Detalles en `ocr-piloto/LEEME.md` y `metadatos/LEEME.md`.

### Límites

- La tasa de error sale de solo 17 páginas. `metadatos/ediciones.csv` da, para cada texto, el porcentaje de palabras que no están en el diccionario ni en 10 libros del corpus (mediana 1,94 %).
- El texto es el de las ediciones de los siglos XIX y XX, que puede diferir del de época.
- La fecha de primera edición es aproximada en 13 obras, y en 5 textos el registro de catálogo cubre solo parte del texto; la columna `first_edition_source` lo indica.

### Licencia

Código: MIT. Textos y metadatos: CC BY 4.0, salvo `ocr-piloto/modernizacion-lexica.csv` (CC BY-SA 3.0, derivado de IMPACT-es) y `ocr-piloto/diccionario-es/` (licencia propia). Para citar el corpus, usá el botón *Cite this repository* de la columna derecha.

## English

Catholic religious texts written in Spanish, or translated into Spanish, before 1800. They come from editions of the nineteenth and twentieth centuries, whose regular printing an OCR engine reads with few errors. They are meant for text analysis: comparing authors, religious orders, genres and periods.

**In short.** 151 texts, 123 works, about 17.1 million words. Each text comes in two versions: one clean, with the spelling of the edition, and one modernized. Character error rate, against a reference transcription of 17 pages: 0.74 percent in the clean version and 0.68 percent in the modernized one, without counting accents.

### 1. Download the texts

Choose one of three ways.

- **Nothing to install, in Google Colab.** Click the **Open in Colab** button above. It opens the notebook `primeros-pasos.ipynb`, which downloads the corpus and has every example of this page ready to run (menu *Runtime → Run all*).
- **The whole corpus, to your computer.** Above the list of files, click the green **`<> Code`** button and then **Download ZIP** (or use [this direct link](https://github.com/vegafabianr/catholic-pastoral-texts/archive/refs/heads/main.zip)). Unzip it: the folder `textos-modernizados/` has one `.txt` per text.
- **With git**, if you use it: `git clone https://github.com/vegafabianr/catholic-pastoral-texts.git`

For a single text, open it in the folder `textos-modernizados/` and use the download button (*Download raw file*) at the top right of the text.

### 2. Open the corpus in Python

Start Jupyter (or Python) **inside the unzipped folder** and load the table of texts with pandas:

```python
import pandas as pd

texts = pd.read_csv("metadatos/textos.csv")        # one row per text: work, author, first edition...
editions = pd.read_csv("metadatos/ediciones.csv")  # one row per text: the 19th- or 20th-century edition used

def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

text = read_text("textos-modernizados/luis-de-granada-guia-de-pecadores.txt")
print(text[:500])
```

They can also be read from the internet, without downloading anything:

```python
import pandas as pd, urllib.request

BASE = "https://raw.githubusercontent.com/vegafabianr/catholic-pastoral-texts/main/"
texts = pd.read_csv(BASE + "metadatos/textos.csv")
text = urllib.request.urlopen(BASE + texts.loc[0, "modern_file"]).read().decode("utf-8")
```

File names give author, title and volume (`rodriguez-ejercicio-de-perfeccion-y-virtudes-cristianas-tomo2.txt`). The column `modern_file` of `textos.csv` has the path of each text.

### 3. Bibliographic analysis with pandas

`textos.csv` describes each text: title, author, religious order of the author (`author_institution`), topic, genre, original language, translator and year of the first edition (`first_edition`). A work in several volumes takes several rows with the same `work_id`.

```python
works = texts.drop_duplicates("work_id")                  # one row per work

works["author_institution"].value_counts()                # works by religious order
pd.crosstab(works["topic"], works["genre"])               # works by topic and genre
works[works["first_edition"] < 1600]                      # works first printed in the sixteenth century
works[(works["author_institution"] == "Jesuita") & (works["original_language"] != "español")]  # translated Jesuits

# Works by decade of first edition, as a chart
(works["first_edition"] // 10 * 10).value_counts().sort_index().plot(kind="bar", figsize=(12, 3))
```

The meaning of each column is in `metadatos/catalogo.xlsx` (sheet *columnas*) and in `metadatos/LEEME.md`. The Excel file also works for filtering by hand.

### 4. Text analysis

The texts keep a few tags: `<pb n="12"/>` (page break), `<head>` (heading), `<small>` (small type) and `<foreign xml:lang="la">` (Latin passage). Remove them before counting words:

```python
import re
from collections import Counter

def words(text):
    text = re.sub(r"<[^>]+>", " ", text)           # remove the tags
    return re.findall(r"[^\W\d_]+", text.lower())  # words, in lowercase

counts = Counter(words(text))
counts.most_common(30)                              # most frequent words

# Concordance: each occurrence of "conciencia" with its context
for m in list(re.finditer(r"\bconciencia\b", text))[:10]:
    print(text[m.start() - 60:m.end() + 60].replace("\n", " "))
```

The notebook [`primeros-pasos.ipynb`](primeros-pasos.ipynb) has more examples: stopwords, concordances and the vocabulary that sets two groups of authors apart (Jesuits and Carmelites) with scikit-learn.

### 5. Analyze in Voyant Tools, without programming

[Voyant Tools](https://voyant-tools.org/) analyzes texts in the browser: frequencies, word clouds, trends, contexts.

**The whole corpus is already loaded:** [open it in Voyant](https://voyant-tools.org/?corpus=9b3cdbaeec7055ab26e73a1352736732). It holds the 151 texts of `textos-modernizados/`, without tags and **without accents** (so Voyant does not tell *el* from *él*, *si* from *sí* or *mas* from *más*). Each document has title, author, date of the first edition and the author's order or state (*collection*). Since **Trends** shows documents in corpus order, not by date, they are sorted by year of first edition, and each title starts with that year.

**To work with a selection,** the last part of `primeros-pasos.ipynb` builds `seleccion-voyant.zip` with the texts you choose (for instance, all those by one author), with accents and without tags. In Voyant, press **Upload** and choose that file.

### Contents

| Folder or file | What it has |
| --- | --- |
| `textos-modernizados/` | One `.txt` per text, with modernized spelling. For most analyses, use this one |
| `textos-limpios/` | The same texts, with the spelling of the edition |
| `textos-ocr/` | The OCR output, one row per line, with its position on the page |
| `metadatos/` | The work, its author and its first edition (`textos.csv`), the edition used (`ediciones.csv`), the authors (`autores.csv`), all together in `catalogo.xlsx` |
| `primeros-pasos.ipynb` | The tutorial of this page |
| `ocr-piloto/` | The notebooks that go from the PDF to the two versions of the text |
| `registro-modernizacion.csv.gz`, `registro-correcciones.csv` | Every word that the modernization changed |

### Method

1. **Selection.** Works written or translated into Spanish before 1800, in an edition printed from the nineteenth century on; one edition per work.
2. **Text.** Title pages, licenses, indexes and the material of later editors are cut from each PDF. The PDFs are not in this repository.
3. **OCR.** Tesseract 5.4, model `spa`, 300 DPI.
4. **Cleaning.** Rules based on the position and size of each line remove headers, footnotes, margin notes and ornaments.
5. **Modernization.** Rules for spelling and accents, correction of OCR errors with the vocabulary of the corpus, and a list of old forms ("ansí" → "así").

Details in `ocr-piloto/LEEME.md` and `metadatos/LEEME.md`.

### Limits

- The error rate comes from 17 pages only. `metadatos/ediciones.csv` gives, for each text, the share of words found neither in the dictionary nor in 10 books of the corpus (median 1.94 percent).
- The text is that of the nineteenth- and twentieth-century editions, which may differ from the early modern one.
- The date of first edition is approximate in 13 works, and in 5 texts the catalog record covers only part of the text; the column `first_edition_source` says so.

### License

Code: MIT. Texts and metadata: CC BY 4.0, except `ocr-piloto/modernizacion-lexica.csv` (CC BY-SA 3.0, derived from IMPACT-es) and `ocr-piloto/diccionario-es/` (its own license). To cite the corpus, use the *Cite this repository* button in the right column.
