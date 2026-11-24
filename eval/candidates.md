# Candidate locations for the 35 stakeholder questions

Working notes for filling in `expected_source` and `expected_location` in `eval/questions.csv`. This file holds no reference answers and does not pick between candidates.

## How these were found

- By reading `TOC.md` and then the article texts in `index/articles.jsonl` (806 entries: `ley-168-21.pdf` 420, `decreto-755-22.pdf` 318, `decreto-609-24.pdf` 64, `norma-01-2023.pdf` 4).
- `retrieval.py`, the `search` tool, the embeddings and every API were left alone. To decide which articles to open beyond the ones the table of contents pointed to, the article texts were scanned for literal words and phrases (case and accents ignored, and two frequent OCR misreads tolerated: `c` read as `e`, `rn` read as `m`). The words scanned are listed wherever nothing was found.
- `eval/questions.csv` was not touched.

## How to read an entry

- Each candidate gives the file name, the article number, the title and the PDF page as they stand in `index/articles.jsonl`, then the quote.
- **Quotes are copied from the `text` field, with line breaks turned into single spaces and nothing else changed.** OCR errors and stray characters are kept (`faetura`, `¡J`, `M5`), so a quote can be found again in the file. ` […] ` joins two passages of the same article, for example the lead-in of a list and one of its items. Every passage was checked by script to be an exact substring of its article.
- Up to three candidates per question, or per part of a two-part question, in document order (law, then Decreto 755-22, then the rest; by article number). The order is not a ranking.
- **Scope** is a one-line remark on what the quoted text is about when that is not obvious from the quote. It is not an answer.
- **Not found** says which aspect of the question no article covers, with the words searched. **No candidate found** means nothing was found for the whole part.
- **Also read, not listed** names other articles that were read and touch the subject, so the limit of three hides nothing.

## Three things about the index that affect `expected_location`

1. **Article 4 of the law is one entry with 89 definitions.** `TOC.md` says each definition is its own chunk in the index, but the location would still be written `Artículo 4`. Where a definition is a candidate, its number is given.
2. **`norma-01-2023.pdf` is in `index/articles.jsonl` but not in `TOC.md`.** Its four entries are numbered 1 to 4 and have no title; they are the resolution's PRIMERO to CUARTO, not articles. It is quoted below only once, as nearest text for V9.
3. **Some articles have no title in the index** (for example Decreto 755-22 arts. 83, 156, 163 and 170). They are shown with the first words of their text.

## Summary

One row per question. **Candidates** counts the distinct articles listed as candidates across the parts of the question; text shown as "nearest" is not counted. **Looks covered by** is a judgement on the question as asked, not a choice among the candidates:

- **one article**: a single article among the candidates is enough to answer it.
- **two or more articles**: the answer has to be put together from two or more of them.
- **only partly**: the articles answer one part or the general point, and something the question asks for is not in the index. The "Not found" and "No candidate found" lines say what.
- **not at all**: nothing in the index answers it.

Totals: 4 one article, 11 two or more, 17 only partly, 3 not at all.

| Question | Candidates | Looks covered by |
| --- | ---: | --- |
| A1 | 6 | two or more articles |
| A2 | 3 | one article |
| A3 | 6 | only partly |
| A4 | 6 | only partly |
| A5 | 3 | only partly |
| A6 | 6 | two or more articles |
| A7 | 8 | only partly |
| A8 | 3 | two or more articles |
| A9 | 3 | only partly |
| A10 | 0 | not at all |
| V1 | 6 | two or more articles |
| V2 | 3 | only partly |
| V3 | 3 | one article |
| V4 | 2 | only partly |
| V5 | 5 | only partly |
| V6 | 3 | one article |
| V7 | 2 | only partly |
| V8 | 3 | only partly |
| V9 | 2 | only partly |
| V10 | 3 | only partly |
| P1 | 3 | only partly |
| P2 | 3 | only partly |
| P3 | 3 | only partly |
| P4 | 0 | not at all |
| P5 | 3 | two or more articles |
| P6 | 3 | only partly |
| P7 | 3 | two or more articles |
| P8 | 3 | two or more articles |
| P9 | 3 | two or more articles |
| P10 | 0 | not at all |
| P11 | 3 | only partly |
| P12 | 3 | two or more articles |
| P13 | 3 | two or more articles |
| P14 | 3 | one article |
| P15 | 3 | two or more articles |

Seven of these calls are close:

- **A9, V4 and P3** are "only partly" by a thin margin. The candidates are general (origin and certificates; what the declaration states; access to the audit file) and the specific thing asked (DR-CAFTA rules and the tariff; what an invoice must contain; reference values) is not in the index.
- **P5** is marked "two or more" because the provisional character of the determination (Ley art. 89) and the rule on changing a criterion (Ley art. 217) answer it together. No article deals with a long-standing practice as such.
- **P12 and P13** are general questions for which the index has no general rule, only rules for particular decisions and deadlines. They are marked "two or more" because those rules can be put together into an answer.
- **P14** is marked "one article" because Ley art. 217 answers both halves of the question; Ley art. 214 adds one more circumstance.

## Agente aduanal (A1 to A10)

### A1. ¿Qué plazo tenemos para presentar la declaración aduanera una vez que el contenedor llega a un puerto dominicano y qué sanciones se aplican si no cumplimos con ese plazo?

**Part 1. Plazo para presentar la declaración una vez que llega el contenedor**

1. `ley-168-21.pdf` · Artículo 199 · «Plazo para declarar» · p. 126

   > Una vez que las mercancías han arribado en el medio de transporte correspondiente y han sido presentadas a la autoridad aduanera en el puerto, aeropuerto o paso fronterizo terrestre, nace para el consignatario, importador o para quien tenga la libre disposición de las mercancías, la obligación de iniciar el proceso de despacho, teniendo un plazo de cinco (5) días para declarar.

2. `decreto-755-22.pdf` · Artículo 145 · «Inicio del plazo para realizar la declaración aduanera» · p. 63

   > El computo del plazo de los cinco (5) días hábiles para la declaración inicia a partir de la fecha de la recepción legal del medio de transporte.

3. `decreto-755-22.pdf` · Artículo 146 · «De la prórroga del plazo para la presentación de la declaración» · p. 63

   > Excepcionalmente, a solicitud del declarante, la Aduana podrá prorrogar el plazo fijado para la presentación de la declaración de las mercancías, a los fines de evitar las sanciones aplicables en el artículo 374 por concepto de declaración tardía. […] PÁRRAFO IV. El plazo aprobado será solamente de cinco (5) dias hábiles, salvo en casos excepcionales de fuerza mayor, debidamente justificada y comprobada, en cuyo caso podrá prorrogarse el plazo por tres (3) dias hábiles adicionales.

   Scope: About extending the deadline, not the deadline itself.

**Part 2. Sanciones si no se cumple ese plazo**

1. `ley-168-21.pdf` · Artículo 112 · «Abandono de hecho» · p. 87

   > Las mercancías serán consideradas legalmente en abandono de hecho en los siguientes casos: […] 1) Cuando no se solicite una destinación dentro de un plazo de treinta (30) días, contados desde la fecha de llegada de las mercancías a la zona primaria de jurisdicción aduanera, salvo en caso fortuito o de fuerza mayor debidamente comprobada;

   Scope: A consequence listed under abandonment, not under penalties.

2. `ley-168-21.pdf` · Artículo 373 · «Faltas aduaneras» · p. 207

   > Incurre en faltas aduaneras, la persona que: […] 6) No presente la declaración de destinación aduanera de las mercancías dentro de los plazos establecidos en la presente ley;

3. `ley-168-21.pdf` · Artículo 374 · «Sanciones a faltas aduaneras» · p. 209

   > Párrafo I: Para el caso de la falta aduanera sobre declaración tardía, se impondrá a partir del vencimiento del plazo un recargo de cinco por ciento (5%), por la primera semana o fracción de ésta, y un tres por ciento (3%) después de la primera semana o fracción de semana, el que será calculado tomando como base el valor de la mercancía.

Also read, not listed: Ley art. 355 (fines accrue interest); Decreto 755-22 art. 146 párr. V (a request for extension does not suspend the deadline), art. 152 párr. V (no late-declaration penalty under an incomplete declaration), art. 236 (2 % monthly interest on fines).

### A2. ¿Podemos presentar la declaración aduanera antes de que llegue el contenedor desde China para agilizar el despacho de la mercancía?

1. `ley-168-21.pdf` · Artículo 208 · «Declaración anticipada» · p. 129

   > Es la declaración que se presenta cuando las mercancías no han llegado a zona primaria aduanera oao- y el declarante posee los documentos o informaciones correspondientes, la cual tiene por finalidad exclusiva el avance de los trámites, la que sólo tendrá efectos jurídicos cuando se presenten todos los elementos de la obligación tributaria aduanera.

2. `decreto-755-22.pdf` · Artículo 151 · «Modalidades de la declaración aduanera» · p. 71

   > 4) Modalidad de declaración anticipada. La declaración se considera anticipada siempre y cuando la carga aún no haya llegado a zona primaria aduanera (para importación). Puede ser presentada con copias legibles de los documentos requeridos, por vía electrónica.

3. `decreto-755-22.pdf` · Artículo 154 · «De la modalidad de declaración anticipada» · p. 74

   > La modalidad de declaración anticipada puede ser usada por cualquier empresa. En caso de que el operador o agente representante realice la declaración anticipada previo a la presentación del manifiesto de carga, debe enlazar el documento de embarque a la declaración, tan pronto se manifieste la carga, mediante el procedimiento establecido a tales fines.

Also read, not listed: Ley art. 207 (the declaration may be made "anticipada (antes de la llegada de las mismas)"; it is a fourth article on the same point, left out only because of the limit of three), art. 82 párrafo (an advance declaration that does not match the goods is treated as not accepted); Decreto 755-22 art. 143 párr. V (acceptance of an advance declaration is provisional), art. 160 num. 2 (advance declaration made with a pro forma invoice).

### A3. Si Aduanas considera que el valor declarado de nuestros maniquíes o mobiliario comercial es demasiado bajo, ¿puede aumentarlo? ¿Qué documentación podemos presentar para justificar el precio original de compra?

**Part 1. ¿Puede Aduanas aumentar el valor declarado?**

1. `ley-168-21.pdf` · Artículo 89 · «Revisión de la determinación» · p. 77

   > En el ejercicio de sus facultades, la autoridad aduanera podrá revisar, de manera oficiosa, la determinación de la obligación, hecha en zona primaria aduanera. Dicha determinación tendrá carácter de provisionalidad y podrá ser modificada en el plazo de prescripción establecido en esta ley.

2. `ley-168-21.pdf` · Artículo 238 · «Discrepancias con el resultado de la verificación» · p. 144

   > Párrafo: La Aduana procederá a corregir la declaración, sin perjuicio de las sanciones que correspondan, conforme se establece en esta ley y ¡J su reglamento, cuando se detecten las siguientes diferencias: 1) Cuando se encuentren mercancías de diferente naturaleza, unidad de £{,¿5 medida, calidad, peso, características o condiciones que las individualicen o identifiquen o cuando la verificación física arroje una incorrecta clasificación arancelaria, origen o valor de las mercancías.

3. `decreto-755-22.pdf` · Artículo 65 · «Dudas y hallazgos sobre el valor detectado en el curso de una fiscalización aduanera» · p. 32

   > Si en el marco del desarrollo de un procedimiento de fiscalización los órganos fiscalizadores poseen dudas sobre el valor declarado, deberán iniciar el procedimiento de duda razonable instaurado a tales efectos, el cual constituye un presupuesto procesal necesario para revisar, ajustar o negar el valor de transacción.

   Scope: Placed in the chapter on fiscalización. It names the "procedimiento de duda razonable" but that procedure is not set out in any indexed article.

**Part 2. ¿Qué documentación podemos presentar para justificar el precio original de compra?**

Not found: No article lists the documents accepted to support a declared price when customs questions it at clearance. The "procedimiento de duda razonable" (Decreto 755-22 art. 65) and the "Reglamento de Valoración Aduanera" (Decreto 755-22 art. 70) are named but are not in the index.

Searched for: duda razonable, valor declarado, subvaluación, valor de transacción, valoración, precio pagado / precio de compra, prueba de pago / comprobante de pago / transferencia bancaria, contrato de compraventa, factura.

1. `decreto-755-22.pdf` · Artículo 37 · «La práctica de la prueba en la fiscalización aduanera» · p. 19

   > PÁRRAFO I. Por su parte, corresponde a los sujetos fiscalizados aportar pruebas mediante la presentación de documentos e informes, presentar sus alegatos, aportar sus pruebas a descargo y solicitar las medidas de instrucción tendentes a sustanciar el procedimiento o rebatir los hallazgos e incidencias que pudieran verificarse en el informe de fiscalización correspondiente.

   Scope: Evidence in a fiscalización procedure.

2. `decreto-755-22.pdf` · Artículo 52 · «Entrega de documentación a la Comisión de Fiscalización» · p. 25

   > asi como de los documentos reales que avalen las transacciones comerciales de las mismas, como son facturas comerciales, transferencias bancarias, documentos de embarque, dígase, conocimientos de embarque, guías aéreas o carta de porte terrestre, contratos de compraventa internacional de mercancías, intercambios de correos electrónicos con el proveedor, agente de aduanas, transportista, contable u otra persona vinculada que soporten la transacción, lista de empaques o packing list, notas de crédito u otras modalidades de fmanciamiento en relación con la operación de compraventa, órdenes de compras, cotizaciones de los proveedores

   Scope: A list of what the audit commission copies during a fiscalización visit, not of what an importer may file in a value dispute. The quote is part of one long sentence.

3. `decreto-755-22.pdf` · Artículo 170 · (no title in the index; the text starts "ARTÍCULO 170. La revisión documental de las informaciones a …") · p. 83

   > La revisión documental de las informaciones a que hace referencia el numeral 9 del articulo de la Ley núm. 168-21 puede abarcar a los relacionados a la operación de compraventa internacional, a la forma de pago, fuente de fmanciamiento de la operación y los canales de intermediación financiera, al transporte de la mercancía, a su inocuidad, aspectos relativos a obstáculos técnicos al comercio e información que ayude a clasificar o identificar técnicamente las características de las mercancías.

   Scope: As extracted, the text says "el numeral 9 del articulo de la Ley" without the article number.

Also read, not listed: Ley art. 80 (taxable base by reference to the WTO valuation agreement), art. 90 and 231 (the aforo checks value), art. 93 and 97 (liquidation corrected, charge for the difference), art. 370 lit. c (subvaluación as a falta tributaria), art. 50 num. 3; Decreto 755-22 art. 55 (additional documents, 10 working days), art. 156 (documents the DGA may require), art. 172 (differences in customs value recorded in an acta).

### A4. ¿Qué pasa si la cantidad de bultos o el peso indicado en la lista de empaque (packing list) no coincide con el conocimiento de embarque (Bill of Lading) o el manifiesto de carga? ¿Quién es responsable de corregir esa discrepancia?

**Part 1. ¿Qué pasa si la cantidad de bultos o el peso no coincide?**

Not found: No article compares the packing list with the bill of lading or the manifest. The articles below compare the manifest with the cargo actually loaded or unloaded. The packing list is named in one article only, Decreto 755-22 art. 52 (documents copied during an audit visit).

Searched for: lista de empaque, packing, lista de bultos, lista de carga, cantidad de bultos, número de bultos, peso bruto.

1. `ley-168-21.pdf` · Artículo 168 · «Plazo para la justificación de bultos cargados o descargados de más o de menos» · p. 110

   > Los faltantes o sobrantes de bultos, en relación con la cantidad consignada en el manifiesto de carga, deberán justificarse dentro del plazo máximo de quince (15) días. […] Párrafo II: Transcurrido este plazo, sin que se hubiere justificado las diferencias, se promoverán las acciones legales que correspondan.

2. `ley-168-21.pdf` · Artículo 170 · «Rectificación del manifiesto de carga» · p. 111

   > Párrafo II: En caso de que no se justifiquen los sobrantes, los bultos de más se considerarán en abandono y serán objeto de decomiso por la autoridad aduanera para ser sometidas al proceso de subasta. Párrafo III: Cuando el transportista no pueda justificar ninguna de las situaciones anteriores, incurrirá en las faltas correspondientes, sin perjuicio de la responsabilidad por los delitos o las faltas previstas en esta ley o de las causas eximentes de responsabilidad.

3. `decreto-755-22.pdf` · Artículo 121 · «Eximentes de responsabilidad» · p. 53

   > Se eximirá de la aplicación del régimen sancionador de faltas aduaneras aquellas correcciones relacionadas con los bultos cargados o descargados de más o de menos que se realicen dentro del plazo de los quince (15) días calendarios establecido en el artículo 168 de la Ley de Aduanas, y que la misma esté debidamente justificada. En caso de que no se Justifiquen los bultos cargados o descargados de más o de menos a satisfacción de la Administración Aduanera de la jurisdicción competente, se aplicarán las sanciones previstas en el artículo 373, numeral 3, de la Ley núm. 168-21, según corresponda, así como el comiso de los bultos sobrantes en virtud del artículo 170, párrafo II, de dicha ley.

**Part 2. ¿Quién es responsable de corregir esa discrepancia?**

1. `ley-168-21.pdf` · Artículo 167 · «Enmiendas al manifiesto de carga» · p. 110

   > Dentro del plazo de cinco (5) días, contados a partir de la finalización de las operaciones de descargue del medio de transporte, el transportista o su agente podrá transmitir al administrador de la Aduana respectiva una solicitud de enmienda al manifiesto o documento de transporte, l/] detallando las mercancías destinadas a ese puerto y no entregadas a la Aduana y aquellas que hayan sido entregadas sin estar incluidas en el citado documento.

2. `ley-168-21.pdf` · Artículo 169 · «Responsables de justificar los bultos cargados o descargados de más o de menos» · p. 110

   > Los responsables de justificar los bultos cargados o descargados de más o de menos son: 1) El transportista, porteador o su representante autorizado en el puerto de carga o descarga, en el caso de exportación o importación, respectivamente; […] 3) El consolidador o desconsolidador, la empresa de despacho expreso de envíos (courier), según sea el caso, o el consignatario, cuando sea éste el que realizó el envío y el transportista haya recibido los contenedores cerrados con dispositivos de seguridad.

3. `decreto-755-22.pdf` · Artículo 120 · «Corrección del manifiesto después de la llegada del medio de transporte» · p. 52

   > Dentro de un plazo que no exceda los diez (10) días calendario, contados a partir de la llegada del medio de transporte o recepción legal, el transportista podrá solicitar correcciones al manifiesto de carga, por errores cometidos involuntariamente sin intención de fraude y siempre que la corrección se produzca antes de que el oficial de Aduanas detecte dichos errores, en los casos siguientes: […] 3) Correeciones relaeionadas eon la carga, tales como descripción general de la carga, cantidad de bultos, exeedentes de mercancías o bultos de más, faltantes de mercancías o bultos de menos.

Also read, not listed: Ley art. 4 defs. 17, 27 and 56 (bulto, conocimiento de embarque, manifiesto de carga), art. 151 (written request within 10 days), art. 153 párrafo (weight and quantity checked on reception), art. 154 (the carrier reports inconsistencies in packages or weight), art. 166, art. 170 párr. I (justification issued by the carrier's representative at the port of loading), art. 203 (the declarant answers for the match between declaration and documents), art. 356 párr. III, art. 373 num. 3; Decreto 755-22 art. 105 (manifest data), art. 122, 124, 125, art. 160 num. 4 (declaration corrected after a manifest correction).

### A5. ¿Puede Aduanas rechazar una factura comercial porque describe la mercancía simplemente como «mobiliario comercial», sin especificar los materiales, las cantidades y los precios unitarios?

Not found: No article speaks of rejecting a commercial invoice, or sets what an invoice must contain (materials, quantities, unit prices). The candidates below are about the description of the goods in the declaration and about incomplete documents.

Searched for: factura (the 14 articles that contain the word), rechaz-, descripción genérica / general, clara e inmediata, precio unitario, valor unitario, mobiliario, mueble.

1. `ley-168-21.pdf` · Artículo 205 · «Suministro de información» · p. 129

   > El declarante será ¿5 responsable de suministrar la información y los datos reales y necesarios para determinar la obligación tributaria aduanera, especialmente respecto a la descripción de la mercancía, su clasificación arancelaria, cantidad, tributos aplicables, cumplimiento K\ de las regulaciones arancelarias y no arancelarias que rigen para las mercancías, de conformidad con lo previsto en normas legales.

2. `ley-168-21.pdf` · Artículo 373 · «Faltas aduaneras» · p. 207

   > Incurre en faltas aduaneras, la persona que: […] 5) Presente en forma incompleta o incorrecta los documentos necesarios para practicar el aforo aduanero;

3. `decreto-755-22.pdf` · Artículo 148 · «Contenido de una declaración aduanera» · p. 65

   > h) De las mercancías. Informaciones referentes a las mercancías importadas o exportadas, tales como: 1) Descripción de la mercancía. […] 3) Detalle de las características que permitan su clara e inmediata identificación.

   Scope: Content of the declaration (DUA), not of the invoice.

Also read, not listed: Ley art. 204 num. 1 (the invoice is one of the documents that accompany the declaration), art. 229 (documentary review covers the description of the goods), art. 235 (customs may approve the inspection result, reject the declaration or correct it), art. 316 párrafo (courier shipments: "En caso de no admitirse o no existir la factura"); Decreto 755-22 art. 174 párr. I num. 8, art. 227 (courier parcels held for a missing or false invoice).

### A6. Si Aduanas inspecciona un contenedor y encuentra 120 maniquíes cuando solamente se declararon 100, ¿podemos rectificar la declaración o esto constituye automáticamente una infracción aduanera?

**Part 1. ¿Podemos rectificar la declaración?**

1. `ley-168-21.pdf` · Artículo 219 · «Corrección» · p. 134

   > El operador aduanero podrá solicitar \ correcciones a la declaración previa a la verificación (aforo) de las mercancías. En todo caso, la Aduana tendrá la facultad de aceptar o rechazar la solicitud de corrección a la luz de los hechos verificados.

2. `ley-168-21.pdf` · Artículo 356 · «Eximente de responsabilidad» · p. 196

   > Párrafo II: En los casos en que conforme la selectividad del sistema de análisis de riesgo, la mercancía sea sometida a un procedimiento de inspección no intrusiva o invasiva, se permitirá la rectificación de la declaración, sin la aplicación de sanciones, siempre que se compruebe la buena fe del operador aduanero y la misma se realice de acuerdo con el procedimiento, y plazo previsto en el reglamento a esta ley.

3. `decreto-755-22.pdf` · Artículo 162 · «De las causales de rectificación a la declaración aduanera» · p. 79

   > 1) Cuando las mercancías hayan sido despachadas sin reconocimiento físico o a través de inspección no intrusiva, y el declarante constate en su almacén o instalaciones, que recibió mercancías de más o de menos de las consignadas en la factura comercial y declaradas. […] PARRAFO II. Lo anterior no aplica en el caso que la DGA previamente haya iniciado un procedimiento de fiscalización, o acción de control tendente a detectar la falta.

**Part 2. ¿Constituye automáticamente una infracción aduanera?**

1. `ley-168-21.pdf` · Artículo 370 · «Faltas tributarias aduaneras» · p. 205

   > Será sancionada la persona física o jurídica, con la imposición de una multa correspondiente al doble del valor de los impuestos dejado de pagar, quien incurra en los siguientes hechos: […] b) Cuando al momento de haberse efectuado la inspección física se encuentren mercancías de más de las declaradas o manifestadas, cuya reincidencia en esta conducta, podrá generar un incremento adicional de un 50% si se comprueba que una misma persona ha incurrido más de dos veces en este tipo de falta, en un periodo no menor de un año, salvo las justificaciones previstas en esta ley para las mercancías descargadas de más;

2. `decreto-755-22.pdf` · Artículo 172 · «Discrepancias con el resultado de la verificación» · p. 83

   > La Aduana enviará una notificación al declarante o representante por sistema informático, en un plazo no mayor a ocho (8) horas laborables después de haber sido verificada físicamente la carga, esto sin perjuicio de las sanciones que correspondan. En los casos que se encuentren mercancías de más en la declaración, diferencias en el valor aduanero, clasificación arancelaria, peso, tamaño, capacidad, origen, entre otras discrepancias que puedan ocurrir en el proceso de verificación y que afecte el monto de los tributos a pagar.

3. `decreto-755-22.pdf` · Artículo 235 · «Configuración de la falta tributaria de mercancías encontradas de más» · p. 103

   > En el supuesto o conducta tipificada como falta tributaria consistente en mercancias encontradas de más de las declaradas o manifestadas, se tendrá como configurada dicha falta, cuando el personal actuante de la Aduana lleve a cabo la inspección física a la que hace mención el literal b del articulo 370 de la Ley núm. 168-21 en zona primaria aduanera, asi como en zona secundaria aduanera, ya sea durante o posterior al despacho aduanero, durante un proceso de fiscalización o durante una verificación a destino en las instalaciones autorizadas.

Also read, not listed: Ley art. 220, art. 236 num. 3, art. 238 (customs corrects the declaration "sin perjuicio de las sanciones"), art. 357 (gradualidad), art. 358 (negligence is punishable), art. 366 (reductions of fines); Decreto 755-22 art. 157 párr. III (excess found in an examen previo), art. 159 (correction before the inspection starts), art. 163 (5 working days after release for excess found at the importer's premises).

### A7. Si detectamos un error en la clasificación arancelaria o en el valor declarado después de presentar la declaración aduanera, ¿en qué circunstancias podemos rectificarla, qué plazos tenemos y qué cambia si Aduanas ya ha iniciado una inspección?

**Part 1. ¿En qué circunstancias podemos rectificarla?**

1. `ley-168-21.pdf` · Artículo 219 · «Corrección» · p. 134

   > El operador aduanero podrá solicitar \ correcciones a la declaración previa a la verificación (aforo) de las mercancías. […] Párrafo: Se permitirá la corrección siempre y cuando: 1) Se compruebe que no hubo ilícito aduanero.

2. `decreto-755-22.pdf` · Artículo 160 · «De las causales de corrección a la declaración aduanera» · p. 78

   > Las causales de correcciones a la declaración aduanera susceptibles de ser aceptadas por la Administración aduanera correspondiente son las siguientes: 1) Errores involuntarios o inadvertencias en la digitación, donde se omiten o agreguen datos.

   Scope: The article lists seven grounds; the quote is the lead-in and the first.

3. `decreto-755-22.pdf` · Artículo 162 · «De las causales de rectificación a la declaración aduanera» · p. 79

   > Se podrá admitir la rectificación de la declaración al amparo de lo establecido en la ley en los siguientes casos: […] 6) Cuando se el importador o su representante debidamente autorizado haya detectado una incorrecta clasificación arancelaria u origen posterior al levante, y no se haya podido detectar en el proceso de reconocimiento físico de mercancías, o que las mercancías no hayan sido objeto de dicho reconocimiento, siempre que, por la propia iniciativa del importador, rm consignatario o su representante debidamente autorizado, se haga del conocimiento a la DGA el error objeto de rectificación.

**Part 2. ¿Qué plazos tenemos?**

Not found: No article gives a deadline, in days, to ask for the rectification of a classification or value error after release. Ley art. 220 leaves "las causales, plazos y el procedimiento" to the reglamento, and Decreto 755-22 art. 162 num. 6 (classification found wrong after release) states no deadline.

Searched for: rectificación, corrección, plazo, días hábiles (read in Ley arts. 219-222 and Decreto 755-22 arts. 147, 159-163, 168).

1. `decreto-755-22.pdf` · Artículo 159 · «De la corrección a la declaración aduanera» · p. 77

   > El importador, exportador consignatario o su representante debidamente autorizado podrá solicitar correcciones a la declaración, previo al inicio del proceso de reconocimiento de la mercancía, ya sea en zona primaria aduanera o en domicilio comercial del consignatario.

2. `decreto-755-22.pdf` · Artículo 161 · «Procedimiento para rectificación de la declaración de mercancías que hayan sido despachadas» · p. 78

   > PARRAFO I. En el caso de que la rectificación de la declaración aduanera implique una reliquidación por las diferencias de los derechos e impuestos a las mercancías, se procederá a ím notificar en un plazo de diez (10) días hábiles el monto con-espondiente dejado de pagar a la Administración aduanera.

   Scope: A deadline inside the rectification procedure, not a deadline to ask for it.

3. `decreto-755-22.pdf` · Artículo 163 · (no title in the index; the text starts "ARTICULO 163. Plazos, requisitos y procedimientos para ampararse en …") · p. 80

   > El declarante tendrá un plazo de cinco (5) días hábiles a partir del levante de las mercancías para comunicar a la Administración aduanera correspondiente la constatación de mercancías de más o de menos, debiendo aportar los elementos probatorios documentales que Justifiquen su solicitud.

   Scope: For goods found in excess or short, not for classification or value.

**Part 3. ¿Qué cambia si Aduanas ya ha iniciado una inspección?**

1. `ley-168-21.pdf` · Artículo 238 · «Discrepancias con el resultado de la verificación» · p. 144

   > Párrafo: La Aduana procederá a corregir la declaración, sin perjuicio de las sanciones que correspondan, conforme se establece en esta ley y ¡J su reglamento, cuando se detecten las siguientes diferencias: 1) Cuando se encuentren mercancías de diferente naturaleza, unidad de £{,¿5 medida, calidad, peso, características o condiciones que las individualicen o identifiquen o cuando la verificación física arroje una incorrecta clasificación arancelaria, origen o valor de las mercancías.

2. `ley-168-21.pdf` · Artículo 356 · «Eximente de responsabilidad» · p. 196

   > Párrafo II: En los casos en que conforme la selectividad del sistema de análisis de riesgo, la mercancía sea sometida a un procedimiento de inspección no intrusiva o invasiva, se permitirá la rectificación de la declaración, sin la aplicación de sanciones, siempre que se compruebe la buena fe del operador aduanero y la misma se realice de acuerdo con el procedimiento, y plazo previsto en el reglamento a esta ley.

3. `decreto-755-22.pdf` · Artículo 162 · «De las causales de rectificación a la declaración aduanera» · p. 79

   > PARRAFO I. En tales casos se exime de la sanción aplicable a las faltas, cuando por propia iniciativa del declarante se informe oportunamente a la DGA, se rectifique el error, siempre que no se haya incurrido en negligencia o fraude. PARRAFO II. Lo anterior no aplica en el caso que la DGA previamente haya iniciado un procedimiento de fiscalización, o acción de control tendente a detectar la falta.

Also read, not listed: Ley art. 107 (three-year prescription), art. 201 (an accepted declaration admits no modification), art. 219 num. 2 (48 hours, exports only), art. 220, art. 366 (reductions of fines for voluntary repair), art. 370 lits. a and c (wrong classification and subvaluación as faltas tributarias); Decreto 755-22 art. 147 (no unilateral change once accepted), art. 159 párr. III (48 hours, exports only), art. 168 (5 working days, damaged goods).

### A8. Si Display proporciona información incorrecta a su agente aduanal y este presenta la declaración basándose en dicha información, ¿quién es legalmente responsable de las sanciones correspondientes: el importador, el agente aduanal o ambos?

1. `ley-168-21.pdf` · Artículo 48 · «Responsabilidad» · p. 56

   > Los Agentes de Aduanas son responsables, salvo la exclusión de responsabilidad prevista en el artículo 50, del pago de los derechos e impuestos cuya aplicación y fiscalización corresponda a Aduanas, y del total del valor de las multas que resulten de faltas cometidas por su acción u omisión en los despachos y gestiones de representación a su cargo. Párrafo I: Los mandantes son responsables del pago de todos los derechos e impuestos cuya aplicación y fiscalización corresponda a Aduanas, cualquiera que sea su naturaleza y finalidad, así como del total del valor de las multas que resulten de las faltas cometidas en los despachos y gestiones de representación a cargo de los agentes de Aduanas, cuando se demuestre que se reúnan cualquiera de las condiciones eximentes de los agentes de Aduanas estipuladas por el artículo 50 de esta ley.

   Scope: Párrafo II of the same article (no joint liability when the act or omission follows from the principal's) is not quoted here.

2. `ley-168-21.pdf` · Artículo 50 · «Eximentes de responsabilidad para los agentes de Aduanas» · p. 57

   > El agente de Aduanas quedará eximido de responsabilidad en LybS los siguientes casos: 1) Del pago de todos los tributos y sanciones, si estos provienen de V) la inexactitud o falsedad de datos y documentos que el importador hubiera proporcionado al agente de Aduanas, siempre que este último no hubiera podido conocer dicha inexactitud o falsedad por no poder examinar las mercancías, o debido al hecho de que al examinar las mercancías, no se pueda apreciar a la vista, la inexactitud o falsedad de las mismas y por requerir para su identificación de análisis químico o de análisis de laboratorio, tratándose de mercancías que mediante normas generales establezca la Dirección General de Aduanas;

   Scope: Numerals 2 and 3 of the same article give two more exemptions (certificate of origin; value arising from the sale contract).

3. `ley-168-21.pdf` · Artículo 359 · «Responsabilidad operador aduanero» · p. 199

   > Todo operador aduanero que se compruebe su participación en hechos vinculantes a una determinada falta aduanera y falta tributaria aduanera, será responsable con su representado, del cumplimiento de las obligaciones tributarias aduaneras y al pago de los recargos e intereses moratorios, que se deriven de su participación en el hecho, sin perjuicio que se proceda a iniciar el respectivo procedimiento administrativo sancionador de suspensión del ejercicio de cualquier actividad vinculada a las Aduanas dominicanas.

Also read, not listed: Ley art. 40 (apoderados especiales), art. 47 (a declaration filed by the agent is presumed made with the consignee's consent), art. 49 (the agent's right to recover from the principal), art. 203 (declarants answer for the content of the declaration and must ask their principals for the documents), art. 372, arts. 375-378 (personal and joint liability).

### A9. Si compramos góndolas fabricadas en China a un proveedor estadounidense y las embarcamos desde Miami, ¿podemos acogernos al tratamiento arancelario preferencial del DR-CAFTA? ¿Qué arancel de importación se aplicaría?

**Part 1. ¿Podemos acogernos al tratamiento arancelario preferencial del DR-CAFTA?**

Not found: No article contains the DR-CAFTA rules of origin, or any rule on goods made in a third country and shipped from a member country. The candidates below speak of preferential origin in general. DR-CAFTA is named only in norma-01-2023.pdf (entry 2, on the currency of service fees). "Libre comercio" also appears in that file's fee table (entry 1, the price of a form), in Decreto 755-22 art. 148 (the declaration states the agreement to apply) and in art. 177 (courier shipments).

Searched for: CAFTA, tratado de libre comercio / libre comercio, Estados Unidos, China, Miami, preferenc-, certificado de origen, normas / reglas de origen, país de origen, expedición directa, transporte directo, tercer país, triangulación.

1. `ley-168-21.pdf` · Artículo 4 · «Definiciones» · p. 8 · definitions 22 "Certificado de origen" and 63 "Normas de origen"

   > 22) Certificado de origen: Documento expedido por la autoridad competente, un productor, exportador o importador, para dar fe de que cierta mercancía ha sido extraída, obtenida, cosechada, elaborada o producida en determinado país; se utiliza con la finalidad de demostrar que una mercancía cumple con los requisitos para aprovechar las preferencias arancelarias pactadas en un acuerdo comercial, asi como para aplicar determinadas medidas de política comercial, como los contingentes, medidas de defensa comercial, entre otras. […] 63) Normas de origen: Son disposiciones específicas desarrolladas a partir de los principios establecidos por la legislación nacional o por convenios internacionales ("criterios de origen") aplicados por un país a fin de determinar el origen de las mercancías. Estas se pueden dividir en reglas de origen preferenciales y no preferenciales.

2. `ley-168-21.pdf` · Artículo 204 · «Documentos que deben acompañar la declaración» · p. 128

   > La declaración deberá acompañarse con los documentos que le sirven de base, según el régimen aduanero de que se trate, que son los siguientes: […] 3) Certificado de origen de las mercancías, cuando proceda;

3. `ley-168-21.pdf` · Artículo 230 · «Determinación de origen preferencial y no preferencial» · p. 141

   > El origen de las mercancías se podrá determinar para efectos preferenciales arancelarios, no preferenciales, aplicación impuestos compensatorios, salvaguardas, cupos y para cualquiera otra medida que algún acuerdo comercial o decreto establezca. Párrafo: El origen podrá corresponder a uno o más países, o a una zona o territorio geográfico determinado.

**Part 2. ¿Qué arancel de importación se aplicaría?**

**No candidate found.**

Searched for: arancel de Aduanas, tasa arancelaria, tipo arancelario, derechos arancelarios, ad valorem, gravamen, tarifa, góndola, mobiliario, mueble, estantería.

The tariff schedule is not one of the four indexed documents. Ley art. 80 says the taxable base is the one set by national legislation, and the only article that ties a rate to a tariff heading is Ley art. 410 (sugar).

Also read, not listed: Ley art. 31 nums. 7 and 9 and párr. I (checks of origin rules for tariff preferences, "posible triangulación"), art. 50 num. 2 (certificate of origin needed for a preferential tariff under a treaty), art. 97 párr. II (refund when preferential treatment was not requested), art. 212 num. 4 (advance ruling on preferential origin "de acuerdo con el tratado que se invoque"), art. 370 lit. e (wrong declaration of origin); Decreto 755-22 art. 148 párr. II lit. g (the declaration states the trade agreement to apply).

### A10. Si Aduanas ya ha autorizado el levante de nuestro contenedor, pero no podemos retirarlo del puerto, ¿cuánto nos cobrará la naviera por demora y detención (demurrage y detention) y de cuántos días libres disponemos?

**Part 1. ¿Cuánto cobrará la naviera por demora y detención?**

**No candidate found.**

Searched for: demurrage, detention, demora, detención, sobreestadía / sobrestadía, días libres, libre de almacenaje, tiempo libre, días de gracia, naviera / naviero, almacenaje / almacenamiento, tarifa.

**Part 2. ¿De cuántos días libres disponemos?**

**No candidate found.**

Searched for: demurrage, detention, demora, detención, sobreestadía / sobrestadía, días libres, libre de almacenaje, tiempo libre, días de gracia, naviera / naviero, almacenaje / almacenamiento, tarifa.

Nearest text, about a different situation. Not counted as a candidate:

1. `ley-168-21.pdf` · Artículo 112 · «Abandono de hecho» · p. 87

   > 7) Cuando transcurra un plazo de treinta (30) días a partir de la entrega de la liquidación o autorización del levante por la autoridad aduanera;

   Scope: The customs deadline after release is authorised (abandonment), not the shipping line's free days.

2. `ley-168-21.pdf` · Artículo 239 · «Cumplimiento de formalidades» · p. 145

   > Párrafo: La entrega de las mercancías, con posterioridad a la autorización del levante, la realizará el agente naviero transportista o porteador, depositario, operador portuario, aeroportuario u otro operador autorizado que las tenga bajo su custodia y control, al importador, consignatario, dueño o sus 3yhS representantes, previo cumplimiento de las formalidades prevista en esta ley y su reglamento de aplicación.

   Scope: The only place where the shipping agent appears in this situation; it says nothing about charges.

Also read, not listed: Ley art. 4 def. 11 (agencia naviera), art. 13 and art. 61 párrafo (DGA and warehouse service fees); Decreto 755-22 art. 82 párr. V; norma-01-2023.pdf entry 1 (DGA fee table: no line for demora, detención or almacenaje).

## Vicepresidente de Logística (V1 to V10)

### V1. ¿Cuáles son los documentos que obligatoriamente debo tener listos antes de entregarle el expediente del embarque al agente aduanal? ¿Hay alguno que pueda entregar después de que llegue el contenedor?

**Part 1. Documentos que obligatoriamente deben estar listos**

1. `ley-168-21.pdf` · Artículo 46 · «Mandato» · p. 55

   > En todo caso, el documento que contiene el mandato deberá ser depositado en original e instrumentado / mediante acto auténtico o bajo firma privada debidamente registrado ante las instituciones competentes.

   Scope: The mandate given to the agent, not a document of the shipment.

2. `ley-168-21.pdf` · Artículo 204 · «Documentos que deben acompañar la declaración» · p. 128

   > La declaración deberá acompañarse con los documentos que le sirven de base, según el régimen aduanero de que se trate, que son los siguientes: M5 1) Factura comercial física, electrónica o por cualquier medio de data, presentada en original; 2) Documento de transporte original físico o electrónico pudiendo ser el conocimiento de embarque marítimo en cualquiera de su características, carta de porte, guía aérea u otro document equivalente presentados por cualquier medio de data o electrónico; 3) Certificado de origen de las mercancías, cuando proceda; 4) Licencias, permisos o certificados referidos al cumplimiento de las restricciones y regulaciones no arancelarias a que estén sujetas las mercancías, resoluciones y demás autorizaciones exigibles en razón de su naturaleza y del régimen aduanero a que se destinen; y, 5) Otros documentos que requiera la Dirección General de Aduanas.

   Scope: The whole list is one sentence.

3. `decreto-755-22.pdf` · Artículo 156 · (no title in the index; the text starts "ARTÍCULO 156. Los documentos a que hace referencia el …") · p. 74

   > Los documentos a que hace referencia el numeral 5 del artículo 204 de la Ley núm. 168-21 son los relacionados a la operación de compraventa internacional, al transporte de la íím. mercancía, al origen, a su inocuidad, a aspectos relativos a obstáculos técnicos al comercio e información que ayude a clasificar o identificar técnicamente las características de las mercancías.

**Part 2. ¿Hay alguno que pueda entregarse después de que llegue el contenedor?**

1. `decreto-755-22.pdf` · Artículo 83 · (no title in the index; the text starts "ARTÍCULO 83. El levante de las mercancías será admisible …") · p. 37

   > Dentro de las causas que justifican la exigibilidad de una garantía como condición para el levante de las mercancías, están las siguientes: 1) Cuando sea necesario demorar la determinación del valor, la clasificación arancelaria, el origen o falte la presentación de documentos esenciales para el despacho aduanero.

2. `decreto-755-22.pdf` · Artículo 146 · «De la prórroga del plazo para la presentación de la declaración» · p. 63

   > La Administración de Aduanas podrá autorizar la solicitud de extensión de plazo en los siguientes casos: 1. Comprobación de documento retrasado de parte del embarcador o proveedor. En caso de tener copia del documento, se puede autorizar la presentación.

3. `decreto-755-22.pdf` · Artículo 151 · «Modalidades de la declaración aduanera» · p. 71

   > 1) Declaraciones incompletas. El declarante que, por razones que la Aduana considere válidas, no posea toda la información necesaria para realizar una declaración de mercancías, se encontrará autorizado a presentar una declaración incompleta, a condición de que la mercancía haya arribado o desembarcado, y que contenga la información que la Aduana considere necesaria para el levante y que el declarante se haga responsable de completarla en el plazo establecido en este Reglamento. […] Esta modalidad es aplicable solo a las empresas de bajo riesgo o con Certificación de Operador Económico Autorizado (OEA).

   Scope: About missing information, not a missing document.

Also read, not listed: Ley art. 74 (documents kept for ten years), art. 203 párr. I (declarants must ask their principals for the documents), art. 208 párrafo; Decreto 755-22 art. 148 (data of the declaration), art. 152 (three working days after unloading to complete an incomplete declaration), art. 157 párr. I, art. 174 párr. I num. 8.

### V2. Si el proveedor chino me envía una factura comercial con un nombre de empresa distinto al que aparece en el Bill of Lading, ¿esto nos puede generar problemas con Aduanas?

Not found: No article deals with a company name that differs between the commercial invoice and the bill of lading. The candidates below are about names in the declaration and in the manifest.

Searched for: nombre del consignatario / importador / proveedor / vendedor / embarcador / consignante, razón social, cambio de consignatario, titularidad, endoso, factura.

1. `ley-168-21.pdf` · Artículo 229 · «Verificación, aforo o inspección documental» · p. 140

   > La revisión documental consistirá en el análisis, por parte del funcionario autorizado, de la información declarada y su cotejo con los documentos que sustentan la declaración de mercancías y demás informaciones que se soliciten al declarante o su representante y que consten en los archivos o base de datos del servicio aduanero. […] 2) Datos de los operadores económicos registrados en dicha declaración: Importador, exportador, agente de Aduana y transportista, cuando corresponda;

2. `ley-168-21.pdf` · Artículo 238 · «Discrepancias con el resultado de la verificación» · p. 144

   > Párrafo: La Aduana procederá a corregir la declaración, sin perjuicio de las sanciones que correspondan, conforme se establece en esta ley y ¡J su reglamento, cuando se detecten las siguientes diferencias: […] 2) Cuando se detecten errores u omisiones en el nombre del importador, exportador, embarcador, consignatario, tamaño y número de contenedor, sellos, entre otras de las informaciones contenidas en la declaración aduanera.

3. `decreto-755-22.pdf` · Artículo 120 · «Corrección del manifiesto después de la llegada del medio de transporte» · p. 52

   > 1) Correcciones relacionadas con el consignatario, tales como rectificaciones del documento de identidad, de la dirección, del Registro Nacional del Contribuyente (RNC) o del domicilio. Siempre que estas enmiendas se traten de errores materiales, que no impliquen, bajo ningún concepto, un cambio del consignatario que figure en el documento de embarque original, salvo en los casos de despacho expreso de envíos o que se trate de correcciones del consignatario las cuales se deriven de un error material, para lo cual deben sustentar que se trata de un error a satisfacción de la Aduana y corregir el contrato de transporte original.

   Scope: Correction of the manifest, requested by the carrier.

Also read, not listed: Ley art. 4 def. 29 (the consignee is the person named in the bill of lading), art. 203 (the declarant answers for the match between declaration and documents), art. 373 num. 5; Decreto 755-22 art. 148 párr. II lits. a, c and d (names stated in the declaration), art. 157 párr. I (invoice and transport document show who owns the goods).

### V3. ¿Necesito tener los documentos originales en físico o son suficientes las copias digitales que nos envían los proveedores?

1. `ley-168-21.pdf` · Artículo 204 · «Documentos que deben acompañar la declaración» · p. 128

   > 1) Factura comercial física, electrónica o por cualquier medio de data, presentada en original; 2) Documento de transporte original físico o electrónico pudiendo ser el conocimiento de embarque marítimo en cualquiera de su características, carta de porte, guía aérea u otro document equivalente presentados por cualquier medio de data o electrónico;

2. `ley-168-21.pdf` · Artículo 208 · «Declaración anticipada» · p. 129

   > Párrafo: Les documentos a presentar en la declaración anticipada pueden ser electrónicos, digitales o por cualquier tipo de data a los cuales no se les negarán efectos jurídicos, validez o fuerza obligatoria, por la sola razón de que están en dicha forma o en razón de no haber sido presentados en su forma original, siempre y cuando cumplan con todos los requisitos de la ley y normas aplicables.

   Scope: Said of the advance declaration.

3. `decreto-755-22.pdf` · Artículo 151 · «Modalidades de la declaración aduanera» · p. 71

   > 4) Modalidad de declaración anticipada. La declaración se considera anticipada siempre y cuando la carga aún no haya llegado a zona primaria aduanera (para importación). Puede ser presentada con copias legibles de los documentos requeridos, por vía electrónica.

   Scope: Said of the advance declaration.

Also read, not listed: Ley art. 46 (the agent's mandate is filed in original), art. 74 (documents kept for ten years), art. 197 párr. II (the declaration is made by electronic transmission); Decreto 755-22 art. 146 párr. II num. 1 (a copy of a delayed document), art. 177 (courier shipments: invoice "original o copia").

### V4. Si traemos un contenedor con maniquíes, góndolas, carritos y piezas de repuesto, ¿la factura tiene que especificar el valor unitario de cada tipo de producto o podemos agrupar algunos artículos?

Not found: No article sets what the commercial invoice must contain, so none says whether unit values are required or items may be grouped. The candidates below are about what the declaration must state for the goods.

Searched for: valor unitario, precio unitario, agrupar / agrupación, por ítem, por línea, factura (the 14 articles that contain the word).

1. `ley-168-21.pdf` · Artículo 205 · «Suministro de información» · p. 129

   > El declarante será ¿5 responsable de suministrar la información y los datos reales y necesarios para determinar la obligación tributaria aduanera, especialmente respecto a la descripción de la mercancía, su clasificación arancelaria, cantidad, tributos aplicables, cumplimiento K\ de las regulaciones arancelarias y no arancelarias que rigen para las mercancías, de conformidad con lo previsto en normas legales.

2. `decreto-755-22.pdf` · Artículo 148 · «Contenido de una declaración aduanera» · p. 65

   > 2) Código arancelario: Subpartida arancelaria a ocho (8) dígitos de las mercancias, de acuerdo con el código numérico del arancel de Aduanas que se acoge al sistema armonizado de designación y codificación de mercancía. […] 8) Valor (US$): Indiear el valor en dólares estadounidenses que figure en la faetura comercial.

   Scope: Content of the declaration (DUA), not of the invoice.

Also read, not listed: Ley art. 202 (goods on one invoice cannot be split among regimes in one declaration), art. 204 num. 1, art. 229; Decreto 755-22 art. 148 párr. II lit. h nums. 1, 3 and 6 (description, identifying detail, quantity).

### V5. Cuando un proveedor nos incluye piezas de repuesto o muestras sin costo adicional, ¿tenemos que declararlas y asignarles un valor aduanero?

**Part 1. ¿Tenemos que declararlas?**

1. `ley-168-21.pdf` · Artículo 198 · «Obligación de declarar» · p. 125

   > Toda mercancía que arribe o salga del territorio aduanero debe declararse, aunque no esté sujeta al pago de tributos de algún tipo, por los medios y en los formatos que establezca la Dirección General de Aduanas, salvo aquellas que se transporten en condición de tránsito o transbordo internacional.

2. `ley-168-21.pdf` · Artículo 370 · «Faltas tributarias aduaneras» · p. 205

   > Será sancionada la persona física o jurídica, con la imposición de una multa correspondiente al doble del valor de los impuestos dejado de pagar, quien incurra en los siguientes hechos: […] b) Cuando al momento de haberse efectuado la inspección física se encuentren mercancías de más de las declaradas o manifestadas, cuya reincidencia en esta conducta, podrá generar un incremento adicional de un 50% si se comprueba que una misma persona ha incurrido más de dos veces en este tipo de falta, en un periodo no menor de un año, salvo las justificaciones previstas en esta ley para las mercancías descargadas de más;

   Scope: What follows when goods are found that were not declared.

**Part 2. ¿Tenemos que asignarles un valor aduanero?**

Not found: No article says how goods supplied free of charge are valued, and none exempts free samples or spare parts from declaration (the exemptions in Ley art. 198 párr. I and Decreto 755-22 art. 144 are travellers' baggage, courier shipments, supplies sold to ships and aircraft, and gifts).

Searched for: muestra, sin valor comercial, sin costo, gratuito / gratuitamente, obsequio, regalo, bonificación, repuesto.

1. `ley-168-21.pdf` · Artículo 80 · «Base imponible y su determinación» · p. 74

   > Párrafo I: Para los impuestos ad valorem se determinará conforme a los métodos establecidos en el Artículo VII sobre el Acuerdo del Valor de la OMC, así como los elementos cuantitativos previstos en la legislación nacional.

   Scope: Refers to the WTO valuation agreement, which is not in the index.

2. `ley-168-21.pdf` · Artículo 192 · «Mercancías en depósito temporal» · p. 122

   > Durante su permanencia en el depósito aduanero temporal, y antes de la aceptación a trámite de la declaración correspondiente por parte de la Aduana, las mercancías pueden ser objeto de reconocimiento, reembarque o división, para garantizar su conservación, someterlas a cortes, perforación u otras formas de inutilización, a fin de conferirles carácter de muestras sin valor comercial, previa autorización del Administrador.

   Scope: The only article that says how goods become "muestras sin valor comercial".

3. `decreto-755-22.pdf` · Artículo 148 · «Contenido de una declaración aduanera» · p. 65

   > Bienes y servicios suministrados al importador, gratuitamente o a precio reducido y utilizados en la producción y venta para la exportación de las mercancías importadas.

   Scope: One item of the value data in the declaration (letter l, read by the OCR as "1)"). It is the only mention of goods supplied free of charge in a valuation context.

Also read, not listed: Ley art. 4 def. 59 (mercancía), art. 205; Decreto 755-22 art. 162 num. 1 (rectification when more goods arrive than invoiced and declared), art. 177 (courier categories mention "muestras comerciales").

### V6. Si compramos mercancía bajo condiciones FOB, ¿qué gastos de transporte, seguro y otros conceptos debo comunicarle al agente aduanal para que calcule correctamente los impuestos de importación?

Not found: No article says in so many words that freight and insurance are added to an FOB price. FOB itself appears only in Ley art. 277 and Decreto 609-24 art. 56, on other matters.

Searched for: FOB, CIF, Incoterm, flete, seguro, gastos, valoración.

1. `ley-168-21.pdf` · Artículo 80 · «Base imponible y su determinación» · p. 74

   > Párrafo I: Para los impuestos ad valorem se determinará conforme a los métodos establecidos en el Artículo VII sobre el Acuerdo del Valor de la OMC, así como los elementos cuantitativos previstos en la legislación nacional.

   Scope: Refers to the WTO valuation agreement, which is not in the index.

2. `ley-168-21.pdf` · Artículo 229 · «Verificación, aforo o inspección documental» · p. 140

   > Se deberá revisar la información contenida en la declaración, en ^^~~ relación con los siguientes aspectos: […] 7) Valor flete y seguro;

3. `decreto-755-22.pdf` · Artículo 148 · «Contenido de una declaración aduanera» · p. 65

   > 9) Informaciones vinculadas a la operación de compraventa internacional que forman parte de la Declaraeión del Valor en Aduanas (DVA), tales eomo: a) Término de eomercio internacional o "Incoterm" pactado. […] o) Gastos de entrega hasta el lugar de importación. p) Gastos de transporte por manejo y entrega en el exterior hasta el lugar de empaque, q) Gastos de transporte desde el lugar de embarque hasta lugar de importaeión. r) Gastos de carga, descarga y manipulación, s) Seguro.

   Scope: The list runs from a) to x); the quote is its lead-in and items o) to s).

Also read, not listed: Ley art. 4 def. 82 (Incoterms), art. 80 párr. II (exchange rate); Decreto 755-22 art. 105 num. 2 lit. i (freight in the manifest), art. 160 num. 6 (declared freight differs from the manifest).

### V7. ¿Cuánto tiempo tenemos para despachar un contenedor antes de que Aduanas considere la mercancía en abandono? ¿Ese plazo es diferente de los días libres que nos concede la naviera?

**Part 1. Tiempo para despachar antes de que la mercancía se considere en abandono**

1. `ley-168-21.pdf` · Artículo 112 · «Abandono de hecho» · p. 87

   > 1) Cuando no se solicite una destinación dentro de un plazo de treinta (30) días, contados desde la fecha de llegada de las mercancías a la zona primaria de jurisdicción aduanera, salvo en caso fortuito o de fuerza mayor debidamente comprobada; […] 5) Cuando transcurra un plazo de cuarenta y cinco (45) días, contados a partir de la declaración, sin que las mismas sean retiradas de zona primaria de jurisdicción aduanera, salvo en caso fortuito o de fuerza mayor debidamente comprobada; […] 7) Cuando transcurra un plazo de treinta (30) días a partir de la entrega de la liquidación o autorización del levante por la autoridad aduanera;

   Scope: Three of the nine cases of the article; they start from different events.

2. `decreto-755-22.pdf` · Artículo 82 · «Abandono de hecho» · p. 36

   > Los plazos de abandono establecidos en la Ley núm. 168- 21 se reputarán como días hábiles. […] PÁRRAFO IV. En los casos del numeral 5 y 7 del artículo 112 de la Ley núm. 168-21, el plazo de abandono se suspenderá cuando exista una controversia o diferencia entre el sujeto pasivo y la Aduana, en sede administrativa o judicial, y la mercancía no haya sido despachada mediante garantía, por no reunir los requisitos estipulados en este Reglamento.

**Part 2. ¿Es diferente de los días libres que concede la naviera?**

**No candidate found.**

Searched for: demurrage, detention, demora, detención, sobreestadía / sobrestadía, días libres, libre de almacenaje, tiempo libre, días de gracia, naviera / naviero, almacenaje / almacenamiento, tarifa.

Also read, not listed: Ley art. 4 def. 1 and art. 110 (what abandonment is), art. 128 (goods can be recovered until 24 hours before the auction), art. 221 párrs. I-II (10 days after withdrawing a declaration); Decreto 755-22 art. 82 párr. V.

### V8. Si el proveedor comete un error en la factura o en el packing list y el contenedor ya está en tránsito, ¿podemos presentar los documentos corregidos sin tener problemas con Aduanas?

Not found: No article deals with replacing or correcting the commercial invoice or the packing list before the declaration is filed. Every correction rule found is about the declaration or about the manifest.

Searched for: proforma, documentos corregidos, factura corregida, nueva factura, sustituir, corrección, lista de empaque / packing, en tránsito.

1. `ley-168-21.pdf` · Artículo 219 · «Corrección» · p. 134

   > El operador aduanero podrá solicitar \ correcciones a la declaración previa a la verificación (aforo) de las mercancías. En todo caso, la Aduana tendrá la facultad de aceptar o rechazar la solicitud de corrección a la luz de los hechos verificados.

2. `decreto-755-22.pdf` · Artículo 159 · «De la corrección a la declaración aduanera» · p. 77

   > El importador, exportador consignatario o su representante debidamente autorizado podrá solicitar correcciones a la declaración, previo al inicio del proceso de reconocimiento de la mercancía, ya sea en zona primaria aduanera o en domicilio comercial del consignatario. […] En tales casos, se absuelve de la sanción aplicable a las faltas, cuando por la propia iniciativa del declarante se informe oportunamente a la Aduana y subsane el error.

3. `decreto-755-22.pdf` · Artículo 160 · «De las causales de corrección a la declaración aduanera» · p. 78

   > Las causales de correcciones a la declaración aduanera susceptibles de ser aceptadas por la Administración aduanera correspondiente son las siguientes: 1) Errores involuntarios o inadvertencias en la digitación, donde se omiten o agreguen datos. 2) Declaraciones en la modalidad anticipada que se haya presentado haciendo uso de una factura proforma y esta difiera de la factura comercial definitiva.

Also read, not listed: Ley art. 82 párrafo, art. 201 and Decreto 755-22 art. 147 (an accepted declaration cannot be changed unilaterally), Ley art. 356 párr. III (manifest and shipping documents corrected within 10 calendar days of arrival); Decreto 755-22 art. 119 (manifest corrections before arrival), art. 146 párr. II num. 1 (document delayed by the shipper or supplier).

### V9. Si nuestro contenedor es seleccionado para una inspección física, ¿puede estar presente alguien de Display? ¿Quién debe asumir los gastos de apertura, descarga e inspección del contenedor?

**Part 1. ¿Puede estar presente alguien de Display?**

1. `ley-168-21.pdf` · Artículo 90 · «Verificación aforo o inspección de las mercancías» · p. 78

   > Párrafo I: En el caso de que Aduanas requiera la verificación o Lr& reconocimiento de las mercancías deberá citar dentro de un plazo razonable al importador o consignatario o al exportador para que asistan personalmente o por medio de apoderado a dicho reconocimiento.

2. `decreto-755-22.pdf` · Artículo 75 · «Verificación o reconocimiento de las mercancías» · p. 34

   > Para la verificación o reconocimiento físico de las mercancías se requerirá la presencia del importador, consignatario o exportador para que asistan personalmente o por medio de un apoderado o representante a dicho proceso. […] PÁRRAFO. En caso de que el importador, consignatario, exportador o su representante no comparezca al reconocimiento de la mercancía la DGA procederá con el proceso de verificación, concluido el mismo, les notificará el resultado.

**Part 2. ¿Quién asume los gastos de apertura, descarga e inspección del contenedor?**

**No candidate found.**

Searched for: gastos, costo, por cuenta de, correrán por cuenta, a cargo de, tasa por servicio, apertura del contenedor, descarga, manipulación, movilización, desconsolidación.

Nearest text, about a different situation. Not counted as a candidate:

1. `decreto-755-22.pdf` · Artículo 163 · (no title in the index; the text starts "ARTICULO 163. Plazos, requisitos y procedimientos para ampararse en …") · p. 80

   > PARRAFO 11. La Administración aduanera designará una comisión y coordinará una visita a las instalaciones del solicitante, para constatar y verificar lo solicitado, en cuyo caso el consignatario estará obligado al pago de las tasas por servicio brindado como resultado del proceso de traslado a sus instalaciones y verificación de las mercancías.

   Scope: A visit to the importer's premises after release, in the procedure for goods in excess or short.

2. `decreto-755-22.pdf` · Artículo 168 · «Solicitud de rectificación por tratarse de mercancías averiadas» · p. 83

   > Todos los gastos en que se incurran por concepto del servicio que brinde la Administración aduanera para confirmar la averia correrán por cuenta del declarante.

   Scope: Confirming damage to goods after release.

3. `norma-01-2023.pdf` · Artículo 1 · (no title in the index; the text starts "PRIMERO: En cumplimiento de lo que disponen el artículo …") · p. 6

   > VERIFICACIÓNES A DESTINO PARA CONTENEDORES 40' O 45' CON DISTANCIA DE 0-30 KM RD$ 3,750.00

   Scope: One line of the DGA fee table. The table has lines for verification "a destino" and "en origen" and for "DESPACHO CONTENEDORES IMPORTADOS", none for opening or unloading a container, and it does not say who pays.

Also read, not listed: Ley art. 13 num. 2 (DGA fees limited to the approximate cost of the service), art. 224, art. 226, art. 231 (inspection within eight hours); Decreto 755-22 art. 76, art. 172 (the acta is signed by customs and the declarant), art. 173 (inspection at the importer's premises).

### V10. Si necesitamos entregar urgentemente mercancía para la apertura de una tienda de un cliente, pero existe un problema de documentación con otro producto dentro del mismo contenedor, ¿podemos solicitar el levante parcial de la mercancía que está correctamente documentada?

Not found: No article speaks of releasing part of an import shipment. "Despachos parciales o fraccionados" exist only for exports (Ley art. 188, Decreto 755-22 art. 138). The candidates below are about release under guarantee when something is pending.

Searched for: levante parcial, parcial / parcialmente, fraccionado / fraccionamiento, retención / retenida, garantía.

1. `ley-168-21.pdf` · Artículo 96 · «Levante de las mercancías con garantía» · p. 80

   > La autoridad aduanera podrá autorizar el levante de las mercancías, previa rendición de garantía por el adeudo fiscal, cuando sea necesario demorar la determinación de la obligación tributaria aduanera o cuando se impugne mediante recurso administrativo el resultado de la determinación tributaria en el tiempo y forma que dispone esta ley. […] Párrafo I: El sujeto pasivo deberá rendir garantía suficiente por la parte discutida y cancelar los tributos correspondientes por la parte no discutida.

2. `ley-168-21.pdf` · Artículo 202 · «Declaración en partes o de diversos regímenes» · p. 127

   > No se aceptará en una misma declaración aduanera el fraccionamiento de mercancías para distintos regímenes cuando estén consignadas en una misma factura o documento de embarque, salvo en el caso de que se )r¡ trate de mercancías consolidadas.

   Scope: About splitting goods among regimes in one declaration, not about releasing part of them.

3. `decreto-755-22.pdf` · Artículo 83 · (no title in the index; the text starts "ARTÍCULO 83. El levante de las mercancías será admisible …") · p. 37

   > El levante de las mercancías será admisible previa rendición de garantía cuando se trate de aspectos relacionados a la determinación de la obligación tributaria aduanera. […] 1) Cuando sea necesario demorar la determinación del valor, la clasificación arancelaria, el origen o falte la presentación de documentos esenciales para el despacho aduanero.

Also read, not listed: Ley art. 95 and art. 239 (release once duties are paid and formalities met), art. 240; Decreto 755-22 art. 78 ("El levante de las mercancías es la regla, la retención es la excepción"), art. 84 to 86 (amount and procedure of the guarantee, cases where it is refused), art. 174 párr. I (cases where release within 24 hours is not guaranteed).

## Third stakeholder (P1 to P15)

### P1. Entiendo que el flete forma parte del valor CIF, pero ¿cuál es el fundamento legal para que se tribute sobre un servicio de transporte y no exclusivamente sobre el valor de la mercancía?

Not found: No article says that the taxable base is the CIF value, or that freight is part of it. "CIF" appears only in the rules for courier shipments (Decreto 755-22 arts. 177, 178 and 189).

Searched for: CIF, FOB, Incoterm, flete, seguro, base imponible, valor en aduana, valor aduanero, elementos cuantitativos.

1. `ley-168-21.pdf` · Artículo 80 · «Base imponible y su determinación» · p. 74

   > La base imponible en i la determinación de los tributos aduaneros será la que disponga la C legislación nacional. […] Párrafo I: Para los impuestos ad valorem se determinará conforme a los métodos establecidos en el Artículo VII sobre el Acuerdo del Valor de la OMC, así como los elementos cuantitativos previstos en la legislación nacional.

   Scope: Both sentences point elsewhere: to national legislation and to the WTO valuation agreement. Neither is in the index.

2. `ley-168-21.pdf` · Artículo 229 · «Verificación, aforo o inspección documental» · p. 140

   > Se deberá revisar la información contenida en la declaración, en ^^~~ relación con los siguientes aspectos: […] 7) Valor flete y seguro;

   Scope: What customs checks in the documentary review.

3. `decreto-755-22.pdf` · Artículo 148 · «Contenido de una declaración aduanera» · p. 65

   > 9) Informaciones vinculadas a la operación de compraventa internacional que forman parte de la Declaraeión del Valor en Aduanas (DVA), tales eomo: a) Término de eomercio internacional o "Incoterm" pactado. […] o) Gastos de entrega hasta el lugar de importación. p) Gastos de transporte por manejo y entrega en el exterior hasta el lugar de empaque, q) Gastos de transporte desde el lugar de embarque hasta lugar de importaeión. r) Gastos de carga, descarga y manipulación, s) Seguro.

   Scope: Data of the value declaration. The list runs from a) to x); the quote is its lead-in and items o) to s).

Also read, not listed: Ley art. 4 defs. 64 and 87 (obligación tributaria aduanera, valoración en Aduanas), art. 78 and art. 81 (the tax obligation and the event that gives rise to it); Decreto 755-22 art. 70 (value set "tomando en cuenta las disposiciones del Acuerdo del Valor GATT y el Reglamento de Valoración Aduanera"), art. 105 num. 2 lit. i (freight in the manifest), art. 160 num. 6.

### P2. ¿Hasta qué punto tiene Aduanas discrecionalidad para rechazar el valor de transacción cuando tenemos toda la documentación que acredita el precio pagado?

Not found: No article sets the grounds on which customs may reject a transaction value, or what documents rule a rejection out. The procedure and the valuation rules are named (Decreto 755-22 arts. 65 and 70) but are not in the index.

Searched for: valor de transacción, duda razonable, valor declarado, subvaluación, valoración, precio pagado, discrecional, razonabilidad.

1. `ley-168-21.pdf` · Artículo 80 · «Base imponible y su determinación» · p. 74

   > Párrafo I: Para los impuestos ad valorem se determinará conforme a los métodos establecidos en el Artículo VII sobre el Acuerdo del Valor de la OMC, así como los elementos cuantitativos previstos en la legislación nacional.

   Scope: Refers to the WTO valuation agreement, which is not in the index.

2. `ley-168-21.pdf` · Artículo 87 · «Autodeterminación» · p. 76

   > Autodeterminación es el acto mediante la presentación de la declaración aduanera, realizada por el consignatario, importador o agente Aduanal se establecerá la cuantía de la obligación tributaria aduanera y el pago de ios tributos'"' adeudados, conforme las disposiciones de la presente ley y suí reglamentos, presumiéndose siempre la buena fe del declarante.

   Scope: Said of the declarant's own determination of the tax.

3. `decreto-755-22.pdf` · Artículo 65 · «Dudas y hallazgos sobre el valor detectado en el curso de una fiscalización aduanera» · p. 32

   > Si en el marco del desarrollo de un procedimiento de fiscalización los órganos fiscalizadores poseen dudas sobre el valor declarado, deberán iniciar el procedimiento de duda razonable instaurado a tales efectos, el cual constituye un presupuesto procesal necesario para revisar, ajustar o negar el valor de transacción.

   Scope: Placed in the chapter on fiscalización. The "procedimiento de duda razonable" it names is not set out in any indexed article.

Also read, not listed: Ley art. 17 (customs powers exercised "en estricto apego de la presente ley"), art. 18 num. 27, art. 89 (revision of the determination), art. 238, art. 370 lit. c, art. 396 (appeals against any customs act, the determination included); Decreto 755-22 art. 31 (principles of the audit power: legality, reasonableness, objectivity, good faith), art. 33, art. 37 (evidence).

### P3. Si Aduanas utiliza valores de referencia para ajustar el valor de una mercancía, ¿está obligada a informarnos de dónde obtiene esos valores y cómo los determina?

Not found: No article mentions reference values, or the source or method of any value customs uses to adjust a declared value. The candidates below are general duties to give access to the file and to give reasons, most of them inside an audit.

Searched for: valores de referencia, precios de referencia, valores criterio, base de datos, banco de datos, acceso a la información, información pública, transparencia.

1. `ley-168-21.pdf` · Artículo 18 · «Atribuciones» · p. 34

   > Sin perjuicio de las facultades previstas en ésta y otras leyes, la Dirección General de Aduanas tendrá las siguientes atribuciones: […] 13) Velar por el cumplimiento de las disposiciones aplicables por Ley sobre el Derecho de Libre Acceso a la Información Pública;

   Scope: One of 38 listed powers of the DGA; the access-to-information law itself is not in the index.

2. `decreto-755-22.pdf` · Artículo 33 · «Derechos y garantías de los sujetos de fiscalización» · p. 16

   > La persona sujeta a la fiscalización tendrá derecho a: […] 3) Tener acceso al expediente administrativo con los elementos probatorios con que se cuente. […] 7) Obtener una resolución que ponga fin al procedimiento de fiscalización debidamente motivada, que incluya la valoración de las pruebas practicadas que constituyan los fundamentos de la decisión y que resuelva todas las cuestiones planteadas en el expediente dentro de plazo razonable, sin que se puedan aceptar hechos distintos de los determinados en el curso del procedimiento.

   Scope: Rights in a fiscalización procedure.

3. `decreto-755-22.pdf` · Artículo 59 · «De la resolución que decide la fiscalización posterior» · p. 28

   > PÁRRAFO II. Además de las informaeiones indicadas, la resolución deberá contener mínimamente las siguientes informaciones: […] 4) La valoración que se haga de los hechos, de la prueba y las circunstancias del caso.

   Scope: Content of the resolution that closes a post-clearance audit.

Also read, not listed: Ley art. 89 párr. II (the revision is notified in writing), art. 229 (data "que consten en los archivos o base de datos del servicio aduanero"); Decreto 755-22 art. 25 (a risk database, not a value database), art. 31 (transparency among the audit principles), art. 56 (preliminary report), art. 65, art. 74.

### P4. Cuando una inspección genera sobrecostos para el importador y no se detecta ninguna irregularidad, ¿existe algún mecanismo legal para reclamar esos gastos?

**No candidate found.**

Searched for: sobrecosto, costos adicionales, gastos, indemnización, daños y perjuicios, perjuicios ocasionados, resarcimiento, responsabilidad patrimonial, reclamar / reclamación, reembolso.

Nearest text, about a different situation. Not counted as a candidate:

1. `ley-168-21.pdf` · Artículo 18 · «Atribuciones» · p. 34

   > Sin perjuicio de las facultades previstas en ésta y otras leyes, la Dirección General de Aduanas tendrá las siguientes atribuciones: […] 14) Conocer y decidir de las solicitudes y reclamaciones presentadas por los interesados, de acuerdo con la legislación vigente;

   Scope: A general power to decide claims; it does not mention costs.

2. `ley-168-21.pdf` · Artículo 364 · «Notificación» · p. 203

   > Las medidas provisionales adoptadas por el funcionario de la autoridad aduanera deberán ser notificadas a la parte afectada, la cual de considerarla lesiva a sus intereses podrá interponer los recursos correspondientes, por ante el Tribunal Administrativo de lugar, la falta de notificación de la referida decisión no generará ningún efecto para la parte interesada y cualquier decisión que sea tomada sin el cumplimiento de este requisito podrá repercutir en daños directos por parte del funcionario actuante y en la nulidad de lo actuado.

   Scope: The only place where damages caused by an officer's act are mentioned. It is about provisional measures that were not notified, not about inspections.

3. `ley-168-21.pdf` · Artículo 396 · «Recursos administrativos y contenciosos» · p. 220

   > Cualquier acto administrativo dictado por Aduanas, incluyendo el resultado de la determinación tributaria, podrá ser objeto de los recursos administrativos, así como de los recursos contenciosos ante la Jurisdicción Contenciosa Administrativa, en la forma y plazos contemplados en la Ley núm. 107-13 del 8 de agosto de 2013, sobre los Derechos de las Personas en sus Relaciones con la Administración y de Procedimiento Administrativo y la Ley núm. 13-07 del 5 de febrero de 2007, que crea el Tribunal Contencioso Tributario y Administrativo, respectivamente.

   Scope: Appeals against customs acts, by reference to two laws that are not in the index.

Also read, not listed: Ley art. 97 párr. I (refund of duties and taxes charged in excess, not of costs), art. 231 párr. I (inspection within eight hours); Decreto 755-22 art. 163 párr. II and art. 168 (cases where the importer pays for a verification), art. 242 num. 7 (the operation must not be delayed disproportionately by a sanctioning procedure), art. 252 (provisional measures must not cause harm that cannot be repaired).

### P5. ¿Puede Aduanas cambiar el criterio de clasificación arancelaria de un producto que llevamos años importando bajo la misma partida sin haber cambiado sus características?

1. `ley-168-21.pdf` · Artículo 89 · «Revisión de la determinación» · p. 77

   > Dicha determinación tendrá carácter de provisionalidad y podrá ser modificada en el plazo de prescripción establecido en esta ley. […] Párrafo I: Cuando se haya determinado definitivamente uno o varios de los elementos que conforman la obligación tributaria aduanera, como resultado final del procedimiento de revisión o por sentencia judicial <-rt> í con autoridad de la cosa irrevocablemente juzgada, estos elementos no se podrán modificar posteriormente.

2. `ley-168-21.pdf` · Artículo 217 · «Carácter vinculante de las consultas anticipadas» · p. 133

   > Párrafo: La Autoridad Aduanera podrá cambiar de criterio respecto a una materia consultada. Este nuevo criterio deberá recogerse en una disposición publicada, que surtirá efecto respecto de todas las mercancías no declaradas a la fecha de su entrada en vigor.

   Scope: Said of criteria given in reply to an advance consultation.

3. `ley-168-21.pdf` · Artículo 356 · «Eximente de responsabilidad» · p. 196

   > 4) El error de derecho cuando se haya actuado conforme a los criterios de la autoridad aduanera competente establecidos a través de normas generales, publicaciones o cuando las conductas, actuaciones, acciones u omisiones del sujeto imputado como infractor actuare de acuerdo con lo establecido en una respuesta escrita a una consulta de la autoridad aduanera competente.

   Scope: One of the grounds that exempt from the penalty; párrafo I of the article says they do not excuse the tax.

Also read, not listed: Ley art. 20 num. 4 (controls after release, within the prescription period), art. 107 (three-year prescription), art. 212 num. 1 (advance rulings on classification), art. 370 lit. a (wrong classification as a falta tributaria); Decreto 755-22 art. 44, art. 162 num. 6. Nothing was found under precedente, confianza legítima or seguridad jurídica that bears on classification.

### P6. Si dos administraciones aduaneras aplican criterios distintos a una misma mercancía, ¿qué mecanismo existe para exigir que se unifique ese criterio?

Not found: No article provides a procedure to demand that two customs administrations apply the same criterion. The candidates below are the consultation that binds the DGA towards the person who asks, and the DGA's power to interpret the reglamento.

Searched for: unificar / unificación, uniforme, homogéneo, criterio, precedente, consulta, resolución anticipada.

1. `ley-168-21.pdf` · Artículo 212 · «Resoluciones anticipadas» · p. 131

   > Las resoluciones anticipadas son actos previos de naturaleza vinculante, mediante las cuales la autoridad aduanera competente resuelve consultas formuladas sobre: 1) Clasificación arancelaria;

   Scope: The article lists eight subjects; the quote is the lead-in and the first.

2. `ley-168-21.pdf` · Artículo 217 · «Carácter vinculante de las consultas anticipadas» · p. 133

   > La respuesta a las consultas previas presentadas surtirá efectos vinculantes para la Dirección General de Aduanas solo respecto al consultante, salvo que hayan cambiado la ley, los hechos o circunstancias que justifique esta respuesta.

3. `decreto-755-22.pdf` · Artículo 3 · «Autoridad» · p. 3

   > PÁRRAFO. La Dirección General de Aduanas (DGA) es el ente administrativo competente para interpretar, a efectos administrativos, los preceptos del presente Reglamento y para proveer todo cuanto se requiera para su aplicación, pudiendo adoptar y autorizar las medidas que fuesen necesarias atendiendo a parámetros de razonabilidad y en función de los casos que por su naturaleza ameriten un trato diferenciado, en razón de las circunstancias particulares que concurran ííáí^ en los mismos y que deberán ser ponderadas objetivamente por los funcionarios del área competente.

   Scope: About interpreting the reglamento.

Also read, not listed: Ley art. 18 nums. 14 and 16 (the DGA decides claims and answers consultations), art. 213 to 216, art. 356 num. 4 (a reply to someone else's consultation on the same facts exempts from the penalty), art. 396 (appeals); Decreto 755-22 art. 67 ("Interpretación homogénea": how the reglamento is to be read, not a mechanism).

### P7. ¿En qué circunstancias podemos solicitar el levante de una mercancía mediante una garantía mientras se resuelve una controversia con Aduanas?

1. `ley-168-21.pdf` · Artículo 96 · «Levante de las mercancías con garantía» · p. 80

   > La autoridad aduanera podrá autorizar el levante de las mercancías, previa rendición de garantía por el adeudo fiscal, cuando sea necesario demorar la determinación de la obligación tributaria aduanera o cuando se impugne mediante recurso administrativo el resultado de la determinación tributaria en el tiempo y forma que dispone esta ley. […] Párrafo I: El sujeto pasivo deberá rendir garantía suficiente por la parte discutida y cancelar los tributos correspondientes por la parte no discutida.

2. `decreto-755-22.pdf` · Artículo 83 · (no title in the index; the text starts "ARTÍCULO 83. El levante de las mercancías será admisible …") · p. 37

   > Dentro de las causas que justifican la exigibilidad de una garantía como condición para el levante de las mercancías, están las siguientes: […] 2) Cuando exista diferencia de tributos entre lo declarado por el sujeto pasivo y lo verificado por la Aduana y, como consecuencia, el sujeto pasivo impugne o recurra la liquidación o determinación efectuada por la Aduana.

   Scope: The article lists nine causes; the quote is the lead-in and the second.

3. `decreto-755-22.pdf` · Artículo 85 · «Casos en que no se autorizará el levante con la constitución de una garantía» · p. 38

   > La Aduana no admitirá el levante con garantía en los siguientes casos: […] 4) Cuando se inicie un procedimiento de fiscalización durante el proceso de despacho, y la retención de las mercancías sea necesaria para ejercer las labores de comprobación encaminada a una correcta determinación las obligaciones aduaneras y tributarias, o porque el levante constituya una amenaza a la vulneración de los bienes jurídicamente protegidos por ley.

   Scope: The article lists five cases where release under guarantee is refused; the quote is the lead-in and the fourth.

Also read, not listed: Ley art. 95, art. 117 to 120 (sufficiency, global guarantee, amount), art. 239; Decreto 755-22 art. 78, art. 79, art. 82 párr. IV (abandonment period suspended during a dispute), art. 84 (amount and type), art. 86 (request and reasoned reply), art. 87 (release of the guarantee), art. 155 (declaración supeditada).

### P8. ¿Hasta dónde llega la responsabilidad solidaria del importador por actuaciones u omisiones imputables exclusivamente al agente aduanal?

1. `ley-168-21.pdf` · Artículo 48 · «Responsabilidad» · p. 56

   > Los Agentes de Aduanas son responsables, salvo la exclusión de responsabilidad prevista en el artículo 50, del pago de los derechos e impuestos cuya aplicación y fiscalización corresponda a Aduanas, y del total del valor de las multas que resulten de faltas cometidas por su acción u omisión en los despachos y gestiones de representación a su cargo. Párrafo I: Los mandantes son responsables del pago de todos los derechos e impuestos cuya aplicación y fiscalización corresponda a Aduanas, cualquiera que sea su naturaleza y finalidad, así como del total del valor de las multas que resulten de las faltas cometidas en los despachos y gestiones de representación a cargo de los agentes de Aduanas, cuando se demuestre que se reúnan cualquiera de las condiciones eximentes de los agentes de Aduanas estipuladas por el artículo 50 de esta ley.

   Scope: Párrafo II of the same article uses the words "responsabilidad solidaria", for the agent when the act follows from the principal's.

2. `ley-168-21.pdf` · Artículo 375 · «Carácter personal de la responsabilidad por ilícitos aduaneros» · p. 210

   > En principio, las responsabilidades por los ilícitos son personales, salvo que la presente ley o cualquier otra disposición legal dispongan lo contrario.

3. `ley-168-21.pdf` · Artículo 378 · «Responsabilidad por sanciones a los empleados dependientes o representantes» · p. 211

   > Las personas físicas o jurídicas, sociedades, asociaciones y otras entidades colectivas serán solidariamente responsables de las sanciones pecuniarias que se apliquen a sus empleados, cualquier dependiente o sujeto autorizado que actúe como tal o en su representación, en el ejercicio de sus funciones. […] Párrafo: Esta responsabilidad solo tendrá lugar cuando los hechos cometidos por el empleado o dependiente sean en beneficio de su empleador o mandante.

Also read, not listed: Ley art. 40, art. 47, art. 49 (the agent's right to recover from the principal), art. 50 (when the agent is exempt), art. 79 (who the taxpayer is), art. 359 (the operator answers "con su representado"), art. 377.

### P9. Si Aduanas realiza una fiscalización posterior al despacho, ¿qué límites tiene respecto a operaciones que ya fueron inspeccionadas físicamente y aprobadas?

1. `ley-168-21.pdf` · Artículo 89 · «Revisión de la determinación» · p. 77

   > Dicha determinación tendrá carácter de provisionalidad y podrá ser modificada en el plazo de prescripción establecido en esta ley. […] Párrafo I: Cuando se haya determinado definitivamente uno o varios de los elementos que conforman la obligación tributaria aduanera, como resultado final del procedimiento de revisión o por sentencia judicial <-rt> í con autoridad de la cosa irrevocablemente juzgada, estos elementos no se podrán modificar posteriormente.

2. `ley-168-21.pdf` · Artículo 107 · «Prescripción» · p. 85

   > Las acciones para el cobro de la obligación tributaria aduanera prescriben en el plazo de tres (3) años, contados desde la fecha en que debió determinarse o cumplirse dicha obligación, así como sus intereses y recargos de cualquier naturaleza.

3. `decreto-755-22.pdf` · Artículo 44 · «Fundamento del procedimiento de fiscalización posterior» · p. 21

   > La potestad de llevar a cabo una fiscalización aduanera con posterioridad al despacho de las mercancías, descansa en la facultad de revisión que posee la DGA dentro del plazo de prescripción previsto en la ley y rm en el hecho de que la determinación de la obligación hecha en zona primaria aduanera posee un carácter de provisionalidad, que podrá tomarse definitiva, precisamente, una vez sea objeto del ejercicio del control posterior o haya prescrito el plazo para ejercer las acciones correspondientes tendentes al cobro de la obligación tributaria aduanera.

Also read, not listed: Ley art. 20 num. 4, art. 30, art. 201 (acceptance of the declaration "no limita las facultades de fiscalización"), art. 224 párr. I (inspection acts are fixed "sin perjuicio del ejercicio de los controles a posteriori"; it is a fourth article on the point, left out only because of the limit of three), art. 236; Decreto 755-22 art. 38 num. 3, art. 41, art. 45, art. 60, art. 62 (two-year maximum for the audit procedure), art. 235, art. 241 num. 5 (non bis in ídem, for sanctions).

### P10. ¿Qué gastos relacionados con el transporte internacional pueden excluirse legalmente del valor en aduana cuando están desglosados en la factura del flete?

**No candidate found.**

Searched for: excluir / excluido / exclusión, deducir / deducción, desglose / desglosado, flete, gastos de transporte, gastos adicionales, valor en aduana, valor aduanero.

Nearest text, about a different situation. Not counted as a candidate:

1. `ley-168-21.pdf` · Artículo 80 · «Base imponible y su determinación» · p. 74

   > Párrafo I: Para los impuestos ad valorem se determinará conforme a los métodos establecidos en el Artículo VII sobre el Acuerdo del Valor de la OMC, así como los elementos cuantitativos previstos en la legislación nacional.

   Scope: Says where the valuation method is, not what it includes or leaves out.

2. `decreto-755-22.pdf` · Artículo 148 · «Contenido de una declaración aduanera» · p. 65

   > q) Gastos de transporte desde el lugar de embarque hasta lugar de importaeión. r) Gastos de carga, descarga y manipulación, s) Seguro. t) Gastos de entregas postenores a la importación. u) Gastos de construcción, araiado, montaje, mantenimiento, asistencia técnica, realizados después de la importación. v) Derechos de aduanas y otros impuestos. w) Intereses.

   Scope: Items of the value data in the declaration. The article lists them without saying which are added to the value and which are left out.

Also read, not listed: Decreto 755-22 art. 105 num. 2 lit. i (the manifest states the total freight "incluyendo gastos adicionales relativos al transporte de la carga"), art. 160 num. 6 (declared freight and additional costs differ from the manifest), art. 70.

### P11. Si negociamos un descuento retroactivo con un proveedor por volumen anual de compras, ¿podemos solicitar una revisión del valor aduanero de las importaciones anteriores?

Not found: No article says whether a discount agreed after importation changes the customs value, or gives a procedure to revise the value of past imports for that reason. None of the six grounds for rectification in Decreto 755-22 art. 162 is a change of price.

Searched for: descuento, descuento retroactivo, nota de crédito, rebaja, revisión del valor, reembolso, restitución, rectificación.

1. `ley-168-21.pdf` · Artículo 97 · «De los cargos y reembolsos» · p. 80

   > Párrafo I: También se reembolsarán, previa solicitud del sujeto pasivo, dentro del plazo de prescripción establecido en esta ley, los derechos e impuestos que hayan sido cobrados de más, por error de aforo, de cálculo o de cualquier otra naturaleza que sea debidamente comprobada.

2. `ley-168-21.pdf` · Artículo 107 · «Prescripción» · p. 85

   > Prescribe en el mismo plazo la acción del sujeto pasivo ¿'i para reclamar la restitución de lo pagado indebidamente por tributos, intereses y recargos de cualquier naturaleza o solicitar el crédito respectivo, a partir del día siguiente a la fecha en que se efectuó el Xñ pago.

   Scope: "El mismo plazo" is the three years of the sentence before it.

3. `decreto-755-22.pdf` · Artículo 148 · «Contenido de una declaración aduanera» · p. 65

   > 9) Informaciones vinculadas a la operación de compraventa internacional que forman parte de la Declaraeión del Valor en Aduanas (DVA), tales eomo: […] h) Pagos directos, descuentos retroactivos u otros.

   Scope: A data item of the value declaration; the article gives no rule on its effect. It is the only mention of retroactive discounts in the index.

Also read, not listed: Ley art. 18 num. 22, art. 89, art. 98 num. 2 and arts. 104 to 106 (set-off of taxes paid in excess), art. 220; Decreto 755-22 art. 52 (credit notes among the documents an audit copies), art. 161 párr. II (rectification that leads to a refund or a credit), art. 162.

### P12. ¿En qué circunstancias está obligada Aduanas a motivar por escrito una decisión de retención, ajuste de valor o reclasificación arancelaria?

Not found: No article lays down a general duty to give written reasons for every customs decision. The duty appears decision by decision. The general administrative-procedure law the texts refer to (Ley 107-13) is not in the index.

Searched for: motivada / motivado / motivar / motivación, por escrito, resolución, retención, reclasificación, ajuste.

1. `ley-168-21.pdf` · Artículo 89 · «Revisión de la determinación» · p. 77

   > Párrafo II: La revisión será notificada por escrito al interesado en la forma y plazos establecidos en esta ley y sus reglamentos.

2. `ley-168-21.pdf` · Artículo 363 · «Medidas provisionales» · p. 202

   > Estas medidas provisionales podrán consistir en el cierre temporal de las operaciones de la empresa o del operador, la intervención e inspección, suspensión del acceso al sistema aduanero, entre otras. Dicha decisión debe ser motivada a través de una resolución y deberá contener los principales fundamentos en que se pretenda adoptar la misma.

   Scope: Provisional measures in a sanctioning procedure. Párrafo I allows an urgent measure without a written reasoned resolution, with four working days to notify the reasons.

3. `decreto-755-22.pdf` · Artículo 59 · «De la resolución que decide la fiscalización posterior» · p. 28

   > La Subdirección de Fiscalización dictará resolución debidamente motivada, de conformidad con las garantías constitucionales y del debido proceso, en función de los documentos, pruebas y alegaciones que obren en el expediente. […] 2) Base imponible. 3) Clasificación arancelaria y arancel.

   Scope: The resolution that closes a post-clearance audit; the two items are from the list of what it must contain.

Also read, not listed: Ley art. 18 num. 29 (goods retained "cuando haya evidencia comprobada"), art. 238 (differences notified within eight hours), art. 361 (reasoned act opening a sanctioning procedure), art. 364, art. 370 lit. a ("resolución motivada en firme"); Decreto 755-22 art. 33 num. 7, art. 74 (revision notified in writing within 24 working hours), art. 86 (reasoned reply to a request for release under guarantee), art. 121 párr. II, art. 172, art. 242 num. 6, art. 252 párrs. II and V, art. 256, art. 257.

### P13. ¿Qué consecuencias jurídicas tiene que Aduanas incumpla los plazos establecidos por la propia normativa?

Not found: No article gives a general rule on what follows when customs misses a deadline. A consequence is stated only for the three procedures below and for provisional measures. For other deadlines (release within 24 hours, inspection within eight hours, advance rulings within 30 days, replies to correction requests) none is stated.

Searched for: silencio, caducidad, se entenderá aceptada / aprobada / rechazada, no responde, sin respuesta, plazo razonable, nulidad.

1. `decreto-755-22.pdf` · Artículo 62 · «Plazo máximo de duración del procedimiento» · p. 30

   > La duración máxima del procedimiento administrativo de fiscalización posterior es de dos (2) años contados a partir de la notifieación del inicio del proeedimiento. Transcurrido el plazo previsto en este artículo sin que la autoridad encargada y competente realizare algún trámite esencial y se lo notificare a la persona rm objeto de la fiscalización, se procederá, de oficio o a instancia de la parte interesada, a declarar su caducidad y a ordenar el archivo del expediente.

   Scope: Párrafo II of the article adds that the lapse never operates automatically.

2. `decreto-755-22.pdf` · Artículo 146 · «De la prórroga del plazo para la presentación de la declaración» · p. 63

   > PÁRRAFO III. Esta solicitud de plazo debe ser aprobada o aceptada por el administrador de Aduanas de la jurisdicción de competencia a más tardar dos (2) días hábiles luego de la presentación de la solicitud. Si la Administración no responde en el plazo indicado, se entenderá aceptada la solicitud.

   Scope: The request to extend the deadline for declaring.

3. `decreto-755-22.pdf` · Artículo 260 · «Plazo máximo de duración del procedimiento» · p. 114

   > La duración máxima del procedimiento administrativo sancionador ordinario es de ciento veinte (120) días hábiles contados a partir de la notificación del acto de apertura del procedimiento. Transcurrido el plazo previsto en este artículo sin que la autoridad encargada y competente realizare algún trámite esencial y se lo ríáí^ notificare al presunto infractor, se procederá, de oficio o a instancia de la parte interesada, a declarar su caducidad y a ordenar el archivo del expediente.

   Scope: Párrafo II of the article adds that the lapse never operates automatically.

Also read, not listed: Ley art. 215 párrafo, art. 231 párr. I, art. 238, art. 240, art. 363 párr. I, art. 364 (a provisional measure that is not notified has no effect and what was done is null); Decreto 755-22 art. 125, art. 143 párr. III, art. 174, art. 252 párr. IV (provisional measures lapse), art. 256, art. 265.

### P14. ¿Qué carácter vinculante tiene una resolución anticipada de clasificación arancelaria y en qué circunstancias puede Aduanas dejar de aplicarla?

1. `ley-168-21.pdf` · Artículo 212 · «Resoluciones anticipadas» · p. 131

   > Las resoluciones anticipadas son actos previos de naturaleza vinculante, mediante las cuales la autoridad aduanera competente resuelve consultas formuladas sobre: 1) Clasificación arancelaria;

   Scope: The article lists eight subjects; the quote is the lead-in and the first.

2. `ley-168-21.pdf` · Artículo 214 · «Formalidades de las consultas» · p. 132

   > Párrafo II: No tendrá efecto la respuesta a una consulta emitida sobre la base de datos incompletos, inexactos, falsos o engañosos proporcionados por el interesado.

3. `ley-168-21.pdf` · Artículo 217 · «Carácter vinculante de las consultas anticipadas» · p. 133

   > La respuesta a las consultas previas presentadas surtirá efectos vinculantes para la Dirección General de Aduanas solo respecto al consultante, salvo que hayan cambiado la ley, los hechos o circunstancias que justifique esta respuesta. […] Párrafo: La Autoridad Aduanera podrá cambiar de criterio respecto a una materia consultada. Este nuevo criterio deberá recogerse en una disposición publicada, que surtirá efecto respecto de todas las mercancías no declaradas a la fecha de su entrada en vigor.

Also read, not listed: Ley art. 213 (who may ask), art. 214 párr. III, art. 215 (in writing, within 30 days), art. 216 (when a ruling may be refused), art. 356 num. 4.

### P15. ¿Qué beneficios concretos y jurídicamente exigibles tendría Display al certificarse como Operador Económico Autorizado, más allá de las facilidades operativas habituales?

1. `ley-168-21.pdf` · Artículo 407 · «Beneficios de la certificación como operador económico autorizado» · p. 225

   > La Dirección General de Aduanas podrá, sin que la presente lista sea limitativa, otorgar uno o más de los siguientes beneficios: 1) Requisitos reducidos de documentación y datos; 2) Bajo índice de inspecciones físicas y exámenes; 3) Levante rápido, según proceda; 4) Pago diferido de los derechos, impuestos, tasas y cargas hasta por un plazo de quince (15) días. En este caso se cobrará un uno por ciento (1%) del valor aduanero de la mercancía; 5) Utilización de garantías globales o reducción de las garantías; 6) Una sola declaración de Aduana para todas las importaciones o exportaciones realizadas en un período dado; y, 7) Despacho de las mercancías en los locales del operador autorizado o en otro lugar autorizado por la Aduana.

   Scope: The whole list is one sentence.

2. `decreto-755-22.pdf` · Artículo 299 · (no title in the index; the text starts "ARTÍCULO 299. Las personas físicas o morales certificadas como …") · p. 129

   > Las personas físicas o morales certificadas como Operador Económico Autorizado podrán beneficiarse de las simplificaciones en los trámites y facilitación en los controles en zona primaria aduanera, que ban de ser establecidos por las autoridades reguladoras del comercio exterior, en función de las actividades del operador.

3. `decreto-755-22.pdf` · Artículo 305 · «De las obligaciones de las autoridades de control» · p. 131

   > 6) Garantizar a los Operadores Económicos Autorizados el disfrute de los beneficios otorgados a raíz de la expedición de la autorización. […] PÁRRAFO. La DGA, en conjunto con las instituciones señaladas en el artículo 304, deberá elaborar un protocolo que permita establecer las facilidades y beneficios que serán otorgadas a las empresas certificadas DEA.

   Scope: Duties of the control authorities that take part in the certification.

Also read, not listed: Ley art. 404 to 406 and art. 408; Decreto 755-22 art. 22 (OEA declarations stay subject to checks), art. 72 (autodeterminación), art. 151 num. 1 and art. 152 (incomplete declaration), art. 173 (inspection at the operator's premises), art. 220 and art. 221 (courier companies that are OEA), art. 252 párr. I num. 4 (the certification can be suspended as a provisional measure), art. 287, art. 297, art. 298, art. 300, art. 301 (benefits "sin perjuicio de las facultades legales" of the control bodies), art. 302.
