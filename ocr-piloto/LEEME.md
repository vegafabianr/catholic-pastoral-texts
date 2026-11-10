# From PDF to text: OCR, cleaning and modernization

[English](#english) · [Español](#español)

## English

These notebooks turn the PDFs of the corpus into two versions of each text: a clean one, with the spelling of the edition, and a modernized one. They run in order. The PDFs are not in the repository: notebook 4 and the page images of notebook 7 need a local copy; the others start from `../textos-ocr/`.

| Notebook | What it does | Output |
| --- | --- | --- |
| `4-ocr-corpus` | Tesseract 5.4, model `spa`, 300 DPI. One row per line, with its box | `textos-ocr/` |
| `5-limpieza` | Removes headers, footnotes, margin notes, ornaments and the material of later editors; joins split words; marks headings, small type and Latin | `textos-limpios/` |
| `6-modernizacion` | Modernizes spelling and accents and corrects OCR errors with the vocabulary of the corpus. Rules in `reglas_modernizacion_postcorreccion.py` | `textos-modernizados/` |
| `7-paginas-baja-calidad` | Measures quality per book and per page | Error rate |
| `8-correcciones-puntuales` | Point corrections and old forms ("ansí" → "así", "padesció" → "padeció") | `textos-modernizados/` |

Notebook 8 changes the texts in place: after running 6 again, run 8 again.

**Old forms.** Notebook 6 leaves a word as printed when in doubt, so notebook 8 applies a second list, `modernizacion-formas.csv` (8,229 pairs). It was built from the words of the modernized texts missing from the Spanish dictionary: each was rewritten with historical spelling changes (sc/c, ct/t, g/j, x/j, s/x, e/i, o/u, v/b, qu/cu, z/c, h, ll/rl, -des/-is, accents) until it matched a dictionary word of the corpus, and every pair was reviewed by hand ("creatura" → "criatura", "defunctos" → "difuntos", "egercicio" → "ejercicio", "habia" → "había"). Latin, Italian, valid clitic forms ("díjole") and halves of words cut at the end of a line were left out. Some pairs were added by hand: old words with the same meaning ("anque" → "aunque", "dende" → "desde", "cuasi" → "casi") and contractions ("deste" → "de este"). A second pass over the result added the accents of 19th-century printing ("á" → "a", "ó" → "o") and the old endings of the second person plural ("viésedes" → "vieseis", "podríades" → "podríais", "hecistes" → "hicisteis"). Capitalized "Dina", daughter of Jacob, is left alone ("dina" → "digna").

**Logs.** `registro-material-quitado.csv` lists what the cleaning removed; `resumenes-del-editor.csv`, the summaries and notes of later editors that it removes. `../registro-modernizacion.csv.gz` has every word changed by notebook 6 (1,019,552) and `../registro-correcciones.csv`, those of notebook 8 (118,499).

**Quality.** Character error rate (CER) against a transcription of 17 pages made from the page image (`referencia-cer/`):

| | Clean | Modernized |
| --- | --- | --- |
| CER, without accents | 0.74 % | 0.68 % |
| CER, with accents | 0.87 % | 1.33 % |

With accents, the modernized version scores worse because the reference follows the printed spelling. The sample is small.

**Sources.** Spanish dictionary: Hunspell `es_ES` (LibreOffice/RLA-ES), in `diccionario-es/` with its license. Language detection: [lingua](https://github.com/pemistahl/lingua-py). The first rules of modernization come from my [early-modern-spanish-ocr-baseline](https://github.com/vegafabianr/early-modern-spanish-ocr-baseline). `modernizacion-lexica.csv` derives from the lexicon of IMPACT-es (Sánchez-Martínez, Martínez-Sempere, Ivars-Ribes and Carrasco, "An open diachronic corpus of historical Spanish", *Language Resources and Evaluation*, 2013), CC BY-SA 3.0.

**Open.** Latin quotations of one or two words are not marked. Words cut at the end of a line and not joined by the cleaning remain as two halves. Old words with no modern form of the same meaning ("empero", "otrosí", "asaz") were kept.

## Español

Estos notebooks convierten los PDF del corpus en dos versiones de cada texto: una limpia, con la grafía de la edición, y otra modernizada. Se corren en orden. Los PDF no están en el repositorio: el notebook 4 y las imágenes de página del 7 necesitan una copia local; los demás parten de `../textos-ocr/`.

| Notebook | Qué hace | Salida |
| --- | --- | --- |
| `4-ocr-corpus` | Tesseract 5.4, modelo `spa`, 300 DPI. Una fila por renglón, con su caja | `textos-ocr/` |
| `5-limpieza` | Quita encabezados, notas al pie, notas al margen, adornos y el material de editores posteriores; une palabras cortadas; marca títulos, letra chica y latín | `textos-limpios/` |
| `6-modernizacion` | Moderniza grafía y tildes y corrige errores de OCR con el vocabulario del corpus. Reglas en `reglas_modernizacion_postcorreccion.py` | `textos-modernizados/` |
| `7-paginas-baja-calidad` | Mide la calidad por libro y por página | Tasa de error |
| `8-correcciones-puntuales` | Correcciones puntuales y formas antiguas ("ansí" → "así", "padesció" → "padeció") | `textos-modernizados/` |

El 8 cambia los textos en el lugar: si se vuelve a correr el 6, hay que volver a correr el 8.

**Formas antiguas.** El 6 deja la palabra como está cuando duda, así que el 8 aplica una segunda lista, `modernizacion-formas.csv` (8.229 pares). Se armó con las palabras de los textos modernizados que no están en el diccionario español: cada una se reescribió con cambios gráficos históricos (sc/c, ct/t, g/j, x/j, s/x, e/i, o/u, v/b, qu/cu, z/c, h, ll/rl, -des/-is, tildes) hasta dar con una palabra del diccionario presente en el corpus, y cada par se revisó a mano ("creatura" → "criatura", "defunctos" → "difuntos", "egercicio" → "ejercicio", "habia" → "había"). Quedaron fuera el latín, el italiano, los enclíticos correctos ("díjole") y las mitades de palabras cortadas a fin de renglón. Algunos pares se agregaron a mano: palabras antiguas de igual sentido ("anque" → "aunque", "dende" → "desde", "cuasi" → "casi") y contracciones ("deste" → "de este"). Una segunda pasada sobre el resultado sumó las tildes de las imprentas del XIX ("á" → "a", "ó" → "o") y las desinencias antiguas de vosotros ("viésedes" → "vieseis", "podríades" → "podríais", "hecistes" → "hicisteis"). "Dina" con mayúscula, la hija de Jacob, no se toca ("dina" → "digna").

**Registros.** `registro-material-quitado.csv` lista lo que quitó la limpieza; `resumenes-del-editor.csv`, los resúmenes y notas de editores posteriores que quita. `../registro-modernizacion.csv.gz` tiene cada palabra que cambió el notebook 6 (1.019.552) y `../registro-correcciones.csv`, las del 8 (118.499).

**Calidad.** Tasa de error por carácter (CER) contra una transcripción de 17 páginas hecha desde la imagen (`referencia-cer/`):

| | Limpio | Modernizado |
| --- | --- | --- |
| CER, sin tildes | 0,74 % | 0,68 % |
| CER, con tildes | 0,87 % | 1,33 % |

Con tildes, la versión modernizada sale peor porque la referencia sigue la grafía impresa. La muestra es chica.

**Fuentes.** Diccionario español: Hunspell `es_ES` (LibreOffice/RLA-ES), en `diccionario-es/` con su licencia. Detección de idioma: [lingua](https://github.com/pemistahl/lingua-py). Las primeras reglas de modernización vienen de mi [early-modern-spanish-ocr-baseline](https://github.com/vegafabianr/early-modern-spanish-ocr-baseline). `modernizacion-lexica.csv` deriva del léxico de IMPACT-es (Sánchez-Martínez, Martínez-Sempere, Ivars-Ribes y Carrasco, "An open diachronic corpus of historical Spanish", *Language Resources and Evaluation*, 2013), CC BY-SA 3.0.

**Queda abierto.** Las citas latinas de una o dos palabras no se marcan. Las palabras cortadas a fin de renglón que la limpieza no unió quedan en dos mitades. Se conservaron las palabras antiguas sin una forma moderna del mismo sentido ("empero", "otrosí", "asaz").
