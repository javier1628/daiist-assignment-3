# Corpus description

Written by `scripts/describe_corpus.py`. The first part describes the PDFs in `corpus/` before any cleaning, exactly as pypdf 6.21.4 extracts them. "After extraction and cleaning" describes the articles the index stage saves, and the last part, "Chunking dry run", what the chunking rule would make of them.

## Read this first

- `decreto-609-24.pdf` is a **scan**. Its text comes from an OCR layer already inside the PDF, so the figures below describe OCR output, not the original text.
- `decreto-755-22.pdf` is a **scan**. Its text comes from an OCR layer already inside the PDF, so the figures below describe OCR output, not the original text.
- `decreto-755-22.pdf`: 313 of its 318 article numbers appear more than once on the same page, so the page text is probably stored twice. Its word count and 150-word chunk estimate are inflated.
- `ley-168-21.pdf` is a **scan**. Its text comes from an OCR layer already inside the PDF, so the figures below describe OCR output, not the original text.

## Summary

| File | Pages | Size | Text layer | Words | "Artículo N" headings | Numbers consecutive | Chunks, 1 per article | Chunks, 150 words |
|---|---:|---:|---|---:|---:|---|---:|---:|
| `decreto-609-24.pdf` | 38 | 4.0 MB | Scanned page images with an OCR text layer | 9,595 | 64 | yes | 64 | 64 |
| `decreto-755-22.pdf` | 135 | 23.3 MB | Scanned page images with an OCR text layer | 105,261 | 632 | no | 318 | 702 |
| `ley-168-21.pdf` | 230 | 24.4 MB | Scanned page images with an OCR text layer | 52,371 | 420 | no | 419 | 350 |
| `norma-01-2023.pdf` | 10 | 0.3 MB | Real text layer (born-digital) | 3,780 | 0 | no headings | 0 | 26 |
| **Total** | 413 | 52.0 MB | | 171,007 | 1,116 | | 801 | 1,142 |

How the columns are measured:

- **Text layer.** A page has text when pypdf extracts at least 20 non-space characters from it. It holds a full-page image when one of its images is large enough to cover the whole page at 72 dpi or more. Its text is invisible when the page uses text render mode 3, the way OCR layers are stored.
- **"Artículo N" headings.** Lines that start with a capitalised `Artículo` or `ARTÍCULO` (accent optional) followed by a number. Lower-case line starts are treated as cross-references.
- **Chunk estimates.** One per article is the count of distinct article numbers. The other is words divided by 150, rounded up, with no overlap.
- **Samples.** Random positions with a fixed seed (0), so reruns show the same samples.

## decreto-609-24.pdf

- **Pages:** 38
- **File size:** 4.0 MB
- **Text layer:** Scanned page images with an OCR text layer
  - Pages holding a full-page image: 38 of 38
  - Pages with extractable text: 38 of 38
  - Pages whose text is invisible (OCR-style): 38 of 38
  - Pages without text: none
- **PDF creator:** PFU ScanSnap Home 2.21.0 #iX1600; **producer:** PFUPDF Engine 1.3.21
- **Words in the extracted text:** 9,595
- **"Artículo N" headings:** 64 found, 64 distinct numbers, highest 64
- **Numbers run 1 to 64 without gaps:** yes
  - Missing: none
  - Repeated: none
  - Out of order (lower than the heading before it): none
- **Chunk estimate:** 64 at one per article (distinct numbers); 64 at 150 words each

### 10 most repeated lines

```text
   39x  LUIS ABINADER
   38x  PRESIDENTE DE LA REPÚBLICA DOMINICANA
   11x  i
    8x  m
    6x  t
    4x  2)
    3x  SECCIÓN I
    3x  1)
    3x  3)
    3x  6)
```

### 3 random 300-character samples of the raw text

Sample 1: page 3, characters 5,306 to 5,606

```text
ISTA: La Resolución del Ministeriode Hacienda, núm. 111 -2018,del 16 de marzo de 2018, que
establecelosprocedimientosy requisitospara obtenerlalicenciade agente de aduanas.
En ejerciciode las atribucionesque me confiereel artículo128 de laConstituciónde la
República,dictoelsiguiente
REGLAMENTO DE AP
```

Sample 2: page 21, characters 50,494 to 50,794

```text
.Dentrode lostreinta(30)díasa partirde larecepciónde lacomunicación indicada
en elpárrafoanterior,laDGA otorgaráo rechazarálasolicitudde autorización.
PÁRRAFO IV. En cualquiertransferencia,ya seadirectao indirecta,y siempre que éstasea
autorizadaconforme el presenteReglamento, elpropuestoadquiriente
```

Sample 3: page 23, characters 55,125 to 55,425

```text
via presentación de una
certificaciónde la DGA, excepto laobligaciónde tomar eltallerde éticaprofesionaly el
examen de suficienciaestablecidoen elpresenteReglamento.
14)Copia del contratode alquilerdonde estarálocalizadala oficinao copiadelcertificado
de títulode propiedad.
15)Constituiruna garantía
```

## decreto-755-22.pdf

- **Pages:** 135
- **File size:** 23.3 MB
- **Text layer:** Scanned page images with an OCR text layer
  - Pages holding a full-page image: 135 of 135
  - Pages with extractable text: 135 of 135
  - Pages whose text is invisible (OCR-style): 135 of 135
  - Pages without text: none
- **PDF creator:** Nitro Pro 13 (13.70.0.30); **producer:** not recorded
- **Words in the extracted text:** 105,261
- **"Artículo N" headings:** 632 found, 318 distinct numbers, highest 318
- **Numbers run 1 to 318 without gaps:** no
  - Missing: none
  - Repeated: 2–109, 111–124, 126–162, 164–217, 219–318 (count: 313; more than once on a single page: 313)
  - Out of order (lower than the heading before it): 1, 4, 8, 10–11, 14, 17, 20, 24, 28, 32, 35, 38, 42, 45, 49, 51, 53, 57, 60, 63, 65, 69, 71, 76, 80, 84, 86, 88, 90, 93, 96, 98, 102, 112, 114, 121, 123, 126, 129, 132, 135, 137, 142, 145, 147, 149, 153, 160, 164, 166, 168, 173, 176, 178, 181, 184, 190, 193, 197, 201, 207, 215, 222, 229, 232, 235, 240, 244, 250, 255, 258, 261, 263, 266, 271, 276, 278, 282, 285, 289, 291, 294, 296, 298, 306, 311, 316 (occurrences: 88)
  - First 10 in context: Artículo 1 after Artículo 3 (page 3); Artículo 4 after Artículo 7 (page 4); Artículo 8 after Artículo 9 (page 5); Artículo 10 after Artículo 12 (page 6); Artículo 14 after Artículo 16 (page 8); Artículo 17 after Artículo 18 (page 9); Artículo 20 after Artículo 23 (page 11); Artículo 24 after Artículo 27 (page 12); Artículo 28 after Artículo 30 (page 13); Artículo 32 after Artículo 33 (page 16)
- **Chunk estimate:** 318 at one per article (distinct numbers); 702 at 150 words each

### 10 most repeated lines

```text
  267x  LUIS ABINADER
   81x  PRESIDENTE DE LA REPUBLICA DOMINICANA
   60x  PRESIDENTE DE LA REPÚBLICA DOMINICANA
   31x  t
   20x  111
   19x  ííáí^
   19x  m
   17x  rm
   14x  i
   11x  ííá^
```

### 3 random 300-character samples of the raw text

Sample 1: page 52, characters 271,493 to 271,793

```text

ARTÍCULO 120. Corrección del manifiesto después de la llegada del medio de transporte.
Dentro de un plazo que no exceda los diez (10) días calendario, contados a partir de la llegada del
medio de transporte o recepción legal, el transportista podrá solicitar correcciones al manifiesto de
carga, por
```

Sample 2: page 100, characters 509,532 to 509,832

```text
ey y este Reglamento.
PÁRRAFO. La Aduana dictará, mediante normal general, el procedimiento a seguir por el
courier, el consignatario o representante, donde se establecerán los pasos que debe seguir el
courier para solicitar la liberación de un paquete retenido por las causales más arriba mencionada
```

Sample 3: page 106, characters 536,110 to 536,410

```text
o. 
7) A que su operación aduanera no sea retrasada o suspendida de manera desproporcionada o 
injustificada por el inicio del procedimiento administrativo sancionador. 
8) Conocer el estado del procedimiento y conocer el o los responsables de su tramitación . 
9) Actuar en el procedimiento administ
```

## ley-168-21.pdf

- **Pages:** 230
- **File size:** 24.4 MB
- **Text layer:** Scanned page images with an OCR text layer
  - Pages holding a full-page image: 230 of 230
  - Pages with extractable text: 230 of 230
  - Pages whose text is invisible (OCR-style): 230 of 230
  - Pages without text: none
- **PDF creator:** SS Manager for fi Series 1.0.0; **producer:** Adobe PDF Scan Library 3.1
- **Words in the extracted text:** 52,371
- **"Artículo N" headings:** 420 found, 419 distinct numbers, highest 420
- **Numbers run 1 to 420 without gaps:** no
  - Missing: 229
  - Repeated: 22 (count: 1; more than once on a single page: 0)
  - Out of order (lower than the heading before it): 22 (occurrences: 1)
  - In context: Artículo 22 after Artículo 228 (page 140)
- **Chunk estimate:** 419 at one per article (distinct numbers); 350 at 150 words each

### 10 most repeated lines

```text
  191x  ASUNTO: Ley de Aduanas de la República Dominicana.
  190x  CONGRESO NACIONAL
  100x  PAG.
   28x  3
   25x  ^
   25x  5
   21x  \
   18x  SECCIÓN I
   12x  /
   12x  i
```

### 3 random 300-character samples of the raw text

Sample 1: page 108, characters 159,023 to 159,323

```text
do el conductor de
un medio de transporte demuestre que por algún accidente se hubiesen
perdido los documentos necesarios o parte de la carga se hubiere
destruido o desaparecido, en tal forma que hagan imposible establecer
las verdaderas existencias a bordo, el administrador de la Aduana
respectiva 
```

Sample 2: page 143, characters 212,302 to 212,602

```text
ación u otro régimen especial o económico, la inspección será
coordinada con el área de la Dirección General de Aduanas que se
encargue de administrar dichos regímenes o con la oficina de Aduana
ubicada en el parque de zonas francas cuando corresponda.
Artículo 234.- Conclusión del aforo. El proceso
```

Sample 3: page 169, characters 249,874 to 250,174

```text
 francas deberán probar dentro del
plazo de prescripción que señala esta ley, que las mercancías
ingresadas a dicho régimen fueron exportadas o, en su defecto, fueron
nacionalizadas, previo pago de los impuestos y demás obligaciones
aduaneras que correspondan.
Artículo 287.- Documentación y procedim
```

## norma-01-2023.pdf

- **Pages:** 10
- **File size:** 0.3 MB
- **Text layer:** Real text layer (born-digital)
  - Pages holding a full-page image: 0 of 10
  - Pages with extractable text: 10 of 10
  - Pages whose text is invisible (OCR-style): 0 of 10
  - Pages without text: none
- **PDF creator:** Microsoft® Word para Microsoft 365; **producer:** Microsoft® Word para Microsoft 365
- **Words in the extracted text:** 3,780
- **"Artículo N" headings:** 0
- **Chunk estimate:** 0 at one per article (no headings found); 26 at 150 words each

### 10 most repeated lines

No line appears more than once.

### 3 random 300-character samples of the raw text

Sample 1: page 4, characters 7,157 to 7,457

```text
e los servicios ofrecidos. 
 
CONSIDERANDO: Que en virtud de los compromisos internacionales contraídos 
por la República Dominicana, tales como el DR -CAFTA,  los acuerdos 
multilaterales de la Organización Mundial del Comercio (OMC), entre los que 
podemos citar Acuerdo General sobre Aranceles y C
```

Sample 2: page 5, characters 11,732 to 12,032

```text
amente las leyes 
tributarias y sus reglamentos.  
 
DICTA LA SIGUIENTE: 
NORMA GENERAL QUE AJUSTA LAS TASAS POR SERVICIO QUE COBRA 
LA DIRECCIÓN GENERAL DE ADUANAS Y ESTABLECE EL MONTO DE LAS 
 
6 
 
TASAS A SER COBRADAS A LOS CONTRIBUYENTES POR CONCEPTO DE 
SERVICIOS PRESTADOS. 
PRIMERO: En cumpli
```

Sample 3: page 8, characters 19,116 to 19,416

```text
-60 KM RD$ 6,000.00 
VERIFICACIÓNES A DESTINO PARA CONTENEDORES 40' O 45' CON DISTANCIA DE 61-100 KM RD$ 6,000.00 
VERIFICACIÓNES A DESTINO PARA CONTENEDORES FLAT RACK 20' CON DISTANCIA DE >200 KM RD$ 4,500.00 
VERIFICACIÓNES A DESTINO PARA CONTENEDORES FLAT RACK 20' CON DISTANCIA DE 0-30 KM RD$ 3,0
```

## After extraction and cleaning

From `index/articles.jsonl` and `index/cleaning_report.json`, which `uv run python main.py index` writes. Each record of the first file is one article with its source file, number, title, título, capítulo, sección, start page, word count and text. Line breaks are kept as extracted, so every row of the norma's fee table is still one line.

### Words and articles per document

| File | Extraction | Articles | Words in articles | Preamble words left out | Closing words left out |
| --- | --- | ---: | ---: | ---: | ---: |
| `ley-168-21.pdf` | pdfplumber | 420 | 46,936 | 1,334 | 210 |
| `decreto-755-22.pdf` | pypdf, page layer only | 318 | 49,016 | 759 | 46 |
| `decreto-609-24.pdf` | pdfplumber | 64 | 13,665 | 979 | 41 |
| `norma-01-2023.pdf` | pdfplumber | 4 | 1,841 | 1,860 | 32 |
| **Total** |  | 806 | 111,458 | 4,932 | 329 |

The preamble is everything before the first article (considerandos, vistos, the title of the text). The closing is everything from the formula `Dada en ...` or `DADO en ...` after the last article (date, signatures, promulgation). Neither is saved as an article.

### Lines removed, by rule

| Rule | `ley-168-21.pdf` | `decreto-755-22.pdf` | `decreto-609-24.pdf` | `norma-01-2023.pdf` |
| --- | ---: | ---: | ---: | ---: |
| header: CONGRESO NACIONAL | 213 | n/a | n/a | n/a |
| header: ASUNTO: Ley de Aduanas de la República Dominicana. | 250 | n/a | n/a | n/a |
| header: PAG. | 226 | n/a | n/a | n/a |
| page number after PAG. | 195 | n/a | n/a | n/a |
| page number | 0 | 69 | 34 | 10 |
| page number with a stray character | 0 | 8 | 1 | 0 |
| single stray character | 265 | 83 | 28 | 0 |
| only glyph placeholders | 1 | 0 | 0 | 0 |
| junk line inside a heading name | 18 | 0 | 0 | 0 |
| header: LUIS ABINADER | n/a | 135 | 38 | n/a |
| header: PRESIDENTE DE LA REPÚBLICA DOMINICANA | n/a | 135 | 38 | n/a |
| **Lines removed** | 1,168 | 430 | 139 | 10 |
| **Lines extracted** | 6,978 | 4,708 | 1,399 | 372 |

What each rule matches (`n/a` means the rule is not applied to that file):

- **header: ...** The named running header, only within the first 6 non-empty lines of a page. The law's patterns also accept the ways the OCR misreads its header, such as `CONGI L`, `AbUNIO. Lgy ¿g Aduanas de la República Dominicana.` and `PAG- 17C`.
- **page number after PAG.** The line right after the law's `PAG.` header, when it has at most 8 characters and no run of three letters. The stamped page numbers are read as things like `4-06-` or `??Q`.
- **page number** A line made only of the number of the page it is on.
- **page number with a stray character** One stray character, spaces and the number of the page, such as `t  64` on page 64.
- **single stray character** A line holding a single character.
- **only glyph placeholders** A line that held nothing but `(cid:N)` glyph placeholders.
- **junk line inside a heading name** A line without three letters in a row, sitting between a título, capítulo or sección heading and its first article.

Changes made inside lines, which remove no line:

- `ley-168-21.pdf`: 19 `(cid:N)` glyph placeholders deleted.
- `ley-168-21.pdf`: 5 debris tokens deleted from heading names written in capitals (any token that is not capitals, such as `Lyti`, or a lone letter that is not a word).
- `ley-168-21.pdf`: hand fix, `Artículo 22 9.-` changed to `Artículo 229.-`.
- Headings: `TÍTULO`, `CAPÍTULO` and `SECCIÓN` are written with their accent and an upper-case Roman numeral in the article records, reading a lower-case `l` as `I` (the OCR gives `TÍTULO Vil` for VII).

Lines of 2 to 6 characters still inside the articles. No rule removes them: some are real text, others are debris longer than one character.

- `ley-168-21.pdf`: 265 lines. Most frequent: `V)` x6, `LO` x5, `ley.` x4, `M5` x3, `1/` x3, `ti` x2, `en` x2, `í\` x2, `-y` x2, `LybS` x2, `A i` x2, `<0` x2
- `decreto-755-22.pdf`: 122 lines. Most frequent: `ííáí^` x18, `rm` x16, `ííá^` x11, `ffi` x9, `íím` x9, `Ííáí^` x8, `Ííá^` x6, `ím` x6, `ríáí^` x5, `ffl` x4, `ft` x3, `Íííí^` x2
- `decreto-609-24.pdf`: 13 lines. Most frequent: `ííáí^` x4, `ríá^` x1, `(ím` x1, `Ííáí^` x1, `im` x1, `DGA.` x1, `/íáíí^` x1, `/íáí^` x1, `íím` x1, `ley.` x1
- `norma-01-2023.pdf`: 0 lines

### Article length in words

| File | Articles | Min | Median | P90 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ley-168-21.pdf` | 420 | 11 | 73 | 201 | 4,288 |
| `decreto-755-22.pdf` | 318 | 12 | 108.5 | 326 | 1,137 |
| `decreto-609-24.pdf` | 64 | 20 | 123.5 | 474 | 1,160 |
| `norma-01-2023.pdf` | 4 | 26 | 124 | 1,567 | 1,567 |
| **All** | 806 | 11 | 87 | 284 | 4,288 |

P90 is the length that 90% of the articles do not exceed.

### 10 longest articles

| File | Article | Words | Page | Title |
| --- | ---: | ---: | ---: | --- |
| `ley-168-21.pdf` | 4 | 4,288 | 8 | Definiciones |
| `norma-01-2023.pdf` | 1 | 1,567 | 6 | (none) |
| `decreto-609-24.pdf` | 56 | 1,160 | 33 | Responsabilidades de las empresas de envios de entrega rápida, courier |
| `ley-168-21.pdf` | 18 | 1,158 | 34 | Atribuciones |
| `decreto-755-22.pdf` | 148 | 1,137 | 65 | Contenido de una declaración aduanera |
| `decreto-609-24.pdf` | 17 | 1,055 | 11 | Requisitos comunes a personas juridicas |
| `decreto-609-24.pdf` | 4 | 993 | 5 | Registro o inscripción |
| `decreto-755-22.pdf` | 177 | 912 | 86 | (none) |
| `decreto-609-24.pdf` | 34 | 909 | 22 | Requisitos para la obtención de la licencia de agente de aduanas |
| `decreto-755-22.pdf` | 30 | 773 | 13 | Atribuciones de los órganos físcalizadores |

### 10 shortest articles

| File | Article | Words | Page | Title |
| --- | ---: | ---: | ---: | --- |
| `ley-168-21.pdf` | 115 | 11 | 90 | Derecho prendario |
| `decreto-755-22.pdf` | 318 | 12 | 135 | (none) |
| `ley-168-21.pdf` | 133 | 15 | 96 | Adjudicación |
| `decreto-755-22.pdf` | 186 | 15 | 91 | (none) |
| `ley-168-21.pdf` | 38 | 16 | 53 | Representación |
| `decreto-755-22.pdf` | 317 | 16 | 135 | Entrada en vigor |
| `ley-168-21.pdf` | 352 | 17 | 195 | Clasificación de las faltas |
| `ley-168-21.pdf` | 1 | 18 | 7 | Objeto |
| `ley-168-21.pdf` | 244 | 18 | 147 | Regímenes definitivos |
| `ley-168-21.pdf` | 331 | 18 | 184 | Delitos públicos de múltiples víctimas |

### 5 random cleaned articles in full

Drawn from all 806 articles with a fixed seed (0), so reruns show the same ones.

#### `ley-168-21.pdf`, article 395

- **Title:** Decomiso administrativo
- **Under:** TÍTULO IX: DEL RÉGIMEN SANCIONADOR, DELITOS ADUANEROS, FALTAS TRIBUTARIAS ADUANERAS Y FALTAS ADUANERAS / CAPÍTULO III: DE LAS FALTAS / SECCIÓN VIII: DE LAS ESPECIFICIDADES EN EL PROCESO PENAL ADUANERO ACCIÓN PENAL POR DELITOS ADUANEROS
- **Starts on page:** 219; **words:** 129

```text
Artículo 395.- Decomiso administrativo. El decomiso administrativo
procede contra los productos derivados del tabaco, las bebidas
alcohólicas, hidrocarburos y los medicamentos ilícitos, aun en :
ausencia de un autor material o intelectual de las actividades
ilícitas, tras la constatación de la procedencia ilícita de los
productos regulados, su adulteración o falsificación, independientemente
del inicio de un proceso administrativo sancionador.
Párrafo I: Las bebidas alcohólicas, medicamentos y derivados del
tabaco, decomisados en virtud de la presente ley, serán destruidos Mf
públicamente dentro de las cuarenta y ocho (48) horas siguientes de
haberse comprobado su procedencia ilícita o su ilícito comercio.
Párrafo II: En el caso de hidrocarburos decomisados o abandonados, si
no hubiesen sido adulterados, se procederá conforme lo dispuesto en la
presente ley, para la subasta de mercancías restringidas.
```

#### `decreto-609-24.pdf`, article 39

- **Title:** Requisitos para fungir como auxiliar
- **Under:** CAPÍTULO IV: REQUISITOS, FORMALIDADES Y DISPOSICIONES PARTICULARES DE CADA OPERADOR ADUANERO QUE REQUIERA LICENCIA / SECCIÓN II: AUXILIARES DE LA FUNCIÓN PÚBLICA ADUANERA
- **Starts on page:** 26; **words:** 193

```text
ARTÍCULO 39. Requisitos para fungir como auxiliar. El director general de Aduanas, o el
funcionario en quien éste delegue, habilitará a los auxiliares de los agentes y agencias de aduanas,
a solicitud escrita del titular de la licencia, previo cumplimiento de los siguientes requisitos:
1) Formulario debidamente completado, sellado y firmado por el representante autorizado,
solicitando el registro del auxiliar que actuará en representación del agente o agencia
autorizada.
2) Certificado de no antecedentes penales, expedido por la Procuraduría General de la
República a las personas a ser registradas como auxiliares, con un tiempo de haber
sido emitido no mayor a treinta (30) días calendario.
3) Elaber completado el curso básico de técnicas aduaneras en instituciones acreditadas y
legalmente autorizadas.
4) Haber constatado que, en los últimos cinco (5) años, el apoderado especial no posee
incidencias ante la DGA y antecedentes judiciales relativos a la materia aduanera
tributaria, contrabando, lavado de activos, comercio ilícito y otros tipos penales que alteren
el orden económico, la salud pública y el medioambiente.
PÁRRAFO. La DGA se reserva el derecho de realizar entrevistas a los solicitantes y auxiliares,
cuando lo estime pertinente, previo al otorgamiento del registro.
```

#### `decreto-755-22.pdf`, article 11

- **Title:** Objetivo
- **Under:** CAPÍTULO III: DE LA GESTIÓN DE RIESGO
- **Starts on page:** 6; **words:** 159

```text
ARTÍCULO 11. Objetivo. En el presente capítulo se establecen la estructura, los mecanismos y
los procedimientos necesarios para una Gestión Integral de Riesgo (en lo adelante, OIR), que
permitan identificar, evaluar, priorizar y dar el tratamiento efectivo a los riesgos asociados a la
Aduana y el tráfico internacional de mercancías, con el fin de determinar un tratamiento apropiado
para estos, procurando conservar un balance adecuado, de control y cumplimiento, recaudo
eficiente y la facilitación del eomercio exterior.
PÁRRAFO. Asimismo, la gestión de riesgo tiene como objetivo prevenir y mitigar aquellos
riesgos inherentes a las mercancías, medios de transporte, contenedores y otras unidades de
transporte, su ruta o itinerario previo a la llegada o salida, pasajeros, tripulación y operadores
aduaneros que representen un riesgo y, por otro lado, agilizar el levante de aquellas mercancías
que representen un riesgo bajo, disminuyendo el factor discrecional al momento de decidir el tipo
de control a efectuar por las autoridades aduaneras o paraaduaneras competentes.
```

#### `ley-168-21.pdf`, article 42

- **Title:** Rendición de garantía
- **Under:** TÍTULO III: DE LAS PERSONAS VINCULADAS A LA ACTIVIDAD ADUANERA / CAPÍTULO II: DE LAS PERSONAS AUTORIZADAS PARA INTERVENIR ANTE LAS ADUANAS / SECCIÓN III: DE LOS AGENTES DE ADUANAS
- **Starts on page:** 54; **words:** 100

```text
Artículo 42.- Rendición de garantía. Los agentes de Aduanas deberán
depositar una fianza o garantía prevista en la presente ley, para
responder ante la autoridad aduanera como consecuencia de los actos,
omisiones e ilícitos aduaneros en que incurran en el ejercicio de su
actividad aduanera, así como de sus auxiliares, empleados o
apoderados.
Párrafo: Transcurrido el plazo de treinta (30) días hábiles de vencida
la fianza indicada anteriormente, y el titular de la licencia no>
presente la renovación de la misma, la Dirección General de Aduanas
procederá a suspender provisionalmente dicha licencia, hasta tanto se
ffi
presente la renovación correspondiente.
```

#### `ley-168-21.pdf`, article 266

- **Title:** Exigencia de garantías
- **Under:** TÍTULO VII: DE LOS REGÍMENES Y OPERACIONES ADUANERAS / CAPÍTULO III: DE LOS REGÍMENES TEMPORALES O SUSPENSIVOS DE DERECHOS / SECCIÓN III: ADMISIÓN TEMPORAL SIN TRANSFORMACIÓN
- **Starts on page:** 160; **words:** 171

```text
Artículo 266.- Exigencia de garantías. Las mercancías amparadas bajo
este régimen estarán sujetas a la presentación de garantía. Esta
deberá calcularse según el monto de los tributos que pagarían las
mercancías en el momento de aceptarse la declaración en el régimen.
Párrafo I: Se podrá rendir garantía global, por el monto total de
tributos aplicables en las importaciones enumeradas en los numerales
1) , 3), 4), 6), 7) y 8) del artículo 265. No será obligatoria la
presentación de garantía para las mercancías señaladas en los
numerales del 9) al 16) del artículo 265.
Párrafo II: En las demás categorías no indicadas en este artículo, la
Dirección General de Aduanas determinará los casos en que sea
necesario rendir garantía, la cual podrá ser de carácter global,
cuando así lo requiera la naturaleza de la operación.
Párrafo III: Cuando se haya rendido garantía, ésta se hará efectiva si
el régimen no es cancelado dentro del plazo establecido o se
desnaturalizan los fines que originaron su autorización, sin perjuicio
de otras acciones procedentes.
```

## Chunking dry run

Nothing is embedded and no chunk is saved: `index.chunk_article` is applied in memory to the articles in `index/articles.jsonl`. `norma-01-2023.pdf` is left out because it will be added later through the add-document tool. That leaves 802 articles and 109,617 words.

The rule, for a chunk size of LIMIT words:

- An article at or under LIMIT is one chunk.
- A longer article is cut before every line that opens a párrafo (`Párrafo I.-`, `Párrafo:`, `PÁRRAFO II.`) or a numbered item (`1) ...`, `1. ...`). Consecutive pieces are then packed together, in order, while their total stays at or under LIMIT.
- A piece that is over LIMIT by itself has no boundary inside, so it stays whole as one chunk.
- Lettered items (`a) ...`) are not boundaries.
- `ley-168-21.pdf` article 4 (Definiciones) is one numbered item per chunk at every LIMIT: 89 chunks, with the article's opening sentence in the first.
- Every chunk keeps the source file, article number, title, título, capítulo and sección of its article.

| LIMIT | Total chunks | Articles split | Median chunk words | Max chunk words | Chunks over LIMIT |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 200 | 1,105 | 134 | 86 | 222 | 5 |
| 300 | 988 | 74 | 80 | 300 | 0 |
| 400 | 935 | 36 | 78 | 400 | 0 |
| 500 | 915 | 21 | 77 | 499 | 0 |

An article is split when it gives more than one chunk. Chunk words count the text of the chunk only, not the fields kept with it.

### Pieces still over LIMIT

Each of these is a single piece with no párrafo or numbered item inside to cut at. The last column counts its lines that open a lettered item.

LIMIT 200:

| File | Article | Chunk of the article | Words | Starts with | Lettered items inside |
| --- | ---: | ---: | ---: | --- | ---: |
| `ley-168-21.pdf` | 71 | 3 | 222 | 2) Las empresas de servicios de envíos de entrega rápida (Co ... | 8 |
| `decreto-755-22.pdf` | 144 | 2 | 219 | 2) Equipaje de viajeros o pasajeros conteniendo sus efectos  ... | 11 |
| `decreto-755-22.pdf` | 148 | 6 | 211 | 1) Bienes y servicios suministrados al importador, gratuitam ... | 15 |
| `ley-168-21.pdf` | 370 | 1 | 208 | Artículo 370.- Faltas tributarias aduaneras. Será sancionada ... | 5 |
| `ley-168-21.pdf` | 71 | 2 | 206 | 1) Los agentes de Aduanas, cuando: a) La imposición de amone ... | 6 |

LIMIT 300: none.

LIMIT 400: none.

LIMIT 500: none.
